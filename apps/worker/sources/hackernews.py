"""
HackerNews Source
Fetches "Ask HN" and "Show HN" posts via the public HN Firebase API.
"""

import asyncio
import logging
import re
from datetime import UTC, datetime, timezone

import httpx

from apps.worker.sources.base import BaseSource
from packages.core.dedupe import generate_url_hash
from packages.core.models import RawPost

logger = logging.getLogger(__name__)

HN_API_BASE = "https://hacker-news.firebaseio.com/v0"
HN_WEB_BASE = "https://news.ycombinator.com/item?id="
REQUEST_TIMEOUT = 30.0
MAX_ITEMS_PER_FEED = 30
MAX_CONCURRENCY = 10

# Keywords that suggest an app/product idea
IDEA_KEYWORDS = re.compile(
    r"\b(app|tool|build|built|wish|need|want|idea|startup|project|product|saas|side[\s-]?project)\b",
    re.IGNORECASE,
)

_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    """Remove HTML tags from a string."""
    return _HTML_TAG_RE.sub("", text)


class HackerNewsSource(BaseSource):
    """
    Fetches Ask HN and Show HN posts from the HN Firebase API,
    filtering for posts related to app/product ideas.
    """

    async def fetch(self) -> list[RawPost]:
        posts: list[RawPost] = []

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            for feed, label in [
                ("askstories", "ask"),
                ("showstories", "show"),
            ]:
                try:
                    ids = await self._fetch_story_ids(client, feed)
                    items = await self._fetch_items(client, ids[:MAX_ITEMS_PER_FEED])
                    for item in items:
                        post = self._to_raw_post(item, label)
                        if post is not None:
                            posts.append(post)
                except Exception:
                    logger.exception("Error fetching %s feed", feed)

        logger.info("HackerNewsSource fetched %d posts", len(posts))
        return posts

    # ------------------------------------------------------------------

    async def _fetch_story_ids(self, client: httpx.AsyncClient, feed: str) -> list[int]:
        resp = await client.get(f"{HN_API_BASE}/{feed}.json")
        resp.raise_for_status()
        return resp.json()

    async def _fetch_items(
        self, client: httpx.AsyncClient, ids: list[int]
    ) -> list[dict]:
        """Fetch item details in parallel with bounded concurrency."""
        semaphore = asyncio.Semaphore(MAX_CONCURRENCY)

        async def _get(item_id: int) -> dict | None:
            async with semaphore:
                try:
                    resp = await client.get(f"{HN_API_BASE}/item/{item_id}.json")
                    resp.raise_for_status()
                    return resp.json()
                except Exception:
                    logger.warning("Failed to fetch HN item %s", item_id)
                    return None

        results = await asyncio.gather(*[_get(i) for i in ids])
        return [r for r in results if r]

    # ------------------------------------------------------------------

    def _to_raw_post(self, item: dict, feed_type: str) -> RawPost | None:
        """Convert an HN item dict to a RawPost, or None if irrelevant."""
        title = item.get("title", "")
        if not title:
            return None

        if not IDEA_KEYWORDS.search(title):
            return None

        hn_id = item["id"]
        url = f"{HN_WEB_BASE}{hn_id}"
        raw_text = item.get("text") or ""
        content = _strip_html(raw_text).strip() or title

        published_at = None
        ts = item.get("time")
        if ts:
            published_at = datetime.fromtimestamp(ts, tz=UTC)

        return RawPost(
            url=url,
            url_hash=generate_url_hash(url),
            title=title,
            content=content,
            source="hackernews",
            author=item.get("by", ""),
            published_at=published_at,
            fetched_at=datetime.now(tz=UTC),
            source_metadata={
                "score": item.get("score", 0),
                "comments": item.get("descendants", 0),
                "hn_id": hn_id,
                "type": feed_type,
            },
            is_processed=False,
        )
