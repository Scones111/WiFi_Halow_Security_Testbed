from scapy.all import *
from scapy.layers.dot11 import Dot11, Dot11Auth, Dot11FCS
from cryptography.hazmat.primitives.asymmetric import ec


def commit_frame(target_mac:str, src_mac:str,cookie=None):
    # For WPA3 SAE (Dragonfly), we use Authentication Algorithm 3
    # SAE Commit payload for Group 19 consists of:
    # - Group ID: 19 (little-endian: b'\x13\x00')
    # - Scalar: 32 random bytes
    # - Element: 64 random bytes (x and y coordinates)
    curve = ec.SECP256R1()
    private_key = ec.generate_private_key(curve)
    dummy_scalar = private_key.private_numbers().private_value
    public_key = private_key.public_key()
    e1 = public_key.public_numbers().x
    e2 = public_key.public_numbers().y

    dummy_scalar = dummy_scalar.to_bytes(32,"big")
    dummy_element = e1.to_bytes(32,"big") + e2.to_bytes(32,"big") 
    sae_payload = None


    frame = None
    if cookie != None:
        sae_payload = b'\x13\x00' + cookie + dummy_scalar + dummy_element
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
            Dot11Auth(algo=3, seqnum=1, status=0    ) /
            Raw(load=sae_payload)
        )
    
    else:
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