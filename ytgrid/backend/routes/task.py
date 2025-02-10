# ytgrid/backend/routes/task.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ytgrid.backend.task_manager import task_manager

router = APIRouter()

class TaskStartRequest(BaseModel):
    session_id: str
    url: str
    speed: float
    loop_count: int
    task_type: str = "video"  # default type

class TaskStopRequest(BaseModel):
    session_id: str

@router.post("/", status_code=201)
def start_task(request: TaskStartRequest):
    success = task_manager.start_session(
        session_id=request.session_id,
        url=request.url,
        speed=request.speed,
        loop_count=request.loop_count,
        task_type=request.task_type
    )
    if not success:
        raise HTTPException(status_code=400, detail="Session already exists")
    return {"message": f"Task {request.session_id} started."}

@router.post("/stop", status_code=200)
def stop_task(request: TaskStopRequest):
    success = task_manager.stop_session(request.session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": f"Task {request.session_id} stopped."}

@router.get("/")
def get_tasks():
    active_sessions = task_manager.get_active_sessions()
    return {"active_sessions": active_sessions}
