from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from core.database import supabase
from core.auth import get_current_admin
from core.audit import log_audit_action
from schemas import ComputerResponse, RecordingResponse, AuditLogResponse, ComputerEditRequest
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

@router.put("/computers/{device_id}")
def update_computer(device_id: str, req: ComputerEditRequest, admin = Depends(get_current_admin)):
    try:
        res = supabase.table("computers").update({
            "device_name": req.device_name,
            "employee_name": req.employee_name
        }).eq("id", device_id).execute()
        
        if not res.data:
            raise HTTPException(status_code=404, detail="Device not found")
            
        log_audit_action(admin, "EDIT_DEVICE", device_id, {"new_name": req.device_name, "employee": req.employee_name})
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/computers/{device_id}")
def delete_computer(device_id: str, admin = Depends(get_current_admin)):
    try:
        res = supabase.table("computers").delete().eq("id", device_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Device not found")
            
        log_audit_action(admin, "REVOKE_DEVICE", device_id)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/recordings/start/{device_id}")
async def start_recording(device_id: str, admin = Depends(get_current_admin)):
    success = await manager.send_command_to_agent(device_id, "START_RECORDING")
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent is not connected")
    log_audit_action(admin, "START_RECORDING", device_id)
    return {"status": "ok"}

@router.post("/recordings/stop/{device_id}")
async def stop_recording(device_id: str, admin = Depends(get_current_admin)):
    success = await manager.send_command_to_agent(device_id, "STOP_RECORDING")
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent is not connected")
    log_audit_action(admin, "STOP_RECORDING", device_id)
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
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
        
    try:
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
            
        # Optional: log playback
        # log_audit_action(user, "PLAY_RECORDING", details={"recording_id": recording_id})
        
        return FileResponse(filepath, media_type="video/mp4")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/computers/{device_id}/policy")
async def update_policy(device_id: str, req: __import__('schemas').PolicyUpdateRequest, admin = Depends(get_current_admin)):
    try:
        res = supabase.table("computers").update({
            "blocked_websites": req.websites,
            "policy_status": "Pushing..."
        }).eq("id", device_id).execute()
        
        if not res.data:
            raise HTTPException(status_code=404, detail="Device not found")
            
        success = await manager.send_command_to_agent(device_id, "UPDATE_POLICY", websites=req.websites)
        if not success:
            supabase.table("computers").update({"policy_status": "Pending (Offline)"}).eq("id", device_id).execute()
            
        log_audit_action(admin, "UPDATE_POLICY", device_id, {"websites_count": len(req.websites)})
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/audit_logs", response_model=List[AuditLogResponse])
def get_audit_logs(admin = Depends(get_current_admin)):
    try:
        res = supabase.table("audit_logs").select("*").order("created_at", desc=True).limit(100).execute()
        return res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
