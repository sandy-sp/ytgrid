# ytgrid/backend/main.py
from fastapi import FastAPI
from ytgrid.backend.routes import session  # This imports your session router

app = FastAPI(
    title="YTGrid",
    description="Enhanced version with abstract session storage",
    version="2.0.0"
)

# Include the session routes under a common prefix
app.include_router(session.router, prefix="/sessions", tags=["sessions"])

@app.get("/")
async def root():
    return {"message": "YTGrid API v2 is running!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
