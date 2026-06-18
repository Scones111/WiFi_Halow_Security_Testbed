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

if __name__ == "__main__":
    s = None
    while(True):
        try:
            s = socket(AF_INET, SOCK_STREAM)
            s.connect(('127.0.0.1', 5005))
            break
        except:
            print("server not up wait")
            s.close()
            time.sleep(2)
    #s.bind(('0.0.0.0', 5005))
    
    con_devices = check_con_devices()
    for device_n, device_c in con_devices.items():
        print(device_n,device_c)
        msg = f"{device_n},{device_c}".encode('utf-8')
        s.send(msg)
        time.sleep(0.1)

    print("done sending connected devices")
    s.send("done".encode('utf-8'))
    
    print("now waiting for command to run")
    msg = s.recv(1024)
    msg_str = msg.decode('utf-8')
    if msg_str == "run centralized logging":
        print("will now start logging")

    stop_logging = s.recv(1024)

    for i in range(3):
        with open("logs/initial_dragondos_client_metrics.csv","rb") as f:
            data = f.read()

        s.send("initial_dragondos_client_metrics.csv".encode('utf-8'))
        time.sleep(0.1)
        s.send(f"{len(data)}".encode('utf-8'))

        s.sendall(data)

        time.sleep(0.01)
    
    print("done sending")

    
