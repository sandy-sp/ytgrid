import sys
import typer
import requests

app = typer.Typer()

API_BASE_URL = "http://127.0.0.1:8000"

@app.command()
def start(
    session_id: str = typer.Option(..., help="Unique session identifier"),
    url: str = typer.Option(..., help="YouTube video URL"),
    speed: float = typer.Option(1.0, help="Playback speed"),
    loops: int = typer.Option(1, help="Number of loops"),
    task_type: str = typer.Option("video", help="Automation task type (default 'video')")
):
    """Start an automation session."""
    response = requests.post(f"{API_BASE_URL}/tasks/", json={
        "session_id": session_id,
        "url": url,
        "speed": speed,
        "loop_count": loops,
        "task_type": task_type
    })
    if response.status_code == 201:
        typer.echo(f"Session {session_id} started successfully.")
    else:
        typer.echo(f"Error: {response.json().get('detail')}", err=True)
        sys.exit(1)

@app.command()
def stop(
    session_id: str = typer.Option(..., help="Unique session identifier")
):
    """Stop an automation session."""
    response = requests.post(f"{API_BASE_URL}/tasks/stop", json={"session_id": session_id})
    if response.status_code == 200:
        typer.echo(f"Session {session_id} stopped successfully.")
    else:
        typer.echo(f"Error: {response.json().get('detail')}", err=True)
        sys.exit(1)

@app.command()
def status():
    """Show active automation sessions."""
    response = requests.get(f"{API_BASE_URL}/tasks/")
    if response.status_code == 200:
        sessions = response.json().get("active_sessions", [])
        if sessions:
            typer.echo("Active Sessions:")
            for session in sessions:
                typer.echo(f" - Session ID: {session['id']}, Loop: {session['loop']}")
        else:
            typer.echo("No active sessions.")
    else:
        typer.echo("Error fetching sessions.", err=True)
        sys.exit(1)

def main():
    app()

if __name__ == "__main__":
    main()
