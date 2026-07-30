"""
Unit tests for apps/worker/tasks/weekly_digest.py - the weekly top-ideas digest.

Covers pure ranking/formatting logic (no DB/Notion involved) plus the async
task with the DB session and NotionService mocked, matching the mocking
style in tests/unit/test_notion_service.py (AsyncMock/MagicMock/patch).
"""

from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from apps.worker.tasks.weekly_digest import (
    DEFAULT_WEEKLY_DIGEST_SIZE,
    _generate_weekly_digest_async,
    build_digest_description,
    build_digest_record,
    build_digest_source_id,
    build_digest_title,
    compute_digest_score,
    rank_clusters_for_digest,
    week_start,
)
from packages.core.models import Cluster


def _cluster(quality_score=0.0, trend_score=0.0, idea_count=0, **overrides):
    defaults = {
        "id": uuid4(),
        "label": "x",
        "description": "desc",
        "keywords": ["a", "b"],
        "quality_score": quality_score,
        "trend_score": trend_score,
        "idea_count": idea_count,
    }
    defaults.update(overrides)
    return Cluster(**defaults)


class TestComputeDigestScore:
    def test_sums_the_three_components(self):
        c = _cluster(quality_score=0.5, trend_score=0.3, idea_count=10)
        assert compute_digest_score(c) == pytest.approx(10.8)

    def test_none_fields_treated_as_zero(self):
        c = _cluster(quality_score=None, trend_score=None, idea_count=None)
        assert compute_digest_score(c) == 0


class TestRankClustersForDigest:
    def test_picks_correct_top_n_in_right_order(self):
        low = _cluster(quality_score=0.1, trend_score=0.1, idea_count=1, label="low")
        mid = _cluster(quality_score=0.5, trend_score=0.2, idea_count=5, label="mid")
        high = _cluster(
            quality_score=0.9, trend_score=0.5, idea_count=20, label="high"
        )

        ranked = rank_clusters_for_digest([low, mid, high], top_n=2)

        assert [c.label for c in ranked] == ["high", "mid"]

    def test_respects_default_top_n(self):
        clusters = [
            _cluster(idea_count=i, label=f"c{i}") for i in range(DEFAULT_WEEKLY_DIGEST_SIZE + 5)
        ]

        ranked = rank_clusters_for_digest(clusters)

        assert len(ranked) == DEFAULT_WEEKLY_DIGEST_SIZE

    def test_empty_input_returns_empty_list(self):
        assert rank_clusters_for_digest([]) == []


class TestWeekStart:
    def test_wednesday_resolves_to_that_weeks_monday(self):
        wednesday = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)  # Wed
        assert week_start(wednesday) == date(2026, 7, 27)  # Mon

    def test_monday_resolves_to_itself(self):
        monday = datetime(2026, 7, 27, 3, 0, tzinfo=UTC)
        assert week_start(monday) == date(2026, 7, 27)

    def test_sunday_resolves_to_preceding_monday(self):
        sunday = datetime(2026, 8, 2, 23, 0, tzinfo=UTC)
        assert week_start(sunday) == date(2026, 7, 27)


class TestDigestTitleAndSourceId:
    def test_title_format(self):
        assert build_digest_title(date(2026, 7, 27)) == "Idea Digest — 2026-07-27"

    def test_source_id_is_dated_and_stable_for_idempotency(self):
        anchor = date(2026, 7, 27)
        assert build_digest_source_id(anchor) == "weekly-digest-2026-07-27"
        # Same anchor -> same key (idempotent per week)
        assert build_digest_source_id(anchor) == build_digest_source_id(anchor)


class TestBuildDigestDescription:
    def test_empty_list(self):
        assert build_digest_description([]) == "No qualifying clusters this week."

    def test_includes_label_count_trend_and_keywords(self):
        c = _cluster(
            idea_count=8,
            trend_score=0.6,
            label="Book Reading",
            keywords=["reading", "books"],
        )

        text = build_digest_description([c])

        assert "1. Book Reading" in text
        assert "8 ideas" in text
        assert "0.60" in text
        assert "reading, books" in text


class TestBuildDigestRecord:
    def test_record_has_expected_shape_for_notion_service(self):
        anchor = date(2026, 7, 27)
        c = _cluster(label="Book Reading", idea_count=8)

        record = build_digest_record([c], anchor)

        assert record.id == "weekly-digest-2026-07-27"
        assert record.label == "Idea Digest — 2026-07-27"
        assert "Book Reading" in record.description
        assert record.keywords == []


# ---------------------------------------------------------------------------
# Async task - DB session + NotionService mocked
# ---------------------------------------------------------------------------


def _make_session_factory(clusters):
    """Mock AsyncSessionLocal() -> async context manager yielding a session
    whose .execute(...).scalars().all() returns `clusters`."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = clusters

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    return MagicMock(return_value=mock_session)


class TestGenerateWeeklyDigestAsync:
    @pytest.mark.asyncio
    async def test_skips_when_notion_not_enabled(self):
        mock_notion = MagicMock()
        mock_notion.enabled = False
        mock_notion.push_cluster = AsyncMock()

        with (
            patch(
                "apps.worker.tasks.weekly_digest.NotionService",
                return_value=mock_notion,
            ),
            patch(
                "apps.worker.tasks.weekly_digest.AsyncSessionLocal",
                _make_session_factory([]),
            ) as mock_session_factory,
        ):
            result = await _generate_weekly_digest_async()

        assert result == {
            "skipped": True,
            "reason": "NOTION_API_KEY/NOTION_IDEAS_DB_ID not set",
            "pushed": False,
        }
        mock_notion.push_cluster.assert_not_called()
        mock_session_factory.assert_not_called()

    @pytest.mark.asyncio
    async def test_pushes_ranked_digest_when_notion_enabled(self):
        clusters = [
            _cluster(quality_score=0.9, trend_score=0.5, idea_count=20, label="high"),
            _cluster(quality_score=0.1, trend_score=0.1, idea_count=1, label="low"),
        ]

        mock_notion = MagicMock()
        mock_notion.enabled = True
        mock_notion.push_cluster = AsyncMock(return_value=True)

        with (
            patch(
                "apps.worker.tasks.weekly_digest.NotionService",
                return_value=mock_notion,
            ),
            patch(
                "apps.worker.tasks.weekly_digest.AsyncSessionLocal",
                _make_session_factory(clusters),
            ),
        ):
            result = await _generate_weekly_digest_async()

        assert result["skipped"] is False
        assert result["pushed"] is True
        assert result["clusters_considered"] == 2
        assert result["clusters_in_digest"] == 2
        assert result["digest_title"].startswith("Idea Digest — ")
        assert result["source_id"].startswith("weekly-digest-")

        mock_notion.push_cluster.assert_called_once()
        pushed_record = mock_notion.push_cluster.call_args.args[0]
        assert "high" in pushed_record.description
        assert "low" in pushed_record.description
