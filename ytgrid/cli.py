import csv
import subprocess
import time
from pathlib import Path
from typing import Optional

import requests
import typer
from typer import Context

from ytgrid.utils.config import config

app = typer.Typer(
    rich_markup_mode="rich",
    help=(
        "YTGrid CLI for managing YouTube automation sessions.\n\n"
        "This tool provides the following commands:\n"
        "  start        - Start an automation session with the given parameters.\n"
        "                  Options include:\n"
        "                    session_id: A unique identifier (e.g., 'session1').\n"
        "                    url:        The YouTube video URL (e.g., 'https://www.youtube.com/watch?v=XYZ').\n"
        "                    speed:      Playback speed multiplier (e.g., 1.0 for normal speed).\n"
        "                    loops:      Number of times to play the video (e.g., 3).\n"
        "                    task_type:  Type of automation task (default is 'video').\n\n"
        "  status       - Display active automation sessions along with their progress.\n\n"
        "  stop         - Stop an active automation session by providing its session_id.\n\n"
        "  batch        - Start multiple automation sessions from a CSV file.\n"
        "                  The CSV file must have a header row with columns:\n"
        "                    session_id, url, speed, loops, and optionally task_type (defaults to 'video').\n\n"
        "  toggle-celery- Toggle the YTGRID_USE_CELERY setting in the .env file (on/off).\n\n"
        "For more details on each command, use 'ytgrid <command> --help'."
    )
)

# Use a configurable API base URL if provided in config; otherwise, default to localhost.
API_BASE_URL: str = getattr(config, "API_BASE_URL", "http://127.0.0.1:8000")


def print_custom_help() -> None:
    help_message = """
Usage:
  ytgrid [OPTIONS] COMMAND [ARGS]...

Commands:
  start        - Start an automation session with the given parameters.
                 Options include:
                   session_id: A unique identifier (e.g., 'session1').
                   url:        The YouTube video URL (e.g., 'https://www.youtube.com/watch?v=XYZ').
                   speed:      Playback speed multiplier (e.g., 1.0 for normal speed).
                   loops:      Number of times to play the video (e.g., 3).
                   task_type:  Type of automation task (default is 'video').

  status       - Display active automation sessions along with their progress.

  stop         - Stop an active automation session by providing its session_id.

  batch        - Start multiple automation sessions from a CSV file.
                 The CSV file should have a header row with columns:
                   session_id, url, speed, loops, and optionally task_type (defaults to 'video').

  toggle-celery- Toggle the YTGRID_USE_CELERY setting in the .env file (on/off).

General Options:
  --install-completion   Install shell completion for the current shell.
  --show-completion      Show shell completion script for customization.
  --help                 Show this message and exit.
"""
    typer.echo(help_message)


@app.callback(invoke_without_command=True, no_args_is_help=True)
def main(ctx: Context) -> None:
    """
    YTGrid CLI for managing YouTube automation sessions.

    Use a subcommand (start, status, stop, batch, toggle-celery) along with --help for more details.
    """
    if ctx.invoked_subcommand is None:
        print_custom_help()


def is_backend_running() -> bool:
    """Check if the FastAPI backend is running by sending a GET request to the root endpoint."""
    try:
        response = requests.get(f"{API_BASE_URL}/")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False


def start_backend() -> None:
    """
    Start the FastAPI backend in the background if it is not running.

    This function attempts to start the backend using Uvicorn, allowing a short delay for the server to initialize.
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
        help="A unique identifier for the session (e.g., 'session1')."
    ),
    url: str = typer.Option(
        ..., 
        help="The full YouTube video URL to be automated (e.g., 'https://www.youtube.com/watch?v=XYZ')."
    ),
    speed: float = typer.Option(
        1.0, 
        help="Playback speed multiplier (e.g., 1.0 for normal speed; use higher values for faster playback)."
    ),
    loops: int = typer.Option(
        1, 
        help="The number of times to loop the video (e.g., 3 means the video plays three times)."
    ),
    task_type: str = typer.Option(
        "video", 
        help="Type of automation task. Defaults to 'video'."
    ),
):
    """
    Start an automation session.

    This command sends a request to the backend API to initiate a new automation session.

    Example usage:
      ytgrid start --session-id session1 --url "https://www.youtube.com/watch?v=XYZ" --speed 1.5 --loops 3 --task_type video
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
        typer.echo(f"✅ Session '{session_id}' started successfully.")
    else:
        typer.echo(f"❌ Error: {response.json().get('detail')}", err=True)


@app.command()
def status():
    """
    Display active automation sessions.

    This command retrieves active session information from the backend API, including session IDs
    and current loop progress.

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
                typer.echo(f" - Session ID: {session_id}, Current Loop: {loop}")
        else:
            typer.echo("✅ No active sessions.")
    else:
        typer.echo("❌ Error fetching sessions.", err=True)


@app.command()
def stop(
    session_id: str = typer.Option(
        ..., 
        help="The unique identifier of the session to stop (as provided during the start command)."
    )
):
    """
    Stop an active automation session.

    This command sends a request to stop the specified session and cleans up any associated resources.

    Example usage:
      ytgrid stop --session-id session1
    """
    start_backend()
    response = requests.post(f"{API_BASE_URL}/tasks/stop", json={"session_id": session_id})
    if response.status_code == 200:
        typer.echo(f"✅ Session '{session_id}' stopped successfully.")
    else:
        typer.echo(f"❌ Error: {response.json().get('detail')}", err=True)


@app.command()
def batch(
    file: Path = typer.Argument(
        ..., 
        help="Path to a CSV file containing session tasks. The CSV must have a header row with columns: session_id, url, speed, loops, and optionally task_type."
    ),
    delimiter: str = typer.Option(
        ",", 
        help="The CSV delimiter. Default is a comma."
    ),
):
    """
    Start multiple automation sessions from a CSV file.

    The CSV file should have a header row with the following columns:
      - session_id: Unique identifier for the session.
      - url: The YouTube video URL.
      - speed: Playback speed multiplier.
      - loops: Number of loops for the session.
      - task_type (optional): Type of automation task (defaults to 'video').

    Example CSV content:
      session_id,url,speed,loops,task_type
      session1,https://www.youtube.com/watch?v=XYZ,1.0,3,video
      session2,https://www.youtube.com/watch?v=ABC,1.5,2,video

    Example usage:
      ytgrid batch tasks.csv --delimiter ","
    """
    start_backend()
    if not file.exists():
        typer.echo(f"❌ File '{file}' does not exist.", err=True)
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
            typer.echo(f"✅ Session '{session_id}' started successfully.")
        else:
            typer.echo(
                f"❌ Error starting session '{session_id}': {response.json().get('detail')}",
                err=True,
            )
        time.sleep(0.5)  # Slight delay between task submissions


@app.command("toggle-celery")
def toggle_celery(
    env_file: Path = typer.Option(
        ".env", 
        help="Path to the .env file where YTGRID_USE_CELERY is set."
    )
):
    """
    Toggle the YTGRID_USE_CELERY setting in the .env file.

    This command reads the .env file, toggles the value of YTGRID_USE_CELERY between True and False,
    and writes the updated value back to the file. This allows you to enable or disable Celery without
    manually editing the environment file.

    Example usage:
      ytgrid toggle-celery --env-file .env
    """
    if not env_file.exists():
        typer.echo(f"❌ .env file not found at '{env_file}'.", err=True)
        raise typer.Exit(code=1)

    lines = env_file.read_text().splitlines()
    new_lines = []
    toggled = False
    current_value = None
    for line in lines:
        if line.strip().startswith("YTGRID_USE_CELERY="):
            parts = line.split("=", 1)
            if len(parts) == 2:
                value = parts[1].strip().strip('"').strip("'")
                current_value = value
                new_value = "False" if value.lower() == "true" else "True"
                new_line = f"{parts[0]}={new_value}"
                new_lines.append(new_line)
                toggled = True
                continue
        new_lines.append(line)
    if not toggled:
        # If not found, add the variable with True as the default.
        new_lines.append("YTGRID_USE_CELERY=True")
        new_value = "True"

    env_file.write_text("\n".join(new_lines) + "\n")
    typer.echo(f"✅ Toggled YTGRID_USE_CELERY from {current_value} to {new_value}")


def main():
    app()


if __name__ == "__main__":
    main()
