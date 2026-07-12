# WiFi_Halow_Security_Testbed

This is a testbed, that was developed in relation to a master thesis, with the purpose of implementing attacks for Wi-Fi HaLow.

Interoperability has been tested with the following devices
- [HT-H7608](https://heltec.org/project/ht-h7608/)
- [HackRF One](https://greatscottgadgets.com/hackrf/one/)
- [ESP32s3](https://wiki.seeedstudio.com/getting_started_with_wifi_halow_module_for_xiao/) developed

The tool was deployed and conducted in the kali linux virtual machine environment.

To allow for easy execution, [mm-iot-esp32](https://github.com) Developed by seeed studio and [gr-ieee802.11ah](https://github.com) developed by .


## 


## Getting Started
Brief description of what the tool does, its main purpose, and the types of attacks or scenarios it supports (e.g., Evil Twin, Dragonblood resource exhaustion).
The testbed implements two attacks:

Currently supports two different attacks
- Evil Twin
- Dragonblood resource exhaustion

Capabilities:
- Allows for the execution of attacks, with out without logging
- Capture the the metrics of the basenetwork
- Initiate the client for metric logging 

Important detail: to allow for the execution of attacks, and logging of data, it requires at minimum two laptops, such that one can capture the metrics of the connected device and the router. while the other is performing that attack.

The tool has been developed to allow for the creation of multiple TCP client, that will connect and transmit the result to a server, which is the main attack device.

<img width="502" height="152" alt="image" src="https://github.com/user-attachments/assets/558989cb-bdf6-4681-9245-e3dab0ad1f52" />


### Prerequisites

- Python 3.x
- SDR
- Wireshark

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Scones111/WiFi_Halow_Security_Testbed.git
   cd WiFi_Halow_Security_Testbed
   ```

2. **Create a virtual environment:**
   (Assuming a Linux/macOS environment)
   ```bash
   python3 -m venv .venv
   ```

3. **Activate the virtual environment:**
   ```bash
   source .venv/bin/activate
   ```

4. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
