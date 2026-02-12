import pytest
from httpx import AsyncClient

from apps.api.app.config import get_settings
from packages.core.models import Cluster

settings = get_settings()
API_KEY_HEADER = {"X-API-Key": settings.API_KEY}


@pytest.mark.asyncio
async def test_list_clusters_unauthorized(client: AsyncClient):
    """Cluster list should require API key auth."""
    response = await client.get("/api/v1/clusters")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_clusters_search_q_filters_by_label_description_and_keywords(
    client: AsyncClient, db_session
):
    """q filter should search label, description, and keywords."""
    clusters = [
        Cluster(
            label="Budget Planning Toolkit",
            description="Personal finance workflows",
            keywords=["finance", "forecasting"],
            idea_count=5,
            avg_sentiment=0.2,
            quality_score=0.75,
            trend_score=0.35,
        ),
        Cluster(
            label="Team Collaboration Hub",
            description="Shared workspace for planning",
            keywords=["productivity", "budgeting"],
            idea_count=7,
            avg_sentiment=0.4,
            quality_score=0.81,
            trend_score=0.42,
        ),
        Cluster(
            label="Meal Planning Assistant",
            description="Weekly meal prep automation",
            keywords=["health", "nutrition"],
            idea_count=4,
            avg_sentiment=0.1,
            quality_score=0.6,
            trend_score=0.2,
        ),
    ]
    db_session.add_all(clusters)
    await db_session.commit()

    response = await client.get("/api/v1/clusters?q=budget", headers=API_KEY_HEADER)
    assert response.status_code == 200
    payload = response.json()

    labels = {cluster["label"] for cluster in payload["clusters"]}
    assert labels == {"Budget Planning Toolkit", "Team Collaboration Hub"}
    assert payload["pagination"]["total"] == 2


@pytest.mark.asyncio
async def test_list_clusters_search_q_empty_result(client: AsyncClient, db_session):
    """q filter should return empty lists when no matches exist."""
    db_session.add(
        Cluster(
            label="Fitness Tracking",
            description="Workout and progress logs",
            keywords=["health", "exercise"],
            idea_count=3,
            avg_sentiment=0.3,
            quality_score=0.65,
            trend_score=0.22,
        )
    )
    await db_session.commit()

    response = await client.get("/api/v1/clusters?q=astronomy", headers=API_KEY_HEADER)
    assert response.status_code == 200
    payload = response.json()
    assert payload["clusters"] == []
    assert payload["pagination"]["total"] == 0
