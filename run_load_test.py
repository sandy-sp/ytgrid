import requests
import uuid
import time

# Replace these with your actual video URLs
videos = [
    "https://www.youtube.com/watch?v=OaOK76hiW8I",
    "https://www.youtube.com/watch?v=1i4vVuXBeTg",
    "https://www.youtube.com/watch?v=vcxHeOmQTag",
    "https://www.youtube.com/watch?v=ebwk6MGvfx8",
    "https://www.youtube.com/watch?v=1whaC6ymWh4",
    "https://www.youtube.com/watch?v=ZZ63B6tVDzk",
    "https://www.youtube.com/watch?v=nE9kX0K7Pi4",
    "https://www.youtube.com/watch?v=Iury7mcMt2Q",
    "https://www.youtube.com/watch?v=B5m8fC6ELts",
    "https://www.youtube.com/watch?v=k3ViZ3lp94M",
    "https://www.youtube.com/watch?v=4iGDm8Q5VRM",
    "https://www.youtube.com/watch?v=egumcVvb8SA",
    "https://www.youtube.com/watch?v=UXFBUZEpnrc",
]

# Use the service name "web" from Docker Compose.
BASE_URL = "http://web:8000/tasks"

def start_session(session_id, video_url):
    payload = {
        "session_id": session_id,
        "url": video_url,
        "speed": 1.0,         # Adjust playback speed if needed.
        "loop_count": 50,     # Run each video for 50 loops.
        "task_type": "video"  # Using the "video" automation mode.
    }
    try:
        response = requests.post(f"{BASE_URL}/", json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error starting session {session_id}: {e}")
        return None

def main():
    total_tasks = 0
    # For each video URL, submit a task.
    for video_url in videos:
        # Create one session per video (each session will run 50 loops).
        session_id = str(uuid.uuid4())
        result = start_session(session_id, video_url)
        if result:
            print(f"Started session {session_id} for video {video_url}: {result}")
            total_tasks += 1
        else:
            print(f"Failed to start session for video {video_url}")
        # Optionally, delay between requests.
        time.sleep(0.1)
    print(f"Total tasks started: {total_tasks}")

if __name__ == "__main__":
    main()