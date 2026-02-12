"""
App-Idea Miner - FastAPI Application
Main application entry point with routes, middleware, and configuration.
"""

import logging
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.app.config import get_settings
from apps.api.app.database import engine
from packages.core.cache import set_redis_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting App-Idea Miner API...")
    logger.info(f"Database URL: {settings.DATABASE_URL.split('@')[-1]}")  # Hide credentials
    logger.info(f"CORS Origins: {settings.CORS_ORIGINS}")

    # Initialize Redis client for caching
    try:
        redis_client = await aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=False,  # We'll handle JSON encoding
        )
        await redis_client.ping()
        set_redis_client(redis_client)
        logger.info("Redis client initialized for caching")
    except Exception as e:
        logger.warning(f"Failed to connect to Redis: {e}. Caching disabled.")

    yield

    # Shutdown
    logger.info("Shutting down App-Idea Miner API...")
    await engine.dispose()
    logger.info("Database connections closed")

    # Close Redis connection
    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed")


# Create FastAPI application
app = FastAPI(
    title="App-Idea Miner API",
    description="Intelligent opportunity detection platform for discovering validated app ideas",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """
    Health check endpoint.
    Returns service status and basic diagnostics.
    """
    try:
        # Test database connection
        from sqlalchemy import text

        from apps.api.app.database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))

        db_status = "up"
        db_latency = "< 5ms"  # Placeholder, can be measured
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "down"
        db_latency = "N/A"

    return {
        "status": "healthy" if db_status == "up" else "degraded",
        "version": "1.0.0",
        "services": {
            "database": {
                "status": db_status,
                "latency": db_latency,
            },
            "api": {
                "status": "up",
            },
        },
    }


@app.get("/", tags=["System"])
async def root():
    """
    Root endpoint.
    Returns API information and links to documentation.
    """
    return {
        "message": "Welcome to App-Idea Miner API",
        "version": "1.0.0",
        "docs": f"{settings.API_HOST}:{settings.API_PORT}/docs",
        "health": f"{settings.API_HOST}:{settings.API_PORT}/health",
    }


# Import and include routers
from apps.api.app.routers import analytics, clusters, ideas, jobs, posts

# Posts router (Phase 1)
app.include_router(posts.router, prefix="/api/v1/posts", tags=["Posts"])

# Ideas router (Phase 2)
app.include_router(ideas.router, prefix="/api/v1/ideas", tags=["Ideas"])

# Clusters router (Phase 3)
app.include_router(clusters.router, prefix="/api/v1/clusters", tags=["Clusters"])

# Analytics router (Phase 4)
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])

# Jobs router (Phase 4)
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["Jobs"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower(),
    )
