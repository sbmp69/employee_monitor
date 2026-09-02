import os
import sys
import time
import requests
import socket
import threading
import json
import asyncio
import websockets
from mss import mss
from PIL import Image
import io
from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env")

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
WS_URL = BACKEND_URL.replace("http://", "ws://").replace("https://", "wss://")
AGENT_VERSION = "1.0.0"
DEVICE_ID_FILE = ".device_id"

is_streaming = False

def get_device_name():
    return socket.gethostname()

def register_agent():
    if os.path.exists(DEVICE_ID_FILE):
        with open(DEVICE_ID_FILE, "r") as f:
            device_id = f.read().strip()
            if device_id:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Found existing device ID: {device_id}")
                return device_id

    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Registering agent with backend...")
    
    try:
        response = requests.post(f"{BACKEND_URL}/api/agent/register", json={
            "device_name": get_device_name(),
            "agent_version": AGENT_VERSION
        })
        response.raise_for_status()
        device_id = response.json()["device_id"]
        
        with open(DEVICE_ID_FILE, "w") as f:
            f.write(device_id)
            
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Successfully registered. Device ID: {device_id}")
        return device_id
    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Registration failed: {e}")
        return None

def heartbeat_loop(device_id):
    while True:
        try:
            response = requests.post(f"{BACKEND_URL}/api/agent/heartbeat", json={
                "device_id": device_id
            })
            if response.status_code != 200:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Heartbeat failed: {response.text}")
        except Exception as e:
            pass # Silent fail for heartbeats to not spam logs
        time.sleep(30)

async def stream_loop(device_id):
    global is_streaming
    stream_url = f"{WS_URL}/api/ws/agent/{device_id}/stream"
    
    while True:
        if not is_streaming:
            await asyncio.sleep(0.5)
            continue
            
        try:
            async with websockets.connect(stream_url) as ws:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Stream connection established.")
                with mss() as sct:
                    monitor = sct.monitors[1] # Primary monitor
                    while is_streaming:
                        start_time = time.time()
                        
                        # Capture and compress
                        sct_img = sct.grab(monitor)
                        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                        
                        # Resize slightly for MVP bandwidth saving
                        img.thumbnail((1280, 720), Image.Resampling.LANCZOS)
                        
                        buffer = io.BytesIO()
                        img.save(buffer, format="JPEG", quality=60)
                        frame_data = buffer.getvalue()
                        
                        await ws.send(frame_data)
                        
                        # Target ~10 FPS
                        elapsed = time.time() - start_time
                        sleep_time = max(0, 0.1 - elapsed)
                        await asyncio.sleep(sleep_time)
                        
        except Exception as e:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Stream error: {e}")
            await asyncio.sleep(2)

async def control_loop(device_id):
    global is_streaming
    control_url = f"{WS_URL}/api/ws/agent/{device_id}/control"
    
    while True:
        try:
            async with websockets.connect(control_url) as ws:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Control connection established.")
                while True:
                    message = await ws.recv()
                    data = json.loads(message)
                    command = data.get("command")
                    
                    if command == "START_STREAM":
                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Received START_STREAM")
                        is_streaming = True
                    elif command == "STOP_STREAM":
                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Received STOP_STREAM")
                        is_streaming = False
        except Exception as e:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Control connection error: {e}")
            await asyncio.sleep(5)

async def main_async(device_id):
    await asyncio.gather(
        control_loop(device_id),
        stream_loop(device_id)
    )

if __name__ == "__main__":
    print("Employee Monitor Agent Starting...")
    print(f"Target Backend: {BACKEND_URL}")
    
    device_id = None
    while not device_id:
        device_id = register_agent()
        if not device_id:
            time.sleep(5)
            
    # Start HTTP heartbeat in background thread
    threading.Thread(target=heartbeat_loop, args=(device_id,), daemon=True).start()
    
    # Start WebSocket async loops
    asyncio.run(main_async(device_id))
