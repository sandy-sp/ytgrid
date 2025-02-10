import pytest
import requests

BASE_URL = "http://127.0.0.1:8000"

@pytest.fixture
def sample_session():
    return {
        "session_id": "test_session",
        "url": "https://www.youtube.com/watch?v=UXFBUZEpnrc",
        "speed": 1.5,
        "loop_count": 2,
        "task_type": "video"
    }

def test_start_session(sample_session):
    """Test starting a session using API."""
    response = requests.post(f"{BASE_URL}/sessions/start", json=sample_session)
    assert response.status_code == 200
    assert "session_id" in response.json()

def test_get_session_status():
    """Test getting active session status."""
    response = requests.get(f"{BASE_URL}/sessions/status")
    assert response.status_code == 200
    assert "active_sessions" in response.json()

def test_stop_session(sample_session):
    """Test stopping a session using API."""
    response = requests.post(f"{BASE_URL}/sessions/stop", json={"session_id": sample_session["session_id"]})
    assert response.status_code in [200, 404]  # If session exists, 200; else, 404.

def test_start_task(sample_session):
    """Test starting a task using API."""
    response = requests.post(f"{BASE_URL}/tasks/", json=sample_session)
    assert response.status_code == 201

def test_get_tasks():
    """Test retrieving running tasks."""
    response = requests.get(f"{BASE_URL}/tasks/")
    assert response.status_code == 200
    assert "active_sessions" in response.json()

def test_stop_task(sample_session):
    """Test stopping a task using API."""
    response = requests.post(f"{BASE_URL}/tasks/stop", json={"session_id": sample_session["session_id"]})
    assert response.status_code in [200, 404]
