import os
import sys
import time
from attack import attackSelection
from monitor import setupLogging,setupMetricClient,summarizer
from utils import start_sdr_tx
import time

def print_usage():
    usage = """
    Usage: python main.py [option]
    Options:
      attack: Run the attack selection
        - For Evil Twin: python main.py attack 1 <duration> <rate>
        - For Dragon Dos: python main.py attack 2 <sae_pwe> <duration> <rate> <num_macs>
      attack_log: Run the attack and capture logs
        - For Evil Twin: python main.py attack_log 1 <duration> <rate>
        - For Dragon Dos: python main.py attack_log 2 <sae_pwe> <duration> <rate> <num_macs>
      base_network: Capture base network traffic
        - capture: network traffic and metrics
      metric_client: Capture metrics
        - sets up client to capture metrics from the victim devices
      sum: Summarize results
        - For Evil Twin: python main.py sum 1
        - For Dragon Dos: python main.py sum 2
    """
    print(usage)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    opt = sys.argv[1]
    
    sdr_process = None
    try:
        if opt not in ["attack","attack_log","base_network","metric_client","sum"]:
            print("Invalid option. Please choose from: attack, attack_log, base_network, metric_client, sum")
            sys.exit(1)

        if opt in ["attack","attack_log"]:
            sdr_process = start_sdr_tx()
            print("Waiting for SDR to initialize...")
            time.sleep(5)
        if opt == "attack":
            params = sys.argv[2:]
            attackSelection.run(params)

        if opt == "attack_log":
            params = sys.argv[2:]
            setupLogging.load_config()
            setupLogging.start_traffic_log()
            clients = setupLogging.init_metric_logs(params)
            results_folder = attackSelection.run(params)
            setupLogging.stop_metric_logs(clients)
            setupLogging.end_traffic_log()
            setupLogging.post_process(params)

        if opt == "base_network":
            setupLogging.load_config()
            setupLogging.start_traffic_log()
            clients = setupLogging.init_metric_logs()
            input("Press enter to stop monitoring:")
            setupLogging.stop_metric_logs(clients)
            setupLogging.end_traffic_log()
            setupLogging.post_process()
        
        if opt == "metric_client":
            print("You have selected the metric capture!")
            info = """
            By selecting this, you have made this computer a client.
            The client will wait for the main device to run the attacks! 
            To stop the device from running, you can simply press ctrl+c
            """
            print(info)
            while True:
                setupMetricClient.setup_client()
        if opt == "sum":
            params = sys.argv[2:]
            if params[0] == "1":
                summarizer.evilTwin_summarize()
            elif params[0] == "2":
                summarizer.dragonDos_summarize()

    finally:
        # This block ALWAYS runs, even if you press ctrl+c or the script crashes
        if sdr_process is not None:
            print("\n[INFO] Terminating SDR process...")
            sdr_process.terminate()
            sdr_process.wait() # Ensure the process has completely closed
            os.system("hackrf_info") # will softreset the usb connection, eliminates continues TX mode
