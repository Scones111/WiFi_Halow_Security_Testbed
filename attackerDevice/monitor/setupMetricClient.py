from socket import *
import serial
import serial.tools.list_ports
import subprocess
import utils
import time

def check_con_devices():
    con_devices = {device["name"]:False for device in utils.load_json()["STA"]}
    trustedAP = utils.load_json()["TrustedAP"][0]
    con_devices[trustedAP["name"]] = False
    
    print("Remeber to configure the devices to use the correct ports")
    ports = serial.tools.list_ports.comports()
    sta_ports = {device["serial_port"]:device["name"] for device in utils.load_json()["STA"]}

    for port in ports:
        if sta_ports[port] != None:
            con_devices[port] = True

    #ping to check for connection
    res = subprocess.run(f"ping -c 1 {trustedAP['ip']}",stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode
    if res == 0:
        con_devices[trustedAP["name"]] = True

    return con_devices


def setup_client():
    client = None
    #wait till server is ready
    while(True):
        try:
            client = socket(AF_INET, SOCK_STREAM)
            client.connect(('127.0.0.1', 5005))
            break
        except:
            print("server not up wait")
            client.close()
            time.sleep(2)
    
    #check for connected devices
    con_devices = check_con_devices()
    #iterate through devices and transmit, the ones that are true
    for device_n, device_c in con_devices.items():
        print(device_n,device_c)
        if device_c:
            msg = f"{device_n},{device_c}".encode('utf-8')
            client.send(msg)
            time.sleep(0.1)

    print("done sending connected devices")
    #flag to tell server it is done transmitting
    client.send("done".encode('utf-8'))

    print("now waiting for command to run")
    msg = client.recv(1024)
    msg_str = msg.decode('utf-8')
    print(f"command: {msg_str}")

    #Todo implement more options here
    if msg_str == "run centralized logging":
        print("will now start logging")
        #todo implement threading here or subprocess here
        #needs to be none blocking, so we can move recv that will be called when logging should be stopped
    elif msg_str:
        pass

    #stop logging can be anything
    #blocks until server transmit a message
    client.recv(1024)

    #todo iterate through logs stored and transmit them over tcp
    for file in range(3): #change range(3) to be a folder to iterate through
        with open(file,"rb") as f:
            data = f.read()

        #transmit file name
        client.send(f"{file}".encode('utf-8'))
        time.sleep(0.01)
        #transmit length of data
        client.send(f"{len(data)}".encode('utf-8'))

        #transmit all data
        client.sendall(data)

        time.sleep(0.01)
    
    client.close()