import json
import pytest
from fastapi.testclient import TestClient

from ytgrid.backend.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data

def test_health():
    # Assuming you have added a /health endpoint in main.py
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "healthy"

def test_start_and_stop_session():
    # Test starting a session
    payload = {
       "session_id": "test_api_session",
       "url": "https://www.youtube.com/watch?v=UXFBUZEpnrc",
       "speed": 1.0,
       "loop_count": 1,
       "task_type": "video"
    }
    response = client.post("/tasks/", json=payload)
    assert response.status_code == 201

    # Test status endpoint shows the session
    response_status = client.get("/tasks/")
    assert response_status.status_code == 200
    data_status = response_status.json()
    # It may include more sessions; ensure our session is present.
    sessions = data_status.get("active_sessions", [])
    assert any(s.get("id") == "test_api_session" for s in sessions)

    # Test stopping the session
    response_stop = client.post("/tasks/stop", json={"session_id": "test_api_session"})
    assert response_stop.status_code in (200, 404)  # 404 if already stopped
