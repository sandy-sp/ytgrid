"""
Session Store Module (Version 3)

This module defines an abstract base class for session storage and two concrete implementations:
  - InMemorySessionStore: a simple in-memory session store.
  - MultiprocessingSessionStore: a session store intended for use with shared memory in multiprocessing environments.

Both implementations follow the same interface defined by AbstractSessionStore.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

# Type alias for a session record.
SessionRecord = Dict[str, Any]


class AbstractSessionStore(ABC):
    @abstractmethod
    def create_session(self, url: str) -> int:
        """
        Creates a new session given a URL and returns its session ID.
        
        :param url: The URL associated with the session.
        :return: An integer session ID.
        """
        pass

    @abstractmethod
    def stop_session(self, session_id: int) -> bool:
        """
        Stops an active session.
        
        :param session_id: The identifier of the session to stop.
        :return: True if the session was stopped successfully, False otherwise.
        """
        pass

    @abstractmethod
    def get_active_sessions(self) -> List[SessionRecord]:
        """
        Retrieves a list of active sessions.
        
        :return: A list of session records where each record is a dictionary containing session details.
        """
        pass


class InMemorySessionStore(AbstractSessionStore):
    """
    A simple in-memory session store.
    
    This store maintains sessions in a dictionary and uses an incremental counter for session IDs.
    """
    def __init__(self) -> None:
        self.sessions: Dict[int, SessionRecord] = {}
        self.session_id_counter: int = 1

    def create_session(self, url: str) -> int:
        session_id: int = self.session_id_counter
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

    def get_active_sessions(self) -> List[SessionRecord]:
        return [
            session for session in self.sessions.values()
            if session.get("status") == "running"
        ]


class MultiprocessingSessionStore(AbstractSessionStore):
    """
    A session store for use with multiprocessing environments.
    
    This store requires a shared dictionary (e.g., provided by a multiprocessing.Manager) to store sessions,
    and maintains its own session ID counter.
    """
    def __init__(self, shared_sessions: Dict[int, SessionRecord], session_id_counter: int = 1) -> None:
        self.sessions: Dict[int, SessionRecord] = shared_sessions
        self.session_id_counter: int = session_id_counter

    def create_session(self, url: str) -> int:
        session_id: int = self.session_id_counter
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

    def get_active_sessions(self) -> List[SessionRecord]:
        return [
            session for session in self.sessions.values()
            if session.get("status") == "running"
        ]
