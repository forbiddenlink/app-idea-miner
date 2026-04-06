"""Celery tasks for saved-search digest alerts.

Sends webhook notifications when new ideas match saved searches.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from apps.worker.celery_app import celery_app
from packages.core.database import AsyncSessionLocal
from packages.core.models import IdeaCandidate, SavedSearch
from packages.core.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="apps.worker.tasks.saved_search_alerts.send_daily_saved_search_alerts",
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def send_daily_saved_search_alerts(self) -> dict[str, Any]:
    """
    Send daily saved-search digest alerts.

    Finds all saved searches with daily alerts enabled and webhook configured,
    then sends notifications for any new ideas matching the search criteria.
    """
    logger.info("Starting daily saved-search alerts")

    try:
        result = asyncio.run(_send_alerts_async(frequency="daily"))
        logger.info(f"Daily alerts complete: {result}")
        return result
    except Exception as e:
        logger.error(f"Daily alerts failed: {e}", exc_info=True)
        raise


@celery_app.task(
    bind=True,
    name="apps.worker.tasks.saved_search_alerts.send_weekly_saved_search_alerts",
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def send_weekly_saved_search_alerts(self) -> dict[str, Any]:
    """
    Send weekly saved-search digest alerts.

    Finds all saved searches with weekly alerts enabled and webhook configured,
    then sends notifications for any new ideas matching the search criteria.
    """
    logger.info("Starting weekly saved-search alerts")

    try:
        result = asyncio.run(_send_alerts_async(frequency="weekly"))
        logger.info(f"Weekly alerts complete: {result}")
        return result
    except Exception as e:
        logger.error(f"Weekly alerts failed: {e}", exc_info=True)
        raise


async def _send_alerts_async(frequency: str) -> dict[str, Any]:
    """
    Async implementation of alert sending.

    Args:
        frequency: 'daily' or 'weekly'

    Returns:
        Statistics about alerts sent
    """
    stats = {
        "frequency": frequency,
        "searches_checked": 0,
        "alerts_sent": 0,
        "alerts_failed": 0,
        "no_new_matches": 0,
        "executed_at": datetime.now(UTC).isoformat(),
    }

    # Determine lookback window
    if frequency == "daily":
        lookback = timedelta(days=1)
    else:
        lookback = timedelta(days=7)

    cutoff_time = datetime.now(UTC) - lookback

    async with AsyncSessionLocal() as session:
        # Find saved searches with alerts enabled and webhook configured
        stmt = (
            select(SavedSearch)
            .where(SavedSearch.alert_enabled == True)
            .where(SavedSearch.alert_frequency == frequency)
            .where(SavedSearch.webhook_url.isnot(None))
            .where(SavedSearch.webhook_type.isnot(None))
        )

        result = await session.execute(stmt)
        saved_searches = result.scalars().all()

        stats["searches_checked"] = len(saved_searches)
        logger.info(
            f"Found {len(saved_searches)} saved searches for {frequency} alerts"
        )

        notification_service = NotificationService()

        for search in saved_searches:
            try:
                # Find matching ideas since last alert (or since lookback window)
                since_time = search.last_alert_at or cutoff_time
                if since_time < cutoff_time:
                    since_time = cutoff_time

                matching_ideas = await _find_matching_ideas(
                    session, search.query_params, since_time
                )

                if not matching_ideas:
                    stats["no_new_matches"] += 1
                    logger.debug(f"No new matches for search '{search.name}'")
                    continue

                # Format ideas for webhook
                ideas_data = [
                    {
                        "id": str(idea.id),
                        "problem_statement": idea.problem_statement,
                        "domain": idea.domain,
                        "quality_score": idea.quality_score,
                        "sentiment": idea.sentiment,
                        "competitors_mentioned": idea.competitors_mentioned,
                    }
                    for idea in matching_ideas
                ]

                # Send webhook
                success = await notification_service.send_alert(
                    webhook_url=search.webhook_url,
                    webhook_type=search.webhook_type,
                    ideas=ideas_data,
                    search_name=search.name,
                )

                if success:
                    stats["alerts_sent"] += 1
                    # Update last_alert_at
                    search.last_alert_at = datetime.now(UTC)
                    logger.info(
                        f"Sent {frequency} alert for '{search.name}' "
                        f"with {len(matching_ideas)} ideas"
                    )
                else:
                    stats["alerts_failed"] += 1
                    logger.warning(f"Failed to send alert for '{search.name}'")

            except Exception as e:
                stats["alerts_failed"] += 1
                logger.error(
                    f"Error processing search '{search.name}': {e}", exc_info=True
                )

        # Commit last_alert_at updates
        await session.commit()

    return stats


async def _find_matching_ideas(
    session,
    query_params: dict,
    since: datetime,
    limit: int = 20,
) -> list[IdeaCandidate]:
    """
    Find ideas matching the saved search criteria since a given time.

    Args:
        session: Database session
        query_params: Search criteria from saved search
        since: Only include ideas created after this time
        limit: Maximum ideas to return

    Returns:
        List of matching IdeaCandidate objects
    """
    stmt = (
        select(IdeaCandidate)
        .where(IdeaCandidate.is_valid == True)
        .where(IdeaCandidate.extracted_at >= since)
        .options(selectinload(IdeaCandidate.raw_post))
    )

    # Apply filters from query_params
    if query_params.get("domain"):
        stmt = stmt.where(IdeaCandidate.domain == query_params["domain"])

    if query_params.get("sentiment"):
        stmt = stmt.where(IdeaCandidate.sentiment == query_params["sentiment"])

    if query_params.get("min_quality"):
        stmt = stmt.where(
            IdeaCandidate.quality_score >= float(query_params["min_quality"])
        )

    if query_params.get("competitor"):
        stmt = stmt.where(
            IdeaCandidate.competitors_mentioned.contains(
                [query_params["competitor"].lower()]
            )
        )

    # Order by quality and limit
    stmt = stmt.order_by(IdeaCandidate.quality_score.desc()).limit(limit)

    result = await session.execute(stmt)
    return result.scalars().all()


@celery_app.task(
    bind=True,
    name="apps.worker.tasks.saved_search_alerts.send_single_search_alert",
)
def send_single_search_alert(self, search_id: str) -> dict[str, Any]:
    """
    Send alert for a single saved search (on-demand).

    Useful for testing webhook configuration or manual triggers.

    Args:
        search_id: UUID of the saved search

    Returns:
        Result of the alert attempt
    """
    logger.info(f"Sending alert for search {search_id}")

    try:
        result = asyncio.run(_send_single_alert_async(search_id))
        return result
    except Exception as e:
        logger.error(f"Single alert failed: {e}", exc_info=True)
        raise


async def _send_single_alert_async(search_id: str) -> dict[str, Any]:
    """Async implementation of single search alert."""
    from uuid import UUID

    async with AsyncSessionLocal() as session:
        search = await session.get(SavedSearch, UUID(search_id))

        if not search:
            return {"success": False, "error": "Search not found"}

        if not search.webhook_url or not search.webhook_type:
            return {"success": False, "error": "Webhook not configured"}

        # Find recent matching ideas (last 24 hours)
        since = datetime.now(UTC) - timedelta(days=1)
        matching_ideas = await _find_matching_ideas(
            session, search.query_params, since, limit=10
        )

        if not matching_ideas:
            return {
                "success": True,
                "message": "No matching ideas found",
                "ideas_count": 0,
            }

        ideas_data = [
            {
                "id": str(idea.id),
                "problem_statement": idea.problem_statement,
                "domain": idea.domain,
                "quality_score": idea.quality_score,
                "sentiment": idea.sentiment,
                "competitors_mentioned": idea.competitors_mentioned,
            }
            for idea in matching_ideas
        ]

        notification_service = NotificationService()
        success = await notification_service.send_alert(
            webhook_url=search.webhook_url,
            webhook_type=search.webhook_type,
            ideas=ideas_data,
            search_name=search.name,
        )

        if success:
            search.last_alert_at = datetime.now(UTC)
            await session.commit()

        return {
            "success": success,
            "ideas_count": len(matching_ideas),
            "search_name": search.name,
        }
