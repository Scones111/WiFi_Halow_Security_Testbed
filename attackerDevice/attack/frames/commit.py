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


def format_hex(hex_string):
    # Remove any existing whitespace
    hex_string = "".join(hex_string.split())

    # Group into bytes (2 hex characters)
    bytes_list = [hex_string[i:i+2] for i in range(0, len(hex_string), 2)]

    # Group into lines of 16 bytes (32 hex characters)
    lines = [
        " ".join(bytes_list[i:i+16])
        for i in range(0, len(bytes_list), 16)
    ]

    return "\n".join(lines)


# Example usage
hex_data = commit_frame("11:22:33:44:55:66","22:33:44:55:66:77").hex()

print(format_hex(hex_data))

