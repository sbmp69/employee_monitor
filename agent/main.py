import os
import sys
import time
import requests
import socket
import threading
import json
import asyncio
import websockets
import subprocess
import datetime
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
recording_process = None
recording_start_time = None
temp_recording_file = "temp_record.mp4"

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
                    while True:
                        if not is_streaming:
                            await asyncio.sleep(0.5)
                            continue
                            
                        start_time = time.time()
                        
                        sct_img = sct.grab(monitor)
                        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                        
                        img.thumbnail((1280, 720), Image.Resampling.LANCZOS)
                        
                        buffer = io.BytesIO()
                        img.save(buffer, format="JPEG", quality=60)
                        frame_data = buffer.getvalue()
                        
                        await ws.send(frame_data)
                        
                        elapsed = time.time() - start_time
                        sleep_time = max(0, 0.1 - elapsed)
                        await asyncio.sleep(sleep_time)
                        
        except Exception as e:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Stream error: {e}")
            await asyncio.sleep(2)

def upload_recording_task(device_id, start_time, end_time, filepath):
    try:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Uploading recording...")
        with open(filepath, 'rb') as f:
            files = {'file': (os.path.basename(filepath), f, 'video/mp4')}
            data = {
                'device_id': device_id,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat()
            }
            res = requests.post(f"{BACKEND_URL}/api/agent/upload_recording", files=files, data=data)
            res.raise_for_status()
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Recording uploaded successfully.")
        # Clean up local temp file
        os.remove(filepath)
    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Failed to upload recording: {e}")

async def control_loop(device_id):
    global is_streaming, recording_process, recording_start_time
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
                    elif command == "START_RECORDING":
                        if recording_process is None:
                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting FFmpeg recording...")
                            recording_start_time = datetime.datetime.now(datetime.timezone.utc)
                            # Remove old temp file if it exists
                            if os.path.exists(temp_recording_file):
                                os.remove(temp_recording_file)
                            # Spawn FFmpeg
                            cmd = ["ffmpeg", "-f", "gdigrab", "-framerate", "15", "-i", "desktop", 
                                   "-c:v", "libx264", "-preset", "ultrafast", "-y", temp_recording_file]
                            # Use creationflags=subprocess.CREATE_NO_WINDOW to hide console on Windows in production
                            recording_process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    elif command == "STOP_RECORDING":
                        if recording_process is not None:
                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Stopping FFmpeg recording...")
                            # Send 'q' to gracefully stop ffmpeg
                            try:
                                recording_process.stdin.write(b'q')
                                recording_process.stdin.flush()
                                recording_process.communicate(timeout=10)
                            except:
                                recording_process.terminate()
                            
                            end_time = datetime.datetime.now(datetime.timezone.utc)
                            recording_process = None
                            
                            threading.Thread(target=upload_recording_task, args=(device_id, recording_start_time, end_time, temp_recording_file), daemon=True).start()
                    elif command == "UPDATE_POLICY":
                        websites = data.get("websites", [])
                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Received UPDATE_POLICY: {websites}")
                        threading.Thread(target=apply_policy, args=(device_id, websites), daemon=True).start()

        except Exception as e:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Control connection error: {e}")
            await asyncio.sleep(5)

def apply_policy(device_id, websites):
    HOSTS_FILE = r"C:\Windows\System32\drivers\etc\hosts"
    BLOCK_START = "# --- EMPLOYEE MONITOR BLOCK ---"
    BLOCK_END = "# --- END EMPLOYEE MONITOR BLOCK ---"
    
    try:
        if not os.path.exists(HOSTS_FILE):
            report_policy_status(device_id, "Failed: Hosts file not found")
            return
            
        with open(HOSTS_FILE, 'r') as f:
            lines = f.readlines()
            
        # Remove old block
        new_lines = []
        in_block = False
        for line in lines:
            if line.strip() == BLOCK_START:
                in_block = True
                continue
            if line.strip() == BLOCK_END:
                in_block = False
                continue
            if not in_block:
                new_lines.append(line)
                
        # Append new block
        if websites:
            new_lines.append(f"\n{BLOCK_START}\n")
            for site in websites:
                site = site.strip()
                if site:
                    new_lines.append(f"127.0.0.1 {site}\n")
                    new_lines.append(f"127.0.0.1 www.{site}\n")
            new_lines.append(f"{BLOCK_END}\n")
            
        # Requires Admin privileges!
        with open(HOSTS_FILE, 'w') as f:
            f.writelines(new_lines)
            
        report_policy_status(device_id, "Applied successfully")
    except PermissionError:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Permission denied editing hosts file. Run as Admin.")
        report_policy_status(device_id, "Failed: Access Denied (Not Admin)")
    except Exception as e:
        report_policy_status(device_id, f"Failed: {str(e)}")

def report_policy_status(device_id, status):
    try:
        requests.post(f"{BACKEND_URL}/api/agent/policy_status", json={
            "device_id": device_id,
            "status": status
        })
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Policy status reported: {status}")
    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Failed to report policy status: {e}")

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
            
    threading.Thread(target=heartbeat_loop, args=(device_id,), daemon=True).start()
    
    asyncio.run(main_async(device_id))
