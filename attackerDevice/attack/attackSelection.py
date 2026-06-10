from scapy.all import wrpcap
import attack.appMessages as appMessages
from attack.attackLogGenerator import EventHandler
import attack.attacks.setupEvilTwin as setupEvilTwin
import attack.attacks.evilTwin as evilTwin
from attack.attacks import dragonblood

# include a start time to allow sync with wireshark

def run():
    appMessages.print_intro()

    log = EventHandler()
    log.log_event("attack_start", "attack has been started")
    # initialize variables for choice and raw frame
    continue_choice = None
    mode_choice = None
    client = None
    # loop for mode selection
    while(True):
        print("which attack do you want to perform?")
        print("1. evil twin attack")
        print("2. Dragonblood DoS attack")

        while(True):
            mode_choice = input("Enter the number corresponding to the mode: ")
            if mode_choice in ["1", "2"]:
                break
            else:
                print("Invalid choice. Please enter a valid number.")

        if mode_choice == "1":
            print("Evil Twin attack selected")
            #setup evil twin
            client = setupEvilTwin.connect_to_evilTwin()
            setupEvilTwin.start_evil_twin(client)
            log.log_event("evil_twin_initiated","evil twin has been initiated and is transmitting beacon frames")
            #transmit frames
            evilTwin.transmit_frame_deauth(log)
            setupEvilTwin.stop_evil_twin(client)
            setupEvilTwin.disconnect_evil_twin(client)

        elif mode_choice == "2":
            print("Dragonblood DoS attack selected")
            log.log_event("dragonblood_dos_initiated", "transmitting sae commit frames")
            dragonblood.start_dos()
        
        log.end_log()
        # exit or select another mode
        continue_choice = input("\nDo you want to perform another attack? (y/n):")
        while(continue_choice not in ["y", "n"]):
            continue_choice = input("Invalid input. Please enter 'y' for yes or 'n' for no: ")
        if continue_choice == "n":
            break

    print("exiting, writing saving log")
    log.write_log_json("example")
