import paramiko
import time
import argparse
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
    parser = argparse.ArgumentParser(description="Capture CPU/RAM metrics from Heltec Router via SSH")
    parser.add_argument("--ip", default="192.168.0.100", help="Router IP address (default: 192.168.0.100)")
    parser.add_argument("--user", default="root", help="SSH username (default: root)")
    parser.add_argument("--password", default="heltec.org", help="SSH password (default: heltec.org)")
    parser.add_argument("-o", "--output", default="router_logs/router_metrics.csv", help="Output CSV file (default: router_logs/router_metrics.csv)")
    parser.add_argument("-i", "--interval", type=float, default=5.0, help="Polling interval in seconds (default: 5.0)")
    
    args = parser.parse_args()
    
    # Setup CSV Logging
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    csv_file = open(args.output, mode='a', newline='')
    fieldnames = ["host_timestamp", "local_time", "cpu_used_pct", "ram_used_pct"]
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    
    if csv_file.tell() == 0:
        writer.writeheader()
        
    abs_path = os.path.abspath(args.output)
    print(f"[ROUTER] Logging metrics to {abs_path}")
    
    # Connect via SSH
    print(f"[ROUTER] Connecting to {args.user}@{args.ip}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(args.ip, username=args.user, password=args.password, timeout=5)
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
            sleep_time = args.interval - elapsed
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
