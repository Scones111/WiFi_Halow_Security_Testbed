import os
import sys
import pandas as pd
import statistics

TRUSTED_AP_MAC = "78:72:64:ea:b9:14".lower()
ROGUE_AP_MAC = "9c:04:b6:46:07:34".lower()
SERVER_MAC = "3c:22:7f:71:dc:b8".lower()
CLIENT_MAC = "3c:22:7f:71:df:d6".lower()

def print_stats(name, data):
    # Convert pandas series or list to a list, dropping NaNs
    if isinstance(data, pd.Series):
        data = data.dropna().tolist()
    else:
        data = [x for x in data if pd.notna(x)]
        
    # Filter out >= 0 values just in case
    data = [x for x in data if x < 0]
        
    if not data:
        print(f"{name}: No valid RSSI data found.")
        return
        
    avg_rssi = statistics.mean(data)
    if len(data) > 1:
        stdev_rssi = statistics.stdev(data)
    else:
        stdev_rssi = 0.0
        
    print(f"{name}:")
    print(f"  Count: {len(data)}")
    print(f"  Average RSSI: {avg_rssi:.2f} dBm")
    print(f"  Std Dev: {stdev_rssi:.2f} dBm")
    print()

def process_metrics(metrics_df, device_mac, auth_events):
    trusted_rssi = []
    rogue_rssi = []

    if metrics_df.empty:
        return trusted_rssi, rogue_rssi

    # Filter auth events for this specific device
    device_auths = auth_events[(auth_events["dst"].str.lower() == device_mac) & (auth_events["status"] == '0')].sort_values(by="time_stamp")
    
    for _, row in metrics_df.iterrows():
        ts = row["local_time"]
        rssi_val = row["rssi"]
        
        if pd.isna(rssi_val) or rssi_val >= 0:
            continue
            
        past_auths = device_auths[device_auths["time_stamp"] <= ts]
        
        # If the last successful association before this metric was to the Rogue AP
        if not past_auths.empty and past_auths.iloc[-1]["bssid"].lower() == ROGUE_AP_MAC:
            rogue_rssi.append(rssi_val)
        else:
            trusted_rssi.append(rssi_val)
            
    return trusted_rssi, rogue_rssi

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 rssi_calculator.py <path_to_directory>")
        sys.exit(1)
        
    target_path = sys.argv[1]
    
    if os.path.isfile(target_path):
        base_dir = os.path.dirname(target_path)
    else:
        base_dir = target_path

    attack_log_path = os.path.join(base_dir, "ATTACK_LOG.csv")
    client_metrics_path = os.path.join(base_dir, "tcp_client_metrics.csv")
    server_metrics_path = os.path.join(base_dir, "tcp_server_metrics.csv")
    
    missing_files = [p for p in [attack_log_path, client_metrics_path, server_metrics_path] if not os.path.exists(p)]
    if missing_files:
        print("Error: Missing required files in the target directory:")
        for mf in missing_files:
            print(f"  - {mf}")
        sys.exit(1)
            
    print(f"Processing data from {base_dir}...\n")
    
    # 1. Load ATTACK_LOG for AP RSSI and association events
    try:
        attack_log = pd.read_csv(attack_log_path, dtype={'status': str})
    except Exception as e:
        print(f"Error reading ATTACK_LOG.csv: {e}")
        sys.exit(1)
        
    # Convert time_stamp to local time format similar to metrics
    attack_log["time_stamp"] = pd.to_datetime(attack_log['time_stamp'], utc=True).dt.tz_convert("Europe/Copenhagen").dt.tz_localize(None)
    
    # Extract AP RSSI directly from the attack log (Beacons)
    ap_beacons = attack_log[attack_log["event_type"] == "S1G Beacon"]
    trusted_ap_rssi = ap_beacons[ap_beacons["src"].str.lower() == TRUSTED_AP_MAC]["signal_strength"]
    rogue_ap_rssi = ap_beacons[ap_beacons["src"].str.lower() == ROGUE_AP_MAC]["signal_strength"]
    
    print("--- Access Point (AP) RSSI Statistics (from ATTACK_LOG.csv) ---")
    print_stats("Trusted AP", trusted_ap_rssi.tolist())
    print_stats("Rogue AP (Evil Twin)", rogue_ap_rssi.tolist())

    # 2. Extract ESP RSSI from tcp_ metrics, split by pre/post deauth
    auth_events = attack_log[attack_log["event_type"] == "Association Response"]
    
    try:
        client_metrics = pd.read_csv(client_metrics_path)
        client_metrics["local_time"] = pd.to_datetime(client_metrics["local_time"])
        server_metrics = pd.read_csv(server_metrics_path)
        server_metrics["local_time"] = pd.to_datetime(server_metrics["local_time"])
    except Exception as e:
        print(f"Error reading metrics CSVs: {e}")
        sys.exit(1)
        
    client_trusted, client_rogue = process_metrics(client_metrics, CLIENT_MAC, auth_events)
    server_trusted, server_rogue = process_metrics(server_metrics, SERVER_MAC, auth_events)
    
    print("--- Client (STA) RSSI Statistics (from tcp_client_metrics.csv) ---")
    print_stats("Pre-deauthentication (connected to Trusted AP)", client_trusted)
    print_stats("Post-deauthentication (connected to Rogue AP)", client_rogue)
    
    print("--- Server (STA) RSSI Statistics (from tcp_server_metrics.csv) ---")
    print_stats("Pre-deauthentication (connected to Trusted AP)", server_trusted)
    print_stats("Post-deauthentication (connected to Rogue AP)", server_rogue)

if __name__ == "__main__":
    main()
