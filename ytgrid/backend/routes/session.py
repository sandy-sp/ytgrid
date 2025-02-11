"""
Session Routes Module (Version 3)

Provides endpoints to manage session operations:
  - Start a session.
  - Stop a session.
  - Retrieve status of sessions.

Dependencies are injected via the get_session_store function.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any, Dict

from ytgrid.backend.dependencies import get_session_store

router = APIRouter()


class SessionStartRequest(BaseModel):
    """
    Request model for starting a session.
    
    Attributes:
        url (str): The YouTube video URL.
        speed (float): Playback speed multiplier (default is 1.0).
        loop_count (int): Number of loops to play the video (default is 1).
    """
    url: str
    speed: float = 1.0
    loop_count: int = 1


class SessionStopRequest(BaseModel):
    """
    Request model for stopping a session.
    
    Attributes:
        session_id (int): The identifier of the session to stop.
    """
    session_id: int


@router.post("/start", tags=["sessions"], response_model=Dict[str, Any])
async def start_session(
    request: SessionStartRequest,
    session_store: Any = Depends(get_session_store)
) -> Dict[str, Any]:
    """
    Start a new session using the provided URL and parameters.

    :param request: A SessionStartRequest instance with URL, speed, and loop_count.
    :param session_store: The session storage instance injected via dependency.
    :return: A dictionary with the session_id and status.
    """
    session_id = session_store.create_session(request.url)
    return {"session_id": session_id, "status": "running"}


@router.post("/stop", tags=["sessions"], response_model=Dict[str, Any])
async def stop_session(
    request: SessionStopRequest,
    session_store: Any = Depends(get_session_store)
) -> Dict[str, Any]:
    """
    Stop an active session specified by the session_id.

    :param request: A SessionStopRequest instance containing the session_id.
    :param session_store: The session storage instance injected via dependency.
    :return: A dictionary with the session_id and status if the session is stopped.
    :raises HTTPException: If the session is not found.
    """
    if session_store.stop_session(request.session_id):
        return {"session_id": request.session_id, "status": "stopped"}
    raise HTTPException(status_code=404, detail="Session not found")


@router.get("/status", tags=["sessions"], response_model=Dict[str, Any])
async def status(
    session_store: Any = Depends(get_session_store)
) -> Dict[str, Any]:
    """
    Retrieve the status of all active sessions.

    :param session_store: The session storage instance injected via dependency.
    :return: A dictionary containing active_sessions.
    """
    return {"active_sessions": session_store.get_active_sessions()}
