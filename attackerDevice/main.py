import os
import sys
from attack import attackSelection
from monitor import setupLogging,setupMetricClient

if __name__ == "__main__":
    print("Select an option:")
    print("1. Attack")
    print("2. Attack and Capture traffic logs")
    print("3. Capture Base Network")
    print("4. Metrics Capture")
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
        setupLogging.start_log()
        input("Press enter to stop monitoring:")
        setupLogging.end_log()
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
        pass

