from fastapi import FastAPI
from routes import sessions, status

app = FastAPI(title="YTGrid API", description="API for YouTube Automation")

# Include API routes
app.include_router(sessions.router)
app.include_router(status.router)

@app.get("/")
def read_root():
    return {"message": "YTGrid API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
