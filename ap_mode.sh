#!/bin/bash

# 1. Prevent NetworkManager from hijacking the HaLow interface
sudo nmcli device set wlan1 managed no

# 2. Turn on wireless lan and strip away any lingering hardware blocks
sudo nmcli radio wifi on
sudo rfkill unblock wifi

# Wait for the radio to globally enable
while [[ "$(nmcli radio wifi)" != "enabled" ]]; do sleep 1; done

# 3. Wake up the Morse Micro chip from its sleep state
sudo ip link set wlan1 down
sleep 1
sudo ip link set wlan1 up
sleep 1

# 4. Start the custom access point daemon in the background
cd ~/hostap/hostapd
sudo ./hostapd_s1g -B halow_ap.conf

# 5. Assign the gateway IP address to the interface
sudo ip addr add 10.0.0.1/24 dev wlan1

# 6. Fire up the DHCP server to handle client IPs
sudo systemctl restart dnsmasq
