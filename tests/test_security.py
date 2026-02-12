import pytest
from fastapi import APIRouter, Depends, FastAPI
from httpx import ASGITransport, AsyncClient

from apps.api.app.config import get_settings
from apps.api.app.core.rate_limit import RateLimiter
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
