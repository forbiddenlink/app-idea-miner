from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.services.idea_service import IdeaService
from packages.core.models import IdeaCandidate


@pytest.fixture
def mock_db():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def idea_service(mock_db):
    return IdeaService(mock_db)


@pytest.mark.asyncio
async def test_get_ideas_filtering(idea_service, mock_db):
    # Mock database result
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = [
        IdeaCandidate(id="1", domain="tech", sentiment="positive"),
        IdeaCandidate(id="2", domain="tech", sentiment="positive"),
    ]
    mock_result.scalar_one.return_value = 2
    mock_db.execute.return_value = mock_result

    result = await idea_service.get_ideas(domain="tech", sentiment="positive")

    assert len(result["ideas"]) == 2
    assert result["ideas"][0].domain == "tech"
    # Verify execute was called multiple times (count + select)
    assert mock_db.execute.call_count >= 2


@pytest.mark.asyncio
async def test_get_idea_by_id_found(idea_service, mock_db):
    mock_idea = IdeaCandidate(id="123", problem_statement="Test Problem")
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_idea
    mock_db.execute.return_value = mock_result

    result = await idea_service.get_idea_by_id(idea_id="123")

    assert result is not None
    assert result.problem_statement == "Test Problem"


@pytest.mark.asyncio
async def test_get_ideas_stats(idea_service, mock_db):
    # Setup mocks for 4 sequential queries: total, domain, sentiment, avg_quality
    # We need to configure side_effect for execute to return different mocks each time

    mock_total = MagicMock()
    mock_total.scalar_one.return_value = 100

    mock_domain = MagicMock()
    mock_domain.fetchall.return_value = [
        MagicMock(domain="tech", count=50),
        MagicMock(domain="health", count=50),
    ]

    mock_sentiment = MagicMock()
    mock_sentiment.fetchall.return_value = [
        MagicMock(sentiment="positive", count=80),
        MagicMock(sentiment="negative", count=20),
    ]

    mock_quality = MagicMock()
    mock_quality.scalar_one.return_value = 0.75

    mock_db.execute.side_effect = [
        mock_total,
        mock_domain,
        mock_sentiment,
        mock_quality,
    ]

    result = await idea_service.get_ideas_stats()

    assert result["total"] == 100
    assert result["avg_quality_score"] == 0.75
    assert result["by_domain"]["tech"] == 50
    assert result["by_sentiment"]["positive"] == 80
