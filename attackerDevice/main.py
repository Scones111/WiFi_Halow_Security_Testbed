import os
import sys
import time
from attack import attackSelection
from monitor import setupLogging,setupMetricClient,summarizer
import time

def print_usage():
    print("Usage: python main.py [option]")
    print("Options:")
    print("  attack: Run the attack selection")
    print("  capture: Capture traffic logs and metrics")
    print("  monitor: Monitor the network and capture metrics")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print_usage()
        sys.exit(1)

    opt = sys.argv[1]
    

    if opt not in ["attack","attack_log","base_network","metric_client","sum"]:
        print("Invalid option. Please choose from: attack, attack_log, base_network, metric_client, sum")
        sys.exit(1)

    if opt == "attack":
        params = sys.argv[2:]
        if params[0] == "1":
            attackSelection.run(params)

    if opt == "attack_log":
        params = sys.argv[2:]
        setupLogging.load_config()
        setupLogging.start_traffic_log()
        clients = setupLogging.init_metric_logs()
        print("Waiting 3 mins before starting attack...")
        time.sleep(180)
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
"""
    print("1. run attack")
    print("2. run attack and capture logs")
    print("3. Capture Base Network")
    print("4. Capture Metrics")
    choice = input("Type 1, 2, 3 or 4: ")
    print("")
    while choice not in ["1", "2", "3", "4"]:
        print("Not a valid choice try again!")
        choice = input("Type 1, 2, 3 or 4: ")
        print("")

    if choice == "1":
        attackSelection.run()
    elif choice == "2":
        setupLogging.load_config()
        setupLogging.start_traffic_log()
        clients = setupLogging.init_metric_logs()
        print("Waiting 3 mins before starting attack...")
        time.sleep(180)
        results_folder = attackSelection.run()
        setupLogging.stop_metric_logs(clients)
        setupLogging.end_traffic_log()
        setupLogging.post_process(results_folder)
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
        info = "By selecting this, you have made this computer a client.\nThe client will wait for the main device to run the attacks! \nTo stop the device from running, you can simply press ctrl+c"
        print(info)
        while True:
            setupMetricClient.setup_client()

"""