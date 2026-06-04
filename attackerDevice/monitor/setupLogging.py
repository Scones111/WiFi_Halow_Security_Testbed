import os
import paramiko
import subprocess
import signal
import sys
from typing import Optional
import json
from monitor import processLogs

with open("devices.json", "r") as file:
    data = json.load(file)


# SSH Configuration
DEFAULT_HOST = data["Monitor"][0]["ip"]
DEFAULT_USER = data["Monitor"][0]["user"]
DEFAULT_PASSWORD = data["Monitor"][0]["password"]

DEFAULT_INTERFACE = "morse0"

WIRESHARK_FILTER = "(wlan || tcp) && !arp && !stp && !rldp && !mdns && !udp && !icmpv6 && !igmp && !ipv6"

client = None
wireshark = None

PCAP_PATH = "monitor/pcaps"
os.makedirs(PCAP_PATH, exist_ok=True)
PCAP = "testbed_0.pcap"
PCAP_NAME = "testbed"

counter = 0
while os.path.exists(os.path.join(PCAP_PATH, PCAP)):
    counter+=1
    PCAP = f"{PCAP_NAME}_{counter}.pcap"


def cleanup() -> None:
    """Close open resources without exiting the process."""
    global client, wireshark

    print("Cleaning up...")

    if wireshark is not None:
        try:
            wireshark.terminate()
        except Exception:
            pass
        finally:
            wireshark = None
            processLogs.log_events(os.path.join(PCAP_PATH, PCAP),WIRESHARK_FILTER)
            
    if client is not None:
        try:
            client.close()
        except Exception:
            pass
        finally:
            client = None

def _cleanup_and_exit(*args) -> None:
    cleanup()
    sys.exit(0)


def register_signal_handlers() -> None:
    signal.signal(signal.SIGINT, _cleanup_and_exit)
    signal.signal(signal.SIGTERM, _cleanup_and_exit)


def start_monitor_device_logging():
    print("Starting SSH connection to", DEFAULT_HOST)

    shh = paramiko.SSHClient()
    shh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    shh.connect(DEFAULT_HOST, port=22, username=DEFAULT_USER, password=DEFAULT_PASSWORD, timeout=10)

    print("SSH connected")

    tcpdump_command = (
        f"tcpdump "
        f"-i {DEFAULT_INTERFACE} "
        f"-U "
        f"-s0 "
        f"-w - "
    )

    _, stdout, _ = shh.exec_command(tcpdump_command)

    wgui = subprocess.Popen(["wireshark", "-k", "-i", "-","-Y",WIRESHARK_FILTER,"-w",os.path.join(PCAP_PATH, PCAP)], stdin=subprocess.PIPE)

    print(f"Saving packet capture to {os.path.join(PCAP_PATH, PCAP)}")

    while True:
        packets = stdout.channel.recv(4096)
         
        if packets is not None:
            wgui.stdin.write(packets)
            wgui.stdin.flush()

            processLogs.log_events(packets)
            processLogs.MLLog_processing(packets)