import requests
import time

BASE_URL = "http://127.0.0.1:8000"

# Start a session
print("Starting a session via API...")
response = requests.post(f"{BASE_URL}/sessions/start", json={
    "url": "https://www.youtube.com/watch?v=tCDvOQI3pco",
    "speed": 1.5,
    "loop_count": 2
})
session_data = response.json()
print(session_data)

# Wait before checking status
time.sleep(5)

# Get session status
print("\nChecking session status via API...")
response = requests.get(f"{BASE_URL}/status")
print(response.json())

# Stop session
print("\nStopping session via API...")
session_id = session_data.get("session_id", 1)  # Fallback to 1 if session_id is missing
response = requests.post(f"{BASE_URL}/sessions/stop", json={"session_id": session_id})
print(response.json())

print("\nExample API usage complete.")
