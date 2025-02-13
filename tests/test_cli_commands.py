import csv
import time
from pathlib import Path
from typer.testing import CliRunner
import pytest

from ytgrid.cli import app

runner = CliRunner()

def test_help_output():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert "Commands:" in result.output
    assert "start" in result.output
    assert "status" in result.output
    assert "stop" in result.output
    assert "batch" in result.output
    assert "toggle-celery" in result.output

def test_start_cli_command(monkeypatch):
    # For testing, override start_backend and requests.post to simulate a successful response.
    def fake_start_backend():
        print("Fake backend started")
    monkeypatch.setattr("ytgrid.cli.start_backend", fake_start_backend)

    class FakeResponse:
        status_code = 201
        def json(self):
            return {"message": "Session test_cli started successfully."}

    def fake_post(url, json):
        return FakeResponse()

    monkeypatch.setattr("requests.post", fake_post)

    result = runner.invoke(app, [
        "start",
        "--session-id", "test_cli",
        "--url", "https://www.youtube.com/watch?v=UXFBUZEpnrc",
        "--speed", "1.0",
        "--loops", "1",
        "--task_type", "video"
    ])
    assert result.exit_code == 0
    assert "test_cli" in result.output

def test_stop_cli_command(monkeypatch):
    def fake_start_backend():
        print("Fake backend started")
    monkeypatch.setattr("ytgrid.cli.start_backend", fake_start_backend)

    class FakeResponse:
        status_code = 200
        def json(self):
            return {"message": "Session test_cli stopped successfully."}

    def fake_post(url, json):
        return FakeResponse()

    monkeypatch.setattr("requests.post", fake_post)

    result = runner.invoke(app, [
        "stop",
        "--session-id", "test_cli"
    ])
    assert result.exit_code == 0
    assert "test_cli" in result.output

def test_batch_cli_command(tmp_path, monkeypatch):
    # Create a temporary CSV file with batch tasks
    csv_content = """session_id,url,speed,loops,task_type
batch1,https://www.youtube.com/watch?v=UXFBUZEpnrc,1.0,2,video
batch2,https://www.youtube.com/watch?v=OaOK76hiW8I,1.5,3,video
"""
    csv_file = tmp_path / "tasks.csv"
    csv_file.write_text(csv_content)

    def fake_start_backend():
        print("Fake backend started")
    monkeypatch.setattr("ytgrid.cli.start_backend", fake_start_backend)

    class FakeResponse:
        status_code = 201
        def json(self):
            return {"message": "Session started successfully."}

    def fake_post(url, json):
        return FakeResponse()

    monkeypatch.setattr("requests.post", fake_post)

    result = runner.invoke(app, ["batch", str(csv_file), "--delimiter", ","])
    assert result.exit_code == 0
    assert "batch1" in result.output
    assert "batch2" in result.output
