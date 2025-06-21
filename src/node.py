import os
import time
import threading
import logging
from flask import Flask, request, jsonify
from urllib.parse import urlparse
import requests

app = Flask(__name__)

NODE_ID = os.environ.get("NODE_ID", "node1")
OTHER_NODES = os.environ.get("OTHER_NODES", "").split(",")

vector_clock = {}
kv_store = {}
buffer = []
lock = threading.Lock()

logging.basicConfig(level=logging.DEBUG, format=f'%(asctime)s [%(levelname)s] [{NODE_ID}] %(message)s')

def extract_node_id(url):
    return urlparse(url).hostname  # Extracts 'node1' from 'http://node1:1234'

def init_clock():
    global vector_clock
    all_nodes = [NODE_ID] + [extract_node_id(n) for n in OTHER_NODES]
    for node in all_nodes:
        vector_clock[node] = 0
    logging.info(f"Initialized vector clock: {vector_clock}")

@app.route("/write", methods=["POST"])
def write():
    data = request.get_json()
    key, value = data["key"], data["value"]
    with lock:
        vector_clock[NODE_ID] += 1
        kv_store[key] = value
        msg = {
            "key": key,
            "value": value,
            "clock": vector_clock.copy(),
            "sender": NODE_ID
        }
        logging.info(f"Local write: {key}={value}, clock={vector_clock}")
        for node_url in OTHER_NODES:
            logging.debug(f"Sending replication to {node_url}")
            threading.Thread(target=send_replicate, args=(node_url, msg)).start()
    return jsonify({"status": "write committed", "clock": vector_clock})

@app.route("/read", methods=["GET"])
def read():
    key = request.args.get("key")
    with lock:
        value = kv_store.get(key)
        logging.info(f"Read request: {key} => {value}, clock={vector_clock}")
        return jsonify({"value": value, "clock": vector_clock})

@app.route("/replicate", methods=["POST"])
def replicate():
    msg = request.get_json()
    with lock:
        logging.debug(f"Received replication: key={msg['key']}, value={msg['value']}, clock={msg['clock']}")
        if is_deliverable(msg["clock"], msg["sender"]):
            apply_write(msg)
            logging.info(f"Applied replicated write: {msg['key']}={msg['value']}, updated clock={vector_clock}")
        else:
            buffer.append(msg)
            logging.info(f"Buffered message due to unmet dependencies: {msg}")
    return "ok"

def send_replicate(node_url, msg):
    try:
        requests.post(f"{node_url}/replicate", json=msg, timeout=1)
    except Exception as e:
        logging.error(f"Error sending to {node_url}: {e}")

def is_deliverable(msg_clock, sender):
    for node in vector_clock:
        if node == sender:
            if msg_clock[node] != vector_clock[node] + 1:
                return False
        else:
            if msg_clock[node] > vector_clock[node]:
                return False
    return True

def apply_write(msg):
    kv_store[msg["key"]] = msg["value"]
    for node in vector_clock:
        vector_clock[node] = max(vector_clock[node], msg["clock"].get(node, 0))

def buffer_check_loop():
    while True:
        with lock:
            delivered = []
            for msg in buffer:
                if is_deliverable(msg["clock"], msg["sender"]):
                    apply_write(msg)
                    delivered.append(msg)
                    logging.info(f"Delivered buffered message: {msg}")
            for msg in delivered:
                buffer.remove(msg)
        time.sleep(1)

if __name__ == '__main__':
    init_clock()
    threading.Thread(target=buffer_check_loop, daemon=True).start()
    logging.info(f"Node running with peers: {OTHER_NODES}")
    app.run(host="0.0.0.0", port=1234)