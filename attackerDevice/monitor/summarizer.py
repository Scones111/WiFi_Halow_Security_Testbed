
import numpy as np
import matplotlib.pyplot as plt

# 1. Generer simuleret RSSI data baseret på jeres faste 915 MHz HaLow testbed
np.random.seed(42)
n_samples = 150

# Safe State: Signalet fra jeres WM6108 er låst fast (lav varians, gennemsnit på -45 dBm)
safe_rssi = np.random.normal(loc=-45, scale=0.8, size=n_samples)

# Attack State: En Evil Twin spoofer identiteten. Radiokampen spreder signalet voldsomt
attack_rssi = np.random.normal(loc=-35, scale=4.5, size=n_samples)

# Sæt dataene sammen til én sammenhængende tidslinje
timeline_rssi = np.concatenate([safe_rssi, attack_rssi])

# 2. Beregn den løbende varians (Rolling Variance) med et glidende vindue på 30 målinger
window_size = 30
rolling_variance = [
    np.var(timeline_rssi[i-window_size:i]) if i >= window_size else np.nan 
    for i in range(len(timeline_rssi))
]

# 3. Opsæt visualiseringen (To del-grafer under hinanden)
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)

# Øverste graf: Det rå RSSI signal over tid
ax1.plot(range(n_samples), safe_rssi, color='#2ecc71', label='Safe State (Legit WM6108)', alpha=0.8)
ax1.plot(range(n_samples, n_samples*2), attack_rssi, color='#e74c3c', label='Attack State (Evil Twin Spoofing)', alpha=0.8)
ax1.axvline(x=n_samples, color='#34495e', linestyle='--', linewidth=2)
ax1.set_ylabel('Rå RSSI (dBm)', fontsize=12)
ax1.set_title('Wi-Fi HaLow Testbed: Signalbillede og Varians under Angreb', fontsize=14, fontweight='bold')
ax1.grid(True, linestyle=':', alpha=0.6)
ax1.legend(loc='upper right')

# Nederste graf: Den eksploderende varians (Spredningen)
ax2.plot(range(n_samples*2), rolling_variance, color='#9b59b6', linewidth=2.5, label='Løbende Varians (Vinduessize=30)')
ax2.axvline(x=n_samples, color='#34495e', linestyle='--', linewidth=2)
ax2.set_ylabel('RSSI Varians ($\sigma^2$)', fontsize=12)
ax2.set_xlabel('Tidslinje (Måleintervaller / Pakker)', fontsize=12)
ax2.grid(True, linestyle=':', alpha=0.6)
ax2.legend(loc='upper left')

plt.tight_layout()
plt.show()

def dragonDos_summarize():
    pass

def evilTwin_summarize():
    pass