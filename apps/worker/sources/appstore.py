"""
App Store Customer Reviews Source
Fetches customer reviews via Apple's keyless iTunes RSS customer-reviews
endpoint (no API key required), filtering for reviews that read as feature
requests / pain points — a high-intent complaint signal distinct from
HN/Reddit ideation posts.
"""

import logging
import os
import random
import re
from datetime import UTC, datetime
from uuid import uuid4

import httpx

from apps.worker.sources.base import BaseSource
from packages.core.dedupe import generate_url_hash
from packages.core.models import RawPost

logger = logging.getLogger(__name__)

APPSTORE_RSS_BASE = "https://itunes.apple.com"
REQUEST_TIMEOUT = 30.0

# Keywords that suggest a review is a feature request / pain point rather
# than generic praise or noise.
PAIN_POINT_KEYWORDS = re.compile(
    r"\b(wish|need|needs|needed|should|want|wanted|missing|frustrat\w*)\b",
    re.IGNORECASE,
)


class AppStoreSource(BaseSource):
    """
    Fetches App Store customer reviews for a configured list of app IDs via
    Apple's keyless iTunes RSS customer-reviews endpoint, filtering for
    reviews that look like feature requests or pain points.
    """

    def __init__(self):
        app_ids_raw = os.getenv("APPSTORE_APP_IDS", "")
        self.app_ids = [a.strip() for a in app_ids_raw.split(",") if a.strip()]
        self.country = os.getenv("APPSTORE_COUNTRY", "us")

        if not self.app_ids:
            logger.error(
                "APPSTORE_APP_IDS not configured — running in MOCK MODE. "
                "Fabricated reviews (tagged source_metadata['mock']=True) will "
                "be ingested instead of real App Store data. Set "
                "APPSTORE_APP_IDS (comma-separated app IDs) to restore live "
                "ingestion."
            )
            self.is_mock = True
        else:
            self.is_mock = False

    async def fetch(self) -> list[RawPost]:
        if self.is_mock:
            return await self._fetch_mock()

        logger.info("Fetching from App Store customer reviews API...")
        posts: list[RawPost] = []

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            for app_id in self.app_ids:
                try:
                    entries = await self._fetch_reviews(client, app_id)
                    for entry in entries:
                        post = self._to_raw_post(entry, app_id)
                        if post is not None:
                            posts.append(post)
                except Exception:
                    logger.exception(
                        "Error fetching App Store reviews for app %s", app_id
                    )

        logger.info("AppStoreSource fetched %d posts", len(posts))
        return posts

    # ------------------------------------------------------------------

    async def _fetch_reviews(
        self, client: httpx.AsyncClient, app_id: str
    ) -> list[dict]:
        url = (
            f"{APPSTORE_RSS_BASE}/{self.country}/rss/customerreviews/"
            f"id={app_id}/sortBy=mostRecent/json"
        )
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()

        entries = data.get("feed", {}).get("entry", [])
        if isinstance(entries, dict):
            # Apple's JSON feed collapses a single entry into a dict instead
            # of a list.
            entries = [entries]
        return entries

    # ------------------------------------------------------------------

    def _to_raw_post(self, entry: dict, app_id: str) -> RawPost | None:
        """Convert an App Store review entry to a RawPost, or None if irrelevant."""
        # The feed's first entry is app metadata (no author/rating) — skip it,
        # along with any malformed entry missing required fields.
        rating_label = entry.get("im:rating", {}).get("label")
        author_label = entry.get("author", {}).get("name", {}).get("label")
        title_label = entry.get("title", {}).get("label")
        content_label = entry.get("content", {}).get("label")

        if not (title_label and content_label and author_label and rating_label):
            return None

        combined_text = f"{title_label} {content_label}"
        if not PAIN_POINT_KEYWORDS.search(combined_text):
            return None

        review_id = entry.get("id", {}).get("label")
        url = review_id or f"{APPSTORE_RSS_BASE}/{app_id}/{title_label}"

        published_at = None
        updated_label = entry.get("updated", {}).get("label")
        if updated_label:
            try:
                published_at = datetime.fromisoformat(updated_label)
            except ValueError:
                published_at = None

        try:
            rating = int(rating_label)
        except (TypeError, ValueError):
            rating = None

        version = entry.get("im:version", {}).get("label")

        return RawPost(
            url=url,
            url_hash=generate_url_hash(url),
            title=title_label,
            content=content_label,
            source="appstore",
            author=author_label,
            published_at=published_at,
            fetched_at=datetime.now(UTC),
            source_metadata={
                "rating": rating,
                "appId": app_id,
                "country": self.country,
                "version": version,
            },
            is_processed=False,
        )

    # ------------------------------------------------------------------

    async def _fetch_mock(self) -> list[RawPost]:
        """Fabricated data for standalone testing without configured app IDs."""
        logger.info("Fetching from App Store (Mock Mode)...")

        mock_reviews = [
            (
                "Great app but missing dark mode",
                "I really wish this app had a dark mode option, my eyes hurt "
                "at night.",
            ),
            (
                "Needs offline support",
                "This app should really work offline, I lose all my data on "
                "flights.",
            ),
            (
                "Frustrating export flow",
                "So frustrated that I can't export my data to CSV. Please "
                "add this.",
            ),
        ]

        title, content = random.choice(mock_reviews)
        review_id = f"{APPSTORE_RSS_BASE}/{self.country}/review?id={uuid4().hex[:8]}"

        post = RawPost(
            url=review_id,
            url_hash=generate_url_hash(review_id),
            title=title,
            content=content,
            source="appstore",
            author="mock_reviewer",
            published_at=datetime.now(UTC),
            fetched_at=datetime.now(UTC),
            source_metadata={
                "rating": random.randint(1, 3),
                "appId": "mock",
                "country": self.country,
                "version": "1.0.0",
                "mock": True,
            },
            is_processed=False,
        )
        return [post]
