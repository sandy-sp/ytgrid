import csv
import time
from pathlib import Path
from unittest.mock import patch
from typer.testing import CliRunner
import pytest

from ytgrid.cli import app

runner = CliRunner()


def test_help_output():
    """Test that the CLI help command works."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Commands:" in result.output


@patch("ytgrid.cli.requests.post")
def test_start_cli_command(mock_post):
    """Test starting a session via CLI (mocked API)."""
    mock_post.return_value.status_code = 201
    mock_post.return_value.json.return_value = {"message": "Session started successfully."}

    result = runner.invoke(app, [
        "start",
        "--session-id", "test_cli",
        "--url", "https://www.youtube.com/watch?v=UXFBUZEpnrc",
        "--speed", "1.0",
        "--loops", "1"
    ])

    assert result.exit_code == 0
    assert "Session 'test_cli' started successfully." in result.output


@patch("ytgrid.cli.requests.post")
def test_stop_cli_command(mock_post):
    """Test stopping a session via CLI (mocked API)."""
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"message": "Session stopped successfully."}

    result = runner.invoke(app, ["stop", "--session-id", "test_cli"])

    assert result.exit_code == 0
    assert "Session 'test_cli' stopped successfully." in result.output


@patch("ytgrid.cli.requests.get")
def test_status_cli_command(mock_get):
    """Test checking active sessions via CLI (mocked API)."""
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"active_sessions": []}

    result = runner.invoke(app, ["status"])

    assert result.exit_code == 0
    assert "No active sessions." in result.output


@patch("ytgrid.cli.requests.post")
def test_batch_cli_command(mock_post, tmp_path):
    """Test batch session start via CLI using a mock API."""
    mock_post.return_value.status_code = 201
    mock_post.return_value.json.return_value = {"message": "Session started successfully."}

    # Create a temporary CSV file with batch tasks
    csv_content = """session_id,url,speed,loops,task_type
batch1,https://www.youtube.com/watch?v=UXFBUZEpnrc,1.0,2,video
batch2,https://www.youtube.com/watch?v=OaOK76hiW8I,1.5,3,video
"""
    csv_file = tmp_path / "tasks.csv"
    csv_file.write_text(csv_content)

    result = runner.invoke(app, ["batch", str(csv_file), "--delimiter", ","])

    assert result.exit_code == 0
    assert "Session 'batch1' started successfully." in result.output
    assert "Session 'batch2' started successfully." in result.output
