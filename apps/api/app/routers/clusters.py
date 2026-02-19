"""
Cluster API endpoints.

Provides access to discovered opportunity clusters with evidence and analytics.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.constants import DEFAULT_PAGE_LIMIT, MAX_PAGE_LIMIT
from apps.api.app.core.rate_limit import RateLimiter
from apps.api.app.core.security import get_api_key
from apps.api.app.database import get_db
from apps.api.app.services.cluster_service import ClusterService
from packages.core.cache import cached_route

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["clusters"],
    dependencies=[Depends(get_api_key), Depends(RateLimiter(times=100, seconds=60))],
)


@router.get("")
@cached_route(
    "clusters:list",
    ttl=300,
    key_params=["sort_by", "order", "limit", "offset", "min_size", "q"],
)
async def list_clusters(
    sort_by: str = Query(
        "size", description="Sort field: size, quality, trend, sentiment, created_at"
    ),
    order: str = Query("desc", description="Sort order: asc or desc"),
    limit: int = Query(
        DEFAULT_PAGE_LIMIT, ge=1, le=MAX_PAGE_LIMIT, description="Results per page"
    ),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    min_size: int | None = Query(None, ge=1, description="Minimum idea count"),
    q: str | None = Query(
        None, min_length=1, description="Search by label/description/keywords"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    List all clusters with pagination and sorting.

    Returns cluster summaries with metadata (keywords, counts, scores).
    """
    service = ClusterService(db)
    result = await service.get_all_clusters(
        sort_by=sort_by,
        order=order,
        limit=limit,
        offset=offset,
        min_size=min_size,
        q=q,
    )

    logger.info(
        f"Retrieved {len(result['clusters'])} clusters (total: {result['pagination']['total']}, offset: {offset})"
    )

    # Transform ORM objects to response format (if needed, but service returns logic)
    # The service returns ORM objects in 'clusters' key. We format them here or in service.
    # Service returns ORM objects. We format here to match API contract.
    formatted_clusters = [
        {
            "id": str(cluster.id),
            "label": cluster.label,
            "description": cluster.description,
            "keywords": cluster.keywords,
            "idea_count": cluster.idea_count,
            "avg_sentiment": cluster.avg_sentiment,
            "quality_score": cluster.quality_score,
            "trend_score": cluster.trend_score,
            "created_at": cluster.created_at.isoformat(),
            "updated_at": cluster.updated_at.isoformat(),
        }
        for cluster in result["clusters"]
    ]

    return {
        "clusters": formatted_clusters,
        "pagination": result["pagination"],
    }


@router.get("/{cluster_id}")
async def get_cluster(
    cluster_id: UUID,
    include_evidence: bool = Query(True, description="Include representative ideas"),
    evidence_limit: int = Query(5, ge=1, le=20, description="Number of evidence items"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed information about a specific cluster.

    Returns cluster metadata plus representative ideas (evidence).
    """
    service = ClusterService(db)
    result = await service.get_cluster_by_id(
        cluster_id=cluster_id,
        include_evidence=include_evidence,
        evidence_limit=evidence_limit,
    )

    if not result:
        raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")

    logger.info(f"Retrieved cluster {cluster_id}: {result['label']}")

    return result


@router.get("/{cluster_id}/similar")
async def get_similar_clusters(
    cluster_id: UUID,
    limit: int = Query(5, ge=1, le=20, description="Number of similar clusters"),
    db: AsyncSession = Depends(get_db),
):
    """
    Find clusters similar to the given cluster.

    Uses keyword overlap to determine similarity.
    """
    service = ClusterService(db)
    result = await service.find_similar_clusters(cluster_id=cluster_id, limit=limit)

    if not result:
        raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")

    logger.info(
        f"Found {len(result['similar_clusters'])} similar clusters to {cluster_id}"
    )

    return result


@router.get("/trending/list")
async def get_trending_clusters(
    limit: int = Query(10, ge=1, le=50, description="Number of clusters"),
    min_trend_score: float = Query(
        0.5, ge=0.0, le=1.0, description="Minimum trend score"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Get currently trending clusters (high recent growth).

    Returns clusters sorted by trend score.
    """
    service = ClusterService(db)
    trending_clusters = await service.get_trending_clusters(
        limit=limit, min_trend_score=min_trend_score
    )

    logger.info(f"Retrieved {len(trending_clusters)} trending clusters")

    return {
        "trending": [
            {
                "id": str(cluster.id),
                "label": cluster.label,
                "keywords": cluster.keywords,
                "idea_count": cluster.idea_count,
                "trend_score": cluster.trend_score,
                "quality_score": cluster.quality_score,
                "avg_sentiment": cluster.avg_sentiment,
            }
            for cluster in trending_clusters
        ]
    }
