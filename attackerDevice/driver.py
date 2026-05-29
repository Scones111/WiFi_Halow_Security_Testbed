from scapy.all import wrpcap
import time
import appMessages
from attackLogGenerator import EventHandler

import setupEvilTwin
import evilTwin


# include a start time to allow sync with wireshark

if __name__ == "__main__":
    appMessages.print_intro()

    log = EventHandler()


    # initialize variables for choice and raw frame
    raw_frame = None
    continue_choice = None
    event_type = None
    details = None
    mode_choice = None
    client = None

    # loop for mode selection
    while(True):
        print("which attack do you want to perform?")
        print("1. evil twin attack")
        print("2. DoS deauthentication attack")

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
            log.log_event("evil_twin_initiated","evil twin has been initialed and is transmitting beacon frames")
            #transmit frames
            evilTwin.transmit_frame_deauth(log)
            setupEvilTwin.stop_evil_twin(client)
            setupEvilTwin.disconnect_evil_twin(client)

        elif mode_choice == "2":
            print("DoS deauthentication attack selected")
            # insert code for DoS attack
        
        # exit or select another mode
        continue_choice = input("\nDo you want to select another mode? (y/n):")
        while(continue_choice not in ["y", "n"]):
            continue_choice = input("Invalid input. Please enter 'y' for yes or 'n' for no: ")
        if continue_choice == "n":
            break

    print("exiting, writing saving log")
    log.write_log_json("example")
