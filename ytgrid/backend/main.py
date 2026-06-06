"""
YTGrid API Version 3.1

This is the main entry point for the YTGrid API, now stabilized for v3.1.
Key enhancements include:
  - API-key authentication for task, session, profile, and stream endpoints.
  - Multiprocessing and Celery execution paths.
  - Execution profiles backed by SQLite.
  - A basic web dashboard with Server-Sent Events.
  - Startup and shutdown resource management.

Future phases will further decouple the API from the automation workers and
integrate dynamic scheduling based on system resource monitoring.
"""

import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Import the aggregated router which includes both /sessions and /tasks endpoints
from ytgrid.backend.routes import router

# Configure logging (this can be expanded for structured JSON logging later)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s"
)

from contextlib import asynccontextmanager
from ytgrid.optimizer.orchestrator import optimizer
from ytgrid.utils.config import config
from ytgrid.proxy import proxy_pool, ProxyHealthChecker, FileProxySource, EnvProxySource
from ytgrid.database import init_db

proxy_health_checker = ProxyHealthChecker()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    logging.info("YTGrid API is starting up.")
    await init_db()
    optimizer.start()

    if config.PROXY_ENABLED:
        if config.PROXY_SOURCE == "file":
            proxies = FileProxySource(config.PROXY_FILE).fetch()
        elif config.PROXY_SOURCE == "env":
            proxies = EnvProxySource().fetch()
        else:
            proxies = []

        added = proxy_pool.add_proxies(proxies)
        logging.info(f"Loaded {added} proxies into pool.")
        proxy_health_checker.start()

    yield
    logging.info("YTGrid API is shutting down.")
    optimizer.stop()

    if config.PROXY_ENABLED:
        proxy_health_checker.stop()

app = FastAPI(
    title="YTGrid",
    description=(
        "YTGrid v3.1 automation API with task management, execution profiles, "
        "SSE dashboard updates, optional Celery workers, and resource optimization."
    ),
    version="3.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["X-API-Key", "Content-Type"],
)

# Include the aggregated router for sessions and tasks
app.include_router(router)

# Mount static folder for dashboard (absolute path — independent of cwd)
_STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint that confirms the API is running.
    """
    return {"message": "YTGrid API v3.1 is running!"}


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health-check endpoint to verify that the API is up and responsive.
    """
    return {"status": "healthy"}





if __name__ == "__main__":
    # Use uvicorn to run the application. The "reload" option is useful during development.
    # Bind to localhost by default — the API is unauthenticated unless YTGRID_API_KEY
    # is set, so it must not be exposed on all interfaces without explicit intent.
    import uvicorn

    uvicorn.run("ytgrid.backend.main:app", host="127.0.0.1", port=8000, reload=True)
