"""Health check and status API endpoints."""

from datetime import datetime, timezone
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()


@router.get("/health", summary="System Health Check")
def health_check():
    """Verify backend API operational health, version, environment, and server timestamp."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
