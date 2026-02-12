"""
App-Idea Miner - FastAPI Application
Main application entry point with routes, middleware, and configuration.
"""

import logging
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import PlainTextResponse

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
    logger.info(
        f"Database URL: {settings.DATABASE_URL.split('@')[-1]}"
    )  # Hide credentials
    logger.info(f"CORS Origins: {settings.CORS_ORIGINS}")

    redis_client = None

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

# GZip compression middleware (70% size reduction on JSON responses)
app.add_middleware(
    GZipMiddleware,
    minimum_size=1000,  # Only compress responses > 1KB
    compresslevel=6,  # Balanced speed/compression (1-9)
)


# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """
    Enhanced health check endpoint.

    Returns comprehensive service status and diagnostics:
    - Database connection and latency
    - Redis connection and latency
    - Worker status and active tasks
    """
    import time

    from celery import Celery

    from packages.core.cache import get_redis_client

    overall_status = "healthy"
    services = {}

    # 1. Database health check
    try:
        from sqlalchemy import text

        from apps.api.app.database import AsyncSessionLocal

        start_time = time.time()
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        db_latency_ms = round((time.time() - start_time) * 1000, 2)

        services["database"] = {
            "status": "up",
            "latency_ms": db_latency_ms,
            "message": "Connected",
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        services["database"] = {"status": "down", "latency_ms": None, "error": str(e)}
        overall_status = "degraded"

    # 2. Redis health check
    redis_client = get_redis_client()
    if redis_client:
        try:
            start_time = time.time()
            await redis_client.ping()
            redis_latency_ms = round((time.time() - start_time) * 1000, 2)

            services["redis"] = {
                "status": "up",
                "latency_ms": redis_latency_ms,
                "message": "Connected",
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            services["redis"] = {"status": "down", "latency_ms": None, "error": str(e)}
            overall_status = "degraded"
    else:
        services["redis"] = {
            "status": "unknown",
            "message": "Redis client not configured",
        }

    # 3. Worker health check
    try:
        celery_app = Celery(
            "app-idea-miner",
            broker=settings.REDIS_URL,
            backend=settings.REDIS_URL.replace("/0", "/1"),
        )

        # Check worker availability
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()
        stats = inspect.stats()

        if active_tasks is not None and stats is not None:
            # Count total active tasks across all workers
            total_active = (
                sum(len(tasks) for tasks in active_tasks.values())
                if active_tasks
                else 0
            )
            worker_count = len(stats)

            services["worker"] = {
                "status": "up",
                "workers": worker_count,
                "active_tasks": total_active,
                "message": f"{worker_count} worker(s) connected",
            }
        else:
            services["worker"] = {
                "status": "down",
                "workers": 0,
                "active_tasks": 0,
                "error": "No workers available",
            }
            overall_status = "degraded"
    except Exception as e:
        logger.error(f"Worker health check failed: {e}")
        services["worker"] = {"status": "unknown", "error": str(e)}
        # Worker down doesn't degrade overall status (async tasks only)

    # 4. API status (always up if we got here)
    services["api"] = {"status": "up", "message": "Responding"}

    return {
        "status": overall_status,
        "version": "1.0.0",
        "timestamp": time.time(),
        "services": services,
    }


@app.get("/metrics", tags=["System"], response_class=PlainTextResponse)
async def metrics():
    """
    Prometheus-style metrics endpoint.

    Returns basic application metrics for monitoring.
    """
    from sqlalchemy import func, select

    from apps.api.app.database import AsyncSessionLocal
    from packages.core.models import Cluster, IdeaCandidate, RawPost

    try:
        async with AsyncSessionLocal() as session:
            # Count metrics
            posts_result = await session.execute(
                select(func.count()).select_from(RawPost)
            )
            ideas_result = await session.execute(
                select(func.count())
                .select_from(IdeaCandidate)
                .where(IdeaCandidate.is_valid == True)
            )
            clusters_result = await session.execute(
                select(func.count()).select_from(Cluster)
            )

            total_posts = posts_result.scalar_one()
            total_ideas = ideas_result.scalar_one()
            total_clusters = clusters_result.scalar_one()

            # Prometheus format
            metrics_output = f"""# HELP app_posts_total Total number of posts ingested
# TYPE app_posts_total gauge
app_posts_total {total_posts}

# HELP app_ideas_total Total number of valid ideas extracted
# TYPE app_ideas_total gauge
app_ideas_total {total_ideas}

# HELP app_clusters_total Total number of opportunity clusters
# TYPE app_clusters_total gauge
app_clusters_total {total_clusters}

# HELP app_version Application version info
# TYPE app_version gauge
app_version{{version="1.0.0"}} 1
"""
            return metrics_output
    except Exception as e:
        logger.error(f"Metrics endpoint failed: {e}")
        return f"# Error generating metrics: {str(e)}"


@app.get("/", tags=["System"])
async def root(request: Request):
    """
    Root endpoint.
    Returns API information and links to documentation.
    """
    base_url = str(request.base_url).rstrip("/")
    return {
        "message": "Welcome to App-Idea Miner API",
        "version": "1.0.0",
        "docs": f"{base_url}/docs",
        "health": f"{base_url}/health",
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
