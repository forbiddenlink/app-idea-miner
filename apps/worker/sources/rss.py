import logging
import os
from datetime import datetime

import feedparser

from apps.worker.sources.base import BaseSource
from packages.core.dedupe import generate_url_hash
from packages.core.models import RawPost

logger = logging.getLogger(__name__)


class RSSSource(BaseSource):
    """
    Fetches posts from configured RSS feeds.
    Reads RSS_FEEDS environment variable (comma-separated URLs).
    """

    def _extract_source_from_feed_url(self, feed_url: str) -> str:
        if "hnrss.org" in feed_url or "news.ycombinator.com" in feed_url:
            return "hackernews"
        elif "reddit.com" in feed_url:
            return "reddit"
        elif "producthunt.com" in feed_url:
            return "producthunt"
        else:
            return "rss_feed"

    async def fetch(self) -> list[RawPost]:
        rss_feeds_str = os.getenv("RSS_FEEDS", "https://hnrss.org/newest")
        rss_feeds = [feed.strip() for feed in rss_feeds_str.split(",") if feed.strip()]

        fetched_posts = []

        for feed_url in rss_feeds:
            try:
                logger.info(f"Parsing feed: {feed_url}")
                feed = feedparser.parse(feed_url)

                if feed.bozo:
                    logger.warning(
                        f"Feed parsing warning for {feed_url}: {feed.bozo_exception}"
                    )

                for entry in feed.entries:
                    try:
                        url = entry.get("link", "")
                        title = entry.get("title", "")
                        content = entry.get("summary") or entry.get("description") or ""
                        author = entry.get("author", "")

                        if not url or not title:
                            continue

                        # Generate hash
                        url_hash = generate_url_hash(url)

                        # Determine source
                        source = self._extract_source_from_feed_url(feed_url)

                        # Parse date
                        published_at = None
                        if (
                            hasattr(entry, "published_parsed")
                            and entry.published_parsed
                        ):
                            published_at = datetime(*entry.published_parsed[:6])

                        # Create RawPost (transient)
                        post = RawPost(
                            url=url,
                            url_hash=url_hash,
                            title=title,
                            content=content,
                            source=source,
                            author=author,
                            published_at=published_at,
                            fetched_at=datetime.utcnow(),
                            source_metadata={
                                "feed_url": feed_url,
                                "feed_title": feed.feed.get("title", ""),
                                "tags": [tag.term for tag in entry.get("tags", [])],
                            },
                            is_processed=False,
                        )
                        fetched_posts.append(post)

                    except Exception as e:
                        logger.error(f"Error processing RSS entry: {e}")
                        continue

            except Exception as e:
                logger.error(f"Error fetching feed {feed_url}: {e}")
                continue

        return fetched_posts
