import pytest
import requests

BASE_URL = "http://127.0.0.1:8000"

@pytest.fixture
def sample_session():
    """Fixture to create a sample session request object."""
    return {
        "session_id": 1,  # ✅ Ensure it's an integer
        "url": "https://www.youtube.com/watch?v=OaOK76hiW8I",
        "speed": 1.5,
        "loop_count": 2
    }

@pytest.fixture
def sample_task():
    """Fixture to create a sample task request object."""
    return {
        "session_id": "task_1",
        "url": "https://www.youtube.com/watch?v=OaOK76hiW8I",
        "speed": 1.5,
        "loop_count": 2,
        "task_type": "video"
    }

def test_start_session(sample_session):
    """Test starting a session using API."""
    response = requests.post(f"{BASE_URL}/sessions/start", json=sample_session)
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["status"] == "running"

def test_get_session_status():
    """Test getting active session status."""
    response = requests.get(f"{BASE_URL}/sessions/status")
    assert response.status_code == 200
    data = response.json()
    assert "active_sessions" in data

def test_stop_session(sample_session):
    """Test stopping a session using API."""
    response = requests.post(f"{BASE_URL}/sessions/stop", json={"session_id": int(sample_session["session_id"])})  # ✅ Ensure int
    assert response.status_code in [200, 404]

def test_start_task(sample_task):
    """Test starting a task using API."""
    response = requests.post(f"{BASE_URL}/tasks/", json=sample_task)
    assert response.status_code == 201
    data = response.json()
    assert "message" in data

def test_get_tasks():
    """Test retrieving running tasks."""
    response = requests.get(f"{BASE_URL}/tasks/")
    assert response.status_code == 200
    data = response.json()
    assert "active_sessions" in data

def test_stop_task(sample_task):
    """Test stopping a task using API."""
    response = requests.post(f"{BASE_URL}/tasks/stop", json={"session_id": sample_task["session_id"]})
    assert response.status_code in [200, 404]
