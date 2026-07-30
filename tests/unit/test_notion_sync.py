"""
Unit tests for apps/worker/tasks/notion_sync.py - cluster selection logic.

Tests pure Python selection (quality threshold + top-N cap). No database or
Notion API calls involved.
"""

from uuid import uuid4

from apps.worker.tasks.notion_sync import (
    DEFAULT_NOTION_MIN_QUALITY,
    MAX_CLUSTERS_TO_SYNC,
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
