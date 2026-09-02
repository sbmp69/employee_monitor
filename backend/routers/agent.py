from fastapi import APIRouter, HTTPException, Depends
from core.database import supabase
from schemas import AgentRegisterRequest, AgentRegisterResponse, AgentHeartbeatRequest
from datetime import datetime, timezone

router = APIRouter()

@router.post("/register", response_model=AgentRegisterResponse)
def register_agent(req: AgentRegisterRequest):
    # Check if a device with this name already exists
    # (For MVP, we use device_name as unique identifier before assigning an ID)
    # Alternatively, the agent could generate the UUID itself. We will let the DB generate it.
    
    # Let's insert a new record. We let Supabase generate the UUID.
    # If the agent wipes its ID, it will register as a new device. For an MVP this is acceptable.
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
        # Update last_seen and status
        res = supabase.table("computers").update({
            "status": "online",
            "last_seen": datetime.now(timezone.utc).isoformat()
        }).eq("id", req.device_id).execute()
        
        if not res.data:
            raise HTTPException(status_code=404, detail="Device not found")
            
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
