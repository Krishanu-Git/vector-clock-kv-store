import requests
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [CLIENT] %(message)s')

NODES = {
    "node1": "http://localhost:8001",
    "node2": "http://localhost:8002",
    "node3": "http://localhost:8003"
}

def main():
    # PUT A to node1
    logging.info("Sending PUT x=A to node1")
    res = requests.put(f"{NODES['node1']}/put/x", json={"value": "A"})
    logging.info(f"Response: {res.json()}")
    time.sleep(2)

    # PUT B to node2
    logging.info("Sending PUT x=B to node2")
    res = requests.put(f"{NODES['node2']}/put/x", json={"value": "B"})
    logging.info(f"Response: {res.json()}")
    time.sleep(2)

    # GET from node3
    logging.info("Sending GET x to node3")
    res = requests.get(f"{NODES['node3']}/get/x")
    logging.info(f"Response: {res.json()}")

if __name__ == "__main__":
    main()
