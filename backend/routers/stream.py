from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
import asyncio
import json

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        # Maps device_id to Agent Control WebSocket
        self.active_agents: Dict[str, WebSocket] = {}
        # Maps device_id to list of Admin WebSockets viewing it
        self.active_admins: Dict[str, list[WebSocket]] = {}
        # Maps device_id to Agent Stream WebSocket (the one sending frames)
        self.agent_streams: Dict[str, WebSocket] = {}

    async def connect_agent_control(self, websocket: WebSocket, device_id: str):
        await websocket.accept()
        self.active_agents[device_id] = websocket

    def disconnect_agent_control(self, device_id: str):
        if device_id in self.active_agents:
            del self.active_agents[device_id]

    async def connect_agent_stream(self, websocket: WebSocket, device_id: str):
        await websocket.accept()
        self.agent_streams[device_id] = websocket

    def disconnect_agent_stream(self, device_id: str):
        if device_id in self.agent_streams:
            del self.agent_streams[device_id]

    async def connect_admin(self, websocket: WebSocket, device_id: str):
        await websocket.accept()
        if device_id not in self.active_admins:
            self.active_admins[device_id] = []
        self.active_admins[device_id].append(websocket)
        
        # Tell agent to start streaming if it isn't already
        if len(self.active_admins[device_id]) == 1 and device_id in self.active_agents:
            await self.active_agents[device_id].send_text(json.dumps({"command": "START_STREAM"}))

    async def disconnect_admin(self, websocket: WebSocket, device_id: str):
        if device_id in self.active_admins:
            if websocket in self.active_admins[device_id]:
                self.active_admins[device_id].remove(websocket)
            
            # Tell agent to stop streaming if no admins are watching
            if len(self.active_admins[device_id]) == 0:
                del self.active_admins[device_id]
                if device_id in self.active_agents:
                    try:
                        await self.active_agents[device_id].send_text(json.dumps({"command": "STOP_STREAM"}))
                    except:
                        pass

    async def broadcast_frame(self, device_id: str, frame: bytes):
        if device_id in self.active_admins:
            for admin_ws in self.active_admins[device_id]:
                try:
                    await admin_ws.send_bytes(frame)
                except:
                    pass

    async def send_command_to_agent(self, device_id: str, command: str):
        if device_id in self.active_agents:
            await self.active_agents[device_id].send_text(json.dumps({"command": command}))
            return True
        return False

manager = ConnectionManager()

@router.websocket("/ws/agent/{device_id}/control")
async def agent_control_endpoint(websocket: WebSocket, device_id: str):
    await manager.connect_agent_control(websocket, device_id)
    try:
        while True:
            # Keep connection alive, listen for agent status
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_agent_control(device_id)

@router.websocket("/ws/agent/{device_id}/stream")
async def agent_stream_endpoint(websocket: WebSocket, device_id: str):
    await manager.connect_agent_stream(websocket, device_id)
    try:
        while True:
            frame = await websocket.receive_bytes()
            await manager.broadcast_frame(device_id, frame)
    except WebSocketDisconnect:
        manager.disconnect_agent_stream(device_id)

@router.websocket("/ws/admin/{device_id}")
async def admin_stream_endpoint(websocket: WebSocket, device_id: str, token: str = None):
    # In a production app, verify the Supabase JWT token here.
    # supabase.auth.get_user(token) ...
    # For MVP, we will assume token is provided and valid if it reaches here, 
    # but strictly speaking we should await a token validation.
    
    await manager.connect_admin(websocket, device_id)
    try:
        while True:
            # Just keep connection alive from admin side
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect_admin(websocket, device_id)
