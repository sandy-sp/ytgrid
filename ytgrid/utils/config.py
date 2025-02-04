import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    HEADLESS_MODE = os.getenv("YTGRID_HEADLESS_MODE", "True").lower() == "true"
    DEFAULT_SPEED = float(os.getenv("YTGRID_DEFAULT_SPEED", 1.0))
    DEFAULT_LOOP_COUNT = int(os.getenv("YTGRID_DEFAULT_LOOP_COUNT", 1))
    ENABLE_REALTIME_UPDATES = os.getenv("YTGRID_REALTIME_UPDATES", "True").lower() == "true"
    WEBSOCKET_SERVER_URL = os.getenv("YTGRID_WEBSOCKET_SERVER_URL", "ws://127.0.0.1:8000/ws")
    USE_TEMP_USER_DATA = os.getenv("YTGRID_USE_TEMP_USER_DATA", "True").lower() == "true"

config = Config()
