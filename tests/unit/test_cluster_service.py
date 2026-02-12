from datetime import UTC
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.services.cluster_service import ClusterService
from packages.core.models import Cluster


@pytest.fixture
def mock_db():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def cluster_service(mock_db):
    return ClusterService(mock_db)


@pytest.mark.asyncio
async def test_get_all_clusters_sorting(cluster_service, mock_db):
    # Mock database result
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = [
        Cluster(id="1", idea_count=10),
        Cluster(id="2", idea_count=5),
    ]
    mock_result.scalar_one.return_value = 2
    mock_db.execute.return_value = mock_result

    result = await cluster_service.get_all_clusters(sort_by="size", order="desc")

    assert len(result["clusters"]) == 2
    assert result["pagination"]["total"] == 2
    # Check if execute was called (verifying query construction implicitly via successful run)
    assert mock_db.execute.called


@pytest.mark.asyncio
async def test_get_cluster_by_id_found(cluster_service, mock_db):
    from datetime import datetime, timezone

    now = datetime.now(UTC)
    mock_cluster = Cluster(
        id="123",
        label="Test Cluster",
        created_at=now,
        updated_at=now,
        idea_count=5,
        avg_sentiment=0.5,
        quality_score=0.8,
        trend_score=0.9,
        keywords=["test"],
        description="A test cluster",
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_cluster
    mock_db.execute.return_value = mock_result

    result = await cluster_service.get_cluster_by_id(
        cluster_id="123", include_evidence=False
    )

    assert result is not None
    assert result["label"] == "Test Cluster"


@pytest.mark.asyncio
async def test_get_cluster_by_id_not_found(cluster_service, mock_db):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    result = await cluster_service.get_cluster_by_id(cluster_id="999")

    assert result is None
