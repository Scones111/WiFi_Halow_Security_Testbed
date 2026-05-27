#!/bin/bash

# 1. Prevent NetworkManager from hijacking the HaLow interface
sudo nmcli device set wlan1 managed no

# 2. Start the custom access point daemon in the background
cd ~/hostap/hostapd
sudo ./hostapd_s1g -B halow_ap.conf

# 3. Assign the gateway IP address to the interface
sudo ip addr add 10.0.0.1/24 dev wlan1

# 4. Fire up the DHCP server to handle client IPs
sudo systemctl restart dnsmasq
