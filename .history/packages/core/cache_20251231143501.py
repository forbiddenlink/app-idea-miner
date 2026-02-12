"""
Redis caching utilities for API responses.
"""

import hashlib
import json
import logging
from collections.abc import Callable
from functools import wraps
from typing import Any

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

# Global Redis client (set in main.py lifespan)
redis_client: aioredis.Redis | None = None


def set_redis_client(client: aioredis.Redis):
    """
    Set the global Redis client.

    Called from FastAPI lifespan event.
    """
    global redis_client
    redis_client = client
    logger.info("Redis client configured for caching")


def get_redis_client() -> aioredis.Redis | None:
    """Get the global Redis client."""
    return redis_client


def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Generate a cache key from prefix and arguments.

    Args:
        prefix: Cache key prefix (e.g., 'analytics:summary')
        *args: Positional arguments to include in key
        **kwargs: Keyword arguments to include in key

    Returns:
        Cache key string
    """
    # Create a stable string representation of args/kwargs
    key_parts = [prefix]

    if args:
        key_parts.extend(str(arg) for arg in args)

    if kwargs:
        # Sort kwargs for consistent ordering
        sorted_kwargs = sorted(kwargs.items())
        key_parts.extend(f"{k}={v}" for k, v in sorted_kwargs)

    # Join parts and hash if too long
    key_string = ":".join(key_parts)

    if len(key_string) > 200:
        # Hash long keys to keep Redis keys manageable
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"{prefix}:hash:{key_hash}"

    return key_string


async def get_cached(key: str) -> Any | None:
    """
    Get value from cache.

    Args:
        key: Cache key

    Returns:
        Cached value or None if not found
    """
    if not redis_client:
        logger.warning("Redis client not configured, caching disabled")
        return None

    try:
        cached = await redis_client.get(key)
        if cached:
            logger.debug(f"Cache hit: {key}")
            return json.loads(cached)
        else:
            logger.debug(f"Cache miss: {key}")
            return None
    except Exception as e:
        logger.error(f"Redis get error: {e}")
        return None


async def set_cached(key: str, value: Any, ttl: int = 300):
    """
    Set value in cache.

    Args:
        key: Cache key
        value: Value to cache (must be JSON-serializable)
        ttl: Time to live in seconds (default: 5 minutes)
    """
    if not redis_client:
        logger.warning("Redis client not configured, caching disabled")
        return

    try:
        await redis_client.setex(
            key,
            ttl,
            json.dumps(value, default=str),  # default=str handles datetime, UUID, etc.
        )
        logger.debug(f"Cached: {key} (TTL: {ttl}s)")
    except Exception as e:
        logger.error(f"Redis set error: {e}")


async def invalidate_cache(pattern: str):
    """
    Invalidate cache keys matching pattern.

    Args:
        pattern: Redis key pattern (e.g., 'analytics:*')
    """
    import os

    client = redis_client

    # If no global client, create a temporary one
    if not client:
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        try:
            client = await aioredis.from_url(redis_url, encoding="utf-8", decode_responses=False)
            close_client = True
        except Exception as e:
            logger.error(f"Failed to create Redis client for invalidation: {e}")
            return
    else:
        close_client = False

    try:
        keys = await client.keys(pattern)
        if keys:
            await client.delete(*keys)
            logger.info(f"Invalidated {len(keys)} cache keys matching: {pattern}")
    except Exception as e:
        logger.error(f"Redis invalidate error: {e}")
    finally:
        if close_client:
            await client.close()


def cached(prefix: str, ttl: int = 300):
    """
    Decorator to cache async function results.

    Usage:
        @cached("analytics:summary", ttl=300)
        async def get_summary():
            return expensive_query()

    Args:
        prefix: Cache key prefix
        ttl: Time to live in seconds (default: 5 minutes)
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function arguments
            cache_key = generate_cache_key(prefix, *args, **kwargs)

            # Try to get from cache
            cached_result = await get_cached(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            await set_cached(cache_key, result, ttl)

            return result

        return wrapper

    return decorator


def cached_route(prefix: str, ttl: int = 300, key_params: list | None = None):
    """
    Decorator to cache FastAPI route responses.

    Usage:
        @app.get("/analytics/summary")
        @cached_route("analytics:summary", ttl=300)
        async def get_summary():
            return {"data": ...}

    Args:
        prefix: Cache key prefix
        ttl: Time to live in seconds
        key_params: List of query param names to include in cache key
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract query params if specified
            cache_kwargs = {}
            if key_params:
                for param in key_params:
                    if param in kwargs:
                        cache_kwargs[param] = kwargs[param]

            # Generate cache key
            cache_key = generate_cache_key(prefix, **cache_kwargs)

            # Try to get from cache
            cached_result = await get_cached(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute route function
            result = await func(*args, **kwargs)

            # Cache result
            await set_cached(cache_key, result, ttl)

            return result

        return wrapper

    return decorator


# Cache invalidation helpers for specific data types
async def invalidate_analytics_cache():
    """Invalidate all analytics caches."""
    await invalidate_cache("analytics:*")


async def invalidate_clusters_cache():
    """Invalidate cluster list cache."""
    await invalidate_cache("clusters:list:*")


async def invalidate_ideas_cache():
    """Invalidate ideas list cache."""
    await invalidate_cache("ideas:list:*")
