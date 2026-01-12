"""
Health check endpoints
"""

from typing import Dict, Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import httpx
import structlog

from app.database import get_db
from app.services.redis_service import get_redis
from app.config import settings

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "Genaryn AI Deputy Commander"}


@router.get("/health/detailed")
async def detailed_health_check(
    db: AsyncSession = Depends(get_db), redis_service=Depends(get_redis)
) -> Dict[str, Any]:
    """Detailed health check with service status."""
    health_status = {
        "status": "healthy",
        "service": "Genaryn AI Deputy Commander",
        "environment": settings.APP_ENV,
        "services": {
            "database": "unknown",
            "redis": "unknown",
            "llm_endpoint": "unknown",
        },
    }

    # Check database
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        health_status["services"]["database"] = "healthy"
    except Exception as e:
        health_status["services"]["database"] = "unhealthy"
        health_status["status"] = "degraded"
        logger.error("Database health check failed", error=str(e))

    # Check Redis
    try:
        await redis_service.ping()
        health_status["services"]["redis"] = "healthy"
    except Exception as e:
        health_status["services"]["redis"] = "unhealthy"
        health_status["status"] = "degraded"
        logger.error("Redis health check failed", error=str(e))

    # Check LLM endpoint (non-blocking, just connectivity)
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Extract base URL from endpoint
            base_url = settings.DO_LLM_ENDPOINT.replace("/api/v1/chat/completions", "")
            response = await client.get(f"{base_url}/health", follow_redirects=True)
            if response.status_code < 500:
                health_status["services"]["llm_endpoint"] = "healthy"
            else:
                health_status["services"]["llm_endpoint"] = "unhealthy"
                health_status["status"] = "degraded"
    except Exception as e:
        # If health endpoint doesn't exist, try OPTIONS on the main endpoint
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.options(settings.DO_LLM_ENDPOINT)
                health_status["services"]["llm_endpoint"] = "healthy"
        except Exception as e2:
            health_status["services"]["llm_endpoint"] = "unhealthy"
            health_status["status"] = "degraded"
            logger.warning("LLM endpoint health check failed", error=str(e2))

    return health_status


@router.get("/ready")
async def readiness_check(
    db: AsyncSession = Depends(get_db), redis_service=Depends(get_redis)
) -> Dict[str, str]:
    """Kubernetes readiness probe."""
    try:
        # Check database
        result = await db.execute(text("SELECT 1"))
        result.scalar()

        # Check Redis
        await redis_service.ping()

        return {"status": "ready"}
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        return {"status": "not_ready", "error": str(e)}


@router.get("/live")
async def liveness_check() -> Dict[str, str]:
    """Kubernetes liveness probe."""
    return {"status": "alive"}