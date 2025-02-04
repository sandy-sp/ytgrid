from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, create_session, stop_session
from models import Session as SessionModel
import threading
import sys
import os

# Fix module import error
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from automation.player import play_video

router = APIRouter(prefix="/sessions", tags=["Sessions"])

def run_video(url, speed=1.0):
    play_video(url, speed)

@router.post("/start-session")
def start_session(url: str, speed: float = 1.0, db: Session = Depends(get_db)):
    session = create_session(db, url)

    # Run Selenium automation in a separate thread
    thread = threading.Thread(target=run_video, args=(url, speed))
    thread.start()

    return {"message": "Session started", "session_id": session.id, "url": session.url, "speed": speed}
