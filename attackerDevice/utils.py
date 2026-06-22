import json
from pathlib import Path
import csv
import os
import pandas as pd
#import attackerDevice.attack.frames as frames
#from attackerDevice.attack.frames.deauth import deauth_frame

#get device file path
DEVICE_FILE = "devices.json"

def load_json():
    with open(DEVICE_FILE, "r") as f:
        return json.load(f)

def get_mac(device_name):
    devices = load_json()[device_name]
    macs = []
    for device in devices:
        macs.append(device['mac'])

    return macs

def write_to_attacklog(row,folder_path):
    header = False
    if not os.path.exists(os.path.join(folder_path, "ATTACK_LOG.csv")):
        header = True
    with open(os.path.join(folder_path, "ATTACK_LOG.csv"), "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())

        if header:
            writer.writeheader()

        writer.writerow(row)

def write_to_tcp_log(row,folder_path):
    header = False
    if not os.path.exists(os.path.join(folder_path, "TCP_LOG.csv")):
        header = True

    with open(os.path.join(folder_path, "TCP_LOG.csv"), "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())       
        
        if header:
            writer.writeheader()

        writer.writerow(row)

def turn_hex_to_string(hex:str):
    hex = hex.replace(':','')
    hex_bytes = bytes.fromhex(hex)
    return hex_bytes.decode('utf-8', errors='replace')

def write_to_ml_log(features:pd.DataFrame,folder_path):
    features.to_csv(os.path.join(folder_path, "ML_LOG.csv"), mode='a', header=not os.path.exists(os.path.join(folder_path, "ML_LOG.csv")), index=False)
