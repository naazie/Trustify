from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient

from config import settings
from routers import scans, findings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.mongo = AsyncIOMotorClient(settings.mongo_uri)
    app.state.db = app.state.mongo.get_default_database()
    os.makedirs(settings.workspace_dir, exist_ok=True)
    print("✅  MongoDB connected")
    yield
    # Shutdown
    app.state.mongo.close()
    print("🔌  MongoDB disconnected")


app = FastAPI(
    title="Trustify API",
    description="AI-powered SAST orchestration platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scans.router, prefix="/api/scans", tags=["Scans"])
app.include_router(findings.router, prefix="/api/findings", tags=["Findings"])


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "trustify-backend"}
