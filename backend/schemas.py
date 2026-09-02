from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from datetime import datetime

class AgentRegisterRequest(BaseModel):
    device_name: str
    agent_version: str

class AgentRegisterResponse(BaseModel):
    device_id: str

class AgentHeartbeatRequest(BaseModel):
    device_id: str

class ComputerResponse(BaseModel):
    id: str
    device_name: str
    employee_name: Optional[str] = None
    status: str
    last_seen: datetime
    agent_version: Optional[str] = None
    blocked_websites: Optional[List[str]] = []
    policy_status: Optional[str] = None

class ComputerEditRequest(BaseModel):
    device_name: str
    employee_name: Optional[str] = None

class RecordingResponse(BaseModel):
    id: str
    device_id: str
    filename: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    file_size: Optional[int] = None
    created_at: datetime

class PolicyUpdateRequest(BaseModel):
    websites: List[str]

class AgentPolicyStatusRequest(BaseModel):
    device_id: str
    status: str

class AuditLogResponse(BaseModel):
    id: str
    action: str
    admin_email: Optional[str] = None
    target_device_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    created_at: datetime
