import pyshark
import pandas as pd

df = pd.read_csv('MLlogs.txt', sep='\t', header=None, names=['Time', 'RSSI'])

