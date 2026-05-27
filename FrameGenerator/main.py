import frames
from SDRtransmitTCP import transmitData
from scapy.all import wrpcap

if __name__ == "__main__":
    print("Frame Generator")
    print("=========================================================================")
    print("This script was created as a part of a master thesis project to generate frames for testing and evaluation of WiFi HaLow networks.\n")
    print("The script is designed to generate frames and allowing for saving them to a pcap file or transmitting them directly to GNU Radio for over-the-air transmission using a Software Defined Radio (SDR).\n")
    print("For over the air transmission using a SDR, please ensure that GNU Radio is running and ready to receive frames on the specified port.\n")
    print("by default, the script will attempt to connect to GNU Radio on localhost (127.0.0.1:52001), but you can modify the host and port in the transmitData function if needed.\n")
    print("=========================================================================")
    raw_frame = None
    continue_choice = None
    while(True):
        print("Do you want to generate Frames or transmit raw frames? (1 for write frames to pcap, 2 for transmit raw frames)")
        mode_choice = input("Enter the number corresponding to the mode: ")
        while(True):
            invalid_frame_choice = True
            print("\nselect frame type to generate:")
            print("1. deauthentication Frame")
            frame_choice = input("Enter the number corresponding to the frame type: ")
            match (frame_choice):
                case "1":
                    invalid_frame_choice = False
                    raw_frame = frames.start_deauthentication_frame_generator()
                case _:
                    print("Invalid choice. Please enter a valid number.")
                    continue


            if mode_choice == "1" and not invalid_frame_choice:
                print("write frames to pcap")
                print("Please enter the name of the pcap file to save the frames (e.g., 'frame').")
                pcap_name = input("Pcap name:")
                path = input("Enter the path to save the pcap file (e.g., 'C:/Users/username/Desktop/'): ")
                full_path = f"{path}{pcap_name}.pcap"
                wrpcap(full_path, raw_frame)


            elif mode_choice == "2" and not invalid_frame_choice:
                print("transmit raw frames")
                transmitData(raw_frame)


            print("\nDo you want to select another frame type? (y/n)")
            continue_choice = input("Enter 'y' for yes or 'n' for no: ")
            while(continue_choice not in ["y", "n"]):
                continue_choice = input("Invalid input. Please enter 'y' for yes or 'n' for no: ")
                
            if continue_choice == "n":
                print("Exiting...")
                break
        
        continue_choice = input("\nDo you want to select another mode? (y/n):")
        while(continue_choice not in ["y", "n"]):
            continue_choice = input("Invalid input. Please enter 'y' for yes or 'n' for no: ")
        if continue_choice == "n":
            break
