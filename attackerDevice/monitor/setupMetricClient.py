from socket import *
import serial
import serial.tools.list_ports
import subprocess
import utils
import time
import os

def check_con_devices():
    con_devices = {device["name"]:False for device in utils.load_json()["STA"]}
    trustedAP = utils.load_json()["TrustedAP"][0]
    con_devices[trustedAP["name"]] = False
    
    print("Remeber to configure the devices to use the correct ports")
    ports = serial.tools.list_ports.comports()
    sta_ports = {device["serial_port"]:device["name"] for device in utils.load_json()["STA"]}

    for port in ports:
        if port.device in sta_ports:
            con_devices[sta_ports[port.device]] = True

    #ping to check for connection
    res = -1
    try:
        res = subprocess.run(f"ping -c 1 {trustedAP['ip']}",stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode
    except:
        pass

    if res == 0:
        con_devices[trustedAP["name"]] = True

    return con_devices


def setup_client():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    esp32_script = os.path.join(base_dir, "capture_esp32_metrics.py")
    router_script = os.path.join(base_dir, "capture_router_metrics.py")
    centralized_script = os.path.join(base_dir, "centralized_metrics_logger.py")
    logger_process = None
    router_process = None
    esp_process = None
    
    #wait till server is ready
    while(True):
        client = socket(AF_INET, SOCK_STREAM)
        try:
            client.connect(('10.209.201.56', 5005))
            print("connected to server")
            break
        except:
            print("server not up wait")
            client.close()
            time.sleep(2)
    
    #check for connected devices
    print("checking connected devices")
    con_devices = check_con_devices()
    #iterate through devices and transmit, the ones that are true
    for device_n, device_c in con_devices.items():
        print(device_n,device_c)
        if device_c:
            msg = f"{device_n},{device_c}\n".encode('utf-8')
            client.send(msg)
            time.sleep(0.1)

    print("done sending connected devices")
    #flag to tell server it is done transmitting
    client.send("done\n".encode('utf-8'))

    print("now waiting for command to run")
    msg = client.recv(1024)
    msg_str = msg.decode('utf-8')
    print(f"command: {msg_str}")

    #Todo implement more options here
    if msg_str == "run centralized logging":
        print("will now start logging router and esp devices")
        try:
            logger_process = subprocess.Popen([sys.executable, os.path.abspath(centralized_script)])
        except Exception as e:
            print(f"Error starting logger: {e}")
        #needs to be none blocking, so we can move recv that will be called when logging should be stopped
    elif msg_str == "run router logging":
        print("will now start logging router")
        try:
            router_process = subprocess.Popen([sys.executable, os.path.abspath(router_script)])
        except Exception as e:
            print(f"Error starting router process: {e}")
    elif msg_str == "run esp logging":
        print("will now start logging esp devices")
        try:
            esp_process = subprocess.Popen([sys.executable, os.path.abspath(esp32_script)])
        except Exception as e:
            print(f"Error starting esp process: {e}")

    #stop logging can be anything
    #blocks until server transmit a message
    stop_msg = client.recv(1024).decode('utf-8')
    if stop_msg == "stop logging":
        if logger_process:
            logger_process.terminate()
            logger_process.wait()
        if router_process:
            router_process.terminate()
            router_process.wait()
        if esp_process:
            esp_process.terminate()
            esp_process.wait()

    #todo iterate through logs stored and transmit them over tcp
    for file in range(3): #change range(3) to be a folder to iterate through
        file_name = str(file)
        if not os.path.exists(file_name):
            continue
            
        with open(file_name,"rb") as f:
            data = f.read()

        #transmit file name
        client.send(f"{file_name}\n".encode('utf-8'))
        time.sleep(0.01)
        #transmit length of data
        client.send(f"{len(data)}\n".encode('utf-8'))

        #transmit all data
        client.sendall(data)

        time.sleep(0.01)
    
    client.close()