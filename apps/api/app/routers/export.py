"""
Export API endpoints.

Provides server-side CSV/JSON export for clusters, ideas, and posts.
"""

import csv
import io
import json
import logging
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.rate_limit import RateLimiter
from apps.api.app.core.security import get_api_key
from apps.api.app.database import get_db
from packages.core.models import Cluster, IdeaCandidate, RawPost

logger = logging.getLogger(__name__)

EXPORT_LIMIT = 10000

router = APIRouter(
    tags=["export"],
    dependencies=[Depends(get_api_key), Depends(RateLimiter(times=10, seconds=60))],
)

CLUSTER_CSV_FIELDS = [
    "id",
    "label",
    "description",
    "idea_count",
    "avg_sentiment",
    "quality_score",
    "trend_score",
    "keywords",
    "created_at",
]

IDEA_CSV_FIELDS = [
    "id",
    "problem_statement",
    "domain",
    "sentiment",
    "sentiment_score",
    "quality_score",
    "source_url",
    "extracted_at",
]

POST_CSV_FIELDS = [
    "id",
    "url",
    "title",
    "source",
    "author",
    "published_at",
    "is_processed",
]


def _serialize(value) -> str:
    """Convert a value to a CSV-safe string."""
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return "; ".join(str(v) for v in value)
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def _build_csv(rows: list[dict], fields: list[str]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({f: _serialize(row.get(f)) for f in fields})
    return buf.getvalue()


async def _export_clusters(db: AsyncSession) -> tuple[list[dict], list[str]]:
    result = await db.execute(
        select(Cluster).order_by(Cluster.idea_count.desc()).limit(EXPORT_LIMIT)
    )
    clusters = result.scalars().all()
    rows = [
        {
            "id": str(c.id),
            "label": c.label,
            "description": c.description,
            "idea_count": c.idea_count,
            "avg_sentiment": c.avg_sentiment,
            "quality_score": c.quality_score,
            "trend_score": c.trend_score,
            "keywords": c.keywords,
            "created_at": c.created_at,
        }
        for c in clusters
    ]
    return rows, CLUSTER_CSV_FIELDS


async def _export_ideas(db: AsyncSession) -> tuple[list[dict], list[str]]:
    result = await db.execute(
        select(IdeaCandidate)
        .order_by(IdeaCandidate.quality_score.desc())
        .limit(EXPORT_LIMIT)
    )
    ideas = result.scalars().all()
    rows = [
        {
            "id": str(i.id),
            "problem_statement": i.problem_statement,
            "domain": i.domain,
            "sentiment": i.sentiment,
            "sentiment_score": i.sentiment_score,
            "quality_score": i.quality_score,
            "source_url": None,  # populated below if raw_post loaded
            "extracted_at": i.extracted_at,
        }
        for i in ideas
    ]
    return rows, IDEA_CSV_FIELDS


async def _export_posts(db: AsyncSession) -> tuple[list[dict], list[str]]:
    result = await db.execute(
        select(RawPost).order_by(RawPost.created_at.desc()).limit(EXPORT_LIMIT)
    )
    posts = result.scalars().all()
    rows = [
        {
            "id": str(p.id),
            "url": p.url,
            "title": p.title,
            "source": p.source,
            "author": p.author,
            "published_at": p.published_at,
            "is_processed": p.is_processed,
        }
        for p in posts
    ]
    return rows, POST_CSV_FIELDS


_EXPORTERS = {
    "clusters": _export_clusters,
    "ideas": _export_ideas,
    "posts": _export_posts,
}


@router.get(
    "/{export_type}",
    response_class=StreamingResponse,
    responses={400: {"description": "Invalid export type"}},
)
async def export_data(
    export_type: str,
    format: Annotated[
        str, Query(description="Export format", pattern="^(csv|json)$")
    ] = "json",
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    """
    Export clusters, ideas, or posts as CSV or JSON file download.

    - **export_type**: `clusters`, `ideas`, or `posts`
    - **format**: `csv` or `json`
    """
    exporter = _EXPORTERS.get(export_type)
    if exporter is None:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid export_type '{export_type}'. Must be one of: clusters, ideas, posts",
        )

    rows, fields = await exporter(db)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    filename = f"{export_type}_{timestamp}"

    if format == "csv":
        content = _build_csv(rows, fields)
        return StreamingResponse(
            iter([content]),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}.csv"'},
        )

    # JSON
    # Serialize datetimes for JSON output
    serialized = [
        {k: _serialize(v) if isinstance(v, datetime) else v for k, v in row.items()}
        for row in rows
    ]
    content = json.dumps(serialized, indent=2, default=str)
    return StreamingResponse(
        iter([content]),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}.json"'},
    )
