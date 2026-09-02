from pydantic import BaseModel
from typing import Optional
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
