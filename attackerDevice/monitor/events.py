import attackerDevice.utils as utils
from attackerDevice.attack.frames.deauth import deauth_frame
from attackerDevice.attack.frames.generateAllFrames import retrieve_all_attack_frames

EVIL_TWIN = utils.get_mac("EvilTwin")#utils.load_json()["EvilTwin"][0]["mac"]
TRUSTED_AP = utils.get_mac("TrustedAP")#utils.load_json()["TrustedAP"][0]["mac"]
STA_MACS = utils.get_mac("STA")
KNOWN_DEAUTH_FRAME = retrieve_all_attack_frames()

# TCP events
def handle_tcp(event):
    if event['bssid'] in EVIL_TWIN:
        event["attack_type"] = "Evil Twin Attack"
        event["details"] = "Transmitting data using Evil Twin AP"
    elif event['bssid'] in TRUSTED_AP:
        event["details"] = "Transmitting data using Trusted AP"

#todo add more specific events for tcp

#wlan events
def handle_deauth(event,packet,deauth_no):
    if packet.frame_raw.value[int(packet.radiotap.length)*2:] in KNOWN_DEAUTH_FRAME:
        deauth_no += 1
        event["attack_type"] = "Deauthentication Attack"
        event["details"] = f"Deauthentication frame number {deauth_no} sent by attacker"
    else:
        event["details"] = "Legitimate Deauthentication frame not sent by attacker"

def handle_probe_req(event):
    if event["src"] in STA_MACS:
        event["details"] = "STA is broadcasting probe request"
    
def handle_probe_resp(event):
    if event["bssid"] in EVIL_TWIN:
        event["attack_type"] = "Evil Twin Attack"
        event["details"] = "Evil Twin is sending probe response to STA"
    if event["bssid"] in TRUSTED_AP:
        event["details"] = "Trusted AP is sending probe response to STA"

def handle_authentication(event):
    if event["src"] != event["bssid"]:
        handle_authentication_req(event)
    elif event["src"] == event["bssid"]:
        handle_authentication_resp(event)

def handle_authentication_req(event):
    if event["bssid"] in EVIL_TWIN:
        event["attack_type"] = "Evil Twin Attack"
        event["details"] = "STA is Sending Authentication request to Evil Twin"
    elif event['src'] not in STA_MACS and event["bssid"] in TRUSTED_AP:
        event["attack_type"] = "Dragonblood DoS"
        event["details"] = "Attacker is Sending Authentication request to trusted AP"
    elif event["bssid"] in TRUSTED_AP:
        event["details"] = "STA is Sending Authentication request to Trusted AP"
    return event

def handle_authentication_resp(event):
    if event["status"] == 0:
        event["details"] = "Successful Authentication to "
    elif event["status"] == 19:
        event["details"] = "Successful Authentication (SAE commit) to "
    else: 
        event["details"] = "Unsuccessful Authentication (check status code) to "

    if event["bssid"] in EVIL_TWIN:
        event["attack_type"] = "Evil Twin Attack"
        event["details"] += "Evil Twin"
    elif event["bssid"] in TRUSTED_AP:
        event["details"] += "Trusted AP"

    return event

def handle_association_req(event):
    if event["bssid"] in EVIL_TWIN:
        event["attack_type"] = "Evil Twin Attack"
        event["details"] = "STA is Sending association request to Evil Twin"
    elif event["bssid"] in TRUSTED_AP:
        event["details"] = "STA is Sending association request to Trusted AP"

    return event

def handle_association_resp(event):
    if event["status"] == 0:
        event["details"] = "Successful association to "
    else: 
        event["details"] = "Unsuccessful association (check status code) to "

    if event["bssid"] in EVIL_TWIN:
        event["attack_type"] = "Evil Twin Attack"
        event["details"] += "Evil Twin"
    elif event["bssid"] in TRUSTED_AP:
        event["attack_type"]
        event["details"] += "Trusted AP"
    return event

def handle_s1g_beacon(event):
    if event["src"] in EVIL_TWIN:
        event["attack_type"] = "Evil Twin Attack"
        event["details"] = "Evil Twin s1g Beacon"
    elif event["src"] in TRUSTED_AP:
        event["attack_type"]
        event["details"] = "Trusted AP s1g Beacon"

#todo: add more events here

handle_wlan_events = {
    "Deauthentication": handle_deauth,
    "Probe Request": handle_probe_req,
    "Probe Response": handle_probe_resp,
    "Authentication": handle_authentication,
    "Association Request": handle_association_req,
    "Association Response":handle_association_resp,
    "S1G Beacon": handle_s1g_beacon
}

#todo implement for different tcp events:
handle_tcp_events = {
}
