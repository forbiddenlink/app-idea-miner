"""
Ingestion Tasks
Fetches posts from RSS feeds and other data sources.
"""

import asyncio
import logging
import os
from datetime import datetime

import feedparser
from sqlalchemy import select

from apps.api.app.database import AsyncSessionLocal
from apps.worker.celery_app import celery_app
from packages.core.dedupe import generate_url_hash, is_duplicate_title
from packages.core.models import RawPost

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="apps.worker.tasks.ingestion.fetch_rss_feeds")
def fetch_rss_feeds(self):
    """
    Fetch posts from configured RSS feeds.
    Scheduled to run every 6 hours via Celery Beat.

    Reads RSS_FEEDS environment variable (comma-separated URLs),
    parses each feed, checks for duplicates, and inserts new posts.

    Returns:
        dict: Statistics (total_fetched, new_posts, duplicates, errors)
    """
    logger.info("Starting RSS feed ingestion...")

    try:
        # Get RSS feeds from environment
        rss_feeds_str = os.getenv("RSS_FEEDS", "https://hnrss.org/newest")
        rss_feeds = [feed.strip() for feed in rss_feeds_str.split(",") if feed.strip()]

        logger.info(f"Fetching from {len(rss_feeds)} RSS feeds")

        total_fetched = 0
        new_posts = 0
        duplicates = 0
        errors = 0

        for feed_url in rss_feeds:
            try:
                # Parse RSS feed
                logger.info(f"Parsing feed: {feed_url}")
                feed = feedparser.parse(feed_url)

                if feed.bozo:  # Feed parsing error
                    logger.warning(f"Feed parsing warning for {feed_url}: {feed.bozo_exception}")

                entries = feed.entries
                total_fetched += len(entries)
                logger.info(f"Found {len(entries)} entries in {feed_url}")

                # Process each entry
                for entry in entries:
                    try:
                        # Extract data
                        url = entry.get("link", "")
                        title = entry.get("title", "")
                        content = entry.get("summary") or entry.get("description") or ""
                        author = entry.get("author", "")

                        # Parse published date
                        published_at = None
                        if hasattr(entry, "published_parsed") and entry.published_parsed:
                            published_at = datetime(*entry.published_parsed[:6])

                        # Skip if no URL or title
                        if not url or not title:
                            logger.debug("Skipping entry with missing URL or title")
                            continue

                        # Check for duplicate
                        url_hash = generate_url_hash(url)
                        is_duplicate = asyncio.run(_check_duplicate_async(url_hash, title))

                        if is_duplicate:
                            duplicates += 1
                            logger.debug(f"Duplicate post: {title[:50]}...")
                            continue

                        # Extract source from feed
                        source = _extract_source_from_feed_url(feed_url)

                        # Create metadata
                        metadata = {
                            "feed_url": feed_url,
                            "feed_title": feed.feed.get("title", ""),
                            "tags": [tag.term for tag in entry.get("tags", [])],
                        }

                        # Save to database
                        asyncio.run(
                            _save_raw_post_async(
                                url=url,
                                url_hash=url_hash,
                                title=title,
                                content=content,
                                source=source,
                                author=author,
                                published_at=published_at,
                                metadata=metadata,
                            )
                        )

                        new_posts += 1
                        logger.debug(f"Saved new post: {title[:50]}...")

                    except Exception as e:
                        logger.error(f"Error processing entry: {e}", exc_info=True)
                        errors += 1
                        continue

            except Exception as e:
                logger.error(f"Error fetching feed {feed_url}: {e}", exc_info=True)
                errors += 1
                continue

        result = {
            "status": "success",
            "total_fetched": total_fetched,
            "new_posts": new_posts,
            "duplicates": duplicates,
            "errors": errors,
            "feeds_processed": len(rss_feeds),
        }

        logger.info(f"RSS ingestion complete: {result}")
        return result

    except Exception as e:
        logger.error(f"RSS ingestion failed: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=300)  # Retry after 5 minutes


def _extract_source_from_feed_url(feed_url: str) -> str:
    """
    Extract source name from feed URL.

    Args:
        feed_url: RSS feed URL

    Returns:
        Source identifier string
    """
    if "hnrss.org" in feed_url or "news.ycombinator.com" in feed_url:
        return "hackernews"
    elif "reddit.com" in feed_url:
        return "reddit"
    elif "producthunt.com" in feed_url:
        return "producthunt"
    else:
        return "rss_feed"


async def _check_duplicate_async(url_hash: str, title: str) -> bool:
    """
    Check if post already exists in database.

    Args:
        url_hash: Hash of the URL
        title: Post title

    Returns:
        True if duplicate exists
    """
    async with AsyncSessionLocal() as session:
        # Check by URL hash (fast)
        result = await session.execute(select(RawPost).where(RawPost.url_hash == url_hash))
        existing = result.scalar_one_or_none()

        if existing:
            return True

        # Check by similar title (slower, checks all posts)
        # For MVP, only check recent posts to avoid performance issues
        result = await session.execute(
            select(RawPost).order_by(RawPost.fetched_at.desc()).limit(1000)
        )
        recent_posts = result.scalars().all()

        for post in recent_posts:
            if is_duplicate_title(title, post.title):
                return True

        return False


async def _save_raw_post_async(
    url: str,
    url_hash: str,
    title: str,
    content: str,
    source: str,
    author: str = None,
    published_at: datetime = None,
    metadata: dict = None,
) -> None:
    """
    Save raw post to database.
    """
    async with AsyncSessionLocal() as session:
        post = RawPost(
            url=url,
            url_hash=url_hash,
            title=title,
            content=content,
            source=source,
            author=author,
            published_at=published_at,
            fetched_at=datetime.utcnow(),
            source_metadata=metadata or {},
            is_processed=False,
        )

        session.add(post)
        await session.commit()
        logger.debug(f"Saved post {post.id} to database")


@celery_app.task(bind=True, name="apps.worker.tasks.ingestion.fetch_from_source")
def fetch_from_source(self, source_name: str):
    """
    Fetch posts from a specific data source.

    Args:
        source_name: Name of the source to fetch from

    TODO: Implement custom source fetching
    - Support multiple source types
    - Handle API authentication
    - Rate limiting
    """
    logger.info(f"Fetching from source: {source_name}")

    try:
        # Placeholder implementation
        logger.info(f"Source fetching completed: {source_name} (placeholder)")
        return {"status": "success", "source": source_name, "posts_fetched": 0}

    except Exception as e:
        logger.error(f"Source fetching failed for {source_name}: {e}")
        raise self.retry(exc=e, countdown=300)
