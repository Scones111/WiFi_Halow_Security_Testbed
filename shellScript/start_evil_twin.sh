#!/bin/bash

echo "initiating evil Twin"

sshpass -p "halow" ssh rpi5@10.42.0.2 "./ap_mode.sh"

echo "evil twin up - can now disconnect ethernet cable"
