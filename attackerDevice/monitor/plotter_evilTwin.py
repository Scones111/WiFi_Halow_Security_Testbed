import pandas as pd
import matplotlib.pyplot as plt
import os

Eviltwin = "9c:04:b6:46:07:34"
trustedAP = "78:72:64:ea:b9:14"
server = "3c:22:7f:71:dc:b8"
client ="3c:22:7f:71:df:d6"

#attack_log = pd.read_csv('attackerDevice/monitor/results/evilTwin/second_evilTwin_50_0.02/ATTACK_LOG.csv')
#client_metric = pd.read_csv('attackerDevice/monitor/results/evilTwin/second_evilTwin_50_0.02/tcp_client_metrics.csv')
#server_metric = pd.read_csv('attackerDevice/monitor/results/evilTwin/second_evilTwin_50_0.02/tcp_server_metrics.csv')

attack_log = pd.read_csv('ATTACK_LOG.csv')
client_metric = pd.read_csv('tcp_client_metrics.csv')
server_metric = pd.read_csv('tcp_server_metrics.csv')

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

def plot_segmented_metric(df, device_mac, metric_col, label_prefix, color, auth_events, Eviltwin):
    if df.empty:
        return
        
    device_auths = auth_events[(auth_events["dst"] == device_mac) & (auth_events["status"] == 0)].sort_values(by="time_stamp")
    
    linestyles = []
    for _, row in df.iterrows():
        ts = row["local_time"]
        past_auths = device_auths[device_auths["time_stamp"] <= ts]
        
        if not past_auths.empty and past_auths.iloc[-1]["bssid"] == Eviltwin:
            linestyles.append(":") # dotted for Evil Twin
        else:
            linestyles.append("-") # solid for Trusted AP
            
    df["linestyle"] = linestyles
    
    segments = []
    current_segment = {"linestyle": df.iloc[0]["linestyle"], "times": [df.iloc[0]["local_time"]], "values": [df.iloc[0][metric_col]]}
    
    for i in range(1, len(df)):
        ls = df.iloc[i]["linestyle"]
        ts = df.iloc[i]["local_time"]
        val = df.iloc[i][metric_col]
        
        if ls == current_segment["linestyle"]:
            current_segment["times"].append(ts)
            current_segment["values"].append(val)
        else:
            current_segment["times"].append(ts)
            current_segment["values"].append(val)
            segments.append(current_segment)
            current_segment = {"linestyle": ls, "times": [ts], "values": [val]}
            
    segments.append(current_segment)
    
    trusted_labeled = False
    et_labeled = False
    
    for seg in segments:
        ls = seg["linestyle"]
        if ls == "-" and not trusted_labeled:
            plt.plot(seg["times"], seg["values"], label=f"{label_prefix} (Trusted AP)", color=color, linestyle=ls)
            trusted_labeled = True
        elif ls == ":" and not et_labeled:
            plt.plot(seg["times"], seg["values"], label=f"{label_prefix} (Evil Twin)", color=color, linestyle=ls)
            et_labeled = True
        else:
            plt.plot(seg["times"], seg["values"], color=color, linestyle=ls)

plt.figure(figsize=(12, 6))
label = set()
for idx, deauth in deauth_events.iterrows():
    if "deauth" not in label:
        plt.axvline(x=deauth['time_stamp'], color='orange', label="Deauthentication", linestyle='--', alpha=0.7, linewidth=1.2)
        label.add("deauth")
    else:
        plt.axvline(x=deauth['time_stamp'], color='orange', linestyle='--', alpha=0.7, linewidth=1.2)

plot_segmented_metric(client_metric, client, "rssi", "Client RSSI", "blue", auth_events, Eviltwin)
plot_segmented_metric(server_metric, server, "rssi", "Server RSSI", "red", auth_events, Eviltwin)

plt.xlabel("Device received RSSI over time")
plt.ylabel("RSSI (dBm)")
plt.legend(loc='best')
plt.grid()
plt.savefig('devices_RSSI.png')


plt.figure(figsize=(12, 6))
label = set()
for idx, deauth in deauth_events.iterrows():
    if "deauth" not in label:
        plt.axvline(x=deauth['time_stamp'], color='orange', label="Deauthentication", linestyle='--', alpha=0.7, linewidth=1.2)
        label.add("deauth")
    else:
        plt.axvline(x=deauth['time_stamp'], color='orange', linestyle='--', alpha=0.7, linewidth=1.2)

plot_segmented_metric(client_metric, client, "throughput_bps", "Client Throughput", "blue", auth_events, Eviltwin)
plot_segmented_metric(server_metric, server, "throughput_bps", "Server Throughput", "red", auth_events, Eviltwin)

plt.xlabel('Throughput (bps) over Time')
plt.ylabel("Throughput")
plt.legend(loc='best')
plt.grid()
plt.savefig('device_throuhput.png')

# Show all figures simultaneously
plt.show()
