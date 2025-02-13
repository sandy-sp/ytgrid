import csv
import subprocess
import time
from pathlib import Path
from typing import Optional

import requests
import typer

from ytgrid.utils.config import config

app = typer.Typer(
    help=(
        "YTGrid CLI for managing YouTube automation sessions.\n\n"
        "Commands:\n"
        "  start   - Start an automation session with specified parameters.\n"
        "  status  - Display all active automation sessions.\n"
        "  stop    - Stop a specific automation session by session ID.\n"
        "  batch   - Start multiple sessions from a CSV file containing session details.\n\n"
        "Use the --help option with any command for more details."
    )
)

# Use a configurable API base URL if provided in config; otherwise, default to localhost.
API_BASE_URL: str = getattr(config, "API_BASE_URL", "http://127.0.0.1:8000")


def is_backend_running() -> bool:
    """Check if the FastAPI backend is running by making a GET request to the root endpoint."""
    try:
        response = requests.get(f"{API_BASE_URL}/")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False


def start_backend() -> None:
    """
    Start the FastAPI backend in the background if it is not running.

    This function checks if the backend is active; if not, it starts it using Uvicorn.
    A short sleep is included to allow the server time to initialize.
    """
    if not is_backend_running():
        typer.echo("🔄 Starting YTGrid backend...")
        subprocess.Popen(
            ["uvicorn", "ytgrid.backend.main:app", "--host", "0.0.0.0", "--port", "8000"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(3)  # Allow time for the server to start
        if is_backend_running():
            typer.echo("✅ YTGrid backend started successfully!")
        else:
            typer.echo("❌ Failed to start YTGrid backend. Please start it manually.")


@app.command()
def start(
    session_id: str = typer.Option(
        ..., 
        help="Unique session identifier. This must be unique across all active sessions."
    ),
    url: str = typer.Option(
        ..., 
        help="The YouTube video URL to be automated."
    ),
    speed: float = typer.Option(
        1.0, 
        help="Playback speed multiplier (e.g., 1.0 for normal speed)."
    ),
    loops: int = typer.Option(
        1, 
        help="The number of times the video should loop during the session."
    ),
    task_type: str = typer.Option(
        "video", 
        help="The type of automation task. Defaults to 'video'."
    ),
):
    """
    Start an automation session.

    This command triggers a new automation session by sending a POST request to the YTGrid backend API.
    
    Example usage:
        ytgrid start --session-id my_session --url "https://www.youtube.com/watch?v=XYZ" --speed 1.5 --loops 3
    """
    start_backend()
    payload = {
        "session_id": session_id,
        "url": url,
        "speed": speed,
        "loop_count": loops,
        "task_type": task_type,
    }
    response = requests.post(f"{API_BASE_URL}/tasks/", json=payload)
    if response.status_code == 201:
        typer.echo(f"✅ Session {session_id} started successfully.")
    else:
        typer.echo(f"❌ Error: {response.json().get('detail')}", err=True)


@app.command()
def status():
    """
    Display all active automation sessions.

    This command retrieves the current session information from the backend API and displays the
    session IDs and their progress (e.g., current loop count).

    Example usage:
        ytgrid status
    """
    start_backend()
    response = requests.get(f"{API_BASE_URL}/tasks/")
    if response.status_code == 200:
        sessions = response.json().get("active_sessions", [])
        if sessions:
            typer.echo("📌 Active Sessions:")
            for session in sessions:
                session_id = session.get("id")
                loop = session.get("loop", 0)
                typer.echo(f" - Session ID: {session_id}, Loop: {loop}")
        else:
            typer.echo("✅ No active sessions.")
    else:
        typer.echo("❌ Error fetching sessions.", err=True)


@app.command()
def stop(
    session_id: str = typer.Option(
        ..., 
        help="The unique identifier of the session you want to stop."
    )
):
    """
    Stop an active automation session.

    This command sends a request to stop the automation session with the specified session ID.
    
    Example usage:
        ytgrid stop --session-id my_session
    """
    start_backend()
    response = requests.post(f"{API_BASE_URL}/tasks/stop", json={"session_id": session_id})
    if response.status_code == 200:
        typer.echo(f"✅ Session {session_id} stopped successfully.")
    else:
        typer.echo(f"❌ Error: {response.json().get('detail')}", err=True)


@app.command()
def batch(
    file: Path = typer.Argument(
        ..., 
        help="Path to a CSV file containing multiple session tasks."
    ),
    delimiter: str = typer.Option(
        ",", 
        help="CSV delimiter. Default is a comma."
    ),
):
    """
    Start multiple automation sessions from a CSV file.

    The CSV file should have a header row with the following columns:
      - session_id: Unique identifier for the session.
      - url: The YouTube video URL to automate.
      - speed: Playback speed multiplier.
      - loops: The number of loops for the session.
      - task_type (optional): Type of automation task (defaults to 'video').

    Example usage:
        ytgrid batch tasks.csv --delimiter ","
    """
    start_backend()
    if not file.exists():
        typer.echo(f"❌ File {file} does not exist.", err=True)
        raise typer.Exit(code=1)

    with file.open("r", newline="") as csvfile:
        reader = csv.DictReader(csvfile, delimiter=delimiter)
        tasks = list(reader)

    if not tasks:
        typer.echo("❌ No tasks found in the CSV file.", err=True)
        raise typer.Exit(code=1)

    for task in tasks:
        session_id = task.get("session_id")
        url = task.get("url")
        speed = float(task.get("speed", 1.0))
        loops = int(task.get("loops", 1))
        task_type = task.get("task_type", "video")
        payload = {
            "session_id": session_id,
            "url": url,
            "speed": speed,
            "loop_count": loops,
            "task_type": task_type,
        }
        response = requests.post(f"{API_BASE_URL}/tasks/", json=payload)
        if response.status_code == 201:
            typer.echo(f"✅ Session {session_id} started successfully.")
        else:
            typer.echo(
                f"❌ Error starting session {session_id}: {response.json().get('detail')}",
                err=True,
            )
        time.sleep(0.5)  # Slight delay between task submissions


def main():
    app()


if __name__ == "__main__":
    main()
