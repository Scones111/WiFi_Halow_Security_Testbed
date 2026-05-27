#!/bin/ash

iw dev wlan0 del
iw phy phy0 interface add mon0 type monitor
ifconfig mon0 up && ifconfig morse0 up
morse_cli -i mon0 channel -c 920500 -o 1 -p 1 -n 0
