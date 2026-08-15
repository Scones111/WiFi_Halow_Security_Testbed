from scapy.all import *
from scapy.layers.dot11 import Dot11Auth, Dot11FCS
from cryptography.hazmat.primitives.asymmetric import ec


def commit_frame(target_mac:str, src_mac:str,cookie=None,status=126):
    # For WPA3 SAE (Dragonfly), we use Authentication Algorithm 3
    # SAE Commit payload for Group 19 consists of:
    # - Group ID: 19 (little-endian: b'\x13\x00')
    # - Scalar: 32 random bytes
    # - Element: 64 random bytes (x and y coordinates)
    curve = ec.SECP256R1() # curve P-256
    private_key = ec.generate_private_key(curve)
    dummy_scalar = private_key.private_numbers().private_value
    public_key = private_key.public_key()
    e1 = public_key.public_numbers().x
    e2 = public_key.public_numbers().y

    dummy_scalar = dummy_scalar.to_bytes(32,"big")
    dummy_element = e1.to_bytes(32,"big") + e2.to_bytes(32,"big") 

    # Determine payload structure based on the status (which carries the pwe setting)
    # pwe=0 (status=0): cookie comes directly after the Group ID
    # pwe=1 (status=126): cookie comes at the end as an Extension Tag
    if status == 0 and cookie is not None:
        sae_payload = b'\x13\x00' + cookie + dummy_scalar + dummy_element
    else:
        sae_payload = b'\x13\x00' + dummy_scalar + dummy_element
        if cookie is not None:
            sae_payload += cookie

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
        Dot11Auth(algo=3, seqnum=1, status=status) /
        Raw(load=sae_payload)
    )

    return bytes(frame)
