class SessionStore:
    """Manages active video automation sessions in memory."""

    def __init__(self):
        self.sessions = {}
        self.session_id_counter = 1

    def create_session(self, url):
        session_id = self.session_id_counter
        self.sessions[session_id] = {"id": session_id, "url": url, "status": "running"}
        self.session_id_counter += 1
        return session_id

    def stop_session(self, session_id):
        """Updates session status to stopped."""
        if session_id in self.sessions:
            self.sessions[session_id]["status"] = "stopped"
            return True
        return False

    def get_active_sessions(self):
        """Returns only running sessions."""
        return [session for session in self.sessions.values() if session["status"] == "running"]

# Create a global session store instance
session_store = SessionStore()
