import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os

# 1. Define your parameters
fps_rates = [4, 8, 12, 16, 20, 30]
pwe_values = [0, 1]
macs_to_test = [1, 4, 10]

# 2. Iterate through folders and extract peak CPU %
# data structure: data[pwe][macs]['peak' or 'avg']
data = {pwe: {macs: {'peak': [], 'avg': []} for macs in macs_to_test} for pwe in pwe_values}

for pwe in pwe_values:
    base_dir = f"./sae_pwe={pwe}"
    for macs in macs_to_test:
        for fps in fps_rates:
            folder_name = f"dragondos_10_{fps}_{macs}"
            csv_path = os.path.join(base_dir, folder_name, "router_metrics.csv")
            
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                # Clean the dataset: ignore values below 30 in the 'cpu_used_pct' column
                df_filtered = df[df['cpu_used_pct'] >= 30]
                
                if not df_filtered.empty:
                    # Find the average and peak CPU usage in the 'cpu_used_pct' column
                    peak_cpu = df_filtered['cpu_used_pct'].max()
                    avg_cpu = df_filtered['cpu_used_pct'].mean()
                    data[pwe][macs]['peak'].append(peak_cpu)
                    data[pwe][macs]['avg'].append(avg_cpu)
                else:
                    data[pwe][macs]['peak'].append(np.nan)
                    data[pwe][macs]['avg'].append(np.nan)
            else:
                # If the specific configuration wasn't tested, use np.nan
                data[pwe][macs]['peak'].append(np.nan)
                data[pwe][macs]['avg'].append(np.nan)

# 3. Setup the academic plot style
plt.style.use('seaborn-v0_8-whitegrid') # Clean, readable grid
fig, axs = plt.subplots(2, 2, figsize=(14, 10), sharex=True, sharey=True)

colors = {1: '#1f77b4', 4: '#ff7f0e', 10: '#2ca02c'}
markers = {1: 'o', 4: 's', 10: '^'}
linestyles = {1: '-', 4: '--', 10: '-.'}
labels = {1: '1 Randomized MAC', 4: '4 Randomized MACs', 10: '10 Randomized MACs'}

# 4. Plot the data lines for Peak and Average CPU
for j, pwe in enumerate(pwe_values):
    # Plot Peak CPU
    ax_peak = axs[0, j]
    for macs in macs_to_test:
        ax_peak.plot(fps_rates, data[pwe][macs]['peak'], marker=markers[macs], linestyle=linestyles[macs], 
                     linewidth=2, color=colors[macs], label=labels[macs])
    
    ax_peak.set_title(f'CPU Peak (SAE PWE={pwe})', fontsize=14, pad=10)
    if j == 0:
        ax_peak.set_ylabel('Peak Router CPU Usage (%)', fontsize=12)
    ax_peak.set_ylim(0, 110)
    ax_peak.legend(loc='lower right', fontsize=11, frameon=True, shadow=True)
    
    # Plot Average CPU
    ax_avg = axs[1, j]
    for macs in macs_to_test:
        ax_avg.plot(fps_rates, data[pwe][macs]['avg'], marker=markers[macs], linestyle=linestyles[macs], 
                    linewidth=2, color=colors[macs], label=labels[macs])
    
    ax_avg.set_title(f'CPU Average (SAE PWE={pwe})', fontsize=14, pad=10)
    ax_avg.set_xlabel('SAE Commit Frames Per Second (fps)', fontsize=12)
    if j == 0:
        ax_avg.set_ylabel('Average Router CPU Usage (%)', fontsize=12)
    ax_avg.set_ylim(0, 110)
    ax_avg.set_xticks(fps_rates)
    ax_avg.legend(loc='lower right', fontsize=11, frameon=True, shadow=True)

plt.suptitle('Impact of SAE Commit Frame Injection on CPU Load', fontsize=16, y=0.98)

# 5. Save the figure in a high-quality format for LaTeX
plt.tight_layout()
plt.savefig('synthesized_cpu_load.pdf', format='pdf', dpi=300)
plt.show()