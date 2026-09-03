"""Application configuration module using Pydantic Settings."""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings for local dev & production."""

    PROJECT_NAME: str = "Merchant Risk Sentinel"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # CORS origins for local frontend dev
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    # Model & Risk Threshold Settings
    HIGH_RISK_THRESHOLD: float = 0.70
    CRITICAL_RISK_THRESHOLD: float = 0.85

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env")


settings = Settings()
