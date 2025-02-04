import requests

API_BASE_URL = "http://127.0.0.1:8000"

def add_video(url):
    response = requests.post(f"{API_BASE_URL}/sessions/start-session", params={"url": url})
    return response.json()

def remove_video(url):
    return {"message": "Remove functionality not implemented"}

def start_session():
    return {"message": "Use 'add' command instead"}

def stop_session(session_id):
    response = requests.post(f"{API_BASE_URL}/sessions/stop-session", params={"session_id": session_id})
    return response.json()

def get_status():
    response = requests.get(f"{API_BASE_URL}/status/")
    return response.json()
