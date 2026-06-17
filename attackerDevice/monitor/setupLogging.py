import os
import paramiko
import subprocess
import signal
import sys
from typing import Optional
import json
from monitor import processLogs
from pathlib import Path
import utils
import queue

devices = utils.load_json()

#load monitor device config
MON_IP = devices["Monitor"][0]["ip"]
MON_USER = devices["Monitor"][0]["user"]
MON_PASS = devices["Monitor"][0]["password"]


WIRESHARK_FILTER = "(wlan || tcp) && !arp && !stp && !rldp && !mdns && !udp && !icmpv6 && !igmp && !ipv6 && (wlan.sa != )"

PCAP_SRC = "monitor/tempPcap"
PCAP_DST = "monitor/pcaps"

PCAP = "testbed_0.pcap"
PCAP_NAME = "testbed"

counter = 0
while os.path.exists(os.path.join(PCAP_DST, PCAP)):
    counter+=1
    PCAP = f"{PCAP_NAME}_{counter}.pcap"

PCAP_PATH = PCAP_DST + "/" + PCAP

tcpdump = None

def start_log():
    global tcpdump
    # start monitor mode
    os.system(f"sshpass -p 'halow' ssh root@10.42.01 'date -s \'@$(date -u +%s)\''")

    os.system(f"sshpass -p '{MON_PASS}' ssh {MON_USER}@{MON_IP} './../sniffer_mode.sh'")

    with open(PCAP_PATH, "wb") as pcap_file:
        tcpdump_cmd = [
            "sshpass", "-p" ,MON_PASS, 
            "ssh" ,f"{MON_USER}@{MON_IP}", 
            "tcpdump", "-i", "morse0", "-U", "-s0", "-w", "-"
            ]
        
        tcpdump = subprocess.Popen(
            tcpdump_cmd, 
            stdout=pcap_file,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=True
            )
    

def end_log():
    global tcpdump
    os.system(f"sshpass -p '{MON_PASS}' ssh {MON_USER}@{MON_IP} 'kill $(pgrep tcpdump)'")
    #stop logging process
    tcpdump.terminate()
    tcpdump.wait()

def post_process():
    processLogs.log_events(PCAP_PATH,WIRESHARK_FILTER)


"""
def start_monitor_device_logging():
    for temppcap in Path(PCAP_SRC).iterdir():
        if temppcap.is_file() and temppcap.suffix == ".pcap":
            processLogs.log_events(temppcap,WIRESHARK_FILTER)

            print("done prcessing logs")
            temppcap.rename(os.path.join(PCAP_DST,PCAP))
            print("moved processed pcap to the pcaps folder")
"""