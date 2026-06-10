import os
import sys
import subprocess

# Add parent directory to sys.path to import centralized_metrics_logger
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

import centralized_metrics_logger
from attack import attackSelection
from monitor import setupLogging

if __name__ == "__main__":
    print("Select an option:")
    print("1. Attacker")
    print("2. Logger")
    print("3. Metrics Capture")
    choice = input("Type 1, 2, or 3: ")
    print("")
    while choice not in ["1", "2", "3"]:
        print("Not a valid choice try again!")
        choice = input("Type 1, 2, or 3: ")
        print("")

    if choice == "1":
        attackSelection.run()
    elif choice == "2":
        setupLogging.start_monitor_device_logging()
    elif choice == "3":
        print("Select an option:")
        print("1. ESP32 Metrics Capture")
        print("2. Router Metrics Capture")
        print("3. All of the above (make sure you're on the router's network)")
        choice = input("Type 1, 2, or 3: ")
        print("")
        while choice not in ["1", "2", "3"]:
            print("Not a valid choice try again!")
            choice = input("Type 1, 2, or 3: ")
            print("")

        if choice == "1":
            client_port = input("Enter client serial port (leave blank if none): ").strip()
            server_port = input("Enter server serial port (leave blank if none): ").strip()
            
            script_path = os.path.join(os.path.dirname(__file__), "..", "mm-iot-esp32", "capture_esp32_metrics.py")
            cmd = [sys.executable, os.path.abspath(script_path)]
            
            if client_port:
                cmd.extend(["--client-port", client_port])
            if server_port:
                cmd.extend(["--server-port", server_port])
            
            if not client_port and not server_port:
                print("You must specify at least one port.")
            else:
                try:
                    subprocess.run(cmd)
                except KeyboardInterrupt:
                    print("\nMetrics capture stopped.")
        elif choice == "2":
            router_ip = input("Enter router IP (leave blank for default 192.168.0.100): ").strip()
            router_user = input("Enter SSH username (leave blank for default root): ").strip()
            router_pass = input("Enter SSH password (leave blank for default heltec.org): ").strip()
            
            script_path = os.path.join(os.path.dirname(__file__), "..", "capture_router_metrics.py")
            cmd = [sys.executable, os.path.abspath(script_path)]
            
            if router_ip:
                cmd.extend(["--ip", router_ip])
            if router_user:
                cmd.extend(["--user", router_user])
            if router_pass:
                cmd.extend(["--password", router_pass])
                
            try:
                subprocess.run(cmd)
            except KeyboardInterrupt:
                print("\nRouter metrics capture stopped.")
        elif choice == "3":
            ml_logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "monitor", "MLLogs")
            
            args_list = [
                "--router-output", os.path.join(ml_logs_dir, "router_metrics.csv"),
                "--client-output", os.path.join(ml_logs_dir, "client_metrics.csv"),
                "--server-output", os.path.join(ml_logs_dir, "server_metrics.csv")
            ]
            
            centralized_metrics_logger.main(args_list)
