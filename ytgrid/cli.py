import csv
import subprocess
import time
from pathlib import Path
from typing import Optional

import requests
import typer

from ytgrid.utils.config import config

app = typer.Typer()

# Use a configurable API base URL if provided in config; otherwise, default to localhost.
API_BASE_URL: str = getattr(config, "API_BASE_URL", "http://127.0.0.1:8000")


def is_backend_running() -> bool:
    """Check if the FastAPI backend is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False


def start_backend() -> None:
    """Start the FastAPI backend in the background if it is not running."""
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
    session_id: str = typer.Option(..., help="Unique session identifier"),
    url: str = typer.Option(..., help="YouTube video URL"),
    speed: float = typer.Option(1.0, help="Playback speed"),
    loops: int = typer.Option(1, help="Number of loops"),
    task_type: str = typer.Option("video", help="Automation task type"),
):
    """Start an automation session."""
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
    """Show active automation sessions."""
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
def stop(session_id: str = typer.Option(..., help="Session identifier to stop")):
    """Stop an active automation session."""
    start_backend()
    response = requests.post(f"{API_BASE_URL}/tasks/stop", json={"session_id": session_id})
    if response.status_code == 200:
        typer.echo(f"✅ Session {session_id} stopped successfully.")
    else:
        typer.echo(f"❌ Error: {response.json().get('detail')}", err=True)


@app.command()
def batch(
    file: Path = typer.Argument(..., help="Path to CSV file with session tasks"),
    delimiter: str = typer.Option(",", help="CSV delimiter (default is comma)"),
):
    """
    Start multiple automation sessions from a CSV file.
    
    The CSV file should have a header row with the following columns:
      session_id, url, speed, loops, task_type (optional; defaults to 'video')
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
