import attack.appMessages as appMessages
import attack.attacks.evilTwin as evilTwin
from attack.attacks import dragonblood

def run(params):
    if params[0] == "1":
        if len(params) < 2:
            print("invalid number of parameters for Evil Twin Attack.")
            return
        evilTwin.transmit_frame_deauth(params[1:])
    elif params[0] == "2":
        if len(params) < 4:
            print("Invalid number of parameters for Dragonblood DoS attack.")
            return
        dragonblood.start_dos(params[1:])

"""

    # initialize variables for choice and raw frame
    continue_choice = None
    mode_choice = None
    results_folder = None

    # loop for mode selection
    while(True):
        print("which attack do you want to perform?")
        print("1. evil twin attack")
        print("2. Dragonblood DoS attack")
        print("Note: that you can wait, to collect more data outside of attack")

        mode_choice = "2"
        print("Automated input: mode_choice = 2")
        # while(True):
        #     mode_choice = input("Enter the number corresponding to the mode: ")
        #     if mode_choice in ["1", "2"]:
        #         break
        #     else:
        #         print("Invalid choice. Please enter a valid number.")

        if mode_choice == "1":
            print("Evil Twin attack selected")
            print("remember to plug in evil twin AP")
            evilTwin.transmit_frame_deauth()

        elif mode_choice == "2":
            print("Dragonblood DoS attack selected")
            results_folder = dragonblood.start_dos()
        
        # exit or select another mode
        print("\nWaiting 3 mins before stopping...")
        import time
        time.sleep(180)
        continue_choice = "n"
        print("Automated input: continue_choice = n")
        # continue_choice = input("\nDo you want to perform another attack? (y/n):")
        # while(continue_choice not in ["y", "n"]):
        #     continue_choice = input("Invalid input. Please enter 'y' for yes or 'n' for no: ")
        if continue_choice == "n":
            break

    return results_folder
"""
