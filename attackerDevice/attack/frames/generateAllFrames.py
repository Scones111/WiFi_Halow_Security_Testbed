from attackerDevice.attack.frames.deauth import deauth_frame
from attackerDevice.utils import get_mac
def retrieve_all_attack_frames():
    attack_frames = []
    # extend this to include all frames we are transmitting for attacks

    #load all deauth frames we can generate
    attack_frames.append(deauth_frame("FF:FF:FF:FF:FF:FF").hex())

    for mac in get_mac("STA"):
        attack_frames.append(deauth_frame(mac).hex())

    #todo: add more frames for other attacks
    return attack_frames