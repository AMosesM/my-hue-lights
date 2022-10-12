import json
import os
import socket
from time import sleep
from huesdk import Hue, Light
import urllib3
import yaml


CONFIG_FILE = os.path.realpath("/opt/app/conf.yaml")
CONFIG = yaml.safe_load(open(CONFIG_FILE))

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

os.makedirs('/opt/app', exist_ok=True)

bridge_cache_filename = '/opt/app/bridge_cache.json'
bridge_cache = []

if os.path.exists(bridge_cache_filename):
    with open(bridge_cache_filename, 'r') as f:
        bridge_cache = json.load(f)

def setup_bridge(url):
    global bridge_cache

    tmp_bridge=None
    ip=str(socket.gethostbyname(url))
    bridge_cache_query = [b for b in bridge_cache if b.get('bridge_url') == url]

    if bridge_cache_query:
        username = bridge_cache_query[0].get('username')
        print("using cached username: {}".format(username))
    else:
        username = Hue.connect(bridge_ip=ip)
    
    if username:
        tmp_bridge = Hue(bridge_ip=ip, username=username)

        if tmp_bridge.username and tmp_bridge.username not in [x.get('username') for x in bridge_cache]:
            bridge_cache.append({
                'bridge_url': url,
                'username': tmp_bridge.username
            })
    
    return tmp_bridge

if __name__ == "__main__":
    for bridge in CONFIG.get("bridges").keys():
        bridge_result = None
        bridge_url = CONFIG.get("bridges").get(bridge).get('url')
        while not bridge_result:
            try:
                bridge_result = setup_bridge(bridge_url)
            except Exception as e:
                print(e)
            if not bridge_result:
                print("waiting for hub button press on {}".format(bridge_url))
                sleep(3)

    if bridge_cache:
        with open(bridge_cache_filename, 'w') as f:
            json.dump(bridge_cache, f)