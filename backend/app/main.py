"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Merchant Risk Sentinel — AI Risk Manager for Razorpay Buildathon (Track 02)",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", summary="Root Info")
def root_info():
    """Root metadata response pointing to API documentation and health status."""
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs_url": "/docs",
        "health_check": f"{settings.API_V1_STR}/health",
        "risk_assess_endpoint": f"{settings.API_V1_STR}/risk/assess",
    }
