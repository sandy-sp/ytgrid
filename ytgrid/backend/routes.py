from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from ytgrid.backend.session_store import session_store
from ytgrid.backend.task_manager import task_manager
import asyncio

router = APIRouter()

# Store active WebSocket connections
active_connections = []

class StartSessionRequest(BaseModel):
    url: str
    speed: float = 1.0
    loop_count: int = 1

async def websocket_handler(websocket: WebSocket):
    """Handles WebSocket connections for real-time updates."""
    await websocket.accept()
    active_connections.append(websocket)

    try:
        while True:
            await websocket.receive_text()  # Keeps connection alive
    except WebSocketDisconnect:
        active_connections.remove(websocket)

async def send_update_to_clients(message):
    """Broadcasts updates to all active WebSocket clients."""
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except:
            active_connections.remove(connection)

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time loop tracking."""
    await websocket_handler(websocket)

@router.post("/sessions/start")
def start_session(request: StartSessionRequest):
    """Starts a YT automation session with multiprocessing support."""
    session_id = session_store.create_session(request.url)
    task_manager.start_session(session_id, request.url, request.speed, request.loop_count)
    return {"message": "Session started", "session_id": session_id, "url": request.url, "speed": request.speed, "loops": request.loop_count}

class StopSessionRequest(BaseModel):
    session_id: int

@router.post("/sessions/stop")
def stop_session(request: StopSessionRequest):
    """Stops an active session."""
    success = task_manager.stop_session(request.session_id)
    if success:
        return {"message": f"Session {request.session_id} stopped"}
    return {"error": f"Session {request.session_id} not found"}

@router.get("/status")
def get_status():
    """Returns the status of all active sessions with loop progress."""
    active_sessions = task_manager.get_active_sessions()
    session_info = [
        {
            "id": session["id"],
            "url": session_store.sessions[session["id"]]["url"],
            "status": "running",
            "current_loop": session["loop"]
        }
        for session in active_sessions
    ]
    return {"active_sessions": session_info}
