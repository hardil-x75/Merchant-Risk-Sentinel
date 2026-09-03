"""Main API Router v1."""

from fastapi import APIRouter
from app.api.v1.endpoints import health, risk

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(risk.router, prefix="/risk", tags=["Risk Engine"])
