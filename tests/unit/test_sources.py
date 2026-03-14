"""
Unit tests for apps/worker/sources/rss.py and apps/worker/sources/hackernews.py.

Tests RSS feed parsing and HackerNews API fetching with mocked external APIs.
No network requests or external services required.
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from apps.worker.sources.hackernews import (
    IDEA_KEYWORDS,
    HackerNewsSource,
    _strip_html,
)
from apps.worker.sources.rss import RSSSource
from packages.core.models import RawPost

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_feed_entry(
    link="https://example.com/post/1",
    title="I wish there was an app for that",
    summary="Great idea for a new tool",
    author="testuser",
    published_parsed=(2025, 6, 15, 12, 0, 0, 0, 0, 0),
    tags=None,
):
    """Create a mock feedparser entry with configurable fields."""
    entry = MagicMock()
    entry.get = lambda k, default="": {
        "link": link,
        "title": title,
        "summary": summary,
        "description": summary,
        "author": author,
    }.get(k, default)
    entry.published_parsed = published_parsed
    if tags is not None:
        entry.get = lambda k, default="": {  # noqa: E731
            "link": link,
            "title": title,
            "summary": summary,
            "description": summary,
            "author": author,
            "tags": tags,
        }.get(k, default)
    else:
        # Override get for tags to return empty list
        _orig_get = entry.get

        def _get_with_tags(k, default=""):
            if k == "tags":
                return []
            return {
                "link": link,
                "title": title,
                "summary": summary,
                "description": summary,
                "author": author,
            }.get(k, default)

        entry.get = _get_with_tags
    return entry


def _make_feed(entries, feed_title="Test Feed", bozo=False, bozo_exception=None):
    """Create a mock feedparser result."""
    feed = MagicMock()
    feed.entries = entries
    feed.bozo = bozo
    feed.bozo_exception = bozo_exception
    feed.feed = MagicMock()
    feed.feed.get = lambda k, default="": {"title": feed_title}.get(k, default)
    return feed


def _make_hn_item(
    item_id=12345,
    title="Show HN: I built a tool for tracking habits",
    text="<p>Check out my new app</p>",
    by="hnuser",
    score=42,
    descendants=10,
    time_=1718400000,
):
    """Create an HN API item dict."""
    return {
        "id": item_id,
        "title": title,
        "text": text,
        "by": by,
        "score": score,
        "descendants": descendants,
        "time": time_,
    }


# ---------------------------------------------------------------------------
# RSSSource — _extract_source_from_feed_url
# ---------------------------------------------------------------------------


class TestRSSSourceExtractSource:
    def test_hackernews_hnrss(self):
        source = RSSSource()
        assert (
            source._extract_source_from_feed_url("https://hnrss.org/newest")
            == "hackernews"
        )

    def test_hackernews_official(self):
        source = RSSSource()
        assert (
            source._extract_source_from_feed_url("https://news.ycombinator.com/rss")
            == "hackernews"
        )

    def test_reddit(self):
        source = RSSSource()
        assert (
            source._extract_source_from_feed_url(
                "https://www.reddit.com/r/AppIdeas/.rss"
            )
            == "reddit"
        )

    def test_producthunt(self):
        source = RSSSource()
        assert (
            source._extract_source_from_feed_url("https://www.producthunt.com/feed")
            == "producthunt"
        )

    def test_generic_rss(self):
        source = RSSSource()
        assert (
            source._extract_source_from_feed_url("https://blog.example.com/rss.xml")
            == "rss_feed"
        )


# ---------------------------------------------------------------------------
# RSSSource — fetch()
# ---------------------------------------------------------------------------


class TestRSSSourceFetch:
    @pytest.mark.asyncio
    async def test_fetch_returns_raw_posts(self):
        """fetch() returns a list of RawPost objects from parsed feed entries."""
        entries = [
            _make_feed_entry(link="https://example.com/1", title="Idea one"),
            _make_feed_entry(link="https://example.com/2", title="Idea two"),
        ]
        feed = _make_feed(entries, feed_title="My RSS Feed")

        source = RSSSource()
        with patch.dict("os.environ", {"RSS_FEEDS": "https://blog.example.com/rss"}):
            with patch("apps.worker.sources.rss.asyncio.to_thread", return_value=feed):
                posts = await source.fetch()

        assert len(posts) == 2
        assert all(isinstance(p, RawPost) for p in posts)
        assert posts[0].title == "Idea one"
        assert posts[1].title == "Idea two"

    @pytest.mark.asyncio
    async def test_fetch_generates_url_hash(self):
        """Each post should have a non-empty url_hash."""
        entries = [_make_feed_entry(link="https://example.com/42", title="Some idea")]
        feed = _make_feed(entries)

        source = RSSSource()
        with patch.dict("os.environ", {"RSS_FEEDS": "https://feed.example.com/rss"}):
            with patch("apps.worker.sources.rss.asyncio.to_thread", return_value=feed):
                posts = await source.fetch()

        assert len(posts) == 1
        assert posts[0].url_hash
        assert len(posts[0].url_hash) == 64  # SHA-256 hex digest

    @pytest.mark.asyncio
    async def test_fetch_metadata_includes_feed_info(self):
        """source_metadata should contain feed_url, feed_title, and tags."""
        tag_mock = MagicMock()
        tag_mock.term = "python"
        entries = [
            _make_feed_entry(
                link="https://example.com/99", title="Tagged post", tags=[tag_mock]
            )
        ]
        feed = _make_feed(entries, feed_title="Tech Feed")

        source = RSSSource()
        with patch.dict("os.environ", {"RSS_FEEDS": "https://tech.example.com/feed"}):
            with patch("apps.worker.sources.rss.asyncio.to_thread", return_value=feed):
                posts = await source.fetch()

        assert len(posts) == 1
        meta = posts[0].source_metadata
        assert meta["feed_url"] == "https://tech.example.com/feed"
        assert meta["feed_title"] == "Tech Feed"
        assert "python" in meta["tags"]

    @pytest.mark.asyncio
    async def test_fetch_empty_feed_returns_empty_list(self):
        """An RSS feed with no entries should produce an empty list."""
        feed = _make_feed(entries=[], feed_title="Empty Feed")

        source = RSSSource()
        with patch.dict("os.environ", {"RSS_FEEDS": "https://empty.example.com/rss"}):
            with patch("apps.worker.sources.rss.asyncio.to_thread", return_value=feed):
                posts = await source.fetch()

        assert posts == []

    @pytest.mark.asyncio
    async def test_fetch_skips_entries_missing_url(self):
        """Entries without a url (link) should be skipped."""
        entries = [
            _make_feed_entry(link="", title="No URL entry"),
            _make_feed_entry(link="https://example.com/ok", title="Has URL"),
        ]
        feed = _make_feed(entries)

        source = RSSSource()
        with patch.dict("os.environ", {"RSS_FEEDS": "https://feed.example.com/rss"}):
            with patch("apps.worker.sources.rss.asyncio.to_thread", return_value=feed):
                posts = await source.fetch()

        assert len(posts) == 1
        assert posts[0].title == "Has URL"

    @pytest.mark.asyncio
    async def test_fetch_skips_entries_missing_title(self):
        """Entries without a title should be skipped."""
        entries = [
            _make_feed_entry(link="https://example.com/notitle", title=""),
            _make_feed_entry(link="https://example.com/ok", title="Valid Title"),
        ]
        feed = _make_feed(entries)

        source = RSSSource()
        with patch.dict("os.environ", {"RSS_FEEDS": "https://feed.example.com/rss"}):
            with patch("apps.worker.sources.rss.asyncio.to_thread", return_value=feed):
                posts = await source.fetch()

        assert len(posts) == 1
        assert posts[0].title == "Valid Title"

    @pytest.mark.asyncio
    async def test_fetch_sets_source_from_feed_url(self):
        """The source field should reflect the feed type."""
        entries = [_make_feed_entry(link="https://example.com/1", title="HN idea")]
        feed = _make_feed(entries)

        source = RSSSource()
        with patch.dict("os.environ", {"RSS_FEEDS": "https://hnrss.org/newest"}):
            with patch("apps.worker.sources.rss.asyncio.to_thread", return_value=feed):
                posts = await source.fetch()

        assert posts[0].source == "hackernews"

    @pytest.mark.asyncio
    async def test_fetch_handles_feed_error_gracefully(self):
        """If feedparser raises, fetch() should continue and return empty list."""
        source = RSSSource()
        with patch.dict("os.environ", {"RSS_FEEDS": "https://broken.example.com/rss"}):
            with patch(
                "apps.worker.sources.rss.asyncio.to_thread",
                side_effect=Exception("Connection refused"),
            ):
                posts = await source.fetch()

        assert posts == []

    @pytest.mark.asyncio
    async def test_fetch_multiple_feeds(self):
        """fetch() should combine posts from multiple comma-separated feeds."""
        entries_a = [_make_feed_entry(link="https://a.com/1", title="Feed A post")]
        entries_b = [_make_feed_entry(link="https://b.com/1", title="Feed B post")]
        feed_a = _make_feed(entries_a, feed_title="Feed A")
        feed_b = _make_feed(entries_b, feed_title="Feed B")

        call_count = 0

        async def mock_to_thread(fn, url):
            nonlocal call_count
            call_count += 1
            if "feedA" in url:
                return feed_a
            return feed_b

        source = RSSSource()
        with patch.dict(
            "os.environ", {"RSS_FEEDS": "https://feedA.com/rss,https://feedB.com/rss"}
        ):
            with patch(
                "apps.worker.sources.rss.asyncio.to_thread", side_effect=mock_to_thread
            ):
                posts = await source.fetch()

        assert len(posts) == 2


# ---------------------------------------------------------------------------
# HackerNewsSource — helpers
# ---------------------------------------------------------------------------


class TestHackerNewsHelpers:
    def test_strip_html_removes_tags(self):
        assert _strip_html("<p>Hello <b>world</b></p>") == "Hello world"

    def test_strip_html_empty_string(self):
        assert _strip_html("") == ""

    def test_strip_html_no_tags(self):
        assert _strip_html("plain text") == "plain text"

    def test_idea_keywords_matches_app(self):
        assert IDEA_KEYWORDS.search("I built an app for X")

    def test_idea_keywords_matches_tool(self):
        assert IDEA_KEYWORDS.search("Show HN: A tool to simplify deployments")

    def test_idea_keywords_matches_build(self):
        assert IDEA_KEYWORDS.search("I want to build something cool")

    def test_idea_keywords_matches_startup(self):
        assert IDEA_KEYWORDS.search("My startup journey so far")

    def test_idea_keywords_matches_side_project(self):
        assert IDEA_KEYWORDS.search("Working on a side project")

    def test_idea_keywords_matches_saas(self):
        assert IDEA_KEYWORDS.search("Launching my first SaaS")

    def test_idea_keywords_no_match(self):
        assert IDEA_KEYWORDS.search("The weather is nice today") is None


# ---------------------------------------------------------------------------
# HackerNewsSource — _to_raw_post
# ---------------------------------------------------------------------------


class TestHNToRawPost:
    def test_converts_item_to_raw_post(self):
        source = HackerNewsSource()
        item = _make_hn_item()
        post = source._to_raw_post(item, "show")

        assert isinstance(post, RawPost)
        assert post.source == "hackernews"
        assert post.title == "Show HN: I built a tool for tracking habits"
        assert "12345" in post.url
        assert post.source_metadata["score"] == 42
        assert post.source_metadata["comments"] == 10
        assert post.source_metadata["hn_id"] == 12345
        assert post.source_metadata["type"] == "show"

    def test_returns_none_for_empty_title(self):
        source = HackerNewsSource()
        item = _make_hn_item(title="")
        assert source._to_raw_post(item, "ask") is None

    def test_returns_none_when_no_idea_keywords(self):
        source = HackerNewsSource()
        item = _make_hn_item(title="The weather forecast for next week")
        assert source._to_raw_post(item, "ask") is None

    def test_strips_html_from_content(self):
        source = HackerNewsSource()
        item = _make_hn_item(text="<p>Check out <b>this</b> app</p>")
        post = source._to_raw_post(item, "show")
        assert "<p>" not in post.content
        assert "<b>" not in post.content

    def test_uses_title_as_content_fallback(self):
        source = HackerNewsSource()
        item = _make_hn_item(text="")
        post = source._to_raw_post(item, "show")
        assert post.content == post.title

    def test_url_hash_is_sha256(self):
        source = HackerNewsSource()
        item = _make_hn_item()
        post = source._to_raw_post(item, "show")
        assert len(post.url_hash) == 64

    def test_published_at_from_timestamp(self):
        source = HackerNewsSource()
        item = _make_hn_item(time_=1718400000)
        post = source._to_raw_post(item, "show")
        assert isinstance(post.published_at, datetime)


# ---------------------------------------------------------------------------
# HackerNewsSource — fetch()
# ---------------------------------------------------------------------------


class TestHNFetch:
    @pytest.mark.asyncio
    async def test_fetch_returns_raw_posts(self):
        """fetch() should return RawPost objects from both ask and show feeds."""
        source = HackerNewsSource()

        ask_ids = [1, 2]
        show_ids = [3]

        items = {
            1: _make_hn_item(item_id=1, title="Ask HN: Need an app for meal planning"),
            2: _make_hn_item(item_id=2, title="Ask HN: Best tool for team management"),
            3: _make_hn_item(item_id=3, title="Show HN: I built a budgeting app"),
        }

        async def mock_get(url, **kwargs):
            resp = MagicMock(spec=httpx.Response)
            resp.raise_for_status = MagicMock()
            if "askstories" in url:
                resp.json.return_value = ask_ids
            elif "showstories" in url:
                resp.json.return_value = show_ids
            else:
                # Item endpoint
                item_id = int(url.split("/")[-1].replace(".json", ""))
                resp.json.return_value = items[item_id]
            return resp

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(side_effect=mock_get)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "apps.worker.sources.hackernews.httpx.AsyncClient", return_value=mock_client
        ):
            posts = await source.fetch()

        assert len(posts) == 3
        assert all(isinstance(p, RawPost) for p in posts)

    @pytest.mark.asyncio
    async def test_fetch_filters_non_idea_posts(self):
        """Posts without idea keywords should be excluded."""
        source = HackerNewsSource()

        ask_ids = [1, 2]
        items = {
            1: _make_hn_item(
                item_id=1, title="Ask HN: Best laptop for 2025?"
            ),  # no idea keyword
            2: _make_hn_item(
                item_id=2, title="Ask HN: I wish someone would build a sleep tracker"
            ),
        }

        async def mock_get(url, **kwargs):
            resp = MagicMock(spec=httpx.Response)
            resp.raise_for_status = MagicMock()
            if "askstories" in url:
                resp.json.return_value = ask_ids
            elif "showstories" in url:
                resp.json.return_value = []
            else:
                item_id = int(url.split("/")[-1].replace(".json", ""))
                resp.json.return_value = items[item_id]
            return resp

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(side_effect=mock_get)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "apps.worker.sources.hackernews.httpx.AsyncClient", return_value=mock_client
        ):
            posts = await source.fetch()

        assert len(posts) == 1
        assert "build" in posts[0].title.lower()

    @pytest.mark.asyncio
    async def test_fetch_handles_api_failure_gracefully(self):
        """Network errors should not crash fetch(); returns empty list."""
        source = HackerNewsSource()

        async def mock_get(url, **kwargs):
            raise httpx.ConnectError("Connection refused")

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(side_effect=mock_get)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "apps.worker.sources.hackernews.httpx.AsyncClient", return_value=mock_client
        ):
            posts = await source.fetch()

        assert posts == []

    @pytest.mark.asyncio
    async def test_fetch_handles_bad_item_json(self):
        """If an individual item fetch fails, it should be skipped."""
        source = HackerNewsSource()

        ask_ids = [1, 2]

        call_count = 0

        async def mock_get(url, **kwargs):
            nonlocal call_count
            resp = MagicMock(spec=httpx.Response)
            resp.raise_for_status = MagicMock()
            if "askstories" in url:
                resp.json.return_value = ask_ids
            elif "showstories" in url:
                resp.json.return_value = []
            elif "/item/1.json" in url:
                raise httpx.ReadTimeout("timeout")
            else:
                resp.json.return_value = _make_hn_item(
                    item_id=2, title="Ask HN: Need a tool for X"
                )
            return resp

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(side_effect=mock_get)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "apps.worker.sources.hackernews.httpx.AsyncClient", return_value=mock_client
        ):
            posts = await source.fetch()

        # Only item 2 should succeed
        assert len(posts) == 1

    @pytest.mark.asyncio
    async def test_fetch_score_and_comments_in_metadata(self):
        """source_metadata should include score and comments count."""
        source = HackerNewsSource()

        item = _make_hn_item(
            item_id=99, title="Show HN: My new app", score=150, descendants=30
        )

        async def mock_get(url, **kwargs):
            resp = MagicMock(spec=httpx.Response)
            resp.raise_for_status = MagicMock()
            if "askstories" in url:
                resp.json.return_value = []
            elif "showstories" in url:
                resp.json.return_value = [99]
            else:
                resp.json.return_value = item
            return resp

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(side_effect=mock_get)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "apps.worker.sources.hackernews.httpx.AsyncClient", return_value=mock_client
        ):
            posts = await source.fetch()

        assert len(posts) == 1
        assert posts[0].source_metadata["score"] == 150
        assert posts[0].source_metadata["comments"] == 30

    @pytest.mark.asyncio
    async def test_fetch_uses_semaphore_for_concurrency(self):
        """Parallel item fetches should be bounded by semaphore."""
        source = HackerNewsSource()

        ids = list(range(1, 16))  # 15 items
        max_concurrent = 0
        current_concurrent = 0
        lock = asyncio.Lock()

        async def mock_get(url, **kwargs):
            nonlocal max_concurrent, current_concurrent
            resp = MagicMock(spec=httpx.Response)
            resp.raise_for_status = MagicMock()
            if "askstories" in url:
                resp.json.return_value = ids
            elif "showstories" in url:
                resp.json.return_value = []
            else:
                async with lock:
                    current_concurrent += 1
                    max_concurrent = max(max_concurrent, current_concurrent)
                await asyncio.sleep(0.01)  # simulate network latency
                async with lock:
                    current_concurrent -= 1
                item_id = int(url.split("/")[-1].replace(".json", ""))
                resp.json.return_value = _make_hn_item(
                    item_id=item_id, title=f"Show HN: App idea #{item_id}"
                )
            return resp

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(side_effect=mock_get)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "apps.worker.sources.hackernews.httpx.AsyncClient", return_value=mock_client
        ):
            posts = await source.fetch()

        # MAX_CONCURRENCY in hackernews.py is 10
        assert max_concurrent <= 10
        assert len(posts) == 15
