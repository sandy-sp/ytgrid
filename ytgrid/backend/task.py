"""
YTGrid Task Routes (Version 3)

This module provides endpoints for managing automation tasks:
  - Starting a task.
  - Stopping a task.
  - Retrieving active tasks.
  - Streaming task updates via SSE.
"""

import json
import asyncio
from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ytgrid.backend.task_manager import task_manager

router = APIRouter()


class TaskStartRequest(BaseModel):
    session_id: str
    url: str
    speed: float
    loop_count: int
    task_type: str = "video"


class TaskStopRequest(BaseModel):
    session_id: str


@router.post("/", status_code=201, tags=["tasks"])
async def start_task(request: TaskStartRequest) -> Dict[str, str]:
    """
    Start a new automation task.

    :param request: TaskStartRequest containing session_id, URL, speed, loop_count, and task_type.
    :return: A message confirming the task has started.
    :raises HTTPException: 400 if the session already exists.
    """
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


@router.post("/stop", status_code=200, tags=["tasks"])
async def stop_task(request: TaskStopRequest) -> Dict[str, str]:
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
async def get_tasks() -> Dict[str, Any]:
    """
    Retrieve a list of active automation tasks.

    :return: A dictionary with active_sessions key containing a list of active session details.
    """
    active_sessions = task_manager.get_active_sessions()
    return {"active_sessions": active_sessions}


@router.get("/stream", tags=["tasks"])
async def stream_tasks() -> StreamingResponse:
    """
    SSE endpoint to stream active session status updates every 5 seconds.

    :return: A StreamingResponse yielding session updates in SSE format.
    """
    async def event_generator():
        while True:
            sessions = task_manager.get_active_sessions()
            data = json.dumps({"active_sessions": sessions})
            yield f"data: {data}\n\n"
            await asyncio.sleep(5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
