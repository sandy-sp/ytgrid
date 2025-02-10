# ytgrid/backend/routes/__init__.py

from fastapi import APIRouter
from ytgrid.backend.routes.session import router as session_router
from ytgrid.backend.routes.task import router as task_router

router = APIRouter()
router.include_router(session_router, prefix="/sessions", tags=["sessions"])
router.include_router(task_router, prefix="/tasks", tags=["tasks"])
