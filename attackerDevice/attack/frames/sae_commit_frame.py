from scapy.all import *
from scapy.layers.dot11 import Dot11, Dot11Auth
import os

def commit_frame(target_mac:str, src_mac:str):
    # For WPA3 SAE (Dragonfly), we use Authentication Algorithm 3
    # SAE Commit payload for Group 19 consists of:
    # - Group ID: 19 (little-endian: b'\x13\x00')
    # - Scalar: 32 random bytes
    # - Element: 64 random bytes (x and y coordinates)
    dummy_scalar = os.urandom(32)
    dummy_element = os.urandom(64)
    sae_payload = b'\x13\x00' + dummy_scalar + dummy_element

    frame = (
        Dot11FCS(
            proto=0,
            type=0,
            subtype=11, # 11 is Authentication
            FCfield=0,
            addr1=target_mac,
            addr2=src_mac,
            addr3=target_mac, # BSSID is typically the AP's MAC
            SC=(1 << 4)
            ) /
        Dot11Auth(algo=3, seqnum=1, status=126) /
        Raw(load=sae_payload)
    )

    return bytes(frame)

