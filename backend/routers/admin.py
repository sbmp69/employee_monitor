from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from core.database import supabase
from core.auth import get_current_admin
from schemas import ComputerResponse, RecordingResponse
from routers.stream import manager
from typing import List
import os

router = APIRouter()

@router.get("/computers", response_model=List[ComputerResponse])
def get_computers(admin = Depends(get_current_admin)):
    try:
        res = supabase.table("computers").select("*").order("last_seen", desc=True).execute()
        return res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/recordings/start/{device_id}")
async def start_recording(device_id: str, admin = Depends(get_current_admin)):
    success = await manager.send_command_to_agent(device_id, "START_RECORDING")
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent is not connected")
    return {"status": "ok"}

@router.post("/recordings/stop/{device_id}")
async def stop_recording(device_id: str, admin = Depends(get_current_admin)):
    success = await manager.send_command_to_agent(device_id, "STOP_RECORDING")
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent is not connected")
    return {"status": "ok"}

@router.get("/recordings/{device_id}", response_model=List[RecordingResponse])
def get_recordings(device_id: str, admin = Depends(get_current_admin)):
    try:
        res = supabase.table("recordings").select("*").eq("device_id", device_id).order("created_at", desc=True).execute()
        return res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recordings/play/{recording_id}")
def play_recording(recording_id: str, token: str = None):
    # For a real app, securely validate the token via query parameter or cookie
    # Since HTML5 video src doesn't easily send Auth headers.
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
        
    try:
        # verify token
        user = supabase.auth.get_user(token)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
            
        res = supabase.table("recordings").select("filename").eq("id", recording_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Recording not found in DB")
            
        filename = res.data[0]['filename']
        filepath = os.path.join("recordings", filename)
        
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="Recording file not found on disk")
            
        return FileResponse(filepath, media_type="video/mp4")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
