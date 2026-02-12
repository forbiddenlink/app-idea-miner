# API Compression Middleware for FastAPI
# Reduces payload size by 70-80% using gzip/brotli

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware


def setup_compression(app: FastAPI):
    """
    Add response compression to reduce API payload sizes

    Benefits:
    - 70-80% size reduction for JSON responses
    - Automatic compression for responses > 1KB
    - Improves performance on slow connections
    - No changes needed on frontend (browsers handle automatically)
    """

    # Add GZip compression (supported by all browsers)
    app.add_middleware(
        GZipMiddleware,
        minimum_size=1000,  # Only compress responses > 1KB
        compresslevel=6,  # Balance between speed and compression (1-9)
    )

    return app


def setup_cache_headers(app: FastAPI):
    """
    Add HTTP cache headers to reduce unnecessary API calls

    Strategy:
    - Static data (cluster details): Cache for 5 minutes
    - Dynamic data (analytics): Cache for 1 minute
    - Real-time data (job status): No cache
    """

    from starlette.middleware.base import BaseHTTPMiddleware

    class CacheHeaderMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            response = await call_next(request)

            # Cache strategy by endpoint
            if "/api/v1/clusters/" in request.url.path and request.method == "GET":
                # Cluster details - cache for 5 minutes
                response.headers["Cache-Control"] = "public, max-age=300"

            elif "/api/v1/analytics/" in request.url.path:
                # Analytics - cache for 1 minute
                response.headers["Cache-Control"] = "public, max-age=60"

            elif "/api/v1/jobs/" in request.url.path:
                # Job status - no cache
                response.headers["Cache-Control"] = (
                    "no-cache, no-store, must-revalidate"
                )

            else:
                # Default - cache for 30 seconds
                response.headers["Cache-Control"] = "public, max-age=30"

            # Add ETag for conditional requests (future)
            # response.headers['ETag'] = generate_etag(response.body)

            return response

    app.add_middleware(CacheHeaderMiddleware)
    return app


# Usage in main.py:
"""
from packages.core.compression import setup_compression, setup_cache_headers

app = FastAPI(title="App-Idea Miner API")

# Add compression first (before other middleware)
setup_compression(app)

# Add cache headers
setup_cache_headers(app)

# Then add other middleware (CORS, etc.)
app.add_middleware(CORSMiddleware, ...)
"""
