from fastapi.testclient import TestClient

from ytgrid.backend import auth
from ytgrid.backend.main import app
from ytgrid.backend.task import task_manager


client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "YTGrid API v3.1 is running!"}


def test_health_endpoint_open_when_auth_enabled(monkeypatch):
    monkeypatch.setattr(auth.config, "API_KEY", "secret")
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_tasks_requires_api_key_when_auth_enabled(monkeypatch):
    monkeypatch.setattr(auth.config, "API_KEY", "secret")
    response = client.get("/tasks/")
    assert response.status_code == 401


def test_tasks_accepts_valid_api_key(monkeypatch):
    monkeypatch.setattr(auth.config, "API_KEY", "secret")
    monkeypatch.setattr(task_manager, "get_active_sessions", lambda: [])
    response = client.get("/tasks/", headers={"X-API-Key": "secret"})
    assert response.status_code == 200
    assert response.json() == {"active_sessions": []}


def test_local_desktop_origin_is_cors_enabled(monkeypatch):
    monkeypatch.setattr(auth.config, "API_KEY", "secret")
    response = client.options(
        "/tasks/",
        headers={
            "Origin": "http://localhost:1420",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "X-API-Key",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:1420"


def test_start_task_rejects_invalid_task_type(monkeypatch):
    monkeypatch.setattr(auth.config, "API_KEY", "")
    response = client.post(
        "/tasks/",
        json={
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "speed": 1.0,
            "loop_count": 1,
            "task_type": "unsupported",
        },
    )
    assert response.status_code == 422


def test_start_task_reports_duplicate_session(monkeypatch):
    monkeypatch.setattr(auth.config, "API_KEY", "")

    def duplicate(**kwargs):
        task_manager.last_start_error = "Session already exists"
        return False

    monkeypatch.setattr(task_manager, "start_session", duplicate)
    response = client.post(
        "/tasks/",
        json={
            "session_id": "dup",
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "speed": 1.0,
            "loop_count": 1,
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Session already exists"
