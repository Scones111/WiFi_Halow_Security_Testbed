import serial
import re
import csv
import json
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
    config_path = os.path.join(os.path.dirname(__file__), "..", "attackerDevice", "devices.json")
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file {os.path.abspath(config_path)} not found.")
        sys.exit(1)

    stas = config.get("STA", [])
    
    metrics_config = config.get("MetricsCapture", {})
    baud = metrics_config.get("baudrate", 115200)
    
    attacker_device_dir = os.path.join(os.path.dirname(__file__), "..", "attackerDevice")
    timestamp_str = time.strftime("%Y%m%d_%H%M")
    output_folder = os.path.join(attacker_device_dir, metrics_config.get("output_folder", "../logs/metrics/"), f"{timestamp_str}/")
    
    if not stas:
        print("Error: No STA devices found in devices.json")
        sys.exit(1)
        
    devices = []
    
    for sta in stas:
        port = sta.get("serial_port")
        name = sta.get("name", "unknown_sta")
        
        if port:
            output_file = os.path.join(output_folder, f"{name}_metrics.csv")
            dev = setup_device(port, baud, output_file, name)
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
