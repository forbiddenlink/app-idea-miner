"""
Configuration management using Pydantic Settings.
Loads environment variables and provides type-safe configuration.
"""

import os
from functools import lru_cache

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """

    # Environment
    ENV: str = "development"

    # Proxy trust settings (for rate limiting behind load balancers)
    TRUST_PROXY_HEADERS: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/appideas"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "appideas"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4
    CORS_ORIGINS: str | list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        "https://app-idea-miner.vercel.app",
        "https://*.vercel.app",
    ]
    LOG_LEVEL: str = "INFO"
    API_KEY: str = "dev-api-key"

    @field_validator("API_KEY")
    @classmethod
    def validate_api_key_strength(cls, v: str) -> str:
        """Ensure API key meets minimum security requirements."""
        if len(v) < 16 and os.getenv("ENV") == "production":
            raise ValueError("API_KEY must be at least 16 characters in production")
        return v

    @model_validator(mode="after")
    def parse_cors_origins(self):
        """Parse CORS_ORIGINS from comma-separated string to list."""
        if isinstance(self.CORS_ORIGINS, str):
            self.CORS_ORIGINS = [
                origin.strip() for origin in self.CORS_ORIGINS.split(",")
            ]
        return self

    @model_validator(mode="after")
    def validate_production_secrets(self):
        """Ensure default secrets are not used in production."""
        if self.ENV == "production":
            if self.API_KEY == "dev-api-key":
                raise ValueError(
                    "API_KEY must be changed from default in production. "
                    "Set a secure API_KEY environment variable."
                )
            if self.SECRET_KEY == "development-secret-key-change-in-production":
                raise ValueError(
                    "SECRET_KEY must be changed from default in production. "
                    "Set a secure SECRET_KEY environment variable."
                )
        return self

    # Worker Configuration
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/1"
    CELERY_WORKERS: int = 2

    # Data Sources
    RSS_FEEDS: str = "https://hnrss.org/newest"
    FETCH_INTERVAL_HOURS: int = 6

    # Clustering Configuration
    MIN_CLUSTER_SIZE: int = 3
    MAX_FEATURES: int = 500
    RECLUSTER_THRESHOLD: int = 100

    # Security (for future use)
    SECRET_KEY: str = "development-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    LRU cache ensures settings are loaded once and reused.
    """
    return Settings()
