"""
Unit tests for packages/core/services/notion_service.py - NotionService.

Covers field mapping, the idempotency key (Source ID query before create/update),
and the fail-open no-op when the Notion sink is not configured.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import httpx
import pytest

from packages.core.models import Cluster
from packages.core.services.notion_service import NotionService


def _make_cluster(**overrides):
    defaults = {
        "id": uuid4(),
        "label": "Book Reading & Progress Tracking",
        "description": "Cluster of 8 related app ideas",
        "keywords": ["reading", "books", "progress"],
        "idea_count": 8,
        "avg_sentiment": 0.4,
        "quality_score": 0.82,
        "trend_score": 0.6,
    }
    defaults.update(overrides)
    return Cluster(**defaults)


def _make_mock_client(query_results, create_status=200, patch_status=200):
    """Mock httpx.AsyncClient that routes the idempotency query vs create vs update."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)

    async def mock_post(url, **kwargs):
        resp = MagicMock(spec=httpx.Response)
        if url.endswith("/query"):
            resp.status_code = 200
            resp.json.return_value = {"results": query_results}
        else:
            resp.status_code = create_status
            resp.text = "created"
        return resp

    async def mock_patch(url, **kwargs):
        resp = MagicMock(spec=httpx.Response)
        resp.status_code = patch_status
        resp.text = "updated"
        return resp

    mock_client.post = AsyncMock(side_effect=mock_post)
    mock_client.patch = AsyncMock(side_effect=mock_patch)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    return mock_client


@pytest.fixture
def service():
    return NotionService(api_key="test-key", data_source_id="test-ds-id")


class TestFieldMapping:
    def test_build_properties_maps_expected_fields(self, service):
        cluster = _make_cluster()

        properties = service._build_properties(cluster)

        assert properties["Idea"]["title"][0]["text"]["content"] == cluster.label
        assert properties["Context"]["select"]["name"] == "Personal"
        assert properties["Status"]["select"]["name"] == "Idea"
        assert "start" in properties["Date Added"]["date"]
        assert properties["Source ID"]["rich_text"][0]["text"]["content"] == str(
            cluster.id
        )

        notes = properties["Notes"]["rich_text"][0]["text"]["content"]
        assert cluster.description in notes
        assert "Keywords: reading, books, progress" in notes
        assert "[auto-mined by app-idea-miner]" in notes

    def test_build_properties_leaves_curated_fields_untouched(self, service):
        cluster = _make_cluster()

        properties = service._build_properties(cluster)

        for curated_field in (
            "Potential Revenue",
            "Confidence",
            "Complexity",
            "Skill Fit",
            "Stack",
        ):
            assert curated_field not in properties

    def test_build_properties_handles_empty_keywords_and_description(self, service):
        cluster = _make_cluster(keywords=[], description=None)

        properties = service._build_properties(cluster)

        notes = properties["Notes"]["rich_text"][0]["text"]["content"]
        assert "Keywords: \n[auto-mined by app-idea-miner]" in notes


    def test_build_properties_renders_top_competitors_in_notes(self, service):
        cluster = _make_cluster()
        top_competitors = [
            {"name": "notion", "count": 7},
            {"name": "todoist", "count": 3},
        ]

        properties = service._build_properties(cluster, top_competitors)

        notes = properties["Notes"]["rich_text"][0]["text"]["content"]
        assert "Incumbents mentioned: notion (7), todoist (3)" in notes

    def test_build_properties_omits_incumbents_line_when_none(self, service):
        cluster = _make_cluster()

        properties = service._build_properties(cluster, None)

        notes = properties["Notes"]["rich_text"][0]["text"]["content"]
        assert "Incumbents mentioned" not in notes


class TestIdempotency:
    @pytest.mark.asyncio
    async def test_queries_by_source_id_before_writing(self, service):
        cluster = _make_cluster()
        mock_client = _make_mock_client(query_results=[])

        with patch(
            "packages.core.services.notion_service.httpx.AsyncClient",
            return_value=mock_client,
        ):
            await service.push_cluster(cluster)

        query_call = mock_client.post.call_args_list[0]
        assert query_call.args[0] == (
            f"{service.API_BASE}/data_sources/{service.data_source_id}/query"
        )
        query_body = query_call.kwargs["json"]
        assert query_body["filter"]["property"] == "Source ID"
        assert query_body["filter"]["rich_text"]["equals"] == str(cluster.id)

    @pytest.mark.asyncio
    async def test_creates_new_page_when_no_existing_match(self, service):
        cluster = _make_cluster()
        mock_client = _make_mock_client(query_results=[])

        with patch(
            "packages.core.services.notion_service.httpx.AsyncClient",
            return_value=mock_client,
        ):
            result = await service.push_cluster(cluster)

        assert result is True
        mock_client.patch.assert_not_called()
        create_call = mock_client.post.call_args_list[-1]
        assert create_call.args[0] == f"{service.API_BASE}/pages"
        assert create_call.kwargs["json"]["parent"] == {
            "data_source_id": service.data_source_id
        }

    @pytest.mark.asyncio
    async def test_updates_existing_page_when_match_found(self, service):
        cluster = _make_cluster()
        mock_client = _make_mock_client(query_results=[{"id": "existing-page-123"}])

        with patch(
            "packages.core.services.notion_service.httpx.AsyncClient",
            return_value=mock_client,
        ):
            result = await service.push_cluster(cluster)

        assert result is True
        mock_client.patch.assert_called_once()
        patch_call = mock_client.patch.call_args
        assert patch_call.args[0] == f"{service.API_BASE}/pages/existing-page-123"
        mock_client.post.assert_called_once()  # only the idempotency query, no create


class TestNoOp:
    @pytest.mark.asyncio
    async def test_push_cluster_noops_when_not_configured(self):
        service = NotionService(api_key=None, data_source_id=None)
        cluster = _make_cluster()

        with patch(
            "packages.core.services.notion_service.httpx.AsyncClient"
        ) as mock_client_cls:
            result = await service.push_cluster(cluster)

        assert result is False
        mock_client_cls.assert_not_called()

    def test_enabled_false_when_only_api_key_missing(self):
        service = NotionService(api_key=None, data_source_id="test-ds-id")
        assert service.enabled is False

    def test_enabled_false_when_only_data_source_id_missing(self):
        service = NotionService(api_key="test-key", data_source_id=None)
        assert service.enabled is False
