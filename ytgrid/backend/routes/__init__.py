"""
YTGrid Routes Package (Version 3.1)

Aggregates session and task routes for the YTGrid API.
"""

from fastapi import APIRouter
from ytgrid.backend.routes.session import router as session_router
from ytgrid.backend.task import router as task_router
from ytgrid.backend.routes.profiles import router as profiles_router
from ytgrid.backend.routes.dashboard import router as dashboard_router

router = APIRouter()

# Include session routes under /sessions and task routes under /tasks.
router.include_router(session_router, prefix="/sessions", tags=["sessions"])
router.include_router(task_router, prefix="/tasks", tags=["tasks"])
router.include_router(profiles_router, prefix="/profiles", tags=["profiles"])
router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])

__all__ = ["router"]
