from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from core.database import supabase
from schemas import AgentRegisterRequest, AgentRegisterResponse, AgentHeartbeatRequest
from datetime import datetime, timezone
import os
import shutil

router = APIRouter()

os.makedirs("recordings", exist_ok=True)

@router.post("/register", response_model=AgentRegisterResponse)
def register_agent(req: AgentRegisterRequest):
    try:
        res = supabase.table("computers").insert({
            "device_name": req.device_name,
            "agent_version": req.agent_version,
            "status": "online",
            "last_seen": datetime.now(timezone.utc).isoformat()
        }).execute()
        
        if not res.data:
            raise HTTPException(status_code=500, detail="Failed to register computer")
            
        device_id = res.data[0]['id']
        return AgentRegisterResponse(device_id=device_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/heartbeat")
def agent_heartbeat(req: AgentHeartbeatRequest):
    try:
        res = supabase.table("computers").update({
            "status": "online",
            "last_seen": datetime.now(timezone.utc).isoformat()
        }).eq("id", req.device_id).execute()
        
        if not res.data:
            raise HTTPException(status_code=404, detail="Device not found")
            
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload_recording")
async def upload_recording(
    device_id: str = Form(...),
    start_time: str = Form(...),
    end_time: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        # Save file to disk
        filename = f"{device_id}_{int(datetime.now().timestamp())}.mp4"
        filepath = os.path.join("recordings", filename)
        
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        file_size = os.path.getsize(filepath)
        
        # Insert metadata into Supabase
        res = supabase.table("recordings").insert({
            "device_id": device_id,
            "filename": filename,
            "start_time": start_time,
            "end_time": end_time,
            "file_size": file_size
        }).execute()
        
        return {"status": "ok", "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
