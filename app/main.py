"""
Genaryn AI Deputy Commander - Main Application
"""

from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.config import settings
from app.database import init_db, close_db
from app.middleware.logging import LoggingMiddleware
from app.middleware.timing import TimingMiddleware
from app.routers import health, auth, chat, conversations, decisions, websocket, stream
from app.services.redis_service import RedisService
from app.utils.logger import setup_logging

# Setup structured logging
setup_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    logger.info("Starting Genaryn AI Deputy Commander", environment=settings.APP_ENV)

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Initialize Redis
    redis_service = RedisService()
    await redis_service.connect()
    app.state.redis = redis_service
    logger.info("Redis connected")

    # Yield control back to FastAPI
    yield

    # Cleanup on shutdown
    logger.info("Shutting down application")
    await close_db()
    await redis_service.disconnect()
    logger.info("Cleanup completed")


# Create FastAPI application
app = FastAPI(
    title="Genaryn AI Deputy Commander",
    description="AI-powered decision support system for military operations",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "Health",
            "description": "Health check endpoints",
        },
        {
            "name": "Authentication",
            "description": "User authentication and authorization",
        },
        {
            "name": "Chat",
            "description": "AI chat interactions",
        },
        {
            "name": "Conversations",
            "description": "Conversation management",
        },
        {
            "name": "Decisions",
            "description": "Military decision support",
        },
        {
            "name": "WebSocket",
            "description": "Real-time WebSocket connections",
        },
        {
            "name": "Stream",
            "description": "Server-Sent Events streaming",
        },
    ],
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(TimingMiddleware)
app.add_middleware(LoggingMiddleware)

# Include routers
app.include_router(health.router, prefix="", tags=["Health"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(conversations.router, prefix="/conversations", tags=["Conversations"])
app.include_router(decisions.router, prefix="/decisions", tags=["Decisions"])
app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])
app.include_router(stream.router, prefix="/stream", tags=["Stream"])


@app.get("/", response_class=JSONResponse)
async def root() -> Dict[str, Any]:
    """Root endpoint with application information."""
    return {
        "application": "Genaryn AI Deputy Commander",
        "version": "1.0.0",
        "status": "operational",
        "tagline": "Independent AI Judgment. Stronger Commander Decisions.",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "openapi": "/openapi.json",
        },
    }


@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"The requested resource '{request.url.path}' was not found.",
            "status_code": 404,
        },
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Custom 500 handler."""
    logger.error("Internal server error", exc_info=exc, path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later.",
            "status_code": 500,
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.APP_ENV == "development",
        log_level=settings.LOG_LEVEL.lower(),
    )