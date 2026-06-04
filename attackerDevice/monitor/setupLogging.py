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

ssh = None
wgui = None

PCAP_PATH = "monitor/pcaps"
os.makedirs(PCAP_PATH, exist_ok=True)
PCAP = "testbed_0.pcap"
PCAP_NAME = "testbed"

counter = 0
while os.path.exists(os.path.join(PCAP_PATH, PCAP)):
    counter+=1
    PCAP = f"{PCAP_NAME}_{counter}.pcap"


def cleanup() -> None:
    """
    clean up subprocesses and ssh connection
    """
    global ssh, wgui

    print("Cleaning up...")

    if wgui is not None:
        try:
            wgui.terminate()
        except Exception:
            pass
        finally:
            wgui = None
            processLogs.log_events(os.path.join(PCAP_PATH, PCAP),WIRESHARK_FILTER)
            
    if ssh is not None:
        try:
            ssh.close()
        except Exception:
            pass
        finally:
            ssh = None

def _cleanup_and_exit(*args) -> None:
    cleanup()
    sys.exit(0)


def register_signal_handlers() -> None:
    signal.signal(signal.SIGINT, _cleanup_and_exit)
    signal.signal(signal.SIGTERM, _cleanup_and_exit)


def start_monitor_device_logging() -> str:
    
    """
    start monitor device, capture data from ssh connection and store them in a pcap.

    pcap is is kept and logs are processed after logging has been performed
    """
    global ssh, wgui
    register_signal_handlers()

    print("Starting SSH connection to", DEFAULT_HOST)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(DEFAULT_HOST, port=22, username=DEFAULT_USER, password=DEFAULT_PASSWORD, timeout=10)

    print("SSH connected")

    command = (
        f"tcpdump "
        f"-i {DEFAULT_INTERFACE} "
        f"-U "
        f"-s0 "
        f"-w - "
    )

    _, stdout, _ = ssh.exec_command(command)

    wgui = subprocess.Popen(["wireshark", "-k", "-i", "-","-Y",WIRESHARK_FILTER,"-w",os.path.join(PCAP_PATH, PCAP)], stdin=subprocess.PIPE)
    
    print(f"Packet stored in: {os.path.join(PCAP_PATH, PCAP)}")

    try:
        while True:
            data = stdout.channel.recv(4096)
            if not data:
                continue

            wgui.stdin.write(data)
            wgui.stdin.flush()

    except KeyboardInterrupt:
        print("Capture interrupted by user")
    finally:
        cleanup()