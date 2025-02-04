import argparse
import session_manager

def main():
    parser = argparse.ArgumentParser(description="YTGrid CLI - YouTube Automation Manager")

    parser.add_argument("command", choices=["add", "remove", "start", "stop", "status"], help="Command to execute")
    parser.add_argument("--url", type=str, help="YouTube video URL (Required for 'add' command)")
    parser.add_argument("--session_id", type=str, help="Session ID (Required for 'stop' command)")

    args = parser.parse_args()

    if args.command == "add":
        if not args.url:
            print("Error: --url is required for 'add' command")
        else:
            response = session_manager.add_video(args.url)
            print(response)

    elif args.command == "remove":
        if not args.url:
            print("Error: --url is required for 'remove' command")
        else:
            response = session_manager.remove_video(args.url)
            print(response)

    elif args.command == "start":
        response = session_manager.start_session()
        print(response)

    elif args.command == "stop":
        if not args.session_id:
            print("Error: --session_id is required for 'stop' command")
        else:
            response = session_manager.stop_session(args.session_id)
            print(response)

    elif args.command == "status":
        response = session_manager.get_status()
        print(response)

if __name__ == "__main__":
    main()
