"""
YTGrid Task Routes (Version 3.1)

This module provides endpoints for managing automation tasks:
  - Starting a task.
  - Stopping a task.
  - Retrieving active tasks.
  - Streaming task updates via SSE.
"""

import json
import asyncio
import time
import re
from typing import Dict, Any, Literal, Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

from ytgrid.backend.task_manager import task_manager
from ytgrid.backend.auth import verify_api_key

router = APIRouter()

MAX_SSE_CONNECTIONS = 10
_active_sse_connections = 0

import uuid

class TaskStartRequest(BaseModel):
    session_id: Optional[str] = Field(None, pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    url: str
    speed: float = Field(1.0, ge=0.25, le=16.0)
    loop_count: int = Field(1, ge=1, le=1000)
    task_type: Literal["video", "playlist", "channel"] = "video"

    @field_validator("url")
    @classmethod
    def validate_youtube_url(cls, value: str) -> str:
        pattern = r"^(https?://)?(www\.)?(youtube\.com|youtu\.be)/(watch\?v=[\w-]+|playlist\?list=[\w-]+|@[\w-]+|c/[\w-]+|channel/[\w-]+|user/[\w-]+)?"
        if not re.match(pattern, value):
            raise ValueError("Invalid YouTube URL. Must be a valid video, playlist, or channel URL.")
        return value


class TaskStopRequest(BaseModel):
    session_id: str = Field(..., pattern=r"^[a-zA-Z0-9_-]{1,64}$")


@router.post("/", status_code=201, tags=["tasks"])
async def start_task(request: TaskStartRequest, api_key: str = Depends(verify_api_key)) -> Dict[str, str]:
    """
    Start a new automation task.

    :param request: TaskStartRequest containing session_id, URL, speed, loop_count, and task_type.
    :return: A message confirming the task has started.
    :raises HTTPException: 400 if the session already exists.
    """
    session_id = request.session_id or uuid.uuid4().hex[:8]
    success = task_manager.start_session(
        session_id=session_id,
        url=request.url,
        speed=request.speed,
        loop_count=request.loop_count,
        task_type=request.task_type
    )
    if not success:
        detail = task_manager.last_start_error or "Session could not be started"
        status_code = 503 if "resources" in detail.lower() else 400
        raise HTTPException(status_code=status_code, detail=detail)
    return {"message": f"Task {session_id} started.", "session_id": session_id}


@router.post("/stop", status_code=200, tags=["tasks"])
async def stop_task(request: TaskStopRequest, api_key: str = Depends(verify_api_key)) -> Dict[str, str]:
    """
    Stop an active automation task.

    :param request: TaskStopRequest containing the session_id.
    :return: A message confirming the task has been stopped.
    :raises HTTPException: 404 if the session is not found.
    """
    success = task_manager.stop_session(request.session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": f"Task {request.session_id} stopped."}


@router.get("/", tags=["tasks"])
async def get_tasks(api_key: str = Depends(verify_api_key)) -> Dict[str, Any]:
    """
    Retrieve a list of active automation tasks.

    :return: A dictionary with active_sessions key containing a list of active session details.
    """
    active_sessions = task_manager.get_active_sessions()
    return {"active_sessions": active_sessions}


@router.get("/stream", tags=["tasks"])
async def stream_tasks(api_key: str = Depends(verify_api_key)) -> StreamingResponse:
    """
    SSE endpoint to stream active session status updates every 5 seconds.

    :return: A StreamingResponse yielding session updates in SSE format.
    """
    global _active_sse_connections
    if _active_sse_connections >= MAX_SSE_CONNECTIONS:
        raise HTTPException(status_code=429, detail="Too many SSE connections")

    async def event_generator():
        global _active_sse_connections
        _active_sse_connections += 1
        max_duration = 3600  # 1 hour max
        start_time = time.time()
        try:
            while time.time() - start_time < max_duration:
                sessions = task_manager.get_active_sessions()
                data = json.dumps({"active_sessions": sessions})
                yield f"data: {data}\n\n"
                await asyncio.sleep(5)
        finally:
            _active_sse_connections -= 1

    return StreamingResponse(event_generator(), media_type="text/event-stream")
