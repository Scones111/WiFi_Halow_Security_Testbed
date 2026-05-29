import paramiko
import json
import time

with open("devices.json", "r") as file:
    data = json.load(file)

# SSH Configuration
HOST = data["EvilTwin"][0]["ip"]
USER = data["EvilTwin"][0]["user"]
PASSWORD = data["EvilTwin"][0]["password"]

client:paramiko.SSHClient

def connect_to_evilTwin():
    print("Starting SSH connection to", HOST)
    # SSH connect
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(
        paramiko.AutoAddPolicy()
    )

    client.connect(
        hostname=HOST,
        username=USER,
        password=PASSWORD,
        timeout=10
    )

    print("SSH connected")
    return client

def start_evil_twin():
    command = (
        f"./ap_mode.sh "
    )
    stdin, stdout, stderr = client.exec_command(
        command
    )
    exit_status = stdout.channel.recv_exit_status()
    return "evil twin running"


def stop_evil_twin():
    # execute command
    command = (
        f"./ap_mode_down.sh "
    )
    stdin, stdout, stderr = client.exec_command(
        command
    )

    #wait for executing
    exit_status = stdout.channel.recv_exit_status()
    return "evil twin down"

def disconnect_evil_twin():
    client.close()


