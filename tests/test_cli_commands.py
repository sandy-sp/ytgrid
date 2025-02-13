import pytest
from unittest.mock import patch
from typer.testing import CliRunner

# ✅ Import the actual CLI app from ytgrid
from ytgrid.cli import app

runner = CliRunner()

def test_help_output():
    """Test that the CLI help command works."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert "COMMAND" in result.output  # ✅ Matches the expected output
    assert "start" in result.output
    assert "stop" in result.output

@patch("requests.post")
def test_start_cli_command(mock_post):
    """Mock CLI session start command."""
    mock_post.return_value.status_code = 201
    mock_post.return_value.json.return_value = {"message": "Session started successfully."}

    result = runner.invoke(app, ["start", "--session-id", "test_cli", "--url", "https://www.youtube.com/watch?v=UXFBUZEpnrc", "--speed", "1.0", "--loops", "1"])
    
    assert result.exit_code == 0
    assert "Session 'test_cli' started successfully." in result.output

@patch("requests.post")
def test_stop_cli_command(mock_post):
    """Mock CLI session stop command."""
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"message": "Session stopped successfully."}

    result = runner.invoke(app, ["stop", "--session-id", "test_cli"])
    
    assert result.exit_code == 0
    assert "Session 'test_cli' stopped successfully." in result.output
