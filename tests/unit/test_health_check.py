"""
Unit tests for the /health endpoint's worker-status check.

Regression coverage for a bug where `_check_worker_sync` (a synchronous
Celery `control.inspect()` call) could block the health endpoint for
several seconds per service (DB, Redis, worker) when no Celery worker was
reachable, because Celery's own `timeout=` kwarg does not reliably cap the
round trip over the Redis transport. That stalled /health well past the
compose healthcheck's 10s timeout and, since the call ran synchronously in
an async request handler, blocked every other in-flight request too.

All external services are mocked; no live Postgres/Redis/Celery required.
"""

import asyncio
from unittest.mock import patch

import pytest

from apps.api.app.main import health_check


@pytest.mark.asyncio
async def test_health_check_worker_timeout_does_not_block(monkeypatch):
    """A slow/unreachable Celery broker must not stall the whole health check."""

    def _slow_worker_check(has_redis: bool, is_serverless: bool) -> dict:
        # Simulate the observed real-world behavior: a bare `time.sleep`
        # standing in for Celery's inspect() call taking far longer than
        # any timeout passed to it.
        import time

        time.sleep(5)
        return {"status": "up", "workers": 1, "active_tasks": 0, "message": "ok"}

    async def _fast_ok(*args, **kwargs):
        return {"status": "up", "message": "Connected", "latency_ms": 1.0}, False

    with (
        patch("apps.api.app.main._check_database", side_effect=_fast_ok),
        patch("apps.api.app.main._check_redis", side_effect=_fast_ok),
        patch("apps.api.app.main._check_worker_sync", side_effect=_slow_worker_check),
    ):
        result = await asyncio.wait_for(health_check(), timeout=3.0)

    assert result["services"]["worker"]["status"] == "unknown"
    assert "timed out" in result["services"]["worker"]["error"].lower()
    # A slow worker check is enrichment-only and must never flip overall health.
    assert result["status"] == "healthy"


@pytest.mark.asyncio
async def test_health_check_worker_up_reports_promptly(monkeypatch):
    """When the worker check returns quickly, its real status is surfaced."""

    async def _fast_ok(*args, **kwargs):
        return {"status": "up", "message": "Connected", "latency_ms": 1.0}, False

    def _fast_worker_check(has_redis: bool, is_serverless: bool) -> dict:
        return {
            "status": "up",
            "workers": 2,
            "active_tasks": 0,
            "message": "2 worker(s) connected",
        }

    with (
        patch("apps.api.app.main._check_database", side_effect=_fast_ok),
        patch("apps.api.app.main._check_redis", side_effect=_fast_ok),
        patch("apps.api.app.main._check_worker_sync", side_effect=_fast_worker_check),
    ):
        result = await asyncio.wait_for(health_check(), timeout=1.0)

    assert result["services"]["worker"]["status"] == "up"
    assert result["services"]["worker"]["workers"] == 2
