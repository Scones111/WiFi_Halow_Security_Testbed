import sys
import os

# Add the current working directory to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))
sys.path.insert(0, project_root)

from datetime import datetime, timezone
from pathlib import Path
import pyshark
from pyshark.packet.packet import Packet
import pandas as pd
import attackerDevice.utils as utils
import attackerDevice.attack.frames.generateAllFrames as generateAllFrames
import attackerDevice.monitor.events as events

#Load MAC address of the known devices
TRUSTED_AP = utils.get_mac("TrustedAP")[0]
EVIL_TWIN = utils.get_mac("EvilTwin")[0]
STA = utils.get_mac("STA")

# Use this to be used to compare and log the known attack frame we are transmitting
# allows for filtering out other similar frames easily
KNOWN_ATTACK_FRAMES =  generateAllFrames.retrieve_all_attack_frames()

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
    "radiotap_channel_freq": ("radiotap", "channel.freq"),
    "wlan_duration": ("wlan", "duration"),
    "wlan_fc_type": ("wlan", "fc_tree", "type"),
    "wlan_fc_subtype": ("wlan", "fc_tree", "subtype"),
    "wlan_fc_ds": ("wlan", "fc_tree", "flags_tree", "tods"),
    "wlan_fc_frag": ("wlan", "fc_tree", "flags_tree", "frag"),
    "wlan_fc_retry": ("wlan", "fc_tree", "flags_tree", "retry"),
    "wlan_fc_pwrmgt": ("wlan", "fc_tree", "flags_tree", "pwrmgt"),
    "wlan_fc_moredata": ("wlan", "fc_tree", "flags_tree", "moredata"),
    "wlan_fc_protected": ("wlan", "fc_tree", "flags_tree", "protected"),
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
# intended for extracting features and assigning labels for machine learning

#function to load attributes
def packet_extract(packet,layers:tuple):
    
    temp_extract = None
    final_extract = None

    if hasattr(packet, layers[0]):
        temp_extract = getattr(packet, layers[0], None)
        final_extract = temp_extract

    for layer in layers[1:]:
        if temp_extract is not None and hasattr(temp_extract, layer):
            temp_extract = getattr(temp_extract, layer)
            final_extract = temp_extract
        else:
            final_extract = None
            break

    return final_extract

def MLLog_processing(packets):
    # load required devices
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

        features.loc[i,"packet_number"] = i

        if hasattr(packet.wlan,"bssid"):
            if packet.wlan.bssid == EVIL_TWIN:
                label = 1
        elif hasattr(packet.wlan,"sa"):
            if packet.wlan.sa == EVIL_TWIN:
                label = 1
        elif packet.frame_raw.value[int(packet.radiotap.length)*2:] in KNOWN_ATTACK_FRAMES:
            label = 1

        features.loc[i,"label"] = label

        for feature in feat_map.keys():
            features.loc[i,feature] = packet_extract(packet,feat_map[feature])

        i += 1

    utils.write_to_ml_log(features)


# ================================================================
# Code for logging the information and events from capture pcap file
# pure attack logging, can contain information for machine learning,
# but intended purpose is to log events and details for better overview of attacks

deauth_no = 0
def deauth_counter():
    global deauth_no 
    deauth_no += 1
    return deauth_no


def process_wlan(packet:Packet):
    packet_number = int(packet.frame_info.number)
    wlan = getattr(packet,"wlan",None)
    ts = packet.sniff_timestamp
    rf =packet.radiotap.dbm_antsignal
    src = getattr(wlan,'sa',None)
    dst = getattr(wlan,'da',None)
    bssid = getattr(wlan,'bssid',None)
    fc_type = int(wlan.fc_tree.type)
    fc_subtype = int(wlan.fc_tree.subtype)
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
    
    if frameTypes[fc_type][fc_subtype] == "Deauthentication":
        store_packet_to_log = True
        events.handle_deauth(event,packet,deauth_counter())


    if frameTypes[fc_type][fc_subtype] == "Probe Request":
        store_packet_to_log = True
        events.handle_probe_req(event)
        print(event)

    elif frameTypes[fc_type][fc_subtype] == "Probe Response":
        store_packet_to_log = True
        events.handle_probe_resp(event)
        print(event)

    elif frameTypes[fc_type][fc_subtype] == "Authentication":
        if src != bssid:
            store_packet_to_log = True
            events.handle_authentication_req(event)
        elif src == bssid:
            store_packet_to_log = True
            events.handle_authentication_resp(event)

    elif frameTypes[fc_type][fc_subtype] == "Association Request":
        store_packet_to_log = True
        events.handle_association_req(event)

    elif frameTypes[fc_type][fc_subtype] == "Association Response":
        store_packet_to_log = True
        events.handle_association_resp(event)

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
    fc_type = int(wlan.fc_tree.type)
    fc_subtype = int(wlan.fc_tree.subtype)


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
    
    events.handle_tcp(event)

    utils.write_to_tcp_log(event)


# implement logging https://docs.zeek.org/en/master/frameworks/logging.html
def log_events(path_to_pcap_file,pcap_filter):
    packets = pyshark.FileCapture(path_to_pcap_file,display_filter=pcap_filter,keep_packets=False)

    for packet in packets:

        has_wlan = hasattr(packet, 'wlan')
        has_tcp  = hasattr(packet, 'tcp')

        if has_wlan and has_tcp:
            process_tcp(packet)
        elif has_wlan:
            process_wlan(packet)
    
    #todo implement post process for machine learning features

    MLLog_processing(packets)

    packets.close()
    
    
# ================================================================    

# test code
"""
filename = Path(__file__).resolve().parent / "testbed_2.pcap"

packets = pyshark.FileCapture(
    filename,
    use_json=True,
    include_raw=True,
    display_filter="(wlan || tcp) && !arp && !stp && !rldp && !mdns && !udp && !icmpv6 && !igmp && !ipv6",
    keep_packets=False
)

post_processing(packets)

packets.close()
"""
