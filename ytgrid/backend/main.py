from fastapi import FastAPI
from ytgrid.backend.routes import router as api_router

app = FastAPI(
    title="YTGrid API",
    description="A FastAPI backend for managing YT automation",
    version="0.1.0"
)

# Include API routes
app.include_router(api_router)

@app.get("/")
def read_root():
    return {"message": "YTGrid API is running!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
