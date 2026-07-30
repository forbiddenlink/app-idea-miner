"""Celery task for syncing top-quality idea clusters to the Notion Ideas Pipeline.

Chained (fire-and-forget, via .delay()) from apps.worker.tasks.clustering.run_clustering
after a successful clustering commit, matching the existing
assign_new_ideas_to_clusters -> run_clustering chaining pattern.
"""

from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import Sequence
from typing import Any

from sqlalchemy import select

from apps.worker.celery_app import celery_app
from packages.core.competitors import aggregate_competitors
from packages.core.database import AsyncSessionLocal
from packages.core.models import Cluster, ClusterMembership, IdeaCandidate
from packages.core.services.notion_service import NotionService

logger = logging.getLogger(__name__)

# Default minimum quality_score for a cluster to be surfaced to Notion, overridable
# via the NOTION_MIN_QUALITY env var.
DEFAULT_NOTION_MIN_QUALITY = 0.6

# Hard cap on clusters synced per run so the Ideas Pipeline database never gets spammed.
MAX_CLUSTERS_TO_SYNC = 10


def select_clusters_for_notion(
    clusters: Sequence[Cluster],
    min_quality: float,
    limit: int = MAX_CLUSTERS_TO_SYNC,
) -> list[Cluster]:
    """
    Select the clusters worth surfacing to Notion.

    Filters to clusters with quality_score >= min_quality, then keeps only the top
    `limit` by quality_score (descending) so the sink never spams the database.

    Args:
        clusters: Candidate clusters
        min_quality: Minimum quality_score to qualify
        limit: Maximum number of clusters to return

    Returns:
        The top `limit` qualifying clusters, sorted by quality_score descending
    """
    qualifying = [c for c in clusters if (c.quality_score or 0) >= min_quality]
    qualifying.sort(key=lambda c: c.quality_score or 0, reverse=True)
    return qualifying[:limit]


@celery_app.task(
    bind=True,
    name="apps.worker.tasks.notion_sync.push_clusters_to_notion",
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def push_clusters_to_notion(self) -> dict[str, Any]:
    """
    Push the top quality clusters to the Notion Ideas Pipeline database.

    No-ops gracefully if NOTION_API_KEY / NOTION_IDEAS_DB_ID are unset (see
    NotionService), so a missing Notion setup never breaks a clustering run.

    Returns:
        Dictionary with sync statistics
    """
    logger.info("Starting Notion Ideas Pipeline sync")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(_push_clusters_to_notion_async())
    finally:
        loop.close()

    logger.info(f"Notion sync complete: {result}")
    return result


async def _push_clusters_to_notion_async() -> dict[str, Any]:
    """Async implementation of the Notion sync task."""
    min_quality = float(
        os.getenv("NOTION_MIN_QUALITY", str(DEFAULT_NOTION_MIN_QUALITY))
    )

    notion_service = NotionService()

    if not notion_service.enabled:
        logger.info("Notion sink not configured - skipping sync")
        return {
            "skipped": True,
            "reason": "NOTION_API_KEY/NOTION_IDEAS_DB_ID not set",
            "pushed": 0,
            "failed": 0,
        }

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Cluster))
        all_clusters = result.scalars().all()

        clusters = select_clusters_for_notion(
            all_clusters, min_quality=min_quality, limit=MAX_CLUSTERS_TO_SYNC
        )

        pushed = 0
        failed = 0

        for cluster in clusters:
            competitor_result = await session.execute(
                select(IdeaCandidate.competitors_mentioned)
                .join(
                    ClusterMembership,
                    ClusterMembership.idea_id == IdeaCandidate.id,
                )
                .where(ClusterMembership.cluster_id == cluster.id)
                .where(IdeaCandidate.competitors_mentioned.isnot(None))
            )
            top_competitors = aggregate_competitors(competitor_result.scalars().all())

            success = await notion_service.push_cluster(cluster, top_competitors)
            if success:
                pushed += 1
            else:
                failed += 1

        return {
            "skipped": False,
            "clusters_considered": len(clusters),
            "pushed": pushed,
            "failed": failed,
            "min_quality": min_quality,
        }
