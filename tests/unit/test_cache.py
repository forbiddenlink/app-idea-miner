"""
Unit tests for packages/core/cache.py — Redis caching utilities.

Tests key generation, CacheMetrics, get/set/invalidate operations,
and graceful error handling. All Redis calls are mocked.
No external services required.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from packages.core.cache import (
    CacheMetrics,
    generate_cache_key,
    get_cached,
    invalidate_cache,
    set_cached,
)

# ---------------------------------------------------------------------------
# generate_cache_key()
# ---------------------------------------------------------------------------


class TestGenerateCacheKey:
    def test_simple_prefix_only(self):
        key = generate_cache_key("analytics:summary")
        assert key == "analytics:summary"

    def test_prefix_with_positional_args(self):
        key = generate_cache_key("clusters", "size", "desc")
        assert key == "clusters:size:desc"

    def test_prefix_with_kwargs(self):
        key = generate_cache_key("analytics", page=1, limit=20)
        # kwargs sorted alphabetically
        assert key == "analytics:limit=20:page=1"

    def test_prefix_with_args_and_kwargs(self):
        key = generate_cache_key("data", "v1", format="json")
        assert key == "data:v1:format=json"

    def test_kwargs_sorted_for_consistency(self):
        key_a = generate_cache_key("x", b=2, a=1)
        key_b = generate_cache_key("x", a=1, b=2)
        assert key_a == key_b

    def test_long_key_gets_md5_hashed(self):
        """Keys exceeding 200 chars should be hashed with MD5."""
        long_value = "x" * 300
        key = generate_cache_key("prefix", long_value)
        assert key.startswith("prefix:hash:")
        # Verify the hash part is a valid 32-char hex MD5
        hash_part = key.split("prefix:hash:")[1]
        assert len(hash_part) == 32

    def test_long_key_hash_is_deterministic(self):
        """Same long inputs should produce the same hashed key."""
        long_value = "y" * 300
        key_a = generate_cache_key("pfx", long_value)
        key_b = generate_cache_key("pfx", long_value)
        assert key_a == key_b

    def test_short_key_not_hashed(self):
        """Keys under 200 chars should NOT be hashed."""
        key = generate_cache_key("short", "a", "b")
        assert ":hash:" not in key


# ---------------------------------------------------------------------------
# CacheMetrics
# ---------------------------------------------------------------------------


class TestCacheMetrics:
    def test_initial_state(self):
        m = CacheMetrics()
        assert m.hits == 0
        assert m.misses == 0
        assert m.errors == 0
        assert m.hit_rate == 0.0

    def test_record_hit(self):
        m = CacheMetrics()
        m.record_hit("analytics:summary")
        assert m.hits == 1
        assert m.misses == 0

    def test_record_miss(self):
        m = CacheMetrics()
        m.record_miss("analytics:summary")
        assert m.misses == 1
        assert m.hits == 0

    def test_record_error(self):
        m = CacheMetrics()
        m.record_error()
        assert m.errors == 1

    def test_hit_rate_calculation(self):
        m = CacheMetrics()
        m.record_hit("k")
        m.record_hit("k")
        m.record_miss("k")
        # 2 hits out of 3 total
        assert abs(m.hit_rate - 2 / 3) < 0.001

    def test_hit_rate_zero_when_no_requests(self):
        m = CacheMetrics()
        assert m.hit_rate == 0.0

    def test_by_prefix_tracking(self):
        m = CacheMetrics()
        m.record_hit("analytics:summary")
        m.record_hit("analytics:trends")
        m.record_miss("clusters:list")

        stats = m.get_stats()
        assert stats["by_prefix"]["analytics"]["hits"] == 2
        assert stats["by_prefix"]["clusters"]["misses"] == 1

    def test_get_stats_returns_complete_dict(self):
        m = CacheMetrics()
        m.record_hit("a:1")
        m.record_miss("b:2")
        m.record_error()

        stats = m.get_stats()
        assert "hits" in stats
        assert "misses" in stats
        assert "errors" in stats
        assert "hit_rate" in stats
        assert "by_prefix" in stats
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["errors"] == 1

    def test_key_without_colon_uses_full_key_as_prefix(self):
        m = CacheMetrics()
        m.record_hit("simple_key")
        stats = m.get_stats()
        assert "simple_key" in stats["by_prefix"]


# ---------------------------------------------------------------------------
# get_cached()
# ---------------------------------------------------------------------------


class TestGetCached:
    @pytest.mark.asyncio
    async def test_returns_none_when_no_redis_client(self):
        """When redis_client is None, get_cached should return None."""
        with patch("packages.core.cache.redis_client", None):
            result = await get_cached("some:key")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_deserialized_data_on_cache_hit(self):
        """When key exists in Redis, return deserialized JSON."""
        expected = {"clusters": [1, 2, 3], "total": 3}
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=json.dumps(expected))

        with patch("packages.core.cache.redis_client", mock_redis):
            result = await get_cached("clusters:list")

        assert result == expected
        mock_redis.get.assert_awaited_once_with("clusters:list")

    @pytest.mark.asyncio
    async def test_returns_none_on_cache_miss(self):
        """When key doesn't exist in Redis, return None."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)

        with patch("packages.core.cache.redis_client", mock_redis):
            result = await get_cached("missing:key")

        assert result is None

    @pytest.mark.asyncio
    async def test_handles_redis_error_gracefully(self):
        """Redis exceptions should be caught; return None without bubbling."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(side_effect=Exception("Redis connection lost"))

        with patch("packages.core.cache.redis_client", mock_redis):
            result = await get_cached("broken:key")

        assert result is None

    @pytest.mark.asyncio
    async def test_records_hit_in_metrics(self):
        """A cache hit should be recorded in cache_metrics."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=json.dumps({"ok": True}))
        mock_metrics = MagicMock(spec=CacheMetrics)

        with (
            patch("packages.core.cache.redis_client", mock_redis),
            patch("packages.core.cache.cache_metrics", mock_metrics),
        ):
            await get_cached("test:key")

        mock_metrics.record_hit.assert_called_once_with("test:key")

    @pytest.mark.asyncio
    async def test_records_miss_in_metrics(self):
        """A cache miss should be recorded in cache_metrics."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_metrics = MagicMock(spec=CacheMetrics)

        with (
            patch("packages.core.cache.redis_client", mock_redis),
            patch("packages.core.cache.cache_metrics", mock_metrics),
        ):
            await get_cached("test:key")

        mock_metrics.record_miss.assert_called_once_with("test:key")

    @pytest.mark.asyncio
    async def test_records_error_in_metrics(self):
        """A Redis error should be recorded in cache_metrics."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(side_effect=Exception("fail"))
        mock_metrics = MagicMock(spec=CacheMetrics)

        with (
            patch("packages.core.cache.redis_client", mock_redis),
            patch("packages.core.cache.cache_metrics", mock_metrics),
        ):
            await get_cached("test:key")

        mock_metrics.record_error.assert_called_once()


# ---------------------------------------------------------------------------
# set_cached()
# ---------------------------------------------------------------------------


class TestSetCached:
    @pytest.mark.asyncio
    async def test_stores_serialized_data_with_ttl(self):
        """set_cached should call Redis setex with JSON-serialized value."""
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock()

        data = {"count": 42, "items": ["a", "b"]}
        with patch("packages.core.cache.redis_client", mock_redis):
            await set_cached("test:key", data, ttl=120)

        mock_redis.setex.assert_awaited_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == "test:key"  # key
        assert call_args[0][1] == 120  # ttl
        assert json.loads(call_args[0][2]) == data  # serialized value

    @pytest.mark.asyncio
    async def test_default_ttl_is_300(self):
        """Default TTL should be 300 seconds (5 minutes)."""
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock()

        with patch("packages.core.cache.redis_client", mock_redis):
            await set_cached("test:key", {"data": True})

        call_args = mock_redis.setex.call_args
        assert call_args[0][1] == 300

    @pytest.mark.asyncio
    async def test_no_op_when_no_redis_client(self):
        """When redis_client is None, set_cached should do nothing."""
        with patch("packages.core.cache.redis_client", None):
            # Should not raise
            await set_cached("test:key", {"data": True})

    @pytest.mark.asyncio
    async def test_handles_redis_error_gracefully(self):
        """Redis exceptions should be caught without bubbling."""
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock(side_effect=Exception("Redis write error"))

        with patch("packages.core.cache.redis_client", mock_redis):
            # Should not raise
            await set_cached("test:key", {"data": True})


# ---------------------------------------------------------------------------
# invalidate_cache()
# ---------------------------------------------------------------------------


class TestInvalidateCache:
    @pytest.mark.asyncio
    async def test_deletes_matching_keys(self):
        """invalidate_cache should find keys by pattern and delete them."""
        mock_redis = AsyncMock()
        mock_redis.keys = AsyncMock(return_value=["analytics:a", "analytics:b"])
        mock_redis.delete = AsyncMock()

        with patch("packages.core.cache.redis_client", mock_redis):
            await invalidate_cache("analytics:*")

        mock_redis.keys.assert_awaited_once_with("analytics:*")
        mock_redis.delete.assert_awaited_once_with("analytics:a", "analytics:b")

    @pytest.mark.asyncio
    async def test_no_delete_when_no_matching_keys(self):
        """If no keys match the pattern, delete should not be called."""
        mock_redis = AsyncMock()
        mock_redis.keys = AsyncMock(return_value=[])
        mock_redis.delete = AsyncMock()

        with patch("packages.core.cache.redis_client", mock_redis):
            await invalidate_cache("nonexistent:*")

        mock_redis.keys.assert_awaited_once()
        mock_redis.delete.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_handles_redis_error_gracefully(self):
        """Redis exceptions during invalidation should be caught."""
        mock_redis = AsyncMock()
        mock_redis.keys = AsyncMock(side_effect=Exception("Redis error"))

        with patch("packages.core.cache.redis_client", mock_redis):
            # Should not raise
            await invalidate_cache("broken:*")

    @pytest.mark.asyncio
    async def test_creates_temp_client_when_no_global_client(self):
        """When redis_client is None, a temporary client should be created."""
        mock_temp_redis = AsyncMock()
        mock_temp_redis.keys = AsyncMock(return_value=["k1"])
        mock_temp_redis.delete = AsyncMock()
        mock_temp_redis.close = AsyncMock()

        # The source does `client = await aioredis.from_url(...)`, so
        # we need from_url to be an AsyncMock that resolves to our client.
        mock_from_url = AsyncMock(return_value=mock_temp_redis)

        with (
            patch("packages.core.cache.redis_client", None),
            patch("packages.core.cache.aioredis.from_url", mock_from_url),
        ):
            await invalidate_cache("pattern:*")

        mock_temp_redis.keys.assert_awaited_once()
        mock_temp_redis.delete.assert_awaited_once_with("k1")
        mock_temp_redis.close.assert_awaited_once()
