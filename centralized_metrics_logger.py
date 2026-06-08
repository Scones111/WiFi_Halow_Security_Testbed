import socket
import paramiko
import time
import argparse
import csv
import sys
import os
import re
import threading
import json
import signal

# Global flag to control threads
running = True

# --- Router Metrics SSH Logic ---
def get_router_metrics(ssh_client):
    try:
        stdin, stdout, stderr = ssh_client.exec_command("cat /proc/stat /proc/meminfo", timeout=2)
        return stdout.read().decode('utf-8')
    except Exception as e:
        print(f"[ROUTER] Error fetching data via SSH: {e}")
        return None

def parse_cpu_stats(raw_data):
    for line in raw_data.split('\n'):
        if line.startswith("cpu "):
            parts = line.split()
            values = [int(p) for p in parts[1:] if p.isdigit()]
            if len(values) >= 4:
                idle = values[3]
                iowait = values[4] if len(values) > 4 else 0
                total_idle = idle + iowait
                total_time = sum(values)
                return total_time, total_idle
    return None, None

def parse_ram_stats(raw_data):
    mem_total = 0
    mem_free = 0
    buffers = 0
    cached = 0
    mem_available = None
    
    for line in raw_data.split('\n'):
        if line.startswith("MemTotal:"):
            mem_total = int(re.sub(r'\D', '', line))
        elif line.startswith("MemFree:"):
            mem_free = int(re.sub(r'\D', '', line))
        elif line.startswith("MemAvailable:"):
            mem_available = int(re.sub(r'\D', '', line))
        elif line.startswith("Buffers:"):
            buffers = int(re.sub(r'\D', '', line))
        elif line.startswith("Cached:"):
            cached = int(re.sub(r'\D', '', line))
            
    if mem_total == 0:
        return 0.0
        
    if mem_available is not None:
        used = mem_total - mem_available
    else:
        used = mem_total - mem_free - buffers - cached
        
    return (used / mem_total) * 100.0

def router_thread_func(args):
    global running
    
    # Setup Router CSV
    os.makedirs(os.path.dirname(os.path.abspath(args.router_output)), exist_ok=True)
    router_csv_file = open(args.router_output, mode='a', newline='')
    router_fieldnames = ["host_timestamp", "local_time", "cpu_used_pct", "ram_used_pct"]
    router_writer = csv.DictWriter(router_csv_file, fieldnames=router_fieldnames)
    
    if router_csv_file.tell() == 0:
        router_writer.writeheader()
        
    print(f"[ROUTER] Logging metrics to {args.router_output}")
    
    # Connect SSH
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(args.ip, username=args.user, password=args.password, timeout=5)
        print(f"[ROUTER] Successfully connected to {args.user}@{args.ip}")
    except Exception as e:
        print(f"[ROUTER] Failed to connect to router: {e}")
        running = False
        return
        
    prev_total_time = 0
    prev_idle_time = 0

    try:
        while running:
            start_time = time.time()
            raw_data = get_router_metrics(ssh)
            
            if raw_data:
                total_time, idle_time = parse_cpu_stats(raw_data)
                cpu_usage = 0.0
                if total_time is not None and prev_total_time != 0:
                    total_delta = total_time - prev_total_time
                    idle_delta = idle_time - prev_idle_time
                    if total_delta > 0:
                        cpu_usage = 100.0 * (1.0 - (idle_delta / total_delta))
                if total_time is not None:
                    prev_total_time = total_time
                    prev_idle_time = idle_time
                
                ram_usage = parse_ram_stats(raw_data)
                
                host_time = time.time()
                metrics = {
                    "host_timestamp": host_time,
                    "local_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(host_time)),
                    "cpu_used_pct": round(cpu_usage, 2),
                    "ram_used_pct": round(ram_usage, 2)
                }
                
                router_writer.writerow(metrics)
                router_csv_file.flush()
                
                print(f"[ROUTER] Capt -> CPU: {cpu_usage:>5.2f}% | RAM: {ram_usage:>5.2f}%")
                
            elapsed = time.time() - start_time
            sleep_time = args.interval - elapsed
            if sleep_time > 0:
                # Sleep in small chunks to remain responsive to 'running' flag
                for _ in range(int(sleep_time * 10)):
                    if not running:
                        break
                    time.sleep(0.1)
    finally:
        ssh.close()
        router_csv_file.close()
        print("[ROUTER] Disconnected and file closed.")

# --- UDP Server Logic for ESP32 ---
def udp_thread_func(args):
    global running
    
    # Setup ESP32 CSVs
    os.makedirs(os.path.dirname(os.path.abspath(args.client_output)), exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(args.server_output)), exist_ok=True)
    
    client_csv_file = open(args.client_output, mode='a', newline='')
    server_csv_file = open(args.server_output, mode='a', newline='')
    
    esp_fieldnames = ["host_timestamp", "local_time", "device", "esp32_uptime_us", "cpu_used_pct", "ram_used_pct", "tcp_disconnects"]
    
    client_writer = csv.DictWriter(client_csv_file, fieldnames=esp_fieldnames)
    server_writer = csv.DictWriter(server_csv_file, fieldnames=esp_fieldnames)
    
    if client_csv_file.tell() == 0: client_writer.writeheader()
    if server_csv_file.tell() == 0: server_writer.writeheader()
        
    print(f"[ESP32] Logging CLIENT metrics to {args.client_output}")
    print(f"[ESP32] Logging SERVER metrics to {args.server_output}")

    # Setup UDP Socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", args.udp_port))
    sock.settimeout(1.0)
    print(f"[UDP] Listening for ESP32 metrics on port {args.udp_port}...")

    try:
        while running:
            try:
                data, addr = sock.recvfrom(1024)
                host_time = time.time() # Synchronize timestamp immediately
                
                payload_str = data.decode('utf-8').strip()
                try:
                    payload = json.loads(payload_str)
                    
                    device = payload.get("device", "unknown")
                    metrics = {
                        "host_timestamp": host_time,
                        "local_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(host_time)),
                        "device": device,
                        "esp32_uptime_us": payload.get("esp32_uptime_us", 0),
                        "cpu_used_pct": payload.get("cpu_used_pct", 0.0),
                        "ram_used_pct": payload.get("ram_used_pct", 0.0),
                        "tcp_disconnects": payload.get("tcp_disconnects", 0)
                    }
                    
                    if device == "client":
                        client_writer.writerow(metrics)
                        client_csv_file.flush()
                        print(f"[CLIENT] Capt -> CPU: {metrics['cpu_used_pct']:>5.2f}% | RAM: {metrics['ram_used_pct']:>5.2f}% | Drops: {metrics['tcp_disconnects']}")
                    elif device == "server":
                        server_writer.writerow(metrics)
                        server_csv_file.flush()
                        print(f"[SERVER] Capt -> CPU: {metrics['cpu_used_pct']:>5.2f}% | RAM: {metrics['ram_used_pct']:>5.2f}% | Drops: {metrics['tcp_disconnects']}")
                    else:
                        print(f"[UDP] Unknown device payload: {payload_str}")
                        
                except json.JSONDecodeError:
                    print(f"[UDP] Malformed JSON received from {addr}: {payload_str}")
                    
            except socket.timeout:
                continue # Timeout just to check the 'running' flag
            except Exception as e:
                print(f"[UDP] Error receiving data: {e}")
                
    finally:
        sock.close()
        client_csv_file.close()
        server_csv_file.close()
        print("[UDP] Server stopped and files closed.")

def signal_handler(sig, frame):
    global running
    print("\n[MAIN] Shutting down...")
    running = False

def main():
    parser = argparse.ArgumentParser(description="Centralized Network Logging for ESP32 and Heltec AP Metrics")
    
    # Heltec AP args
    parser.add_argument("--ip", default="192.168.0.100", help="Heltec AP IP address (default: 192.168.0.100)")
    parser.add_argument("--user", default="root", help="Heltec AP SSH username (default: root)")
    parser.add_argument("--password", default="heltec.org", help="Heltec AP SSH password (default: heltec.org)")
    parser.add_argument("--router-output", default="router_logs/router_metrics.csv", help="Router output CSV (default: router_logs/router_metrics.csv)")
    parser.add_argument("-i", "--interval", type=float, default=5.0, help="Router polling interval in seconds (default: 5.0)")
    
    # ESP32 args
    parser.add_argument("--udp-port", type=int, default=5005, help="UDP port to listen on for ESP32 metrics (default: 5005)")
    parser.add_argument("--client-output", default="logs/client_metrics.csv", help="ESP32 Client output CSV (default: logs/client_metrics.csv)")
    parser.add_argument("--server-output", default="logs/server_metrics.csv", help="ESP32 Server output CSV (default: logs/server_metrics.csv)")

    args = parser.parse_args()

    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("[MAIN] Starting Centralized Metrics Logger...")

    # Start threads
    router_thread = threading.Thread(target=router_thread_func, args=(args,))
    udp_thread = threading.Thread(target=udp_thread_func, args=(args,))

    router_thread.start()
    udp_thread.start()

    # Wait for threads to finish
    router_thread.join()
    udp_thread.join()

    print("[MAIN] Shutdown complete.")

if __name__ == "__main__":
    main()
