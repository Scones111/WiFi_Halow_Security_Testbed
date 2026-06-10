import os
import paramiko
import subprocess
import signal
import sys
from typing import Optional
import json
from monitor import processLogs
from pathlib import Path

WIRESHARK_FILTER = "(wlan || tcp) && !arp && !stp && !rldp && !mdns && !udp && !icmpv6 && !igmp && !ipv6"

PCAP_SRC = "monitor/tempPcap"
PCAP_DST = "monitor/pcaps"

PCAP = "testbed_0.pcap"
PCAP_NAME = "testbed"

counter = 0
while os.path.exists(os.path.join(PCAP_DST, PCAP)):
    counter+=1
    PCAP = f"{PCAP_NAME}_{counter}.pcap"

def start_monitor_device_logging():
    for temppcap in Path(PCAP_SRC).iterdir():
        if temppcap.is_file() and temppcap.suffix == ".pcap":
            processLogs.log_events(temppcap,WIRESHARK_FILTER)

            print("done prcessing logs")
            temppcap.rename(os.path.join(PCAP_DST,PCAP))
            print("moved processed pcap to the pcaps folder")