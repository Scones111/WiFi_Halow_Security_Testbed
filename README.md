# Disclaimer

### ⚠️ Academic Evaluation Notice: Master's Thesis

**Project Origin & Attribution**  
This repository utilizes two open-source projects: **gr-ieee802-11ah by irongiant33** and **mm-iot-esp32 by Seeed Studio**. To ensure proper academic attribution and comply with open-source licensing, we chose to preserve the original `.git` commit history from these repositories. Therefore, the original developers appear in the GitHub contributors sidebar.

**Scope of Original Thesis Work**  
The novel contributions for our Master's thesis begin on **21st of may 2026**, starting specifically from commit `015a261e221b659bd2272f98d74c7ab9fb43fff3`. All commits before this point belong entirely to the original open-source authors of the respective projects. 

For academic evaluation, please refer **only** to the work committed by `Scones111` and `simonhermansen`. 

Our original contributions are located in the following directories:
* `/attackerDevice` - A tool to perform security tests using the tools from the different folders
* `/mm-iot-esp32/tcp-client/main/src/tcp_client.c` - Creates a TCP client to produce background traffic - using the prebuilt configurations made by Seeed Studios, and the underlying morse micro
* `/mm-iot-esp32/tcp-server/main/src/tcp_server.c` - Creates a TCP server to produce background traffic - using the prebuilt configurations made by Seeed Studios, and the underlying morse micro
* `/gr-ieee802-11ah/examples/halow_tx.grc` - adapted to allow for 1MHz transmission for HackRF One
* `./shellscripts` - Helper scripts created throught out this project

# WiFi_Halow_Security_Testbed

This is a testbed that was developed in relation to a master's thesis to implement attacks for Wi-Fi HaLow.

Interoperability has been tested with the following devices
- [HT-H7608](https://heltec.org/project/ht-h7608/)
- [HackRF One](https://greatscottgadgets.com/hackrf/one/)
- [ESP32s3](https://wiki.seeedstudio.com/getting_started_with_wifi_halow_module_for_xiao/) developed

The tool was deployed and executed in the Kali Linux virtual machine environment.

To allow for easy execution, [mm-iot-esp32](https://github.com) Developed by seeed studio and [gr-ieee802.11ah](https://github.com) developed by .


## Getting Started
The testbed implements two attacks:

Currently supports two different attacks
- Evil Twin
- Dragonblood resource exhaustion

Capabilities:
- Allows for the execution of attacks, with or without logging
- Captures the metrics of the basenetwork
- Initiate the client for metric logging

Important detail: to allow for the execution of attacks and logging of data, it requires at minimum two laptops, such that one can capture the metrics of the connected device and the router. while the other is performing that attack.

## Installation guide
First step is to run the -r requirement.txt to provude the necessary libraries.

```bash
pip install -r requirements.txt
```

The tool requires the use of GNU Radio, when running the tool, it will execute a shellscript that will activate a hackrf in tx.

```bash
sudo apt-get install gnuradio
```

### Installation of evil twin
For the installation of the evil twin you can follow the guide in [RPI5 HaLow Build thread](https://community.morsemicro.com/t/build-thread-halow-for-raspberry-pi-os/1124)

It will provide you the necessary tools in order to instiate a RPI5 to act as a station and a AP.

Once the RPI5 has been installed, and the packages from morse micro has been downloaded. Navigate to the **/hostap/hostapd** folder, and create a copy of the hostapd_s1g.conf, called halow_ap.conf.

Inside the shellscript folder exist two different shell scripts for enabling and disabling the AP: ap_mode.sh and ap_mode_down.sh.

Install on rouge AP using, example:
```bash
scp ap_mode.sh rpi@raspberrypi.local:ap_mode.sh
```

### Setup testbed environment
Two laptops are recommended, one laptop is responsible for connection to the esp32 devices and the router, while the other is an attacker in the test environment.

laptop 1, connected to the HackRF One, and a monitor device through an SSH connection

laptop 2, connected to esp32, connected via usb and router connected via ssh

Communication happens over communication, it is recommended to use the tailscale VPN to establish a direct tunnel.

## Example usage
The tool has been developed to allow for the creation of multiple TCP clients that will connect and transmit the result to a server, which is the main attack device.

<img width="502" height="152" alt="image" src="https://github.com/user-attachments/assets/558989cb-bdf6-4681-9245-e3dab0ad1f52" />

To connect a client for router metrics:

```bash
python main.py metric_client
```
For each attack, a duration and rate is set, duration is set in seconds and rate set in frames per seconds.

### Evil Twin
To perform an Evil Twin attack and collect metrics, run attack_log with attack=1, duration=300 seconds (5 minutes), and rate=1 (1 frame/s):
```bash
python main.py attack_log attack 1 300 1
```
Note: The Evil Twin AP requires to be initialized in order to perform attack, so prior to execution, on the rpi5 call:
```bash
./ap_mode.sh
```

### Dragonblood resource exhuastian attack:
To perform Dragonblood resource exhuastian attack, run attack_log with attack=2, duration=399 seconds (5 minutes), and rate=1 (1 frames/s):
```bash
python main.py attack_log attack 2 300 1
```

## Licensing and Dependencies

This project is licensed under the **GNU General Public License v3.0** (see the root `LICENSE` file).

This repository contains third-party components housed in their own subdirectories:
*   **`gr-ieee802-11ah/`**: Licensed under the GNU General Public License v3.0.
*   **`mm-iot-esp32/`**: Licensed under the Apache License 2.0 (fully compatible with GPLv3 distribution).

Please ensure you respect the respective licenses when modifying files within those subdirectories.
