import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from ytgrid.backend.main import app

client = TestClient(app)


def test_root():
    """Test root endpoint to ensure API is running."""
    response = client.get("/")
    assert response.status_code == 200


def test_health():
    """Test health endpoint to ensure API is healthy."""
    response = client.get("/health")
    assert response.status_code == 200


@patch("ytgrid.backend.task_manager.task_manager.start_session", return_value=True)
def test_start_session(mock_start_session):
    """Test starting a session without real automation."""
    payload = {
        "session_id": "test_simple",
        "url": "https://www.youtube.com/watch?v=UXFBUZEpnrc",
        "speed": 1.0,
        "loop_count": 1,
        "task_type": "video"
    }
    response = client.post("/tasks/", json=payload)
    assert response.status_code == 201


@patch("ytgrid.backend.task_manager.task_manager.get_active_sessions", return_value=[])
def test_session_status(mock_get_active_sessions):
    """Test retrieving session status (always returns empty in CI)."""
    response = client.get("/tasks/")
    assert response.status_code == 200


@patch("ytgrid.backend.task_manager.task_manager.stop_session", return_value=True)
def test_stop_session(mock_stop_session):
    """Test stopping a session (mocked)."""
    response = client.post("/tasks/stop", json={"session_id": "test_simple"})
    assert response.status_code == 200
