import socket
import utils
import threading
import select
import time

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(("0.0.0.0", 5005))
s.listen(5)

print("UDP server running...")

lock = threading.Lock()

con_devices = {device["name"]:True for device in utils.load_json()["STA"]}

trustedAP = utils.load_json()["TrustedAP"][0]
con_devices[trustedAP["name"]] = True


clients = {}

def get_in_dev_con(client):
    while(True):
        msg = client.recv(1024)
        msg_str = msg.decode('utf-8')
        if msg is None:
            continue
        if msg_str == "done":
            break
        elif msg:
            msg_split = msg_str.split(',')
            print(msg_split)
            if msg_split[1] == "True":
                with lock:
                    con_devices[msg_split[0]] = True
            if msg_split[1] == "False":
                with lock:
                    if client not in clients:
                        clients[client] = [msg_split[0]]
                    else:
                        clients[client].append(msg_split[0])
                    con_devices[msg_split[0]] = False
    
    print("")
    print("recived everything exiting thread")
    print("")



def con_devices_check(server_socket):
    clients2 = set()
    server_socket.setblocking(False)
    while True:
        with lock:
            if all(value == False for value in con_devices.values()):
                break
        try:
            con, _, = server_socket.accept()
            if con is not None:
                con.setblocking(True)
                clients2.add(con)
                threading.Thread(target=get_in_dev_con, args=(con,)).start()
        except BlockingIOError:
            time.sleep(0.01)
            pass
    
    print("all devices connected")



print("waiting to connect the following devices")
print(con_devices)

con_devices_check(s)

print(clients)

connections = []
centralized = len(clients) == 1


for sock,value in clients.items():
    if centralized:
        sock.send("run centralized logging".encode('utf-8'))
    elif trustedAP['name'] in value:
        sock.send("run router logging".encode('utf-8'))
    else:
        sock.send("run esp logging".encode('utf-8'))

time.sleep(2.0)
for sock, value in clients.items():
    sock.send("stop logging".encode('utf-8'))

def recv_data(client,name):
    file_name = client.recv(1024).decode('utf-8')
    test = client.recv(1024).decode('utf-8')
    file_size = int(test)

    buffer = b""
    while(file_size > len(buffer)):
        data = client.recv(1024*4)
        buffer += data

    with open(f"{name}.csv","wb") as f:
        f.write(buffer)

    print("done")

for sock, value in clients.items():
    for v in value:
        recv_data(sock,v)

    sock.close()

print("test done")
