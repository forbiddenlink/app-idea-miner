import pytest
from httpx import AsyncClient

from apps.api.app.config import get_settings
from packages.core.models import Cluster, IdeaCandidate, RawPost

settings = get_settings()
API_KEY_HEADER = {"X-API-Key": settings.API_KEY}


@pytest.mark.asyncio
async def test_analytics_summary_unauthorized(client: AsyncClient):
    """Analytics endpoints should require API key auth."""
    response = await client.get("/api/v1/analytics/summary")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_analytics_summary_authorized(client: AsyncClient, db_session):
    """Summary should return expected shape and include seeded records."""
    post = RawPost(
        url="http://analytics.com",
        url_hash="analytics-1",
        title="Analytics Post",
        source="test",
    )
    db_session.add(post)
    await db_session.flush()

    idea = IdeaCandidate(
        raw_post_id=post.id,
        problem_statement="Need better analytics dashboards",
        sentiment="positive",
        sentiment_score=0.6,
        quality_score=0.8,
        domain="productivity",
    )
    db_session.add(idea)

    cluster = Cluster(
        label="Analytics Dashboards",
        description="Users asking for dashboard insights",
        keywords=["analytics", "dashboard"],
        idea_count=1,
        avg_sentiment=0.6,
        quality_score=0.8,
        trend_score=0.4,
    )
    db_session.add(cluster)
    await db_session.commit()

    response = await client.get("/api/v1/analytics/summary", headers=API_KEY_HEADER)
    assert response.status_code == 200

    data = response.json()
    assert "overview" in data
    assert "trending" in data
    assert "top_domains" in data
    assert data["overview"]["total_posts"] >= 1
    assert data["overview"]["total_ideas"] >= 1
    assert data["overview"]["total_clusters"] >= 1


@pytest.mark.asyncio
async def test_analytics_trends_invalid_start_date(client: AsyncClient):
    """Invalid ISO dates should return 400 with a clear validation message."""
    response = await client.get(
        "/api/v1/analytics/trends?start_date=not-a-date",
        headers=API_KEY_HEADER,
    )
    assert response.status_code == 400
    assert "Invalid start_date" in response.json()["detail"]


@pytest.mark.asyncio
async def test_analytics_trends_invalid_relative_start_date(client: AsyncClient):
    """Only -<days>d relative format should be accepted."""
    response = await client.get(
        "/api/v1/analytics/trends?start_date=-30x",
        headers=API_KEY_HEADER,
    )
    assert response.status_code == 400
    assert "Use -<days>d" in response.json()["detail"]


@pytest.mark.asyncio
async def test_analytics_trends_rejects_non_positive_relative_days(client: AsyncClient):
    """Relative day format must have a positive day count."""
    response = await client.get(
        "/api/v1/analytics/trends?start_date=-0d",
        headers=API_KEY_HEADER,
    )
    assert response.status_code == 400
    assert "positive day value" in response.json()["detail"]


@pytest.mark.asyncio
async def test_analytics_trends_start_after_end(client: AsyncClient):
    """start_date must be <= end_date."""
    response = await client.get(
        "/api/v1/analytics/trends?start_date=2025-01-03T00:00:00Z&end_date=2025-01-02T00:00:00Z",
        headers=API_KEY_HEADER,
    )
    assert response.status_code == 400
    assert "start_date must be before or equal to end_date" in response.json()["detail"]


@pytest.mark.asyncio
async def test_analytics_trends_accepts_zulu_iso_dates(client: AsyncClient):
    """ISO dates with Z suffix should be parsed and normalized to UTC."""
    response = await client.get(
        "/api/v1/analytics/trends?metric=ideas&interval=day&start_date=2025-01-01T00:00:00Z&end_date=2025-01-02T00:00:00Z",
        headers=API_KEY_HEADER,
    )
    assert response.status_code == 200

    data = response.json()
    assert data["start_date"].endswith("+00:00")
    assert data["end_date"].endswith("+00:00")
    assert "data_points" in data
