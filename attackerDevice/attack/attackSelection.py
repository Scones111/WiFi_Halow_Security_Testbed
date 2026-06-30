import attack.appMessages as appMessages
import attack.attacks.evilTwin as evilTwin
from attack.attacks import dragonblood

def run():
    appMessages.print_intro()

    # initialize variables for choice and raw frame
    continue_choice = None
    mode_choice = None

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
            print("Evil Twin attack selected")
            print("remember to plug in evil twin AP")
            evilTwin.transmit_frame_deauth()

        elif mode_choice == "2":
            print("Dragonblood DoS attack selected")
            dragonblood.start_dos()
        
        # exit or select another mode
        continue_choice = input("\nDo you want to perform another attack? (y/n):")
        while(continue_choice not in ["y", "n"]):
            continue_choice = input("Invalid input. Please enter 'y' for yes or 'n' for no: ")
        if continue_choice == "n":
            break
