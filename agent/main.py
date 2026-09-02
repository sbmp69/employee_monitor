import os
import requests
import time
from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env")

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

def check_backend_health():
    try:
        response = requests.get(f"{BACKEND_URL}/health")
        if response.status_code == 200:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Agent successfully connected to Backend. Status: {response.json()}")
        else:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Agent connected but backend returned status {response.status_code}")
    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Agent failed to connect to backend: {e}")

if __name__ == "__main__":
    print("Employee Monitor Agent Starting...")
    print(f"Target Backend: {BACKEND_URL}")
    while True:
        check_backend_health()
        time.sleep(10)
