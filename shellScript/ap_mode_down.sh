#!/bin/bash

# 1. Kill the custom AP daemon running in the background
sudo killall hostapd_s1g 2>/dev/null

# 2. Remove the static gateway IP address from the interface
sudo ip addr flush dev wlan1

3. Stop the DHCP server
sudo systemctl stop dnsmasq

# 4. Bring the physical interface down safely
sudo ip link set wlan1 down

# 5. Allow NetworkManager to take control of the interface again
sudo nmcli device set wlan1 managed yes

# 6. Turn off wireless lan
sudo nmcli radio wifi off
