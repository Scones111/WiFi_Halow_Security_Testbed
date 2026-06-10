import attack.appMessages as appMessages
import attack.attacks.evilTwin as evilTwin
from pathlib import Path
import os
import time
import json

#helper function to store meta data for attack in csv file
def log_metaData(start,end,type):
    file_number = 0
    file = f"{type}_{file_number}.json"
    path = f"metaData"
    
    os.makedirs(path+"/", exist_ok=True)
    while os.path.exists(os.path.join(path, file)):
        file_number += 1
        file = f"{type}_{file_number}.json"
    
    metaData = {"attackType":type,"attackStart":start,"attackEnd":end}
    with open(os.path.join(path, file),"w") as file:
        json.dump(metaData,file)

def run():
    appMessages.print_intro()

    # initialize variables for choice and raw frame
    continue_choice = None
    mode_choice = None
    attack_start = None
    attack_type = None
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
            attack_start = time.time()
            attack_type = "evil_twin"
            print("Evil Twin attack selected")
            #call shell script to start evil twin AP
            # can disconnect after
            os.system("./../shellScript/start_evil_twin.sh")

            evilTwin.transmit_frame_deauth()

            # connect before stopping evil twin AP
            # call shell script to stop evil twin
            os.system("./../shellScript/stop_evil_twin.sh")

        elif mode_choice == "2":
            print("DoS deauthentication attack selected")
            # insert code for DoS attack
        
        log_metaData(attack_start,time.time(),attack_type)
        # exit or select another mode
        continue_choice = input("\nDo you want to select another mode? (y/n):")
        while(continue_choice not in ["y", "n"]):
            continue_choice = input("Invalid input. Please enter 'y' for yes or 'n' for no: ")
        if continue_choice == "n":
            break

