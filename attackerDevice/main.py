from attackerDevice.attack import attackSelection
from attackerDevice.monitor import setupLogging

if __name__ == "__main__":
    print("Attacker or logger?")
    choice = input("Type 1 for attacker or 2 for logger: ")
    while choice != ["1","2"]:
        print("Not a valid choice try again!")
        choice = input("Type 1 for attacker or 2 for logger: ")

    if choice == "1":
        attackSelection.run()
    elif choice == "2":
        setupLogging.start_monitor_device_logging()
        pass
