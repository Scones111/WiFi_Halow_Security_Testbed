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
TRUSTED_AP = utils.get_mac("TrustedAP")
EVIL_TWIN = utils.get_mac("EvilTwin") # called evil twin but can be a any rouge MAC
STA = utils.get_mac("STA")

# retrieve known attack frames to log them correctly
ATTACK_FRAMES =  generateAllFrames.retrieve_all_attack_frames()

# keep a counter of deauthentication frames
deauth_no = 0

#initialize columns to be used:
columns = [
    "packet_number",
    "timestamp",
    "frame_name",
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
# frame types
mgtSubTypes = {
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

ctrlSubTypes = {
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

extSubType = {
    0: "DMG Beacon",
    1: "S1G Beacon"
}

frameTypes = {
    0: mgtSubTypes,
    1: ctrlSubTypes,
    2: dataSubtypes,
    3: extSubType
}

# ================================================================
# Post processing of logs, the field retrieve are specified in the AWID3 paper

def tags_extract(tags,field):
    for tag in tags:
        if hasattr(tag,field):
            return getattr(tag,field).get_default_value()
    return None

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

def MLLog_processing(packets):
    # normal traffic = 0, malicious traffic = 1
    label=0

    #initialize pandas dataframe
    frt_df = pd.DataFrame(columns=columns)

    i = 0
    #iterate through packets
    for packet in packets:
        #reset label to 0, for normal traffic
        label = 0

        frt_df.loc[i,"packet_number"] = packet_extract(packet,"packet_number")
        fc_type = int(packet_extract(packet,"type"))
        fc_subtype = int(packet_extract(packet,"subtype"))
        frt_df.loc[i,"frame_name"] = frameTypes[fc_type][fc_subtype]

        if hasattr(packet.wlan,"bssid"):
            if packet.wlan.bssid in EVIL_TWIN:
                label = 1
        elif hasattr(packet.wlan,"sa"):
            if packet.wlan.sa in EVIL_TWIN:
                label = 1
            elif packet.wlan.sa not in STA and packet.wlan.sa not in TRUSTED_AP:
                label = 1
        elif packet.frame_raw.value[int(packet.radiotap.length)*2:] in ATTACK_FRAMES:
            label = 1

        frt_df.loc[i,"label"] = label


        for feature in columns:
            if feature not in ["packet_number","frame_name","label"]:
                frt_df.loc[i,feature] = packet_extract(packet,feature)

        i += 1

    utils.write_to_ml_log(frt_df)

# Code for logging the information and events from capture pcap file
# pure attack logging, can contain information for machine learning,
# but intended purpose is to log events and details for better overview of attacks

def process_wlan(packet:Packet):
    global deauth_no
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
    
    write_log = False

    if frameTypes[fc_type][fc_subtype] in events.handle_wlan_events:
        write_log = True
        if frameTypes[fc_type][fc_subtype] == "Deauthentication":
            events.handle_wlan_events[frameTypes[fc_type][fc_subtype]](event,packet,deauth_no)
        else:
            events.handle_wlan_events[frameTypes[fc_type][fc_subtype]](event)
    # write to log if packet detected
    if write_log:
        utils.write_to_attacklog(event)

def process_tcp(packet:Packet):
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


def log_events(pcap_file,pcap_filter):
    packets = pyshark.FileCapture(
        pcap_file,
        display_filter=pcap_filter,
        keep_packets=False,
        use_json=True,
        include_raw=True,
    )

    #iterate through packets
    for packet in packets:
        has_wlan = hasattr(packet, 'wlan')
        has_tcp  = hasattr(packet, 'tcp')

        #process either tcp or wlan
        if has_wlan and has_tcp:
            process_tcp(packet)
        elif has_wlan:
            process_wlan(packet)

    MLLog_processing(packets)

    packets.close()

# test code

"""
filename = Path(__file__).resolve().parent / "testbed_16.pcap"

packets = pyshark.FileCapture(
    filename,
    use_json=True,
    include_raw=True,
    display_filter="(wlan || tcp) && !arp && !stp && !rldp && !mdns && !udp && !icmpv6 && !igmp && !ipv6 and !basicxid",
    keep_packets=False
)
print("amount of packets to be processed: ", len(packets))
i = 0
for packet in packets:
    has_wlan = hasattr(packet, 'wlan')
    has_tcp  = hasattr(packet, 'tcp')

    if has_wlan and has_tcp:
        process_tcp(packet)
    elif has_wlan:
        process_wlan(packet)

    i += 1

MLLog_processing(packets)

packets.close()
"""