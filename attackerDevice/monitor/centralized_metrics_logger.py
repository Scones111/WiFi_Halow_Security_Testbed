import os
import sys
import subprocess
import time

def start_logging():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    esp32_script = os.path.join(base_dir, "capture_esp32_metrics.py")
    router_script = os.path.join(base_dir, "capture_router_metrics.py")
    
    print("Starting Centralized Metrics Logger...")
    
    # We use subprocess.Popen to run both concurrently
    try:
        esp_process = subprocess.Popen([sys.executable, os.path.abspath(esp32_script)])
        router_process = subprocess.Popen([sys.executable, os.path.abspath(router_script)])
        return esp_process, router_process
    except Exception as e:
        print(f"Failed to start metric captures: {e}")
        return None, None
