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

DEFAULT_INTERFACE = "mon0"

client = None
wireshark = None
logfile = None

PCAP_PATH = "monitor/pcaps"
PCAP = "testbed_0.pcap"
PCAP_NAME = "testbed_0"

counter = 0
while os.path.exists(os.path.join(PCAP_PATH, PCAP)):
    counter+=1
    PCAP = f"{PCAP_NAME}_{counter}.csv"

os.makedirs(os.path.dirname(os.path.join(PCAP_PATH,PCAP)), exist_ok=True)

def cleanup() -> None:
    """Close open resources without exiting the process."""
    global client, wireshark, logfile

    print("Cleaning up...")

    if logfile is not None:
        try:
            logfile.close()
        except Exception:
            pass
        finally:
            logfile = None

    if wireshark is not None:
        try:
            wireshark.terminate()
        except Exception:
            pass
        finally:
            wireshark = None

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


def start_monitor_device_logging(
    start_wireshark: bool = True,
    register_signals: bool = True,
) -> str:
    
    """
    Start packet capture from the monitor device and save to a pcap file.

    Returns the actual pcap file path used.
    """
    global client, wireshark, logfile

    if register_signals:
        register_signal_handlers()

    print("Starting SSH connection to", DEFAULT_HOST)

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(DEFAULT_HOST, port=22, username=DEFAULT_USER, password=DEFAULT_PASSWORD, timeout=10)

    print("SSH connected")

    command = (
        f"tcpdump "
        f"-i {DEFAULT_INTERFACE} "
        f"-U "
        f"-s0 "
        f"-w -"
        # went through a filtered out packets were not interested in (only look at wlan and tcp)
        f"\"(wlan or tcp) and not (arp or stp or rldp or mdns or udp or icmpv6 or igmp or ipv6)\"" 
    )

    stdin, stdout, stderr = client.exec_command(command)

    if start_wireshark:
        wireshark = subprocess.Popen(["wireshark", "-k", "-i", "-"], stdin=subprocess.PIPE)
        print("Wireshark started")

    print(f"Saving packet capture to {PCAP}")
    pcapfile = open(os.path.join(PCAP_PATH, PCAP), "wb")

    try:
        while True:
            data = stdout.channel.recv(4096)
            if not data:
                print("tcpdump process ended")
                break

            pcapfile.write(data)
            pcapfile.flush()

            if start_wireshark and wireshark is not None:
                wireshark.stdin.write(data)
                wireshark.stdin.flush()

            processLogs.log_events(data)
    except KeyboardInterrupt:
        print("Capture interrupted by user")
    finally:
        cleanup()
