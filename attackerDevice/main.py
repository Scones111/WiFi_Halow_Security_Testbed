import os
import sys
import time
from attack import attackSelection
from monitor import setupLogging,setupMetricClient
from utils import start_sdr_tx

if __name__ == "__main__":
    print("Select an option:")
    print("1. Attack")
    print("2. Attack and Capture traffic logs")
    print("3. Capture Base Network")
    print("4. Capture Metrics")
    choice = input("Type 1, 2, 3 or 4: ")
    print("")
    while choice not in ["1", "2", "3", "4"]:
        print("Not a valid choice try again!")
        choice = input("Type 1, 2, 3 or 4: ")
        print("")

    sdr_process = None

    try:
        # Only start SDR for the attack options
        if choice in ["1", "2"]:
            sdr_process = start_sdr_tx()
            print("Waiting for SDR to initialize...")
            time.sleep(5)
            print("====================================\n")
            print("You may now continue with the attack")
            print("====================================\n")

        if choice == "1":
            attackSelection.run()
        elif choice == "2":
            setupLogging.load_config()
            setupLogging.start_traffic_log()
            clients = setupLogging.init_metric_logs()
            attackSelection.run()
            setupLogging.stop_metric_logs(clients)
            setupLogging.end_traffic_log()
            setupLogging.post_process()
        elif choice == "3":
            setupLogging.load_config()
            setupLogging.start_traffic_log()
            clients = setupLogging.init_metric_logs()
            input("Press enter to stop monitoring:")
            setupLogging.stop_metric_logs(clients)
            setupLogging.end_traffic_log()
            setupLogging.post_process()
        elif choice == "4":
            print("You have selected the metric capture!")
            info = """
            By selecting this, you have made this computer a client.
            The client will wait for the main device to run the attacks! 
            To stop the device from running, you can simply press ctrl+c
            """
            print(info)
            while True:
                setupMetricClient.setup_client()

    finally:
        # This block ALWAYS runs, even if you press ctrl+c or the script crashes
        if sdr_process is not None:
            print("\n[INFO] Terminating SDR process...")
            sdr_process.terminate()
            sdr_process.wait() # Ensure the process has completely closed

