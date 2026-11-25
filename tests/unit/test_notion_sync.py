"""
Unit tests for apps/worker/tasks/notion_sync.py - cluster selection logic.

Tests pure Python selection (quality threshold + top-N cap). No database or
Notion API calls involved.
"""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from apps.worker.tasks.notion_sync import (
    DEFAULT_NOTION_MIN_QUALITY,
    MAX_CLUSTERS_TO_SYNC,
    _push_clusters_to_notion_async,
    select_clusters_for_notion,
)
from packages.core.models import Cluster


def _cluster(quality_score):
    return Cluster(id=uuid4(), label="x", keywords=[], quality_score=quality_score)


class TestSelectClustersForNotion:
    def test_filters_out_clusters_below_min_quality(self):
        clusters = [_cluster(0.9), _cluster(0.4), _cluster(0.61)]

        selected = select_clusters_for_notion(clusters, min_quality=0.6)

        assert len(selected) == 2
        assert all(c.quality_score >= 0.6 for c in selected)

    def test_caps_at_limit_even_when_all_qualify(self):
        clusters = [_cluster(0.9 - i * 0.01) for i in range(15)]

        selected = select_clusters_for_notion(clusters, min_quality=0.0, limit=10)

        assert len(selected) == 10

    def test_sorts_by_quality_score_descending(self):
        clusters = [_cluster(0.6), _cluster(0.95), _cluster(0.7)]

        selected = select_clusters_for_notion(clusters, min_quality=0.0)

        scores = [c.quality_score for c in selected]
        assert scores == sorted(scores, reverse=True)

    def test_none_quality_score_treated_as_zero(self):
        clusters = [_cluster(None), _cluster(0.7)]

        selected = select_clusters_for_notion(clusters, min_quality=0.5)

        assert len(selected) == 1
        assert selected[0].quality_score == 0.7

    def test_empty_input_returns_empty_list(self):
        assert select_clusters_for_notion([], min_quality=0.6) == []

    def test_defaults_match_spec(self):
        """0.6 quality threshold default, top-10 cap - both env/spec-configurable."""
        assert DEFAULT_NOTION_MIN_QUALITY == 0.6
        assert MAX_CLUSTERS_TO_SYNC == 10


class TestBlankMinQualityEnv:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("raw", ["", "   "])
    async def test_blank_min_quality_env_falls_back_to_default(self, monkeypatch, raw):
        # GitHub Actions passes an unset secret as an empty string, not an absent var.
        monkeypatch.setenv("NOTION_MIN_QUALITY", raw)
        mock_notion = MagicMock()
        mock_notion.enabled = False

        with patch(
            "apps.worker.tasks.notion_sync.NotionService", return_value=mock_notion
        ):
            result = await _push_clusters_to_notion_async()

        assert result["skipped"] is True


class TestNotionSyncInsideRunningLoop:
    """Regression: the CI cron runs Celery eagerly, so clustering (already inside an
    event loop) chains the Notion sync inline. The sync Celery task opens its own
    loop, which raised 'Cannot run the event loop while another loop is running'."""

    @pytest.fixture
    def eager_celery(self):
        from apps.worker.celery_app import celery_app

        keys = ("task_always_eager", "task_eager_propagates")
        before = {k: celery_app.conf[k] for k in keys}
        celery_app.conf.update(task_always_eager=True, task_eager_propagates=True)
        yield
        celery_app.conf.update(**before)

    async def test_schedule_runs_inline_and_skips_when_unconfigured(
        self, eager_celery, monkeypatch, caplog
    ):
        from apps.worker.tasks.notion_sync import schedule_notion_sync

        monkeypatch.delenv("NOTION_API_KEY", raising=False)
        monkeypatch.delenv("NOTION_IDEAS_DB_ID", raising=False)

        with caplog.at_level("INFO"):
            result = await schedule_notion_sync()

        assert result is not None
        assert result["skipped"] is True
        assert result["pushed"] == 0
        assert "Notion sink not configured" in caplog.text

    async def test_schedule_uses_delay_when_not_eager(self, monkeypatch):
        from apps.worker.celery_app import celery_app
        from apps.worker.tasks import notion_sync

        monkeypatch.setitem(celery_app.conf, "task_always_eager", False)
        with patch.object(notion_sync.push_clusters_to_notion, "delay") as delay:
            result = await notion_sync.schedule_notion_sync()

        delay.assert_called_once_with()
        assert result is None
