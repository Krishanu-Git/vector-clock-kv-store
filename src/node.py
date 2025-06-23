from flask import Flask, request, jsonify
import threading
import requests
import time
import json
import os
import logging

app = Flask(__name__)

# Logging setup
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s')
log = logging.getLogger(f"NODE-{os.environ.get('NODE_ID')}")

# Environment config
NODE_ID = os.environ["NODE_ID"]
ALL_NODES = json.loads(os.environ["ALL_NODES"])
NODES = list(ALL_NODES.keys())

vector_clock = {nid: 0 for nid in NODES}
kv_store = {}
buffer = []
lock = threading.Lock()

@app.route('/get/<key>', methods=['GET'])
def get_key(key):
    with lock:
        value = kv_store.get(key, None)
        vc_copy = vector_clock.copy()
    log.info(f"GET key={key} → value={value} | VC={vc_copy}")
    return jsonify({"value": value, "vc": vc_copy})

@app.route('/put/<key>', methods=['PUT'])
def put_key(key):
    data = request.json
    value = data["value"]

    with lock:
        vector_clock[NODE_ID] += 1
        kv_store[key] = value
        vc_copy = vector_clock.copy()

        payload = {
            "sender": NODE_ID,
            "key": key,
            "value": value,
            "vc": vc_copy
        }

    log.info(f"PUT key={key}, value={value} | Updated VC={vc_copy}")

    # Broadcast to peers
    for nid, url in ALL_NODES.items():
        if nid != NODE_ID:
            try:
                res = requests.post(f"{url}/replicate", json=payload)
                log.debug(f"Replicated to {nid}: {res.status_code}")
            except Exception as e:
                log.error(f"Failed to replicate to {nid}: {e}")

    return jsonify({"status": "ok", "vc": vc_copy})

@app.route('/replicate', methods=['POST'])
def replicate():
    data = request.json
    with lock:
        buffer.append(data)
    log.info(f"Buffered replication: {data}")
    return jsonify({"status": "buffered"})

def check_causal_delivery():
    while True:
        time.sleep(1)
        with lock:
            delivered = []
            for msg in buffer:
                sender = msg["sender"]
                msg_vc = msg["vc"]
                if all(msg_vc[n] <= vector_clock[n] for n in NODES if n != sender) and msg_vc[sender] == vector_clock[sender] + 1:
                    kv_store[msg["key"]] = msg["value"]
                    vector_clock[sender] += 1
                    delivered.append(msg)
                    log.info(f"Delivered buffered msg: key={msg['key']}, value={msg['value']} | VC={vector_clock}")
            for msg in delivered:
                buffer.remove(msg)

if __name__ == '__main__':
    threading.Thread(target=check_causal_delivery, daemon=True).start()
    app.run(host='0.0.0.0', port=8000)
