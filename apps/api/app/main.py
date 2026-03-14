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
from starlette.middleware.base import BaseHTTPMiddleware

from apps.api.app.config import get_settings
from apps.api.app.core.logging_middleware import RequestLoggingMiddleware
from apps.api.app.database import engine
from apps.api.app.schemas.common import HealthResponse
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

    Gracefully handles missing database/redis for serverless environments.
    """
    import os

    is_serverless = os.getenv("VERCEL", "") == "1"
    has_database = bool(os.getenv("DATABASE_URL"))
    # Support both standard Redis and Upstash Redis (TLS-based, for serverless)
    redis_url = os.getenv("UPSTASH_REDIS_URL") or os.getenv("REDIS_URL")
    has_redis = bool(redis_url)

    # Startup
    logger.info("Starting App-Idea Miner API...")
    logger.info(f"Environment: {'Vercel Serverless' if is_serverless else 'Standard'}")

    if has_database:
        logger.info(
            f"Database URL: {settings.DATABASE_URL.split('@')[-1]}"
        )  # Hide credentials
    else:
        logger.warning("DATABASE_URL not set - database features disabled")

    logger.info(f"CORS Origins: {settings.CORS_ORIGINS}")

    redis_client = None

    # Initialize Redis client for caching (supports standard Redis and Upstash)
    if has_redis:
        try:
            is_upstash = redis_url.startswith("rediss://")
            redis_client = await aioredis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=False,  # We'll handle JSON encoding
            )
            await redis_client.ping()
            set_redis_client(redis_client)
            redis_type = "Upstash Redis (TLS)" if is_upstash else "Redis"
            logger.info(f"{redis_type} client initialized for caching")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Caching disabled.")
    else:
        logger.warning("No Redis URL configured - caching disabled")

    yield

    # Shutdown
    logger.info("Shutting down App-Idea Miner API...")

    if has_database:
        try:
            await engine.dispose()
            logger.info("Database connections closed")
        except Exception as e:
            logger.warning(f"Error closing database connections: {e}")

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


# Security headers middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # XSS protection (legacy, but still useful for older browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions policy (formerly Feature-Policy)
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
            "magnetometer=(), microphone=(), payment=(), usb=()"
        )

        # Content Security Policy (allow API responses, restrict everything else)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'none'; "
            "style-src 'none'; "
            "img-src 'none'; "
            "frame-ancestors 'none'"
        )

        # HSTS - enforce HTTPS (1 year, include subdomains)
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )

        return response


# Cache-Control middleware for GET endpoints
class CacheControlMiddleware(BaseHTTPMiddleware):
    """Set Cache-Control headers on GET responses based on path."""

    # Path prefixes → (max-age, stale-while-revalidate)
    NO_STORE_PREFIXES = ("/health", "/api/v1/jobs")
    ANALYTICS_PREFIX = "/api/v1/analytics"
    # Detail patterns: paths like /api/v1/clusters/{id} or /api/v1/ideas/{id}
    DETAIL_PREFIXES = ("/api/v1/clusters/", "/api/v1/ideas/")
    LIST_PREFIXES = (
        "/api/v1/clusters",
        "/api/v1/ideas",
        "/api/v1/posts",
        "/api/v1/opportunities",
    )

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        if request.method != "GET" or "cache-control" in response.headers:
            return response

        path = request.url.path

        if any(path.startswith(p) for p in self.NO_STORE_PREFIXES):
            response.headers["Cache-Control"] = "no-store"
        elif path.startswith(self.ANALYTICS_PREFIX):
            response.headers["Cache-Control"] = (
                "public, max-age=900, stale-while-revalidate=300"
            )
        elif any(path.startswith(p) for p in self.DETAIL_PREFIXES):
            response.headers["Cache-Control"] = (
                "public, max-age=600, stale-while-revalidate=120"
            )
        elif any(path == p or path == p + "/" for p in self.LIST_PREFIXES):
            response.headers["Cache-Control"] = (
                "public, max-age=300, stale-while-revalidate=60"
            )

        return response


app.add_middleware(CacheControlMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# Request logging middleware (correlation IDs, timing, structured logs)
app.add_middleware(RequestLoggingMiddleware)


# --- Health check helpers ---


async def _check_database(has_database: bool, is_serverless: bool) -> tuple[dict, bool]:
    """Check database connectivity. Returns (service_info, is_degraded)."""
    import time

    if not has_database:
        info = {"status": "not_configured", "message": "DATABASE_URL not set"}
        return info, (not is_serverless)

    try:
        from sqlalchemy import text

        from apps.api.app.database import AsyncSessionLocal

        start_time = time.time()
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        latency_ms = round((time.time() - start_time) * 1000, 2)

        return {"status": "up", "latency_ms": latency_ms, "message": "Connected"}, False
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {"status": "down", "latency_ms": None, "error": str(e)}, True


async def _check_redis(has_redis: bool) -> tuple[dict, bool]:
    """Check Redis connectivity. Returns (service_info, is_degraded)."""
    import time

    from packages.core.cache import get_redis_client

    if not has_redis:
        return {"status": "not_configured", "message": "REDIS_URL not set"}, False

    redis_client = get_redis_client()
    if not redis_client:
        return {"status": "not_initialized", "message": "Redis client not ready"}, False

    try:
        start_time = time.time()
        await redis_client.ping()
        latency_ms = round((time.time() - start_time) * 1000, 2)

        return {"status": "up", "latency_ms": latency_ms, "message": "Connected"}, False
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {"status": "down", "latency_ms": None, "error": str(e)}, True


def _check_worker(has_redis: bool, is_serverless: bool) -> dict:
    """Check Celery worker status. Returns service_info dict."""
    if is_serverless or not has_redis:
        return {
            "status": "not_applicable",
            "message": "Workers not supported in serverless",
        }

    try:
        from celery import Celery

        celery_app = Celery(
            "app-idea-miner",
            broker=settings.REDIS_URL,
            backend=settings.REDIS_URL.replace("/0", "/1"),
        )

        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()
        stats = inspect.stats()

        if active_tasks is not None and stats is not None:
            total_active = (
                sum(len(tasks) for tasks in active_tasks.values())
                if active_tasks
                else 0
            )
            worker_count = len(stats)
            return {
                "status": "up",
                "workers": worker_count,
                "active_tasks": total_active,
                "message": f"{worker_count} worker(s) connected",
            }

        return {
            "status": "down",
            "workers": 0,
            "active_tasks": 0,
            "error": "No workers available",
        }
    except Exception as e:
        logger.error(f"Worker health check failed: {e}")
        return {"status": "unknown", "error": str(e)}


# Health check endpoint
@app.get("/health", tags=["System"], response_model=HealthResponse)
async def health_check():
    """
    Enhanced health check endpoint.

    Returns comprehensive service status and diagnostics:
    - Database connection and latency (if configured)
    - Redis connection and latency (if configured)
    - Worker status and active tasks (if configured)

    Works in degraded mode for serverless environments without full infra.
    """
    import os
    import time

    is_serverless = os.getenv("VERCEL", "") == "1"
    has_database = bool(os.getenv("DATABASE_URL"))
    has_redis = bool(os.getenv("REDIS_URL"))

    overall_status = "healthy"

    db_info, db_degraded = await _check_database(has_database, is_serverless)
    redis_info, redis_degraded = await _check_redis(has_redis)
    worker_info = _check_worker(has_redis, is_serverless)

    if db_degraded or redis_degraded:
        overall_status = "degraded"

    services = {
        "database": db_info,
        "redis": redis_info,
        "worker": worker_info,
        "api": {"status": "up", "message": "Responding"},
    }

    return {
        "status": overall_status,
        "version": "1.0.0",
        "environment": "serverless" if is_serverless else "standard",
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
import os

_is_serverless = os.getenv("VERCEL", "") == "1"

from apps.api.app.routers import (
    analytics,
    clusters,
    export,
    ideas,
    opportunities,
    posts,
)

# Data query routers - available everywhere (no heavy deps)
app.include_router(posts.router, prefix="/api/v1/posts", tags=["Posts"])
app.include_router(ideas.router, prefix="/api/v1/ideas", tags=["Ideas"])
app.include_router(clusters.router, prefix="/api/v1/clusters", tags=["Clusters"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(
    opportunities.router, prefix="/api/v1/opportunities", tags=["Opportunities"]
)
app.include_router(export.router, prefix="/api/v1/export", tags=["Export"])

# Jobs router requires Celery - only available with workers
if not _is_serverless:
    from apps.api.app.routers import jobs

    app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["Jobs"])
else:
    logger.info("Running in serverless mode - jobs router disabled (requires Celery)")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower(),
    )
