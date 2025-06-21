import requests
import time
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] [CLIENT] %(message)s')

NODES = ["http://localhost:5001", "http://localhost:5002", "http://localhost:5003"]

def test_scenario():
    logging.info("--- Writing k1=v1 to node1 ---")
    res = requests.post(f"{NODES[0]}/write", json={"key": "k1", "value": "v1"})
    logging.debug(f"Response: {res.json()}")

    time.sleep(2)

    logging.info("--- Reading k1 from node2 ---")
    res = requests.get(f"{NODES[1]}/read", params={"key": "k1"})
    logging.debug(f"Response: {res.json()}")

    logging.info("--- Writing k1=v2 to node2 ---")
    res = requests.post(f"{NODES[1]}/write", json={"key": "k1", "value": "v2"})
    logging.debug(f"Response: {res.json()}")

    time.sleep(2)

    logging.info("--- Reading k1 from node3 ---")
    res = requests.get(f"{NODES[2]}/read", params={"key": "k1"})
    logging.debug(f"Response: {res.json()}")

if __name__ == '__main__':
    test_scenario()
