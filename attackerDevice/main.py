import os
import sys
import subprocess
import json

# Add parent directory to sys.path to import centralized_metrics_logger
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

import centralized_metrics_logger
from attack import attackSelection
from monitor import setupLogging

if __name__ == "__main__":
    print("Select an option:")
    print("1. Attack")
    print("2. Attack and Capture traffic logs")
    print("3. Metrics Capture")
    print("4. Capture Base Network")
    choice = input("Type 1, 2, 3 or 4: ")
    print("")
    while choice not in ["1", "2", "3", "4"]:
        print("Not a valid choice try again!")
        choice = input("Type 1, 2, 3 or 4: ")
        print("")

    if choice == "1":
        attackSelection.run()
    elif choice == "2":
        setupLogging.start_log()
        attackSelection.run()
        setupLogging.end_log()
        setupLogging.post_process()
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

        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
        except FileNotFoundError:
            print(f"Error: Configuration file {config_path} not found.")
            config = {}

        if choice == "1":
            client_port = config.get("client_port", "")
            server_port = config.get("server_port", "")
            
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
            router_config = config.get("router", {})
            router_ip = router_config.get("ip", "192.168.0.100")
            router_user = router_config.get("user", "root")
            router_pass = router_config.get("pass", "heltec.org")
            
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
            output_config = config.get("output_files", {})
            
            def resolve_path(path_str, default_name):
                if not path_str:
                    return os.path.join(ml_logs_dir, default_name)
                if os.path.isabs(path_str):
                    return path_str
                return os.path.join(os.path.dirname(os.path.abspath(__file__)), path_str)
            
            args_list = [
                "--router-output", resolve_path(output_config.get("router"), "router_metrics.csv"),
                "--client-output", resolve_path(output_config.get("client"), "client_metrics.csv"),
                "--server-output", resolve_path(output_config.get("server"), "server_metrics.csv")
            ]
            
            centralized_metrics_logger.main(args_list)
    elif choice == "4":
        setupLogging.start_log()
        input("Press enter to stop monitoring:")
        setupLogging.end_log()
        setupLogging.post_process()

