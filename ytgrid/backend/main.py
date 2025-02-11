"""
YTGrid API Version 3

This is the main entry point for the YTGrid API, now upgraded to Version 3.
Key enhancements include:
  - Asynchronous FastAPI endpoints for non-blocking I/O.
  - A dedicated health-check endpoint.
  - Startup and shutdown event handlers for resource initialization/cleanup.
  - Improved metadata for clarity.

Future phases will further decouple the API from the automation workers and
integrate dynamic scheduling based on system resource monitoring.
"""

import logging
from fastapi import FastAPI

# Import the aggregated router which includes both /sessions and /tasks endpoints
from ytgrid.backend.routes import router

# Configure logging (this can be expanded for structured JSON logging later)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s"
)

app = FastAPI(
    title="YTGrid",
    description=(
        "Enhanced version with abstract session storage, asynchronous endpoints, "
        "dynamic scheduling, and robust cloud deployment capabilities."
    ),
    version="3.0.0"
)

# Include the aggregated router for sessions and tasks
app.include_router(router)


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint that confirms the API is running.
    """
    return {"message": "YTGrid API v3 is running!"}


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health-check endpoint to verify that the API is up and responsive.
    """
    return {"status": "healthy"}


@app.on_event("startup")
async def on_startup():
    """
    Event handler for startup.
    Initialize resources such as database connections, dynamic scheduler,
    and any background tasks.
    """
    logging.info("YTGrid API is starting up.")
    # Future enhancement: initialize shared resources here.
    # Example: await scheduler.initialize()


@app.on_event("shutdown")
async def on_shutdown():
    """
    Event handler for shutdown.
    Clean up resources, close connections, and gracefully terminate background tasks.
    """
    logging.info("YTGrid API is shutting down.")
    # Future enhancement: perform cleanup of shared resources here.
    # Example: await scheduler.shutdown()


if __name__ == "__main__":
    # Use uvicorn to run the application. The "reload" option is useful during development.
    import uvicorn

    uvicorn.run("ytgrid.backend.main:app", host="0.0.0.0", port=8000, reload=True)
