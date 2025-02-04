import subprocess
import pytest

def test_cli_start():
    """Test CLI start command"""
    result = subprocess.run(["ytgrid", "start", "--url", "https://www.youtube.com/watch?v=ZZ63B6tVDzk"], capture_output=True, text=True)
    assert "Session Started" in result.stdout

def test_cli_status():
    """Test CLI status command"""
    result = subprocess.run(["ytgrid", "status"], capture_output=True, text=True)
    assert "Active YTGrid Sessions" in result.stdout

def test_cli_stop():
    """Test CLI stop command"""
    result = subprocess.run(["ytgrid", "stop", "--session_id", "1"], capture_output=True, text=True)
    assert "Session Stopped" in result.stdout
