from fastapi import APIRouter, Depends, HTTPException
from core.database import supabase
from core.auth import get_current_admin
from schemas import ComputerResponse
from typing import List

router = APIRouter()

@router.get("/computers", response_model=List[ComputerResponse])
def get_computers(admin = Depends(get_current_admin)):
    try:
        res = supabase.table("computers").select("*").order("last_seen", desc=True).execute()
        return res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
