import attack.appMessages as appMessages
import attack.attacks.evilTwin as evilTwin
from attack.attacks import dragonblood

# include a start time to allow sync with wireshark
from pathlib import Path
import os
import time
import json

#helper function to store meta data for attack in csv file
"""

"""
def run():
    appMessages.print_intro()

    # initialize variables for choice and raw frame
    continue_choice = None
    mode_choice = None
    attack_start = None
    attack_type = None

    att_meta = {"attackType":None,"attackStart":None,"attackEnd":None}
    att_metadata = []
    # loop for mode selection
    while(True):
        print("which attack do you want to perform?")
        print("1. evil twin attack")
        print("2. Dragonblood DoS attack")
        print("Note: that you can wait, to collect more data outside of attack")

        while(True):
            mode_choice = input("Enter the number corresponding to the mode: ")
            if mode_choice in ["1", "2"]:
                break
            else:
                print("Invalid choice. Please enter a valid number.")

        if mode_choice == "1":
            att_meta["attackType"] = "evil_twin"
            att_meta["attackStart"] = time.time()
            print("Evil Twin attack selected")
            print("remeber to plug in rouge AP")
            #call shell script to start evil twin AP
            # can disconnect after
            #os.system("./../shellScript/start_evil_twin.sh")

            evilTwin.transmit_frame_deauth()

            # connect before stopping evil twin AP
            # call shell script to stop evil twin
            #os.system("./../shellScript/stop_evil_twin.sh")

        elif mode_choice == "2":
            att_meta["attackType"] = "DragonBlood_DoS"
            att_meta["attackStart"] = time.time()
            print("Dragonblood DoS attack selected")
            dragonblood.start_dos()
        
        att_meta["attackEnd"] = time.time()
        att_metadata.append(att_metadata)
        #log_metaData(attack_start,time.time(),attack_type)
        # exit or select another mode
        continue_choice = input("\nDo you want to perform another attack? (y/n):")
        while(continue_choice not in ["y", "n"]):
            continue_choice = input("Invalid input. Please enter 'y' for yes or 'n' for no: ")
        if continue_choice == "n":
            break
    
    return att_metadata
