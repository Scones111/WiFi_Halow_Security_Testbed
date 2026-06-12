from scapy.all import *

def transmitData(packet,host="127.0.0.1",port=52001):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.send(packet)
        #print(f"Sent {len(packet)} byte PV0 Management Action frame to GNU Radio")
    except Exception as e:
        print(f"Socket error: {e}")
    finally:
        s.close()