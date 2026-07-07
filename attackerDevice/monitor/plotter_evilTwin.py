import pandas as pd
import matplotlib.pyplot as plt
import os

Eviltwin = "9c:04:b6:46:07:34"
trustedAP = "78:72:64:ea:b9:14"
server = "3c:22:7f:71:dc:b8"
client ="3c:22:7f:71:df:d6"

attack_log = pd.read_csv('attackerDevice/monitor/results/evilTwin/second_evilTwin_50_0.02/ATTACK_LOG.csv')
client_metric = pd.read_csv('attackerDevice/monitor/results/evilTwin/second_evilTwin_50_0.02/tcp_client_metrics.csv')
server_metric = pd.read_csv('attackerDevice/monitor/results/evilTwin/second_evilTwin_50_0.02/tcp_server_metrics.csv')

#attack_log = pd.read_csv('ATTACK_LOG.csv')
#client_metric = pd.read_csv('tcp_client_metrics.csv')
#server_metric = pd.read_csv('tcp_server_metrics.csv')

plt.figure(figsize=(12, 6))
attack_log["time_stamp"] = pd.to_datetime(attack_log['time_stamp'],utc=True).dt.tz_convert("Europe/Copenhagen").dt.tz_localize(None)
client_metric["local_time"] = pd.to_datetime(client_metric["local_time"])
server_metric["local_time"] = pd.to_datetime(server_metric["local_time"])

beacon_log = attack_log[attack_log["event_type"] == "S1G Beacon"]
router =  beacon_log[beacon_log["src"] == trustedAP]
et = beacon_log[beacon_log["src"] == Eviltwin]

plt.plot(router['time_stamp'], router['signal_strength'], label='Trusted AP RSSI (dBm)', color='blue')
plt.plot(et['time_stamp'], et['signal_strength'], label='Evil Twin RSSI (dBm)', color='red')


plt.xlabel("APs RSSI over time")
plt.ylabel("RSSI (dBm)")
plt.legend(loc='best')
plt.grid()
plt.savefig('APs_RSSI.png')

deauth_events = attack_log[attack_log["event_type"] == "Deauthentication"]
auth_events = attack_log[attack_log["event_type"] == "Association Response"]

plt.figure(figsize=(12, 6))
label = set()
for idx, deauth in deauth_events.iterrows():
    if "deauth" not in label:
        plt.axvline(x=deauth['time_stamp'], color='black', label="Deauthentication", linestyle='--', alpha=0.7, linewidth=1.2)
        label.add("deauth")
    else:
        plt.axvline(x=deauth['time_stamp'], color='black', linestyle='--', alpha=0.7, linewidth=1.2)

for idx, auth in auth_events.iterrows():
    if int(auth["status"]) == 0:
        temp = None
        if client == auth["dst"]:
            temp = "Client"
        elif server == auth["dst"]:
            temp = "Server"

        ap = "Evil Twin" if auth["bssid"] == Eviltwin else "Trusted AP"
        label_txt = f"{temp} associated to {ap}"
        color = 'purple' if auth["bssid"] == Eviltwin else 'green'

        if label_txt not in label:
            plt.axvline(x=auth['time_stamp'], color=color, linestyle='--', alpha=0.8, linewidth=1.2, label=label_txt)
            label.add(label_txt)
        else:
            plt.axvline(x=auth['time_stamp'], color=color, linestyle='--', alpha=0.8, linewidth=1.2)

plt.plot(client_metric["local_time"],client_metric["rssi"], label='Clients recieved RSSI from AP (dBm)', color='blue')
plt.plot(server_metric["local_time"],server_metric["rssi"], label='Servers recieved RSSI from AP (dBm)', color='red')
plt.xlabel("Device received RSSI over time")
plt.ylabel("RSSI (dBm)")
plt.legend(loc='best')
plt.grid()
plt.xlabel("APs RSSI over time")
plt.savefig('devices_RSSI.png')


plt.figure(figsize=(12, 6))
label = set()
for idx, deauth in deauth_events.iterrows():
    if "deauth" not in label:
        plt.axvline(x=deauth['time_stamp'], color='black', label="Deauthentication", linestyle='--', alpha=0.7, linewidth=1.2)
        label.add("deauth")
    else:
        plt.axvline(x=deauth['time_stamp'], color='black', linestyle='--', alpha=0.7, linewidth=1.2)

for idx, auth in auth_events.iterrows():
    if int(auth["status"]) == 0:
        temp = None
        if client == auth["dst"]:
            temp = "Client"
        elif server == auth["dst"]:
            temp = "Server"

        ap = "Evil Twin" if auth["bssid"] == Eviltwin else "Trusted AP"
        label_txt = f"{temp} associated to {ap}"
        color = 'purple' if auth["bssid"] == Eviltwin else 'green'

        if label_txt not in label:
            plt.axvline(x=auth['time_stamp'], color=color, linestyle='--', alpha=0.8, linewidth=1.2, label=label_txt)
            label.add(label_txt)
        else:
            plt.axvline(x=auth['time_stamp'], color=color, linestyle='--', alpha=0.8, linewidth=1.2)

plt.plot(client_metric["local_time"],client_metric["throughput_bps"], label='Clients Throughput (bps)', color='blue')
plt.plot(server_metric["local_time"],server_metric["throughput_bps"], label='Servers Throughput (bps)', color='red')
plt.xlabel('Throughput (bps) over Time')
plt.ylabel("Throughput")
plt.legend(loc='best')
plt.grid()
plt.savefig('device_throuhput.png')