#!/bin/bash
sshpass -p "halow" ssh root@10.42.0.1 "kill \$(pgrep tcpdump)"

#store to tempory folder to be processed later
sshpass -p "halow" scp root@10.42.0.1:../pcap/capture.pcap "./../attackerDevice/monitor/tempPcap/capture_$(date +%s).pcap"