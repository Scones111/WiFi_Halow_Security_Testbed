#!/bin/bash
#sync time
TIMESTAMP=$(date +%s)

sshpass -p "halow" ssh root@10.42.0.1 "date -s @$TIMESTAMP"

sshpass -p "halow" ssh root@10.42.0.1 "rm -f ../pcap/capture.pcap"

sshpass -p "halow" ssh root@10.42.0.1 "./../sniffer_mode.sh"

sleep 2

sshpass -p "halow" ssh root@10.42.0.1 "tcpdump -i morse0 -w ../pcap/capture.pcap"

echo "traffic monitor device is setup and running"
