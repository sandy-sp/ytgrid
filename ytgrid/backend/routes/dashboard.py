import json
import time
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from ytgrid.backend.task_manager import task_manager
from ytgrid.backend.auth import verify_api_key

router = APIRouter(tags=["dashboard"])

MAX_DASHBOARD_CONNECTIONS = 10
_active_dashboard_connections = 0


@router.get("/stream", dependencies=[Depends(verify_api_key)])
async def dashboard_stream():
    """Server-Sent Event stream emitting real-time dashboard analytics.

    Auth, a connection cap and a hard duration limit prevent the endpoint
    from being used as a resource-exhaustion vector.
    """
    global _active_dashboard_connections
    if _active_dashboard_connections >= MAX_DASHBOARD_CONNECTIONS:
        raise HTTPException(status_code=429, detail="Too many dashboard connections")

    async def _event_generator():
        global _active_dashboard_connections
        _active_dashboard_connections += 1
        max_duration = 3600  # 1 hour max
        start_time = time.time()
        try:
            while time.time() - start_time < max_duration:
                active_sessions = task_manager.get_active_sessions()
                state = {
                    "active_sessions": active_sessions,
                    "session_count": len(active_sessions),
                    "system_health": {
                        "cpu": "N/A",  # Mocked for now, psutil could be hooked here
                        "ram": "N/A",
                    },
                }
                yield f"data: {json.dumps(state)}\n\n"
                await asyncio.sleep(2)
        finally:
            _active_dashboard_connections -= 1

    return StreamingResponse(_event_generator(), media_type="text/event-stream")
