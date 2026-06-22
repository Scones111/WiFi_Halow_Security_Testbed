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

    print("\nCapturing metrics from both sources... Press Ctrl+C to stop.\n")
    
    try:
        while True:
            time.sleep(1)
            # If both processes have exited for some reason, we can stop
            if esp_process.poll() is not None and router_process.poll() is not None:
                print("Both capture processes have exited.")
                break
    except KeyboardInterrupt:
        print("\nStopping all metrics captures...")
    finally:
        # Clean up the subprocesses
        if esp_process.poll() is None:
            esp_process.terminate()
            esp_process.wait()
        if router_process.poll() is None:
            router_process.terminate()
            router_process.wait()
        print("Centralized Metrics Logger finished.")

if __name__ == "__main__":
    main()
