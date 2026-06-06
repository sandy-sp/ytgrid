import pytest
from pydantic import ValidationError

from ytgrid.backend.task import TaskStartRequest
from ytgrid.backend.routes.session import SessionStartRequest

VALID_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def test_task_request_valid():
    req = TaskStartRequest(url=VALID_URL, speed=1.5, loop_count=3)
    assert req.task_type == "video"
    assert req.speed == 1.5


def test_task_request_rejects_invalid_task_type():
    with pytest.raises(ValidationError):
        TaskStartRequest(url=VALID_URL, task_type="batch")


def test_task_request_rejects_non_youtube_url():
    with pytest.raises(ValidationError):
        TaskStartRequest(url="https://evil.com/watch?v=x")


def test_task_request_speed_bounds():
    with pytest.raises(ValidationError):
        TaskStartRequest(url=VALID_URL, speed=-1)
    with pytest.raises(ValidationError):
        TaskStartRequest(url=VALID_URL, speed=99)


def test_task_request_loop_bounds():
    with pytest.raises(ValidationError):
        TaskStartRequest(url=VALID_URL, loop_count=0)
    with pytest.raises(ValidationError):
        TaskStartRequest(url=VALID_URL, loop_count=99999)


def test_task_request_session_id_pattern():
    with pytest.raises(ValidationError):
        TaskStartRequest(url=VALID_URL, session_id="bad id!")
    ok = TaskStartRequest(url=VALID_URL, session_id="good_id-1")
    assert ok.session_id == "good_id-1"


def test_session_request_defaults_and_rejection():
    ok = SessionStartRequest(url=VALID_URL)
    assert ok.speed == 1.0
    assert ok.loop_count == 1
    with pytest.raises(ValidationError):
        SessionStartRequest(url="ftp://youtube.com/x")
