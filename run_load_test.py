import requests
import uuid
import time
import multiprocessing
from ytgrid.utils.config import config

# 📌 Configuration Section: Modify Input Here
VIDEOS = [
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

TOTAL_LOOPS = 100   # 📌 Set total number of loops per video
PARALLEL_INSTANCES = 5  # 📌 Number of browser instances per video (reduces time)
PLAYBACK_SPEED = 1.5  # 📌 Set video playback speed
USE_CELERY = config.USE_CELERY  # 📌 Toggle Celery execution


BASE_URL = "http://127.0.0.1:8000/tasks"

def start_parallel_video_task(video_url, loops_per_instance):
    """
    Start multiple browser instances for a given video.
    """
    session_id = str(uuid.uuid4())  # Unique session ID

    payload = {
        "session_id": session_id,
        "url": video_url,
        "speed": PLAYBACK_SPEED,
        "loop_count": loops_per_instance,  # Split total loops across instances
        "task_type": "video",
        "use_celery": USE_CELERY
    }

    try:
        response = requests.post(f"{BASE_URL}/", json=payload, timeout=10)
        response.raise_for_status()
        return {"session_id": session_id, "status": "started"}
    except requests.exceptions.RequestException as e:
        print(f"❌ Error starting session {session_id}: {e}")
        return None

def distribute_tasks():
    """
    Distributes video automation across multiple browser instances.
    """
    total_tasks = 0
    workers = []

    # Loop through each video
    for video_url in VIDEOS:
        loops_per_instance = TOTAL_LOOPS // PARALLEL_INSTANCES  # Divide loops equally

        for _ in range(PARALLEL_INSTANCES):
            # Start parallel browser instances
            worker = multiprocessing.Process(target=start_parallel_video_task, args=(video_url, loops_per_instance))
            worker.start()
            workers.append(worker)
            total_tasks += 1

        # Avoid overwhelming the system
        time.sleep(1)

    # Wait for all processes to finish
    for worker in workers:
        worker.join()

    print(f"✅ Total tasks started: {total_tasks}")

if __name__ == "__main__":
    distribute_tasks()
