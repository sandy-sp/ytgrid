from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, create_session, stop_session
from models import Session as SessionModel

router = APIRouter(prefix="/sessions", tags=["Sessions"])

@router.post("/start-session")
def start_session(url: str, db: Session = Depends(get_db)):
    session = create_session(db, url)
    return {"message": "Session started", "session_id": session.id, "url": session.url}

@router.post("/stop-session")
def stop_active_session(session_id: int, db: Session = Depends(get_db)):
    session = stop_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session stopped", "session_id": session_id}
