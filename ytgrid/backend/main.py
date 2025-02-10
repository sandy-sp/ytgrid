from fastapi import FastAPI
from ytgrid.backend.routes import router  # Aggregator for sessions and tasks

app = FastAPI(
    title="YTGrid",
    description="Enhanced version with abstract session storage and automation capabilities.",
    version="2.0.0"
)

# ✅ Use the aggregated router that includes both /sessions and /tasks
app.include_router(router)

@app.get("/")
async def root():
    return {"message": "YTGrid API v2 is running!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
