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
    "frame_name",

    #features according to the specification of Pick Quality Over Quantity: 
    #Expert Feature Selection and Data Preprocessing for 802.11 Intrusion Detection Systems
    #=================================================
    "frame_len",
    "length",
    "dbm_antsignal",
    "channel_freq",
    "type",
    "subtype",
    "ds",
    "frag",
    "retry",
    "pwrmgt",
    "moredata",
    "protected",
    "duration",
    #=================================================
    "label" # ground truth
]

frame_map = {
    "packet_number": ("frame_info","number"),
    "frame_len": ("frame_info", "len"),
    "length": ("radiotap", "length"),
    "dbm_antsignal": ("radiotap", "dbm_antsignal"),
    "channel_freq": ("radiotap", "channel", "freq"),
    "timestamp": ("sniff_timestamp",),
    "src": ("wlan", "sa"),
    "dst": ("wlan", "da"),
    "bssid": ("wlan", "bssid"),
    "duration": ("wlan", "duration"),
    "type": ("wlan", "fc_tree", "type"),
    "subtype": ("wlan", "fc_tree", "subtype"),
    "ds": ("wlan", "fc_tree", "flags_tree", "tods"),
    "frag": ("wlan", "fc_tree", "flags_tree", "frag"),
    "retry": ("wlan", "fc_tree", "flags_tree", "retry"),
    "pwrmgt": ("wlan", "fc_tree", "flags_tree", "pwrmgt"),
    "moredata": ("wlan", "fc_tree", "flags_tree", "moredata"),
    "protected": ("wlan", "fc_tree", "flags_tree", "protected"),
    "ssid_mgt": ("wlan.mgt", "tagged.all", "tag", "ssid"),
    "ssid_ext": ("wlan_ext", "tagged.all", "tag", "ssid"),
    "status": ("wlan.mgt", "all", "status_code"),
    "reason": ("wlan.mgt", "all", "reason_code")
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

#iterate through tags
def tags_extract(tags,field):
    for tag in tags:
        if hasattr(tag,field):
            return getattr(tag,field).get_default_value()
    return None

#function to load attributes
def packet_extract(packet,field):
    temp_fields = frame_map[field]

    temp_extract = packet
    final_extract = None
    for temp_field in temp_fields:
        if hasattr(temp_extract,temp_field):
            temp_extract = getattr(temp_extract, temp_field)
            final_extract = temp_extract
        else:
            final_extract = None
            break

        if temp_field == "tag":
            if isinstance(temp_extract,pyshark.packet.layers.json_layer.JsonLayer):
                temp_extract = [temp_extract]
            final_extract = tags_extract(temp_extract,temp_fields[-1])
            break
    
    return final_extract

def MLLog_processing(pcap, pcap_filter=None):
    packets = pyshark.LiveCapture(
        pcap,
        display_filter=pcap_filter,
        keep_packets=False,
        use_json=True,
        include_raw=True,
    )

    # normal traffic = 0, malicious traffic = 1
    label=0

    #initialize pandas dataframe
    features = pd.DataFrame(columns=columns)

    i = 0
    #iterate through packets
    for packet in packets:
        #reset label to 0, for normal traffic
        label = 0

        features.loc[i,"packet_number"] = packet_extract(packet,"packet_number")
        fc_type = int(packet_extract(packet,"type"))
        fc_subtype = int(packet_extract(packet,"subtype"))
        features.loc[i,"frame_name"] = frameTypes[fc_type][fc_subtype]

        if hasattr(packet.wlan,"bssid"):
            if packet.wlan.bssid == EVIL_TWIN:
                label = 1
        elif hasattr(packet.wlan,"sa"):
            if packet.wlan.sa == EVIL_TWIN:
                label = 1
        elif packet.frame_raw.value[int(packet.radiotap.length)*2:] in KNOWN_ATTACK_FRAMES:
            label = 1

        features.loc[i,"label"] = label


        for feature in columns:
            if feature not in ["packet_number","frame_name","label"]:
                features.loc[i,feature] = packet_extract(packet,feature)

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
    #todo change this code to use packet_extract
    packet_number = packet_extract(packet,"packet_number")
    ts = packet_extract(packet,"timestamp")
    rf = packet_extract(packet,"dbm_antsignal")
    src = packet_extract(packet,"src")
    dst = packet_extract(packet,"dst")
    bssid  = packet_extract(packet,"bssid")
    fc_type = int(packet_extract(packet,"type"))
    fc_subtype = int(packet_extract(packet,"subtype"))

    ssid = None

    if frameTypes[fc_type][fc_subtype] == "S1G Beacon":
        ssid = packet_extract(packet,"ssid_ext")
    else:
        ssid = packet_extract(packet,"ssid_mgt")

    if ssid is not None and ssid != None:
        ssid = utils.turn_hex_to_string(ssid)
    
    status = packet_extract(packet,"status")
    if status is not None:
        status = int(status,16)

    
    reason = packet_extract(packet,"reason")
    if reason is not None:
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
        mgt = getattr(packet,'wlan.mgt')
        ssid = getattr(mgt,'wlan.ssid',None)
        events.handle_probe_req(event)

    elif frameTypes[fc_type][fc_subtype] == "Probe Response":
        store_packet_to_log = True
        events.handle_probe_resp(event)

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
    #todo change this code to use packet_extract
    packet_number = packet_extract(packet,"packet_number")
    ts = packet_extract(packet,"timestamp")
    rf = packet_extract(packet,"dbm_antsignal")
    src = packet_extract(packet,"src")
    dst = packet_extract(packet,"dst")
    bssid  = packet_extract(packet,"bssid")
    fc_type = int(packet_extract(packet,"type"))
    fc_subtype = int(packet_extract(packet,"subtype"))


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
def log_events(pcap,pcap_filter):
    packets = pyshark.LiveCapture(
        pcap,
        display_filter=pcap_filter,
        keep_packets=False,
        use_json=True,
        include_raw=True,
    )

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
    display_filter="(wlan || tcp) && !arp && !stp && !rldp && !mdns && !udp && !icmpv6 && !igmp && !ipv6 and !basicxid",
    keep_packets=False
)

for packet in packets:

    has_wlan = hasattr(packet, 'wlan')
    has_tcp  = hasattr(packet, 'tcp')

    if has_wlan and has_tcp:
        process_tcp(packet)
    elif has_wlan:
        process_wlan(packet)

MLLog_processing(packets)

packets.close()

"""