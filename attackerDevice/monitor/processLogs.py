import sys
import os

# Add the current working directory to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))
sys.path.insert(0, project_root)


from datetime import datetime, timezone
import time
from pathlib import Path
import pyshark
from pyshark.packet.packet import Packet
import pandas as pd
import attackerDevice.utils as utils
from attackerDevice.attack.frames import *


#Load MAC address of the known devices
TRUSTED_AP = utils.get_mac("TrustedAP")[0]
EVIL_TWIN = utils.get_mac("EvilTwin")[0]
STA = utils.get_mac("STA")

# Use this to be used to compare and log the known attack frame we are transmitting
# allows for filtering out other similar frames easily
KNOWN_ATTACK_FRAMES =  deauth_frame("FF:FF:FF:FF:FF:FF")

#initialize columns to be used:


columns = [
    "packet_number", # keep track of packet number in pcap

    #features according to the specification of Pick Quality Over Quantity: 
    #Expert Feature Selection and Data Preprocessing for 802.11 Intrusion Detection Systems
    #=================================================
    "frame_len",
    "radiotap_length",
    "radiotap_dbm_antsignal",
    "radiotap_channel_freq",
    "wlan_fc_type",
    "wlan_fc_subtype",
    "wlan_fc_ds",
    "wlan_fc_frag",
    "wlan_fc_retry",
    "wlan_fc_pwrmgt",
    "wlan_fc_moredata",
    "wlan_fc_protected",
    "wlan_duration",
    #=================================================
    "label" # ground truth
]

# Features to extract according to AWID3 evil twin and flooding falls under impersonation attacks
feat_map = {
    "frame_len": ("frame_info", "len"),
    "radiotap_length": ("radiotap", "length"),
    "radiotap_dbm_antsignal": ("radiotap", "dbm_antsignal"),
    "radiotap_channel_freq": ("radiotap", "channel_freq"),
    "wlan_duration": ("wlan", "duration"),
    "wlan_fc_type": ("wlan", "fc_type"),
    "wlan_fc_subtype": ("wlan", "fc_subtype"),
    "wlan_fc_ds": ("wlan", "fc_ds"),
    "wlan_fc_frag": ("wlan", "fc_frag"),
    "wlan_fc_retry": ("wlan", "fc_retry"),
    "wlan_fc_pwrmgt": ("wlan", "fc_pwrmgt"),
    "wlan_fc_moredata": ("wlan", "fc_moredata"),
    "wlan_fc_protected": ("wlan", "fc_protected"),
}
# ================================================================
# Provided the types from specification of the MAC and PHY as according to ieee802.11
managementSubTypes = {
    0: "Association Request",
    1: "Association Response",
    2: "Reassociation Request",
    3: "Reassociation Response",
    4: "Probe Request",
    5: "Probe Response",
    6: "Timing Advertisement",
    8: "Beacon",
    9: "ATIM",
    10: "Disassociation",
    11: "Authentication",
    12: "Deauthentication",
    13: "Action",
    14: "Action No Ack"
}

controlSubTypes = {
    2: "Trigger",
    3: "TACK",
    4: "Beamforming Report Poll",
    5: "VHT/HE NDP Announcement",
    6: "Control Frame Extension",
    7: "Control wrapper",
    8: "Block ACK Request",
    9: "Block ACK",
    10: "PS-Poll",
    11: "RTS",
    12: "CTS",
    13: "ACK",
    14: "CF-End",
    15: "CF-END+CF-ACK"
}

dataSubtypes = {
    0: "Data",
    1: "EBCS Data",
    4: "Null",
    8: "QoS Data",
    9: "QoS Data + CF-ACK",
    10: "QoS Data + CF-Poll",
    11: "QoS Data + CF-ACK + CF-Poll",
    12: "QoS Null",
    14: "QoS CF-Poll",
    15: "QoS CF-ACK + CF-Poll"
}

extendedSubtypes = {
    0: "DMG Beacon",
    1: "S1G Beacon"
}

frameTypes = {
    0: managementSubTypes,
    1: controlSubTypes,
    2: dataSubtypes,
    3: extendedSubtypes
}

# ================================================================
# Post processing, for machine learning according to AWID3 paper

#function to load attributes
def packet_extract(packet,layer,field):
    if hasattr(packet, layer):
        layer_extract = getattr(packet,layer)
        if hasattr(layer_extract,field):
            return getattr(layer_extract,field) 
    
    return None

def post_processing(filename):
    # load required devices
    maliciousAP=utils.load_json()["EvilTwin"][0]['mac']
    
    # load attack log Used for categorizing:
    attack_start = None
    attack_end = None

    # Load captured pcap
    packets = pyshark.FileCapture(filename)

    # normal traffic = 0, malicious traffic = 1
    # can also use a string to clasify the data
    label=0

    #initialize pandas dataframe
    features = pd.DataFrame(columns=columns)

    i = 0
    #iterate through packets
    for packet in packets:
        #reset label to 0, for normal traffic
        label = 0
        time_stamp = float(packet.sniff_timestamp)

        features.loc[i,"packet_number"] = i

        if hasattr(packet.wlan,"bssid"):
            if packet.wlan.bssid == maliciousAP:
                label = 1
        elif hasattr(packet.wlan,"sa"):
            if packet.wlan.sa == maliciousAP:
                label = 1

        features.loc[i,"label"] = label

        for feature in feat_map.keys():
            features.loc[i,feature] = packet_extract(packet,feat_map[feature][0],feat_map[feature][1])
        
        i += 1
        break

# ================================================================
# Code for logging the information during execution

def deauth_counter():
    global deauth_no 
    deauth_no += 1
    return deauth_no

def handle_authentication_req(event):
    if event["bssid"] == EVIL_TWIN:
        event["attack_type"] = "Evil Twin Attack"
        event["details"] = "STA is Sending association request to Evil Twin"
    elif event["bssid"] == TRUSTED_AP:
        event["details"] = "STA is Sending association request to Trusted AP"

    return event

def handle_authentication_resp(event):
    if event["status"] == 0:
        event["details"] = "Successful Authentication to "
    else: 
        event["details"] = "Unsuccessful Authentication (check status code) to "

    if event["bssid"] == EVIL_TWIN:
        event["attack_type"] = "Evil Twin Attack"
        event["details"] += "Evil Twin"
    elif event["bssid"] == TRUSTED_AP:
        event["details"] += "Trusted AP"

    return event

def handle_association_req(event):
    if event["bssid"] == EVIL_TWIN:
        event["attack_type"] = "Evil Twin Attack"
        event["details"] = "STA is Sending association request to Evil Twin"
    elif event["bssid"] == TRUSTED_AP:
        event["details"] = "STA is Sending association request to Trusted AP"

    return event

def handle_association_resp(event):
    if event["status"] == 0:
        event["details"] = "Successful association to "
    else: 
        event["details"] = "Unsuccessful association (check status code) to "

    if event["bssid"] == EVIL_TWIN:
        event["attack_type"] = "Evil Twin Attack"
        event["details"] += "Evil Twin"
    elif event["bssid"] == TRUSTED_AP:
        event["attack_type"]
        event["details"] += "Trusted AP"

    return event

def process_wlan(packet:Packet):
    packet_number = int(packet.frame_info.number)
    wlan = getattr(packet,"wlan",None)
    ts = packet.sniff_timestamp
    rf =packet.radiotap.dbm_antsignal
    src = getattr(wlan,'sa',None)
    dst = getattr(wlan,'da',None)
    bssid = getattr(wlan,'bssid',None)

    fc_type = int(wlan.fc_type)
    fc_subtype = int(wlan.fc_subtype)
    mgt = None
    ssid = None
    status = None
    reason = None
    if hasattr(packet,"wlan.mgt"):
        mgt = getattr(packet,'wlan.mgt')
        ssid = getattr(mgt,'wlan.ssid',None)
        if ssid != "SSID: <MISSING>" and ssid is not None:
            ssid = utils.turn_hex_to_string(ssid)
        status = getattr(mgt,'wlan_fixed_status_code',None)
        if status:
            status = int(status,16)
        reason = getattr(mgt,'wlan_fixed_status_code',None)
        if reason:
            reason = int(reason,16)

    event = {
        "attack_type":None,
        "packet Number":packet_number,
        "event_type":frameTypes[fc_type][fc_subtype],
        "time_stamp": ts,
        "signal_strength":rf,
        "ssid":ssid,
        "bssid": bssid,
        "src": src,
        "dst": dst,
        "reason":reason,
        "status":status,
        "details":None,
    }

    # Filter out packet frames not relevant to attack
    store_packet_to_log = False
    

    if frameTypes[fc_type][fc_subtype] == "Deauthentication" and packet==KNOWN_ATTACK_FRAMES:
        store_packet_to_log = True
        # todo implement the other log for post processing,
        # maybe we can set up a connection between the attacker and the monitor device
        # allow for remote executing of this script
        deauth_counter()

    elif frameTypes[fc_type][fc_subtype] == "Authentication":
        
        if src != bssid:
            store_packet_to_log = True
            handle_authentication_req(event)
        elif src == bssid:
            store_packet_to_log = True
            handle_authentication_resp(event)

    elif frameTypes[fc_type][fc_subtype] == "Association Request":
        store_packet_to_log = True
        handle_association_req(event)

    elif frameTypes[fc_type][fc_subtype] == "Association Response":
        store_packet_to_log = True
        handle_association_resp(event)

    if store_packet_to_log:
        utils.write_to_attacklog(event)

def process_tcp(packet:Packet):
    packet_number = int(packet.frame_info.number)
    wlan = getattr(packet,"wlan",None)
    ts = packet.sniff_timestamp
    rf = packet.radiotap.dbm_antsignal
    src = getattr(wlan,'sa',None)
    dst = getattr(wlan,'da',None)
    bssid = getattr(wlan,'bssid',None)
    fc_type = int(wlan.fc_type)
    fc_subtype = int(wlan.fc_subtype)


    event = {
        "attack_type":None,
        "packet Number":packet_number,
        "event_type":frameTypes[fc_type][fc_subtype],
        "time_stamp": ts,
        "signal_strength":rf,
        "bssid": bssid,
        "src": src,
        "dst": dst,
        "details":None,
    }
    
    if bssid == EVIL_TWIN:
        event["attack_type"] = "Evil Twin Attack"
        event["details"] = "Transmitting data using Evil Twin AP"
    elif bssid == TRUSTED_AP:
        event["attack_type"]
        event["details"] = "Transmitting data using Trusted AP"

    utils.write_to_tcp_log(event)


# implement logging https://docs.zeek.org/en/master/frameworks/logging.html
def log_events(path_to_pcap_file,pcap_filter):
    packets = pyshark.FileCapture(path_to_pcap_file,display_filter=pcap_filter,keep_packets=False)
    has_wlan = hasattr(packet, 'wlan')
    has_tcp  = hasattr(packet, 'tcp')

    for packet in packets:
        if has_wlan and has_tcp:
            process_tcp(packet)
        elif has_wlan:
            process_wlan(packet)
    
        #todo implement post process for machine learning features
    
# ================================================================    

# test code

"""
filename = Path(__file__).resolve().parent / "pcaps/testbed_0.pcap"
print(filename)
packets = pyshark.FileCapture(
    filename,
    display_filter="(wlan or tcp) and not (arp or stp or rldp or mdns or udp or icmpv6 or igmp or ipv6)",
    keep_packets=False
)


for packet in packets:
    has_wlan = hasattr(packet, 'wlan')
    has_tcp  = hasattr(packet, 'tcp')
    if has_wlan and has_tcp:
        process_tcp(packet)
    elif has_wlan:
        process_wlan(packet)
    

packets.close()
"""