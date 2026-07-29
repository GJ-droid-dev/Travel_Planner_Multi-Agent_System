from fastapi import FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    yield
    # Shutdown tasks

app = FastAPI(
    title="AI Travel Planner",
    description="Multi-Agent System for Dubai Travel Itineraries",
    version="0.1.0",
    lifespan=lifespan,
)

@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "gemini_model": "gemini-3.6-flash",
        "groq_model": "llama-3.3-70b-versatile"
    }
