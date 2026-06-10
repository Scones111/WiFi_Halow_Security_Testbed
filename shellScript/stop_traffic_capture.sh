#!/bin/bash
sshpass -p "halow" ssh root@10.42.0.1 "kill \$(pgrep tcpdump)"

sshpass -p "halow" scp root@10.42.0.1:../pcap/capture.pcap "./capture_$(date +%s).pcap"
