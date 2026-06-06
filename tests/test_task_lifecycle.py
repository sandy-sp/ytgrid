import multiprocessing

import pytest

from ytgrid.backend import tasks
from ytgrid.backend.task_manager import TaskManager, _record_execution_end


def _noop():
    return None


def test_completed_multiprocessing_session_is_pruned_from_active_sessions():
    manager = TaskManager()
    process = multiprocessing.Process(target=_noop)
    process.start()
    process.join(timeout=5)

    manager.processes["done"] = process
    manager.loop_counts["done"] = multiprocessing.Value("i", 1)

    assert manager.get_active_sessions() == []
    assert "done" not in manager.processes
    assert "done" not in manager.loop_counts


def test_celery_task_records_completed_execution(monkeypatch):
    recorded = []

    class DummyPlayer:
        def play_video(self, url, speed, loop_count):
            return True

    monkeypatch.setitem(tasks.AUTOMATION_PLAYERS, "video", DummyPlayer)
    monkeypatch.setattr(
        tasks,
        "_record_execution_end",
        lambda session_id, status, error_message=None: recorded.append(
            (session_id, status, error_message)
        ),
    )

    assert tasks.run_automation("sess-1", "https://youtube.com/watch?v=x", 1.0, 1, "video") == "completed"
    assert recorded == [("sess-1", "completed", None)]


def test_celery_task_records_failed_execution(monkeypatch):
    recorded = []

    class FailingPlayer:
        def play_video(self, url, speed, loop_count):
            raise RuntimeError("boom")

    monkeypatch.setitem(tasks.AUTOMATION_PLAYERS, "video", FailingPlayer)
    monkeypatch.setattr(
        tasks,
        "_record_execution_end",
        lambda session_id, status, error_message=None: recorded.append(
            (session_id, status, error_message)
        ),
    )

    assert tasks.run_automation("sess-1", "https://youtube.com/watch?v=x", 1.0, 1, "video") == "error"
    assert recorded == [("sess-1", "failed", "boom")]


def test_stop_session_records_stopped_execution(monkeypatch):
    recorded = []
    manager = TaskManager()
    process = multiprocessing.Process(target=_noop)
    process.start()
    manager.processes["stop-me"] = process
    manager.loop_counts["stop-me"] = multiprocessing.Value("i", 1)

    monkeypatch.setattr(
        "ytgrid.backend.task_manager._record_execution_end",
        lambda session_id, status, error_message=None: recorded.append(
            (session_id, status, error_message)
        ),
    )

    assert manager.stop_session("stop-me") is True
    assert recorded == [("stop-me", "stopped", None)]


async def test_record_execution_end_inside_running_event_loop(monkeypatch):
    recorded = []

    class DummyRepository:
        async def record_execution_end(self, session_id, status, error_message=None):
            recorded.append((session_id, status, error_message))

    monkeypatch.setattr(
        "ytgrid.database.repository.ProfileRepository",
        DummyRepository,
    )

    _record_execution_end("sess-loop", "stopped")
    assert recorded == [("sess-loop", "stopped", None)]
