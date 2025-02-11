import typer
import requests
import subprocess
import time

from ytgrid.utils.config import config

app = typer.Typer()

API_BASE_URL = "http://127.0.0.1:8000"

def is_backend_running():
    """Check if the FastAPI server is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False

def start_backend():
    """Start the FastAPI server in the background if not already running."""
    if not is_backend_running():
        typer.echo("🔄 Starting YTGrid backend...")
        subprocess.Popen(
            ["uvicorn", "ytgrid.backend.main:app", "--host", "0.0.0.0", "--port", "8000"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(3)  # Give the server time to start
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
    start_backend()  # ✅ Automatically start the backend if not running
    
    response = requests.post(f"{API_BASE_URL}/tasks/", json={
        "session_id": session_id,
        "url": url,
        "speed": speed,
        "loop_count": loops,
        "task_type": task_type
    })

    if response.status_code == 201:
        typer.echo(f"✅ Session {session_id} started successfully.")
    else:
        typer.echo(f"❌ Error: {response.json().get('detail')}", err=True)

@app.command()
def status():
    """Show active automation sessions."""
    start_backend()  # ✅ Automatically start the backend if not running
    
    response = requests.get(f"{API_BASE_URL}/tasks/")
    if response.status_code == 200:
        sessions = response.json().get("active_sessions", [])
        if sessions:
            typer.echo("📌 Active Sessions:")
            for session in sessions:
                typer.echo(f" - Session ID: {session['id']}, Loop: {session.get('loop', 0)}")
        else:
            typer.echo("✅ No active sessions.")
    else:
        typer.echo("❌ Error fetching sessions.", err=True)

def main():
    app()

if __name__ == "__main__":
    main()
