import requests

API_BASE_URL = "http://127.0.0.1:8000"  # FastAPI backend

def add_video(url):
    response = requests.post(f"{API_BASE_URL}/start-session", json={"url": url})
    return response.json()

def remove_video(url):
    response = requests.delete(f"{API_BASE_URL}/remove-video", json={"url": url})
    return response.json()

def start_session():
    response = requests.post(f"{API_BASE_URL}/start-session")
    return response.json()

def stop_session(session_id):
    response = requests.post(f"{API_BASE_URL}/stop-session", json={"session_id": session_id})
    return response.json()

def get_status():
    response = requests.get(f"{API_BASE_URL}/status")
    return response.json()
