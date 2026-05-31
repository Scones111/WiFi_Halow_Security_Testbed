def print_intro():

    intro_message = """
ATTACKER DEVICE
========================================================================
This script was created as a part of a master thesis project to generate 
frames for testing and evaluation of WiFi HaLow networks.

The script is designed to generate frames and allowing for saving them 
to a pcap file or transmitting them directly to GNU Radio for over-the-air 
transmission using a Software Defined Radio (SDR).

For over the air transmission using a SDR, please ensure that GNU Radio 
is running and ready to receive frames on the specified port.

by default, the script will attempt to connect to GNU Radio on localhost 
(127.0.0.1:52001), but you can modify the host and port in the transmitData 
function if needed.
========================================================================
"""
    print(intro_message)
