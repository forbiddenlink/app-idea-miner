"""
Ingestion Tasks
Fetches posts from configured data sources using a plugin architecture.
"""

import asyncio
import logging

from sqlalchemy import select

from apps.worker.celery_app import celery_app

# Source Plugins
from apps.worker.sources.base import BaseSource
from apps.worker.sources.hackernews import HackerNewsSource
from apps.worker.sources.indiehackers import IndieHackersSource
from apps.worker.sources.producthunt import ProductHuntSource
from apps.worker.sources.reddit import RedditSource
from apps.worker.sources.rss import RSSSource
from packages.core.database import AsyncSessionLocal
from packages.core.models import RawPost

logger = logging.getLogger(__name__)


# Registry of available sources
SOURCE_REGISTRY: list[type[BaseSource]] = [
    RSSSource,
    RedditSource,
    ProductHuntSource,
    HackerNewsSource,
    IndieHackersSource,
]


@celery_app.task(
    bind=True,
    name="apps.worker.tasks.ingestion.run_ingestion_cycle",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,  # Max 10 minutes between retries
    retry_jitter=True,
    max_retries=3,
)
def run_ingestion_cycle(self):
    """
    Run the main ingestion cycle for all configured sources.
    Scheduled to run periodically (e.g., every 6 hours).

    Iterates through all registered source plugins, fetches new posts,
    deduplicates them against the database, and saves the new ones.
    """
    logger.info("Starting ingestion cycle...")

    total_stats = {"fetched": 0, "new": 0, "duplicates": 0, "errors": 0}

    # Run everything in an async loop since our DB and sources are likely async
    try:
        asyncio.run(_run_ingestion_async(total_stats))
    except Exception as e:
        logger.error(f"Ingestion cycle failed: {e}", exc_info=True)
        # Don't retry the whole cycle immediately, just log and wait for next schedule
        # raise self.retry(exc=e, countdown=300)

    logger.info(f"Ingestion cycle complete: {total_stats}")
    return total_stats


async def _run_ingestion_async(stats: dict):
    """
    Async implementation of the ingestion runner.

    Uses savepoints per source to ensure partial failures don't corrupt the database.
    Each source's posts are committed independently.
    """
    async with AsyncSessionLocal() as session:
        for SourceClass in SOURCE_REGISTRY:
            source_name = SourceClass.__name__
            source_new = 0
            source_duplicates = 0

            try:
                logger.info(f"Running source: {source_name}")
                source_instance = SourceClass()

                # 1. Fetch
                raw_posts = await source_instance.fetch()
                stats["fetched"] += len(raw_posts)

                # 2. Process & Save with savepoint for atomic per-source commits
                async with session.begin_nested():
                    for post in raw_posts:
                        if await _save_if_new(session, post):
                            source_new += 1
                        else:
                            source_duplicates += 1

                # Commit this source's posts
                await session.commit()
                stats["new"] += source_new
                stats["duplicates"] += source_duplicates
                logger.info(
                    f"Source {source_name}: {source_new} new, {source_duplicates} duplicates"
                )

            except Exception as e:
                logger.error(f"Error running source {source_name}: {e}", exc_info=True)
                stats["errors"] += 1
                # Rollback this source's changes, continue with next source
                await session.rollback()


async def _save_if_new(session, post: RawPost) -> bool:
    """
    Check for duplicates and save if new.
    Returns True if saved, False if duplicate.
    """
    # 1. Check URL Hash (Exact Match)
    # Note: We query the DB for this specific hash.
    # Optimization: Could batch query existing hashes if list is large.
    query = select(RawPost).where(RawPost.url_hash == post.url_hash)
    result = await session.execute(query)
    if result.scalar_one_or_none():
        logger.debug(f"Duplicate URL found: {post.url}")
        return False

    # 2. Save
    session.add(post)
    return True
