"""
Unit tests for apps/worker/sources/appstore.py.

Tests the keyless iTunes RSS customer-reviews source with a mocked httpx
client. No network requests or API keys required.
"""

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from apps.worker.sources.appstore import PAIN_POINT_KEYWORDS, AppStoreSource
from packages.core.models import RawPost

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _label(value):
    return {"label": value}


def _make_review_entry(
    review_id="https://itunes.apple.com/us/review?id=1001",
    title="Wish it had dark mode",
    content="I really wish this app supported dark mode, it hurts my eyes.",
    author="jdoe",
    rating="2",
    version="3.4.1",
    updated="2025-06-15T12:00:00-07:00",
):
    """Build a raw iTunes customer-reviews JSON feed entry."""
    return {
        "id": _label(review_id),
        "title": _label(title),
        "content": _label(content),
        "author": {"name": _label(author), "uri": _label("https://x/id" + author)},
        "im:rating": _label(rating),
        "im:version": _label(version),
        "updated": _label(updated),
    }


def _make_app_metadata_entry():
    """The feed's first entry is app metadata — no author/rating."""
    return {
        "im:name": _label("Some App"),
        "im:image": [],
        "id": _label("https://itunes.apple.com/us/app/some-app/id123"),
    }


def _make_feed(entries):
    return {"feed": {"entry": entries}}


def _mock_client(get_side_effect):
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get = AsyncMock(side_effect=get_side_effect)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    return mock_client


def _json_response(payload):
    resp = MagicMock(spec=httpx.Response)
    resp.raise_for_status = MagicMock()
    resp.json.return_value = payload
    return resp


# ---------------------------------------------------------------------------
# PAIN_POINT_KEYWORDS
# ---------------------------------------------------------------------------


class TestPainPointKeywords:
    @pytest.mark.parametrize(
        "text",
        [
            "I wish this had dark mode",
            "This app needs offline support",
            "It should really export to CSV",
            "I want a widget for this",
            "There's a missing feature here",
            "So frustrating that sync fails",
        ],
    )
    def test_matches_pain_point_language(self, text):
        assert PAIN_POINT_KEYWORDS.search(text)

    def test_no_match_on_generic_praise(self):
        assert PAIN_POINT_KEYWORDS.search("Love this app, five stars!") is None


# ---------------------------------------------------------------------------
# Config / mock-mode integrity
# ---------------------------------------------------------------------------


class TestAppStoreMockMode:
    """Mock mode must be loud + tagged so fabricated data never masquerades
    as real App Store data."""

    def _clear_config(self, monkeypatch):
        monkeypatch.delenv("APPSTORE_APP_IDS", raising=False)
        monkeypatch.delenv("APPSTORE_COUNTRY", raising=False)

    def test_missing_app_ids_sets_mock_true(self, monkeypatch):
        self._clear_config(monkeypatch)
        source = AppStoreSource()
        assert source.is_mock is True

    def test_missing_app_ids_logs_at_error_level(self, monkeypatch, caplog):
        self._clear_config(monkeypatch)
        with caplog.at_level(logging.ERROR, logger="apps.worker.sources.appstore"):
            AppStoreSource()
        assert any(
            r.levelno >= logging.ERROR and "MOCK" in r.message.upper()
            for r in caplog.records
        ), "expected a loud ERROR-level MOCK warning"

    @pytest.mark.asyncio
    async def test_mock_posts_are_tagged(self, monkeypatch):
        self._clear_config(monkeypatch)
        source = AppStoreSource()
        posts = await source.fetch()
        assert posts, "mock fetch should return at least one post"
        assert all(
            p.source_metadata.get("mock") is True for p in posts
        ), "mock posts must be tagged source_metadata[mock]=True"
        assert all(p.source == "appstore" for p in posts)

    def test_configured_app_ids_disables_mock(self, monkeypatch):
        monkeypatch.setenv("APPSTORE_APP_IDS", "12345,67890")
        source = AppStoreSource()
        assert source.is_mock is False
        assert source.app_ids == ["12345", "67890"]

    def test_default_country_is_us(self, monkeypatch):
        monkeypatch.setenv("APPSTORE_APP_IDS", "12345")
        monkeypatch.delenv("APPSTORE_COUNTRY", raising=False)
        source = AppStoreSource()
        assert source.country == "us"

    def test_custom_country_is_read(self, monkeypatch):
        monkeypatch.setenv("APPSTORE_APP_IDS", "12345")
        monkeypatch.setenv("APPSTORE_COUNTRY", "gb")
        source = AppStoreSource()
        assert source.country == "gb"


# ---------------------------------------------------------------------------
# _to_raw_post
# ---------------------------------------------------------------------------


class TestToRawPost:
    def test_converts_entry_to_raw_post(self, monkeypatch):
        monkeypatch.setenv("APPSTORE_APP_IDS", "555")
        source = AppStoreSource()
        entry = _make_review_entry()

        post = source._to_raw_post(entry, "555")

        assert isinstance(post, RawPost)
        assert post.source == "appstore"
        assert post.title == "Wish it had dark mode"
        assert "dark mode" in post.content
        assert post.author == "jdoe"
        assert post.url == "https://itunes.apple.com/us/review?id=1001"
        assert len(post.url_hash) == 64
        assert post.source_metadata["rating"] == 2
        assert post.source_metadata["appId"] == "555"
        assert post.source_metadata["country"] == "us"
        assert post.source_metadata["version"] == "3.4.1"
        assert "mock" not in post.source_metadata

    def test_no_mock_tag_on_real_reviews(self, monkeypatch):
        monkeypatch.setenv("APPSTORE_APP_IDS", "555")
        source = AppStoreSource()
        post = source._to_raw_post(_make_review_entry(), "555")
        assert post.source_metadata.get("mock") is not True

    def test_skips_app_metadata_entry(self, monkeypatch):
        monkeypatch.setenv("APPSTORE_APP_IDS", "555")
        source = AppStoreSource()
        assert source._to_raw_post(_make_app_metadata_entry(), "555") is None

    def test_filters_out_non_pain_point_reviews(self, monkeypatch):
        monkeypatch.setenv("APPSTORE_APP_IDS", "555")
        source = AppStoreSource()
        entry = _make_review_entry(
            title="Great app", content="Love it, works perfectly every day."
        )
        assert source._to_raw_post(entry, "555") is None

    def test_keeps_pain_point_reviews(self, monkeypatch):
        monkeypatch.setenv("APPSTORE_APP_IDS", "555")
        source = AppStoreSource()
        entry = _make_review_entry(
            title="Needs a widget", content="This app needs a home screen widget."
        )
        assert source._to_raw_post(entry, "555") is not None

    def test_missing_rating_returns_none(self, monkeypatch):
        monkeypatch.setenv("APPSTORE_APP_IDS", "555")
        source = AppStoreSource()
        entry = _make_review_entry()
        entry["im:rating"] = _label("")
        assert source._to_raw_post(entry, "555") is None

    def test_missing_author_returns_none(self, monkeypatch):
        monkeypatch.setenv("APPSTORE_APP_IDS", "555")
        source = AppStoreSource()
        entry = _make_review_entry()
        entry["author"] = {}
        assert source._to_raw_post(entry, "555") is None

    def test_invalid_updated_timestamp_falls_back_to_none(self, monkeypatch):
        monkeypatch.setenv("APPSTORE_APP_IDS", "555")
        source = AppStoreSource()
        entry = _make_review_entry(updated="not-a-date")
        post = source._to_raw_post(entry, "555")
        assert post is not None
        assert post.published_at is None


# ---------------------------------------------------------------------------
# fetch()
# ---------------------------------------------------------------------------


class TestAppStoreFetch:
    @pytest.mark.asyncio
    async def test_fetch_returns_raw_posts_for_real_reviews(self, monkeypatch):
        monkeypatch.setenv("APPSTORE_APP_IDS", "111")
        source = AppStoreSource()

        feed = _make_feed(
            [
                _make_app_metadata_entry(),
                _make_review_entry(
                    review_id="https://itunes.apple.com/us/review?id=1",
                    title="Wish it synced",
                    content="I wish this app would sync across devices.",
                ),
                _make_review_entry(
                    review_id="https://itunes.apple.com/us/review?id=2",
                    title="Perfect",
                    content="No notes, love it.",
                ),
            ]
        )

        async def mock_get(url, **kwargs):
            return _json_response(feed)

        mock_client = _mock_client(mock_get)

        with patch(
            "apps.worker.sources.appstore.httpx.AsyncClient",
            return_value=mock_client,
        ):
            posts = await source.fetch()

        # App metadata entry skipped, "Perfect" review filtered (no pain-point
        # keyword), only the "wish it synced" review survives.
        assert len(posts) == 1
        assert all(isinstance(p, RawPost) for p in posts)
        assert posts[0].title == "Wish it synced"
        assert posts[0].source_metadata.get("mock") is not True

    @pytest.mark.asyncio
    async def test_fetch_handles_single_entry_collapsed_to_dict(self, monkeypatch):
        """Apple's JSON feed collapses a single entry into a dict, not a list."""
        monkeypatch.setenv("APPSTORE_APP_IDS", "222")
        source = AppStoreSource()

        feed = {
            "feed": {
                "entry": _make_review_entry(
                    title="Needs export", content="This app needs a CSV export."
                )
            }
        }

        async def mock_get(url, **kwargs):
            return _json_response(feed)

        mock_client = _mock_client(mock_get)

        with patch(
            "apps.worker.sources.appstore.httpx.AsyncClient",
            return_value=mock_client,
        ):
            posts = await source.fetch()

        assert len(posts) == 1
        assert posts[0].title == "Needs export"

    @pytest.mark.asyncio
    async def test_fetch_handles_empty_feed(self, monkeypatch):
        monkeypatch.setenv("APPSTORE_APP_IDS", "333")
        source = AppStoreSource()

        async def mock_get(url, **kwargs):
            return _json_response({"feed": {}})

        mock_client = _mock_client(mock_get)

        with patch(
            "apps.worker.sources.appstore.httpx.AsyncClient",
            return_value=mock_client,
        ):
            posts = await source.fetch()

        assert posts == []

    @pytest.mark.asyncio
    async def test_fetch_handles_malformed_json_gracefully(self, monkeypatch):
        monkeypatch.setenv("APPSTORE_APP_IDS", "444")
        source = AppStoreSource()

        async def mock_get(url, **kwargs):
            resp = MagicMock(spec=httpx.Response)
            resp.raise_for_status = MagicMock()
            resp.json.side_effect = ValueError("not json")
            return resp

        mock_client = _mock_client(mock_get)

        with patch(
            "apps.worker.sources.appstore.httpx.AsyncClient",
            return_value=mock_client,
        ):
            posts = await source.fetch()

        assert posts == []

    @pytest.mark.asyncio
    async def test_fetch_handles_network_error_gracefully(self, monkeypatch):
        monkeypatch.setenv("APPSTORE_APP_IDS", "555")
        source = AppStoreSource()

        async def mock_get(url, **kwargs):
            raise httpx.ConnectError("Connection refused")

        mock_client = _mock_client(mock_get)

        with patch(
            "apps.worker.sources.appstore.httpx.AsyncClient",
            return_value=mock_client,
        ):
            posts = await source.fetch()

        assert posts == []

    @pytest.mark.asyncio
    async def test_fetch_continues_after_one_app_id_fails(self, monkeypatch):
        """A failure fetching one app's reviews shouldn't block the others."""
        monkeypatch.setenv("APPSTORE_APP_IDS", "666,777")
        source = AppStoreSource()

        good_feed = _make_feed(
            [
                _make_review_entry(
                    review_id="https://itunes.apple.com/us/review?id=9",
                    title="Wish it had widgets",
                    content="I wish it had home screen widgets.",
                )
            ]
        )

        async def mock_get(url, **kwargs):
            if "id=666" in url:
                raise httpx.ReadTimeout("timeout")
            return _json_response(good_feed)

        mock_client = _mock_client(mock_get)

        with patch(
            "apps.worker.sources.appstore.httpx.AsyncClient",
            return_value=mock_client,
        ):
            posts = await source.fetch()

        assert len(posts) == 1
        assert posts[0].source_metadata["appId"] == "777"

    @pytest.mark.asyncio
    async def test_fetch_uses_configured_country_in_url(self, monkeypatch):
        monkeypatch.setenv("APPSTORE_APP_IDS", "888")
        monkeypatch.setenv("APPSTORE_COUNTRY", "de")
        source = AppStoreSource()

        called_urls = []

        async def mock_get(url, **kwargs):
            called_urls.append(url)
            return _json_response(_make_feed([]))

        mock_client = _mock_client(mock_get)

        with patch(
            "apps.worker.sources.appstore.httpx.AsyncClient",
            return_value=mock_client,
        ):
            await source.fetch()

        assert called_urls
        assert "/de/rss/customerreviews/id=888/sortBy=mostRecent/json" in called_urls[0]
