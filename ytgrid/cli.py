import sys
import typer
from ytgrid.backend.task_manager import task_manager

app = typer.Typer()

@app.command()
def start(
    session_id: str = typer.Option(..., help="Unique session identifier"),
    url: str = typer.Option(..., help="YouTube video URL"),
    speed: float = typer.Option(1.0, help="Playback speed"),
    loops: int = typer.Option(1, help="Number of loops"),
    task_type: str = typer.Option("video", help="Automation task type (default 'video')")
):
    """Start an automation session."""
    success = task_manager.start_session(session_id, url, speed, loops, task_type)
    if success:
        typer.echo(f"Session {session_id} started successfully.")
    else:
        typer.echo(f"Session {session_id} already exists.", err=True)
        sys.exit(1)

@app.command()
def stop(
    session_id: str = typer.Option(..., help="Unique session identifier")
):
    """Stop an automation session."""
    success = task_manager.stop_session(session_id)
    if success:
        typer.echo(f"Session {session_id} stopped successfully.")
    else:
        typer.echo(f"Session {session_id} not found.", err=True)
        sys.exit(1)

@app.command()
def status():
    """Show active automation sessions."""
    sessions = task_manager.get_active_sessions()
    if sessions:
        typer.echo("Active Sessions:")
        for session in sessions:
            typer.echo(f" - Session ID: {session['id']}, Loop: {session['loop']}")
    else:
        typer.echo("No active sessions.")

def main():
    app()

if __name__ == "__main__":
    main()
