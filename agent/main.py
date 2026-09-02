import os
import sys
import time
import requests
import socket
from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env")

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
AGENT_VERSION = "1.0.0"
DEVICE_ID_FILE = ".device_id"

def get_device_name():
    return socket.gethostname()

def register_agent():
    if os.path.exists(DEVICE_ID_FILE):
        with open(DEVICE_ID_FILE, "r") as f:
            device_id = f.read().strip()
            if device_id:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Found existing device ID: {device_id}")
                return device_id

    # If not registered, hit the register endpoint
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Registering agent with backend...")
    device_name = get_device_name()
    
    try:
        response = requests.post(f"{BACKEND_URL}/api/agent/register", json={
            "device_name": device_name,
            "agent_version": AGENT_VERSION
        })
        response.raise_for_status()
        data = response.json()
        device_id = data["device_id"]
        
        with open(DEVICE_ID_FILE, "w") as f:
            f.write(device_id)
            
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Successfully registered. Device ID: {device_id}")
        return device_id
    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Registration failed: {e}")
        return None

def send_heartbeat(device_id):
    try:
        response = requests.post(f"{BACKEND_URL}/api/agent/heartbeat", json={
            "device_id": device_id
        })
        if response.status_code == 200:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Heartbeat sent successfully.")
        else:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Heartbeat failed: {response.text}")
    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Heartbeat failed: {e}")

if __name__ == "__main__":
    print("Employee Monitor Agent Starting...")
    print(f"Target Backend: {BACKEND_URL}")
    
    device_id = None
    while not device_id:
        device_id = register_agent()
        if not device_id:
            time.sleep(5)
            
    # Heartbeat loop
    while True:
        send_heartbeat(device_id)
        time.sleep(30)
