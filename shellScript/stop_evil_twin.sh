#!/bin/bash

echo "stopping evil twin"

sshpass -p "halow" ssh root@10.42.0.2 "./ap_mode_down.sh"

echo "evil twin is down"
