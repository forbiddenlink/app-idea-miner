"""
Configuration management using Pydantic Settings.
Loads environment variables and provides type-safe configuration.
"""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """

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
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    LOG_LEVEL: str = "INFO"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS_ORIGINS from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

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
