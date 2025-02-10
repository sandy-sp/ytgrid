# ytgrid/backend/routes/session.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from ytgrid.backend.dependencies import get_session_store

router = APIRouter()

class SessionStartRequest(BaseModel):
    url: str
    speed: float = 1.0
    loop_count: int = 1

class SessionStopRequest(BaseModel):
    session_id: int

@router.post("/start")
async def start_session(request: SessionStartRequest, session_store = Depends(get_session_store)):
    session_id = session_store.create_session(request.url)
    return {"session_id": session_id, "status": "running"}

@router.post("/stop")
async def stop_session(request: SessionStopRequest, session_store = Depends(get_session_store)):
    if session_store.stop_session(request.session_id):
        return {"session_id": request.session_id, "status": "stopped"}
    raise HTTPException(status_code=404, detail="Session not found")

@router.get("/status")
async def status(session_store = Depends(get_session_store)):
    return {"active_sessions": session_store.get_active_sessions()}
