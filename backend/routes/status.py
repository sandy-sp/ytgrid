from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db, get_sessions

router = APIRouter(prefix="/status", tags=["Status"])

@router.get("/")
def get_active_sessions(db: Session = Depends(get_db)):
    sessions = get_sessions(db)
    return {"active_sessions": [{"id": s.id, "url": s.url, "status": s.status} for s in sessions]}
