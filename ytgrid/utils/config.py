"""
Configuration Module for YTGrid (Version 3.1)

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
    API_KEY: str = os.getenv("YTGRID_API_KEY", "")
    API_BASE_URL: str = os.getenv("YTGRID_API_BASE_URL", "http://127.0.0.1:8000")
    CORS_ALLOWED_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "YTGRID_CORS_ALLOWED_ORIGINS",
            ",".join(
                [
                    "http://localhost:1420",
                    "http://127.0.0.1:1420",
                    "http://localhost:5173",
                    "http://127.0.0.1:5173",
                    "tauri://localhost",
                    "https://tauri.localhost",
                    "http://tauri.localhost",
                ]
            ),
        ).split(",")
        if origin.strip()
    ]
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

    # Database
    DB_PATH: str = os.getenv(
        "YTGRID_DB_PATH",
        os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ytgrid.db"
        ),
    )

    # Optimizer settings
    OPTIMIZER_ENABLED: bool = os.getenv("YTGRID_OPTIMIZER_ENABLED", "True").lower() == "true"
    TMP_MAX_AGE: int = int(os.getenv("YTGRID_TMP_MAX_AGE", 1800))

    # Proxy settings
    PROXY_ENABLED: bool = os.getenv("YTGRID_PROXY_ENABLED", "False").lower() == "true"
    PROXY_SOURCE: str = os.getenv("YTGRID_PROXY_SOURCE", "file")
    PROXY_FILE: str = os.getenv("YTGRID_PROXY_FILE", "./proxies.txt")
    PROXY_API_URL: str = os.getenv("YTGRID_PROXY_API_URL", "")
    PROXY_API_KEY: str = os.getenv("YTGRID_PROXY_API_KEY", "")
    PROXY_COOLDOWN_SECONDS: int = int(os.getenv("YTGRID_PROXY_COOLDOWN_SECONDS", 300))
    PROXY_HEALTH_CHECK_INTERVAL: int = int(os.getenv("YTGRID_PROXY_HEALTH_CHECK_INTERVAL", 60))
    PROXY_MAX_FAILURE_RATE: float = float(os.getenv("YTGRID_PROXY_MAX_FAILURE_RATE", 0.3))


# Global configuration instance

config = Config()
