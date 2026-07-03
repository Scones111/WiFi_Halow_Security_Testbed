import pyshark

#packets = pyshark.FileCapture("traffic.pcap", 
#                              display_filter="wlan.fc.type=3 and wlan.fc.subtype=1",
#                              keep_packets=False,
#                              use_json=True,
#                              include_raw=True)

# Load data
#df_server = pd.read_csv('tcp_server_metrics.csv').iloc[1:]
#df_client = pd.read_csv('tcp_client_metrics.csv').iloc[1:]
#df_router = pd.read_csv('router_metrics.csv').iloc[1:]
#plot the signal strength of the evil twin and compare it to the original AP

#plot the clock skew of the evil twin and compare it to the original AP
#we use the tsf
# configure later to use the correct logs

#evil_twin_beacon=False
#trustedAP = utils.get_macs("TrustedAP")[0]
#evilTwin = utils.get_macs("EvilTwin")[0]
#for packet in packets:
#    curr_tsf = None
#    curr_offset = None
#    if not first_beacon and packet.wlan.sa == trustedAP:
#        trusted_AP_beacon = True
    

#    if hasattr(packet,"radiotap"):
#        curr_tsf = packet.radiotap.mactime
#        
#        if :
#            tsf = 

#plot the number of droppped packets of the evil twin and compare it to the original AP
# We isolate the clients on the evil twin and see if they can still communicate
import numpy as np
from scipy import stats

# Eksempel på opsamlet data fra jeres testbed (f.eks. 200 pakker hver)
# Udskift med jeres reelle værdier trukket ud via PyShark
rssi_safe = np.random.normal(loc=-45, scale=0.8, size=200)   # WM6108 baseline
rssi_attack = np.random.normal(loc=-35, scale=4.5, size=200) # Evil Twin aktiv

# 1. Beregn grundlæggende statistik
print(f"Safe Mean: {np.mean(rssi_safe):.2f} dBm | Variance: {np.var(rssi_safe):.2f}")
print(f"Attack Mean: {np.mean(rssi_attack):.2f} dBm | Variance: {np.var(rssi_attack):.2f}")

# 2. Matematisk validering via Welchs t-test (Gennemsnitsskit)
t_stat, t_p_value = stats.ttest_ind(rssi_safe, rssi_attack, equal_var=False)
print(f"\nWelch's t-test p-værdi: {t_p_value:.5f}")
if t_p_value < 0.01:
    print("-> VALIDERING: Gennemsnittet har flyttet sig signifikant (Fysisk positions-mismatch bevist).")

# 3. Matematisk validering via F-test (Varians-spredning)
f_stat = np.var(rssi_attack, ddof=1) / np.var(rssi_safe, ddof=1)
f_p_value = 1 - stats.f.cdf(f_stat, len(rssi_attack)-1, len(rssi_safe)-1)
print(f"F-test p-værdi: {f_p_value:.5f}")
if f_p_value < 0.01:
    print("-> VALIDERING: Variansen er eksploderet (Signal-spredning og radiokamp bevist).")

import numpy as np
import pandas as pd

# Fastlås tilfældighed, så vi får præcis samme resultat hver gang
np.random.seed(42)

# Opret tidslinjer for de 3 Markov-faser
t_baseline = np.arange(0, 60, 0.5)       # 0 til 60 sekunder
t_attack = np.arange(60, 140, 0.2)       # 60 til 140 sekunder (højere pakkefrekvens)
t_hijack = np.arange(140, 200, 0.5)      # 140 til 200 sekunder

# 1. Baseline: Ren legitim AP forbindelse (-92 dBm)
sig_baseline = np.random.normal(loc=-92, scale=1.5, size=len(t_baseline))
type_baseline = np.random.choice([12], size=len(t_baseline)) # Kun standard frames

# 2. Angrebsfase: Blandet spektre mellem det legitime signal og Evil Twin
sig_attack = []
type_attack = []
for _ in range(len(t_attack)):
    if np.random.rand() < 0.35: # Legitim AP slipper igennem af og til
        sig_attack.append(np.random.normal(loc=-92, scale=1.8))
        type_attack.append(12) # Standard frame
    else: # Evil Twin dominerer kanalen
        sig_attack.append(np.random.normal(loc=-26, scale=1.0))
        # Evil twin spytter overvejende tomme/null frames (Type 36) ud
        type_attack.append(np.random.choice([36, 36, 12]))

# 3. Hijack Fase: Klienten har sluppet forbindelsen og låst sig på Evil Twin (-26 dBm)
sig_hijack = np.random.normal(loc=-26, scale=1.0, size=len(t_hijack))
type_hijack = np.random.choice([12, 36], size=len(t_hijack))

# Saml alle faser til én stor tidsrække
time_all = np.concatenate([t_baseline, t_attack, t_hijack])
sig_all = np.concatenate([sig_baseline, sig_attack, sig_hijack])
type_all = np.concatenate([type_baseline, type_attack, type_hijack])

# Gem som CSV uden overskrifter (præcis som TShark output)
df_mock = pd.DataFrame({'Time': time_all, 'Signal': sig_all, 'FrameType': type_all})
df_mock.to_csv('eviltwin_3metrics.csv', index=False, header=False)

print("Succes! 'eviltwin_3metrics.csv' er oprettet med realistiske Wi-Fi HaLow angrebsdata.")
