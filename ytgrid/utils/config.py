import os

class Config:
    """Configuration settings for YTGrid."""
    
    # Default playback settings
    DEFAULT_LOOP_COUNT = int(os.getenv("YTGRID_LOOP_COUNT", 1))  # Number of times to repeat the full automation process
    DEFAULT_SPEED = float(os.getenv("YTGRID_DEFAULT_SPEED", 1.0))  # Default video playback speed
    
    # Parallel execution settings
    MAX_CONCURRENT_SESSIONS = int(os.getenv("YTGRID_MAX_SESSIONS", 5))  # Maximum number of parallel video sessions
    
    # WebSocket for real-time updates
    ENABLE_REALTIME_UPDATES = os.getenv("YTGRID_REALTIME_UPDATES", "true").lower() == "true"
    WEBSOCKET_SERVER_URL = os.getenv("YTGRID_WEBSOCKET_URL", "ws://127.0.0.1:8000/ws")  # WebSocket endpoint for live updates

    # Browser settings
    HEADLESS_MODE = os.getenv("YTGRID_HEADLESS_MODE", "true").lower() == "true"
    BROWSER_TIMEOUT = int(os.getenv("YTGRID_BROWSER_TIMEOUT", 20))  # Time to wait for elements to load
    USE_TEMP_USER_DATA = os.getenv("YTGRID_USE_TEMP_USER_DATA", "true").lower() == "true"  # Whether to use fresh browser data each time

config = Config()
