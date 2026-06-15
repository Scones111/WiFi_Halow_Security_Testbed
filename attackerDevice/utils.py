import json
from pathlib import Path
import csv
import os
import pandas as pd
#import attackerDevice.attack.frames as frames
#from attackerDevice.attack.frames.deauth import deauth_frame

#get device file path
DEVICE_FILE = "attackerDevice/devices.json"

# create log files
FILE_DEST = "monitor/logs"
os.makedirs(FILE_DEST, exist_ok=True)

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

#create machine learning log file
ML_FILE_DEST = "monitor/MLLogs"
ML_LOG = "MLLog_0.csv"
ML_LOG_NAME = "MLLog"
os.makedirs(ML_FILE_DEST, exist_ok=True)

while os.path.exists(os.path.join(ML_FILE_DEST, ML_LOG)):
    counter += 1
    ML_LOG = f"{ML_LOG_NAME}_{counter}.csv"

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
    header = False
    if not os.path.exists(os.path.join(FILE_DEST, ATTACK_LOG)):
        header = True
    with open(os.path.join(FILE_DEST, ATTACK_LOG), "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())

        if header:
            writer.writeheader()

        writer.writerow(row)

def write_to_tcp_log(row):
    header = False
    if not os.path.exists(os.path.join(FILE_DEST, TCP_LOG)):
        header = True

    with open(os.path.join(FILE_DEST, TCP_LOG), "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())       
        
        if header:
            writer.writeheader()

        writer.writerow(row)

def turn_hex_to_string(hex:str):
    hex = hex.replace(':','')
    hex_bytes = bytes.fromhex(hex)
    return hex_bytes.decode('utf-8', errors='replace')

def write_to_ml_log(features:pd.DataFrame):
    features.to_csv(os.path.join(ML_FILE_DEST, ML_LOG), mode='a', header=not os.path.exists(os.path.join(ML_FILE_DEST, ML_LOG)), index=False)
