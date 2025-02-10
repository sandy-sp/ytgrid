# ytgrid/backend/session_store.py
from abc import ABC, abstractmethod

class AbstractSessionStore(ABC):
    @abstractmethod
    def create_session(self, url: str) -> int:
        """Creates a new session given a URL and returns its session ID."""
        pass

    @abstractmethod
    def stop_session(self, session_id: int) -> bool:
        """Stops an active session. Returns True if successful."""
        pass

    @abstractmethod
    def get_active_sessions(self):
        """Returns a list of active sessions."""
        pass


class InMemorySessionStore(AbstractSessionStore):
    def __init__(self):
        self.sessions = {}
        self.session_id_counter = 1

    def create_session(self, url: str) -> int:
        session_id = self.session_id_counter
        self.sessions[session_id] = {
            "id": session_id,
            "url": url,
            "status": "running"
        }
        self.session_id_counter += 1
        return session_id

    def stop_session(self, session_id: int) -> bool:
        if session_id in self.sessions:
            self.sessions[session_id]["status"] = "stopped"
            return True
        return False

    def get_active_sessions(self):
        return [
            session for session in self.sessions.values()
            if session["status"] == "running"
        ]


class MultiprocessingSessionStore(AbstractSessionStore):
    def __init__(self, shared_sessions, session_id_counter: int = 1):
        self.sessions = shared_sessions
        self.session_id_counter = session_id_counter

    def create_session(self, url: str) -> int:
        session_id = self.session_id_counter
        self.sessions[session_id] = {
            "id": session_id,
            "url": url,
            "status": "running"
        }
        self.session_id_counter += 1
        return session_id

    def stop_session(self, session_id: int) -> bool:
        if session_id in self.sessions:
            self.sessions[session_id]["status"] = "stopped"
            return True
        return False

    def get_active_sessions(self):
        return [
            session for session in self.sessions.values()
            if session["status"] == "running"
        ]
