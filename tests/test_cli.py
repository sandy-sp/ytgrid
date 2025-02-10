import subprocess
import pytest

@pytest.fixture
def sample_cli_command():
    return [
        "ytgrid", "start",
        "--session-id", "cli_test_session",
        "--url", "https://www.youtube.com/watch?v=UXFBUZEpnrc",
        "--speed", "1.5",
        "--loops", "2",
        "--task-type", "video"
    ]

def test_cli_start(sample_cli_command):
    """Test starting a session via CLI."""
    result = subprocess.run(sample_cli_command, capture_output=True, text=True)
    assert "started successfully" in result.stdout.lower()

def test_cli_status():
    """Test checking session status via CLI."""
    result = subprocess.run(["ytgrid", "status"], capture_output=True, text=True)
    assert "active sessions" in result.stdout.lower() or "no active sessions" in result.stdout.lower()

def test_cli_stop():
    """Test stopping a session via CLI."""
    result = subprocess.run(["ytgrid", "stop", "--session-id", "cli_test_session"], capture_output=True, text=True)
    assert "stopped successfully" in result.stdout.lower() or "not found" in result.stdout.lower()
