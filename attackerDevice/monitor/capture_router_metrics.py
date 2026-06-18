import paramiko
import time
import json
import csv
import sys
import os
import re

def get_router_metrics(ssh_client):
    """
    Executes a single SSH command to fetch both CPU and RAM stats.
    Returns raw text output.
    """
    try:
        # We cat both files in one command to minimize SSH overhead
        stdin, stdout, stderr = ssh_client.exec_command("cat /proc/stat /proc/meminfo", timeout=2)
        return stdout.read().decode('utf-8')
    except Exception as e:
        print(f"Error fetching data via SSH: {e}")
        return None

def parse_cpu_stats(raw_data):
    """
    Parses /proc/stat to calculate total and idle CPU times.
    """
    for line in raw_data.split('\n'):
        if line.startswith("cpu "):
            parts = line.split()
            # /proc/stat values: user, nice, system, idle, iowait, irq, softirq, steal, guest, guest_nice
            # We convert all valid numeric fields to integers
            values = [int(p) for p in parts[1:] if p.isdigit()]
            
            if len(values) >= 4:
                idle = values[3]
                iowait = values[4] if len(values) > 4 else 0
                
                total_idle = idle + iowait
                total_time = sum(values)
                return total_time, total_idle
    return None, None

def parse_ram_stats(raw_data):
    """
    Parses /proc/meminfo to calculate RAM usage percentage.
    """
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
        
    # Prefer MemAvailable if present (modern Linux)
    if mem_available is not None:
        used = mem_total - mem_available
    else:
        # Fallback for older kernels
        used = mem_total - mem_free - buffers - cached
        
    return (used / mem_total) * 100.0

def main():
    config_path = os.path.join(os.path.dirname(__file__), "..", "devices.json")
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file {os.path.abspath(config_path)} not found.")
        sys.exit(1)

    router_config = config.get("TrustedAP", [{}])[0]
    router_ip = router_config.get("ip", "192.168.0.100")
    router_user = router_config.get("user", "root")
    router_pass = router_config.get("pass", "heltec.org")
    
    metrics_config = config.get("MetricsCapture", {})
    attacker_device_dir = os.path.join(os.path.dirname(__file__), "..")
    
    timestamp_str = time.strftime("%Y%m%d_%H%M")
    output_folder = os.path.join(attacker_device_dir, metrics_config.get("output_folder", "../logs/metrics/"), f"{timestamp_str}/")
    output_file = os.path.join(output_folder, "router_metrics.csv")
    
    interval = metrics_config.get("polling_interval", 5.0)
    
    # Setup CSV Logging
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    csv_file = open(output_file, mode='a', newline='')
    fieldnames = ["host_timestamp", "local_time", "cpu_used_pct", "ram_used_pct"]
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    
    if csv_file.tell() == 0:
        writer.writeheader()
        
    abs_path = os.path.abspath(output_file)
    print(f"[ROUTER] Logging metrics to {abs_path}")
    
    # Connect via SSH
    print(f"[ROUTER] Connecting to {router_user}@{router_ip}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(router_ip, username=router_user, password=router_pass, timeout=5)
        print("[ROUTER] Successfully connected!")
    except Exception as e:
        print(f"Failed to connect to router: {e}")
        sys.exit(1)
        
    prev_total_time = 0
    prev_idle_time = 0
    
    print("\nStarting capture... Press Ctrl+C to stop.\n")
    
    try:
        while True:
            start_time = time.time()
            
            # Fetch raw data
            raw_data = get_router_metrics(ssh)
            
            if raw_data:
                # Parse CPU
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
                
                # Parse RAM
                ram_usage = parse_ram_stats(raw_data)
                
                # Log to CSV
                metrics = {
                    "host_timestamp": time.time(),
                    "local_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "cpu_used_pct": round(cpu_usage, 2),
                    "ram_used_pct": round(ram_usage, 2)
                }
                
                writer.writerow(metrics)
                csv_file.flush()
                
                print(f"[ROUTER] Captured => CPU: {cpu_usage:>5.2f}% | RAM: {ram_usage:>5.2f}%")
            
            # Sleep precisely to match the interval
            elapsed = time.time() - start_time
            sleep_time = interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
                
    except KeyboardInterrupt:
        print("\nStopping capture...")
    finally:
        ssh.close()
        csv_file.close()
        print("[ROUTER] SSH connection and file closed.")

if __name__ == "__main__":
    main()
