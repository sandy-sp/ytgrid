import requests
import pytest

BASE_URL = "http://127.0.0.1:8000"

def test_api_start():
    """Test API start session"""
    response = requests.post(f"{BASE_URL}/sessions/start", json={
        "url": "https://www.youtube.com/watch?v=zU9y354XAgM",
        "speed": 1.5,
        "loop_count": 2
    })
    assert response.status_code == 200
    assert "session_id" in response.json()

def test_api_status():
    """Test API status check"""
    response = requests.get(f"{BASE_URL}/status")
    assert response.status_code == 200
    assert "active_sessions" in response.json()

def test_api_stop():
    """Test API stop session"""
    response = requests.post(f"{BASE_URL}/sessions/stop", json={"session_id": 1})
    assert response.status_code == 200
