"""
Configuration Module for YTGrid (Version 3)

This module loads environment variables using python-dotenv and provides configuration settings
via the Config class. These settings include general options, browser parameters, session management,
WebSocket updates, and Celery integration details.
"""

import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()


class Config:
    """Configuration settings for YTGrid."""

    # General settings
    HEADLESS_MODE: bool = os.getenv("YTGRID_HEADLESS_MODE", "True").lower() == "true"
    DEFAULT_SPEED: float = float(os.getenv("YTGRID_DEFAULT_SPEED", 1.0))
    DEFAULT_LOOP_COUNT: int = int(os.getenv("YTGRID_DEFAULT_LOOP_COUNT", 1))

    # Session management
    MAX_CONCURRENT_SESSIONS: int = int(os.getenv("YTGRID_MAX_SESSIONS", 5))

    # WebSocket for real-time updates
    ENABLE_REALTIME_UPDATES: bool = os.getenv("YTGRID_REALTIME_UPDATES", "False").lower() == "true"
    WEBSOCKET_SERVER_URL: str = os.getenv("YTGRID_WEBSOCKET_SERVER_URL", "ws://127.0.0.1:8000/ws")

    # Browser settings
    USE_TEMP_USER_DATA: bool = os.getenv("YTGRID_USE_TEMP_USER_DATA", "True").lower() == "true"
    BROWSER_TIMEOUT: int = int(os.getenv("YTGRID_BROWSER_TIMEOUT", 20))

    # Celery integration
    USE_CELERY: bool = os.getenv("YTGRID_USE_CELERY", "False").lower() == "true"
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")


# Global configuration instance
config = Config()
