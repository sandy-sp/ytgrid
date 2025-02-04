from sqlalchemy.orm import Session
from models import Session as SessionModel, SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_session(db: Session, url: str):
    session = SessionModel(url=url)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

def stop_session(db: Session, session_id: int):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if session:
        session.status = "stopped"
        session.active = False
        db.commit()
        return session
    return None

def get_sessions(db: Session):
    return db.query(SessionModel).filter(SessionModel.active == True).all()
