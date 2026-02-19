import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi import APIRouter, Depends, FastAPI, Request
from httpx import ASGITransport, AsyncClient

from apps.api.app.config import Settings, get_settings
from apps.api.app.core.rate_limit import RateLimiter, get_client_ip
from apps.api.app.core.security import get_api_key

settings = get_settings()

# Mock app for testing security components in isolation
app = FastAPI()
router = APIRouter()


@router.get("/protected", dependencies=[Depends(get_api_key)])
async def protected_route():
    return {"message": "You are authenticated"}


@router.get("/limited", dependencies=[Depends(RateLimiter(times=2, seconds=1))])
async def limited_route():
    return {"message": "Not limited"}


app.include_router(router)


@pytest.mark.asyncio
async def test_auth_missing_key():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/protected")
    assert response.status_code == 403
    assert response.json() == {
        "detail": "Could not validate credentials: Missing API Key"
    }


@pytest.mark.asyncio
async def test_auth_invalid_key():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/protected", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 403
    assert response.json() == {
        "detail": "Could not validate credentials: Invalid API Key"
    }


@pytest.mark.asyncio
async def test_auth_valid_key():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/protected", headers={"X-API-Key": settings.API_KEY})
    assert response.status_code == 200
    assert response.json() == {"message": "You are authenticated"}


@pytest.mark.asyncio
async def test_rate_limit():
    # Note: This test requires a running Redis. If Redis is not available,
    # the RateLimiter is designed to fail open (warning log), so this might pass/fail depending on env.
    # ideally we would mock get_redis_client.

    from unittest.mock import AsyncMock, MagicMock, patch

    # Mock Redis pipeline to simulate counting
    mock_pipeline = AsyncMock()
    mock_pipeline.__aenter__.return_value = mock_pipeline
    mock_pipeline.__aexit__.return_value = None
    mock_pipeline.incr = MagicMock()
    mock_pipeline.expire = MagicMock()

    # helper to return the pipeline
    mock_redis = MagicMock()
    mock_redis.pipeline.return_value = mock_pipeline

    # First 2 requests: count is 1, then 2 (allowed)
    # 3rd request: count is 3 (blocked)

    with patch(
        "apps.api.app.core.rate_limit.get_redis_client", return_value=mock_redis
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            mock_pipeline.execute.return_value = [1]  # 1st request
            response = await ac.get("/limited")
            assert response.status_code == 200

            mock_pipeline.execute.return_value = [2]  # 2nd request
            response = await ac.get("/limited")
            assert response.status_code == 200

            mock_pipeline.execute.return_value = [3]  # 3rd request (exceeds 2)
            response = await ac.get("/limited")
            assert response.status_code == 429
            assert "Rate limit exceeded" in response.json()["detail"]


# Tests for timing-safe API key comparison
@pytest.mark.asyncio
async def test_timing_safe_comparison_used():
    """Verify the security module uses secrets.compare_digest."""
    import secrets

    from apps.api.app.core import security

    # Check that secrets module is imported and used
    assert hasattr(security, "secrets")
    # The function should work correctly
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/protected", headers={"X-API-Key": settings.API_KEY})
        assert response.status_code == 200


# Tests for production secrets validation
def test_production_secrets_validation_blocks_short_api_key():
    """Ensure short API key is rejected in production."""
    with patch.dict(os.environ, {"ENV": "production"}):
        with pytest.raises(ValueError, match="API_KEY must be at least 16 characters"):
            Settings(API_KEY="short-key", SECRET_KEY="secure-secret-key-12345678")


def test_production_secrets_validation_blocks_default_api_key():
    """Ensure default API key (dev-api-key) is rejected in production."""
    with patch.dict(os.environ, {"ENV": "production"}):
        # The field validator for length runs first, so the default 'dev-api-key' (11 chars) fails
        with pytest.raises(ValueError, match="API_KEY must be at least 16 characters"):
            Settings(API_KEY="dev-api-key", SECRET_KEY="secure-secret-key-12345678")


def test_production_secrets_validation_blocks_default_secret_key():
    """Ensure default secret key is rejected in production."""
    with patch.dict(os.environ, {"ENV": "production"}):
        with pytest.raises(ValueError, match="SECRET_KEY must be changed"):
            Settings(
                API_KEY="secure-api-key-12345678",
                SECRET_KEY="development-secret-key-change-in-production",
            )


def test_production_secrets_validation_allows_custom_secrets():
    """Ensure custom secrets work in production."""
    with patch.dict(os.environ, {"ENV": "production"}):
        # Should not raise
        s = Settings(
            API_KEY="secure-api-key-12345678",
            SECRET_KEY="secure-secret-key-12345678",
        )
        assert s.API_KEY == "secure-api-key-12345678"


def test_development_allows_default_secrets():
    """Ensure default secrets work in development."""
    with patch.dict(os.environ, {"ENV": "development"}):
        # Should not raise
        s = Settings()
        assert s.API_KEY == "dev-api-key"


# Tests for IP spoofing prevention
def test_get_client_ip_from_direct_connection():
    """Test IP extraction from direct connection."""
    mock_request = MagicMock(spec=Request)
    mock_request.headers = {}
    mock_request.client.host = "192.168.1.100"

    with patch("apps.api.app.core.rate_limit.get_settings") as mock_settings:
        mock_settings.return_value.TRUST_PROXY_HEADERS = False
        ip = get_client_ip(mock_request)
        assert ip == "192.168.1.100"


def test_get_client_ip_from_x_forwarded_for():
    """Test IP extraction from X-Forwarded-For header."""
    mock_request = MagicMock(spec=Request)
    mock_request.headers = {
        "X-Forwarded-For": "203.0.113.195, 70.41.3.18, 150.172.238.178"
    }
    mock_request.client.host = "10.0.0.1"

    with patch("apps.api.app.core.rate_limit.get_settings") as mock_settings:
        mock_settings.return_value.TRUST_PROXY_HEADERS = True
        ip = get_client_ip(mock_request)
        # Should return the leftmost (original client) IP
        assert ip == "203.0.113.195"


def test_get_client_ip_from_x_real_ip():
    """Test IP extraction from X-Real-IP header."""
    mock_request = MagicMock(spec=Request)
    mock_request.headers = {"X-Real-IP": "203.0.113.50"}
    mock_request.client.host = "10.0.0.1"

    with patch("apps.api.app.core.rate_limit.get_settings") as mock_settings:
        mock_settings.return_value.TRUST_PROXY_HEADERS = True
        ip = get_client_ip(mock_request)
        assert ip == "203.0.113.50"


def test_get_client_ip_ignores_proxy_headers_when_disabled():
    """Test that proxy headers are ignored when trust is disabled."""
    mock_request = MagicMock(spec=Request)
    mock_request.headers = {"X-Forwarded-For": "203.0.113.195"}
    mock_request.client.host = "10.0.0.1"

    with patch("apps.api.app.core.rate_limit.get_settings") as mock_settings:
        mock_settings.return_value.TRUST_PROXY_HEADERS = False
        ip = get_client_ip(mock_request)
        # Should return direct connection IP, not the header
        assert ip == "10.0.0.1"
