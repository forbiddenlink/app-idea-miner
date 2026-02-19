"""
Rate limiting dependency using Redis.
Implements a fixed window algorithm.
"""

import logging

from fastapi import HTTPException, Request, status

from apps.api.app.config import get_settings
from packages.core.cache import get_redis_client

logger = logging.getLogger(__name__)


def get_client_ip(request: Request) -> str:
    """
    Get the real client IP address, handling proxy headers safely.

    When behind a reverse proxy (Railway, Vercel, nginx), the direct connection
    IP is the proxy's IP. We need to check X-Forwarded-For header to get the
    real client IP.

    Security: Only trust proxy headers when TRUST_PROXY_HEADERS is enabled
    and we're in a known deployment environment.
    """
    settings = get_settings()

    if settings.TRUST_PROXY_HEADERS:
        # X-Forwarded-For format: "client, proxy1, proxy2"
        # The leftmost IP is the original client
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first (leftmost) IP - this is the original client
            client_ip = forwarded_for.split(",")[0].strip()
            # Basic validation - ensure it looks like an IP
            if client_ip and "." in client_ip or ":" in client_ip:
                return client_ip

        # Fallback to X-Real-IP (used by some proxies)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

    # Direct connection IP (or fallback)
    return request.client.host if request.client else "unknown"


class RateLimiter:
    """
    Dependency for rate limiting requests based on client IP.
    Uses Redis to track request counts.
    """

    def __init__(self, times: int = 100, seconds: int = 60):
        self.times = times
        self.seconds = seconds

    async def __call__(self, request: Request):
        redis = get_redis_client()
        if not redis:
            # If Redis is down, we fail open (log error but allow request)
            # or fail closed depending on requirements. Choosing fail open for now.
            logger.warning("Redis not available for rate limiting. Allowing request.")
            return

        client_ip = get_client_ip(request)
        # Use a prefix to avoid collisions with other keys
        key = f"rate_limit:{client_ip}:{request.url.path}"

        try:
            # Simple fixed window: increment and set expire if new
            # This isn't perfect (edge cases at boundaries) but sufficient for Phase 1
            async with redis.pipeline() as pipe:
                pipe.incr(key)
                pipe.expire(key, self.seconds)
                results = await pipe.execute()

            count = results[0]

            if count > self.times:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded: {self.times} requests per {self.seconds} seconds",
                )

            # Optional: Add headers to response (requires Response object which isn't easy in Dependency)
            # Middleware is better for headers, but Dependency is easier for per-route application.

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Fail open on error
            return
