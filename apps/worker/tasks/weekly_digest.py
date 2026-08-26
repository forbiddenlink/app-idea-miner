"""Celery task for producing a weekly curated "top ideas" digest.

Unlike apps.worker.tasks.notion_sync (which continuously pushes every
qualifying cluster to the Ideas Pipeline), this task runs on a weekly
cadence and produces ONE dated digest entry ranking the top N clusters of
the week - the IdeaBrowser-style "here are this week's best" hook.

Composes NotionService.push_cluster() - the existing Ideas Pipeline sink -
rather than adding new Notion API surface. NotionService only reads
.id/.label/.description/.keywords off whatever it's given, so a lightweight
SimpleNamespace stands in for a Cluster without any notion_service.py
changes. Idempotent per ISO week: the digest's Source ID is derived from the
Monday of the current week, so re-runs within the same week PATCH the
existing page instead of creating a duplicate (mirrors notion_sync's
Source ID dedup key).
"""

from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace
from typing import Any

from sqlalchemy import select

from apps.worker.celery_app import celery_app
from packages.core.database import AsyncSessionLocal
from packages.core.models import Cluster
from packages.core.services.notion_service import NotionService

logger = logging.getLogger(__name__)

# Number of top clusters to include in the weekly digest, overridable via
# the WEEKLY_DIGEST_SIZE env var.
DEFAULT_WEEKLY_DIGEST_SIZE = 10


def compute_digest_score(cluster: Any) -> float:
    """
    Composite ranking score for the weekly digest.

    quality_score + trend_score + idea_count. Missing/None fields are
    treated as 0, matching the ``c.quality_score or 0`` pattern used in
    notion_sync.select_clusters_for_notion.
    """
    return (
        (cluster.quality_score or 0)
        + (cluster.trend_score or 0)
        + (cluster.idea_count or 0)
    )


def rank_clusters_for_digest(
    clusters: Sequence[Cluster],
    top_n: int = DEFAULT_WEEKLY_DIGEST_SIZE,
) -> list[Cluster]:
    """
    Rank clusters by the composite digest score and return the top `top_n`.

    Args:
        clusters: Candidate clusters
        top_n: Maximum number of clusters to keep

    Returns:
        The top `top_n` clusters, sorted by composite score descending
    """
    ranked = sorted(clusters, key=compute_digest_score, reverse=True)
    return ranked[:top_n]


def week_start(reference: datetime | None = None) -> date:
    """
    The Monday (UTC) of the ISO week containing `reference` (defaults to now).

    Used as the idempotency anchor for the weekly digest - every run within
    the same ISO week resolves to the same date, so re-runs within a week
    update the same Notion page instead of creating a duplicate.
    """
    ref = reference or datetime.now(UTC)
    return (ref - timedelta(days=ref.weekday())).date()


def build_digest_title(anchor: date) -> str:
    """Notion page title for the digest, e.g. 'Idea Digest — 2026-07-27'."""
    return f"Idea Digest — {anchor.isoformat()}"


def build_digest_source_id(anchor: date) -> str:
    """Idempotency key for the digest page (mirrors notion_sync's Source ID use)."""
    return f"weekly-digest-{anchor.isoformat()}"


def build_digest_description(ranked_clusters: Sequence[Cluster]) -> str:
    """
    Render the ranked list into a Notes-friendly summary.

    One line per cluster: label, why-it-matters (idea count + trend +
    keywords).
    """
    if not ranked_clusters:
        return "No qualifying clusters this week."

    lines = []
    for i, cluster in enumerate(ranked_clusters, start=1):
        keywords = ", ".join(cluster.keywords or [])
        lines.append(
            f"{i}. {cluster.label} - {cluster.idea_count or 0} ideas, "
            f"trend {cluster.trend_score or 0:.2f}, keywords: {keywords}"
        )
    return "\n".join(lines)


def build_digest_record(ranked_clusters: Sequence[Cluster], anchor: date) -> Any:
    """
    Build a lightweight cluster-shaped record for NotionService.push_cluster().

    See module docstring: composes the existing sink instead of extending it.
    """
    return SimpleNamespace(
        id=build_digest_source_id(anchor),
        label=build_digest_title(anchor),
        description=build_digest_description(ranked_clusters),
        keywords=[],
    )


@celery_app.task(
    bind=True,
    name="apps.worker.tasks.weekly_digest.generate_weekly_digest",
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def generate_weekly_digest(self) -> dict[str, Any]:
    """
    Generate and push the weekly top-ideas digest to Notion.

    No-ops gracefully if NotionService is not enabled (mirrors
    apps.worker.tasks.notion_sync.push_clusters_to_notion), so a missing
    Notion setup never breaks the beat scheduler.

    Returns:
        Dictionary with digest statistics
    """
    logger.info("Starting weekly idea digest generation")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(_generate_weekly_digest_async())
    finally:
        loop.close()

    logger.info(f"Weekly digest complete: {result}")
    return result


async def _generate_weekly_digest_async() -> dict[str, Any]:
    """Async implementation of the weekly digest task."""
    digest_size = int(os.getenv("WEEKLY_DIGEST_SIZE", str(DEFAULT_WEEKLY_DIGEST_SIZE)))

    notion_service = NotionService()

    if not notion_service.enabled:
        logger.info("Notion sink not configured - skipping weekly digest")
        return {
            "skipped": True,
            "reason": "NOTION_API_KEY/NOTION_IDEAS_DB_ID not set",
            "pushed": False,
        }

    anchor = week_start()

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Cluster))
        all_clusters = result.scalars().all()

    ranked = rank_clusters_for_digest(all_clusters, top_n=digest_size)
    digest_record = build_digest_record(ranked, anchor)

    success = await notion_service.push_cluster(digest_record)

    return {
        "skipped": False,
        "clusters_considered": len(all_clusters),
        "clusters_in_digest": len(ranked),
        "digest_title": digest_record.label,
        "source_id": digest_record.id,
        "pushed": success,
    }
