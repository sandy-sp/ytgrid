import argparse
import requests
import websocket
import json
import threading
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.progress import Progress

API_BASE_URL = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000/ws"

console = Console()


def start_session(url: str, speed: float = 1.0, loops: int = 1):
    """Starts a new YouTube automation session and listens for WebSocket updates."""
    response = requests.post(
        f"{API_BASE_URL}/sessions/start",
        json={"url": url, "speed": speed, "loop_count": loops}
    )

    try:
        data = response.json()
        if "session_id" in data:
            console.print(f"[green]Session Started:[/green] ID: {data.get('session_id')} | URL: {data.get('url')} | Speed: {data.get('speed')} | Loops: {data.get('loops')}")
            listen_for_updates()
        else:
            console.print(f"[red]Error:[/red] {data}")
    except requests.exceptions.JSONDecodeError:
        console.print(f"[red]API returned an invalid response. Check FastAPI logs.[/red]")



def stop_session(session_id: str):
    """Stops an active session."""
    response = requests.post(f"{API_BASE_URL}/sessions/stop", json={"session_id": session_id})
    console.print(f"[red]Session Stopped:[/red] {response.json()}")


def get_status():
    """Fetches the status of all active sessions."""
    response = requests.get(f"{API_BASE_URL}/status")
    data = response.json()

    if not data["active_sessions"]:
        console.print("[yellow]No active sessions.[/yellow]")
        return

    table = Table(title="Active YTGrid Sessions")
    table.add_column("Session ID", justify="center")
    table.add_column("URL", justify="left")
    table.add_column("Status", justify="center")

    for session in data["active_sessions"]:
        table.add_row(str(session["id"]), session["url"], session["status"])

    console.print(table)


def listen_for_updates():
    """Listens for real-time updates from WebSocket."""
    console.print("[blue]Listening for real-time updates...[/blue]")

    def on_message(ws, message):
        data = json.loads(message)
        if data["status"] == "playing":
            console.print(f"[green]Loop {data['loop']}/{data['total_loops']} is running...[/green]")
        elif data["status"] == "completed":
            console.print(f"[yellow]Loop {data['loop']}/{data['total_loops']} completed.[/yellow]")
        elif data["status"] == "all_completed":
            console.print(f"[cyan]All {data['total_loops']} loops completed successfully![/cyan]")

    def on_error(ws, error):
        console.print(f"[red]WebSocket Error:[/red] {error}")

    def on_close(ws, close_status_code, close_msg):
        console.print("[red]WebSocket closed.[/red]")

    def run_ws():
        ws = websocket.WebSocketApp(WS_URL, on_message=on_message, on_error=on_error, on_close=on_close)
        ws.run_forever()

    # Run WebSocket in a separate thread to avoid blocking CLI
    ws_thread = threading.Thread(target=run_ws, daemon=True)
    ws_thread.start()


def main():
    parser = argparse.ArgumentParser(description="YTGrid CLI - YouTube Automation Manager")
    parser.add_argument("command", choices=["start", "stop", "status"], help="Command to execute")
    parser.add_argument("--url", type=str, help="YouTube video URL (Required for 'start')")
    parser.add_argument("--speed", type=float, default=1.0, help="Playback speed (Default: 1.0)")
    parser.add_argument("--loops", type=int, default=1, help="Number of loops for full automation")
    parser.add_argument("--session_id", type=str, help="Session ID (Required for 'stop')")

    args = parser.parse_args()

    if args.command == "start":
        if not args.url:
            console.print("[red]Error:[/red] --url is required for 'start' command")
        else:
            start_session(args.url, args.speed, args.loops)

    elif args.command == "stop":
        if not args.session_id:
            console.print("[red]Error:[/red] --session_id is required for 'stop' command")
        else:
            stop_session(args.session_id)

    elif args.command == "status":
        get_status()


if __name__ == "__main__":
    main()
