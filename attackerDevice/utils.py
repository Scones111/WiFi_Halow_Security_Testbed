import json
from pathlib import Path
import csv
import os
import pandas as pd
import subprocess
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


def start_sdr_tx():
    """
    Initializes the SDR and runs the transmission script in the background.
    Returns the Popen process object so it can be terminated later if needed.
    """
    # Get absolute path to the workspace root directory
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    script_dir = os.path.join(base_dir, "shellScript")
    script_path = os.path.join(script_dir, "compile_and_run_tx.sh")
    
    print(f"[INFO] Starting SDR TX script in background: {script_path}")
    process = subprocess.Popen(
        ["/bin/bash", script_path], 
        cwd=script_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return process
    