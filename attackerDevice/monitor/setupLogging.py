import os
import subprocess
from monitor import processLogs
import utils
import socket
import time
import threading
import json

lock = threading.Lock()

MON_IP = None
MON_USER = None
MON_PASS = None

WIRESHARK_FILTER = "(wlan || tcp) && !arp && !stp && !rldp && !mdns && !udp && !icmpv6 && !igmp && !ipv6"

FULLPATH = None

def load_config():
    global MON_IP, MON_USER, MON_PASS, FULLPATH, FOLDER
    if FULLPATH is not None:
        return
    devices = utils.load_json()

    #load monitor device config
    MON_IP = devices["Monitor"][0]["ip"]
    MON_USER = devices["Monitor"][0]["user"]
    MON_PASS = devices["Monitor"][0]["password"]

    PATH_TO_EXPERIMENTS = "monitor/results/"
    FOLDER_NAME = "experiment_0/"

    counter = 0
    while os.path.exists(os.path.join(PATH_TO_EXPERIMENTS, FOLDER_NAME)):
        FOLDER_NAME = f"experiment_{counter}/"
        counter += 1

    os.makedirs(os.path.join(PATH_TO_EXPERIMENTS, FOLDER_NAME))

    FULLPATH = os.path.join(PATH_TO_EXPERIMENTS, FOLDER_NAME)

def get_in_dev_con(client, con_devices, clients):
    while(True):
        #check for messages of connected devices
        msg = client.recv(1024)
        msg_str = msg.decode('utf-8')
        if msg_str == "done":
            break
        elif msg:
            msg_split = msg_str.split(',')
            if msg_split[1] == "True":
                with lock:
                    #update for break condition
                    con_devices[msg_split[0]] = True
                    # add new client with the know connected device
                    if client not in clients:
                        clients[client] = [msg_split[0]]
                    else:
                        clients[client].append(msg_split[0])

# used for establishing incoming connections
def con_devices_check(server,con_devices,clients):
    #non blocking to break when all devices are connected
    server.setblocking(False)
    while True:
        with lock:
            #break when all devices are have been confirmed to be connected
            if all(value == True for value in con_devices.values()):
                break
        try:
            con, _, = server.accept()
            if con is not None:
                #client sock inherits non blocking, set to be blocking here again
                con.setblocking(True)
                threading.Thread(target=get_in_dev_con, args=(con,con_devices,clients)).start()
        except BlockingIOError:
            #sleep when no device have trying to connect
            time.sleep(0.01)

def init_metric_logs():
    print("TCP server running...")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", 5005))
    server.listen(5)

    # set dict used to check if all devices are connected on remote capture
    sta_names = [sta["name"] for sta in utils.load_json()["STA"]]
    con_devices = {sta:False for sta in sta_names}
    # we only allow for 1 router
    trustetAP = utils.load_json()["TrustedAP"][0]['name']
    con_devices[trustetAP] = False

    print("waiting to connect the following devices")
    print(con_devices)

    clients = {}
    con_devices_check(server=server,con_devices=con_devices,clients=clients)
    print("after con_devices_check")
    print(con_devices)

    centralized = len(clients) == 1

    #specify type of logging to be done depending on devices connected
    for sock,value in clients.items():
        if centralized:
            sock.send("run centralized logging".encode('utf-8'))
        elif utils.load_json()["TrustedAP"][0]['name'] in value and set(value).isdisjoint(sta_names):
            sock.send("run router logging".encode('utf-8'))
        else:
            sock.send("run esp logging".encode('utf-8'))
    print(clients)
    return clients

def recv_metric_data(client):
    #set timeout, avoid block
    client.settimeout(5.0)
    client.send(b"ok")
    #name of file to be stored
    file_name = client.recv(1024).decode('utf-8')
    client.send(b"ok")
    
    print(file_name)
    file_size = client.recv(1024).decode('utf-8')
    file_size = int(file_size)
    client.send(b"ok")

    buffer = b""
    while(file_size > len(buffer)):
        data = client.recv(1024*4)
        buffer += data
    
    #write file name to be stored
    with open(os.path.join(FULLPATH,file_name),"wb") as f:
        f.write(buffer)

    print("done")
    

def stop_metric_logs(clients):
    #can send anything, the client waits on a signal top stop
    stop_msg = "stop logging"
    for client, devices in clients.items():
        client.send(stop_msg.encode('utf-8'))
        for _ in devices:
            recv_metric_data(client)
    


tcpdump = None

def start_traffic_log():
    global tcpdump
    # start monitor mode
    os.system(f"sshpass -p 'halow' ssh root@10.42.01 'date -s \'@$(date -u +%s)\''")

    os.system(f"sshpass -p '{MON_PASS}' ssh {MON_USER}@{MON_IP} './../sniffer_mode.sh'")

    with open(os.path.join(FULLPATH,"traffic.pcap"), "wb") as pcap_file:
        tcpdump_cmd = [
            "sshpass", "-p" ,MON_PASS, 
            "ssh" ,f"{MON_USER}@{MON_IP}", 
            "tcpdump", "-i", "morse0", "-U", "-s0", "-w", "-"
            ]
        
        tcpdump = subprocess.Popen(
            tcpdump_cmd, 
            stdout=pcap_file,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=True
            )
    

def end_traffic_log():
    global tcpdump
    os.system(f"sshpass -p '{MON_PASS}' ssh {MON_USER}@{MON_IP} 'kill $(pgrep tcpdump)'")
    #stop logging process
    tcpdump.terminate()
    tcpdump.wait()

def log_metaData(att_metaData):
    with open(os.path.join(FULLPATH, "attackMetaData.json"),"w") as file:
        json.dump(att_metaData,file)

def post_process():
    cwd = os.path.dirname(os.path.abspath(__file__))
    corrected_path = os.path.normpath(os.path.join(cwd, os.pardir, FULLPATH))
    processLogs.log_events(os.path.join(corrected_path,"traffic.pcap"),WIRESHARK_FILTER,corrected_path)

    plotter_script = os.path.join(cwd, "plotter.py")
    try:
        import sys
        subprocess.run([sys.executable, plotter_script], cwd=corrected_path, check=True)
        print(f"Successfully ran plotter.py in {corrected_path}")
    except Exception as e:
        print(f"Error running plotter.py: {e}")


"""
def start_monitor_device_logging():
    for temppcap in Path(PCAP_SRC).iterdir():
        if temppcap.is_file() and temppcap.suffix == ".pcap":
            processLogs.log_events(temppcap,WIRESHARK_FILTER)

            print("done prcessing logs")
            temppcap.rename(os.path.join(PCAP_DST,PCAP))
            print("moved processed pcap to the pcaps folder")
"""
