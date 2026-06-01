import json
from pathlib import Path
import csv
import os


DEVICE_FILE = "devices.json"

FILE_DEST = "Monitor/logs"
os.makedirs(os.path.dirname(FILE_DEST), exist_ok=True)

ATTACK_LOG = "attackLog_0.csv"
ATTACK_LOG_NAME = "attackLog"

counter = 0
while os.path.exists(os.path.join(FILE_DEST, ATTACK_LOG)):
    counter+=1
    ATTACK_LOG = f"{ATTACK_LOG_NAME}_{counter}.csv"

TCP_LOG = "tcpLog_0.csv"
TCP_LOG_NAME = "tcpLog"

counter = 0
while os.path.exists(os.path.join(FILE_DEST, TCP_LOG)):
    counter+=1
    TCP_LOG = f"{TCP_LOG_NAME}_{counter}.csv"


def load_json():
    with open(DEVICE_FILE, "r") as f:
        return json.load(f)

def get_mac(device_name):
    devices = load_json()[device_name]
    macs = []
    for device in devices:
        macs.append(device['mac'])

    return macs

def write_to_attacklog(row):
    with open(ATTACK_LOG, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())

        # Write header only if file is new
        if not os.path.exists(os.path.join(FILE_DEST, ATTACK_LOG)):
            writer.writeheader()

        writer.writerow(row)

def write_to_tcp_log(row):
    with open(TCP_LOG, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())

        # Write header only if file is new
        if not os.path.exists(os.path.join(FILE_DEST, TCP_LOG)):
            writer.writeheader()

        writer.writerow(row)

def turn_hex_to_string(hex:str):
    hex = hex.replace(':','')
    hex_bytes = bytes.fromhex(hex)
    return hex_bytes.decode('utf-8', errors='replace')

