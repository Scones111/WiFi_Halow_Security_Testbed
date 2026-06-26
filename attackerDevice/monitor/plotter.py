import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Load data
df_server = pd.read_csv('tcp_server_metrics.csv')
df_client = pd.read_csv('tcp_client_metrics.csv')
df_router = pd.read_csv('router_metrics.csv')

# Convert local_time to datetime
df_server['local_time'] = pd.to_datetime(df_server['local_time'])
df_client['local_time'] = pd.to_datetime(df_client['local_time'])
df_router['local_time'] = pd.to_datetime(df_router['local_time'])

# Create a figure with subplots
fig, axes = plt.subplots(3, 1, figsize=(12, 18), sharex=False)

# Time formatter for x-axis (HH:MM:SS)
time_fmt = mdates.DateFormatter('%H:%M:%S')

# Plot CPU usage
axes[0].plot(df_server['local_time'], df_server['cpu_used_pct'], label='TCP Server', color='blue')
axes[0].plot(df_client['local_time'], df_client['cpu_used_pct'], label='TCP Client', color='green')
axes[0].plot(df_router['local_time'], df_router['cpu_used_pct'], label='Router', color='red')
axes[0].set_title('CPU Usage (%) over Time')
axes[0].set_ylabel('CPU Usage (%)')
axes[0].legend()
axes[0].grid(True)
axes[0].xaxis.set_major_formatter(time_fmt)
axes[0].tick_params(axis='x', rotation=45)

# Plot RAM usage
axes[1].plot(df_server['local_time'], df_server['ram_used_pct'], label='TCP Server', color='blue')
axes[1].plot(df_client['local_time'], df_client['ram_used_pct'], label='TCP Client', color='green')
axes[1].plot(df_router['local_time'], df_router['ram_used_pct'], label='Router', color='red')
axes[1].set_title('RAM Usage (%) over Time')
axes[1].set_ylabel('RAM Usage (%)')
axes[1].legend()
axes[1].grid(True)
axes[1].xaxis.set_major_formatter(time_fmt)
axes[1].tick_params(axis='x', rotation=45)

# Plot Throughput
if 'throughput_bps' in df_server.columns and 'throughput_bps' in df_client.columns:
    axes[2].plot(df_server['local_time'], df_server['throughput_bps'], label='TCP Server', color='blue')
    axes[2].plot(df_client['local_time'], df_client['throughput_bps'], label='TCP Client', color='green')
    axes[2].set_title('Throughput (bps) over Time')
    axes[2].set_ylabel('Throughput (bps)')
    axes[2].legend()
    axes[2].grid(True)
    axes[2].xaxis.set_major_formatter(time_fmt)
    axes[2].tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.savefig('device_metrics.png')
print("Plot saved as device_metrics.png")
