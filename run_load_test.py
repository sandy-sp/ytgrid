import requests
import uuid
import time

# Replace these with your actual video URLs
videos = [
    "https://www.youtube.com/watch?v=video1",
    "https://www.youtube.com/watch?v=video2",
    "https://www.youtube.com/watch?v=video3",
    "https://www.youtube.com/watch?v=video4",
    "https://www.youtube.com/watch?v=video5",
    "https://www.youtube.com/watch?v=video6",
    "https://www.youtube.com/watch?v=video7",
    "https://www.youtube.com/watch?v=video8",
    "https://www.youtube.com/watch?v=video9",
    "https://www.youtube.com/watch?v=video10",
    "https://www.youtube.com/watch?v=video11",
    "https://www.youtube.com/watch?v=video12",
    "https://www.youtube.com/watch?v=video13",
    "https://www.youtube.com/watch?v=video14",
]

# The base URL of your API (assuming your FastAPI server is available at port 8000)
BASE_URL = "http://127.0.0.1:8000/tasks"

def start_session(session_id, video_url):
    payload = {
       "session_id": session_id,
       "url": video_url,
       "speed": 1.0,         # You can adjust playback speed if needed
       "loop_count": 50,     # Run each video for 50 loops
       "task_type": "video"  # Using the "video" automation mode
    }
    response = requests.post(f"{BASE_URL}/", json=payload)
    if response.status_code == 201:
        return response.json()
    else:
        print(f"Error starting session {session_id}: {response.text}")
        return None

def main():
    total_tasks = 0
    # For each video URL, submit a new task 50 times
    for video_url in videos:
        for _ in range(1):  # Use 1 if each session already loops 50 times; change this if you want multiple sessions per video.
            session_id = str(uuid.uuid4())
            result = start_session(session_id, video_url)
            if result:
                print(f"Started session {session_id} for video {video_url}: {result}")
                total_tasks += 1
            # Optionally, add a small delay to avoid overwhelming the API
            time.sleep(0.1)
    print(f"Total tasks started: {total_tasks}")

if __name__ == "__main__":
    main()
