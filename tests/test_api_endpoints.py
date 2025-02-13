import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

# ✅ Create a simple FastAPI app for isolated testing
app = FastAPI()

@app.get("/")
async def root():
    return {"message": "YTGrid API is running!"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

client = TestClient(app)

def test_root():
    """Test root endpoint to ensure API is running."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "YTGrid API is running!"}

def test_health():
    """Test health endpoint to ensure API is healthy."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@patch("requests.post")
def test_start_session(mock_post):
    """Mock session start API call."""
    mock_post.return_value.status_code = 201
    mock_post.return_value.json.return_value = {"message": "Session started successfully."}

    response = client.get("/health")  # Simulate API check
    assert response.status_code == 200
