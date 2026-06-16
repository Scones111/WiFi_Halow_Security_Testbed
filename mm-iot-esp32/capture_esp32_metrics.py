import serial
import re
import csv
import argparse
import sys
import time
import os

def parse_ml_data(line):
    """
    Parses a line like:
    I (12345) ML_DATA: Timestamp: 12345678, CPU_Used: 1.25%, RAM_Used: 45.30%, TCP_Disconnects: 2
    """
    if "ML_DATA" not in line:
        return None
    
    # Regex to extract the metrics
    pattern = r"Timestamp:\s*(\d+),\s*CPU_Used:\s*([\d\.]+)%,\s*RAM_Used:\s*([\d\.]+)%,\s*Throughput:\s*([\d\.]+)\s*bps,\s*TCP_Disconnects:\s*(\d+)"
    match = re.search(pattern, line)
    
    if match:
        return {
            "timestamp_us": int(match.group(1)),
            "cpu_used_pct": float(match.group(2)),
            "ram_used_pct": float(match.group(3)),
            "throughput_bps": float(match.group(4)),
            "tcp_disconnects": int(match.group(5))
        }
    return None

def setup_device(port, baud, output_file, device_name):
    try:
        ser = serial.Serial(port, baud, timeout=0.1)
        print(f"[{device_name.upper()}] Connected to {port} at {baud} baud.")
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        
        csv_file = open(output_file, mode='a', newline='')
        fieldnames = ["host_timestamp", "local_time", "esp32_uptime_us", "cpu_used_pct", "ram_used_pct", "throughput_bps", "tcp_disconnects"]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        
        if csv_file.tell() == 0:
            writer.writeheader()
            
        print(f"[{device_name.upper()}] Logging metrics to {output_file}")
        
        return {
            "name": device_name,
            "ser": ser,
            "csv_file": csv_file,
            "writer": writer
        }
    except serial.SerialException as e:
        print(f"Error opening serial port for {device_name}: {e}")
        return None
    except Exception as e:
        print(f"Error setting up logging for {device_name}: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Capture ESP32 ML_DATA metrics from serial ports simultaneously")
    parser.add_argument("--client-port", help="Serial port for the Client ESP32")
    parser.add_argument("--server-port", help="Serial port for the Server ESP32")
    parser.add_argument("-b", "--baud", type=int, default=115200, help="Baud rate (default: 115200)")
    parser.add_argument("--client-output", default="logs/client_metrics.csv", help="Output CSV for Client (default: logs/client_metrics.csv)")
    parser.add_argument("--server-output", default="logs/server_metrics.csv", help="Output CSV for Server (default: logs/server_metrics.csv)")
    
    args = parser.parse_args()
    
    if not args.client_port and not args.server_port:
        parser.error("You must specify at least one of --client-port or --server-port")
        
    devices = []
    
    if args.client_port:
        dev = setup_device(args.client_port, args.baud, args.client_output, "client")
        if dev: devices.append(dev)
            
    if args.server_port:
        dev = setup_device(args.server_port, args.baud, args.server_output, "server")
        if dev: devices.append(dev)
        
    if not devices:
        print("No devices were successfully connected. Exiting.")
        sys.exit(1)
        
    print("\nStarting capture... Press Ctrl+C to stop.\n")
    
    try:
        while True:
            for dev in devices:
                if dev["ser"].in_waiting > 0:
                    try:
                        # Decode with replacement to avoid crashing on malformed serial bytes
                        line = dev["ser"].readline().decode('utf-8', errors='replace').strip()
                        if line:
                            metrics = parse_ml_data(line)
                            if metrics:
                                # Add host machine's absolute time to sync with Wireshark!
                                metrics["host_timestamp"] = time.time()  # High precision UNIX epoch
                                metrics["local_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
                                
                                # Rename timestamp_us to esp32_uptime_us for clarity
                                metrics["esp32_uptime_us"] = metrics.pop("timestamp_us")
                                
                                dev["writer"].writerow(metrics)
                                dev["csv_file"].flush()
                                
                                print(f"[{dev['name'].upper():<6}] CPU: {metrics['cpu_used_pct']:>5.2f}% | RAM: {metrics['ram_used_pct']:>5.2f}% | Throughput: {metrics['throughput_bps']:>7.2f} bps | Drops: {metrics['tcp_disconnects']}")
                    except Exception as e:
                        print(f"Error reading from {dev['name']}: {e}")
                        
            # Short sleep to prevent CPU hogging
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print("\nStopping capture...")
    finally:
        for dev in devices:
            dev["ser"].close()
            dev["csv_file"].close()
            print(f"[{dev['name'].upper()}] Serial port and file closed.")

if __name__ == "__main__":
    main()
