from socket import *
import serial
import serial.tools.list_ports
import subprocess
import utils

def check_con_devices():
    con_devices = {device["name"]:False for device in utils.load_json()["STA"]}
    trustedAP = utils.load_json()["TrustedAP"][0]
    con_devices[trustedAP["name"]] = False
    
    print("Remeber to configure the devices to use the correct ports")
    ports = serial.tools.list_ports.comports()
    sta_ports = {device["serial_port"]:device["name"] for device in utils.load_json()["STA"]}

    for port in ports:
        print(port.device)
        if port.device in sta_ports:
            device_name = sta_ports[port.device]
            con_devices[device_name] = True

    #ping to check for connection
    print(trustedAP["ip"])
    res = subprocess.run(f"ping -c 1 {trustedAP['ip']}",stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode
    if res == 0:
        con_devices[trustedAP["name"]] = True

    return con_devices

if __name__ == "__main__":
    s = socket(AF_INET, SOCK_DGRAM)
    
    con_devices = check_con_devices()
    for device_n, device_c in con_devices.items():
        print(device_n,device_c)
        msg = f"{device_n,device_c}".encode('utf-8')
        s.sendto(msg,('10.209.219.105',5005))
# Create a socket that is bound to port 50000


# Wait for a message to come in on port 50000, and print it