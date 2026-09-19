"""FastAPI Application Main Entrypoint for ReRun."""
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.artifacts import router as artifacts_router
from app.api.stream import router as stream_router
from app.api.tasks import router as tasks_router
from app.core.config import settings
from app.core.logging import logger
from app.database.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes application resources and database tables on startup."""
    logger.info("Initializing ReRun Database Schema...")
    await init_db()
    logger.info("ReRun Autonomous Coding Agent Platform initialized.")
    yield
    logger.info("Shutting down ReRun Platform.")


app = FastAPI(
    title="ReRun API",
    description="Hierarchical Autonomous Coding Agent with Runtime-Guided Recovery and Sandboxed Execution",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(tasks_router, prefix="/api")
app.include_router(stream_router, prefix="/api")
app.include_router(artifacts_router, prefix="/api")


@app.get("/health")
async def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "docker_available": settings.ALLOW_LOCAL_FALLBACK_FOR_TESTING or False,
        "version": "1.0.0",
    }


@app.get("/api")
async def api_root():
    """API metadata and discovery."""
    return {
        "title": "ReRun Autonomous Coding Agent API",
        "endpoints": [
            "POST /api/tasks",
            "GET  /api/tasks",
            "GET  /api/tasks/{id}",
            "POST /api/tasks/{id}/cancel",
            "GET  /api/tasks/{id}/events",
            "WS   /api/ws/tasks/{id}",
            "GET  /api/artifacts/{id}/{filename}",
        ]
    }

# Mount frontend build if available
frontend_dist = settings.BASE_DIR / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
