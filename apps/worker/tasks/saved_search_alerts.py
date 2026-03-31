"""Celery tasks for saved-search digest alerts.

These are intentionally lightweight stubs so scheduling/invocation can be wired
now while delivery and personalization logic is implemented incrementally.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from apps.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="apps.worker.tasks.saved_search_alerts.send_daily_saved_search_alerts",
)
def send_daily_saved_search_alerts(self) -> dict[str, Any]:
    """Placeholder task for daily saved-search digests."""
    logger.info("Saved-search daily alerts stub executed")
    return {
        "status": "queued-stub",
        "frequency": "daily",
        "executed_at": datetime.now(UTC).isoformat(),
    }


@celery_app.task(
    bind=True,
    name="apps.worker.tasks.saved_search_alerts.send_weekly_saved_search_alerts",
)
def send_weekly_saved_search_alerts(self) -> dict[str, Any]:
    """Placeholder task for weekly saved-search digests."""
    logger.info("Saved-search weekly alerts stub executed")
    return {
        "status": "queued-stub",
        "frequency": "weekly",
        "executed_at": datetime.now(UTC).isoformat(),
    }
