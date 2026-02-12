"""
Cluster API endpoints.

Provides access to discovered opportunity clusters with evidence and analytics.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.core.cache import cached_route
from packages.core.database import get_db
from packages.core.models import Cluster, ClusterMembership, IdeaCandidate

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("")
@cached_route(
    "clusters:list", ttl=300, key_params=["sort_by", "order", "limit", "offset", "min_size"]
)
async def list_clusters(
    sort_by: str = Query(
        "size", description="Sort field: size, quality, trend, sentiment, created_at"
    ),
    order: str = Query("desc", description="Sort order: asc or desc"),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    min_size: int | None = Query(None, ge=1, description="Minimum idea count"),
    db: AsyncSession = Depends(get_db),
):
    """
    List all clusters with pagination and sorting.

    Returns cluster summaries with metadata (keywords, counts, scores).
    """
    # Build query
    query = select(Cluster)

    # Apply filters
    if min_size is not None:
        query = query.where(Cluster.idea_count >= min_size)

    # Apply sorting
    sort_field_map = {
        "size": Cluster.idea_count,
        "quality": Cluster.quality_score,
        "trend": Cluster.trend_score,
        "sentiment": Cluster.avg_sentiment,
        "created_at": Cluster.created_at,
    }

    if sort_by not in sort_field_map:
        raise HTTPException(status_code=400, detail=f"Invalid sort_by: {sort_by}")

    sort_field = sort_field_map[sort_by]
    query = query.order_by(desc(sort_field) if order == "desc" else sort_field)

    # Get total count
    count_query = select(func.count()).select_from(Cluster)
    if min_size is not None:
        count_query = count_query.where(Cluster.idea_count >= min_size)

    result = await db.execute(count_query)
    total = result.scalar_one()

    # Apply pagination
    query = query.limit(limit).offset(offset)

    # Execute query
    result = await db.execute(query)
    clusters = result.scalars().all()

    logger.info(f"Retrieved {len(clusters)} clusters (total: {total}, offset: {offset})")

    return {
        "clusters": [
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
            for cluster in clusters
        ],
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total,
        },
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
    # Fetch cluster
    query = select(Cluster).where(Cluster.id == cluster_id)
    result = await db.execute(query)
    cluster = result.scalar_one_or_none()

    if not cluster:
        raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")

    response = {
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

    # Include evidence if requested
    if include_evidence:
        # Fetch representative ideas
        evidence_query = (
            select(ClusterMembership, IdeaCandidate)
            .join(IdeaCandidate, ClusterMembership.idea_id == IdeaCandidate.id)
            .where(
                ClusterMembership.cluster_id == cluster_id,
                ClusterMembership.is_representative == True,
            )
            .order_by(desc(ClusterMembership.similarity_score))
            .limit(evidence_limit)
        )

        result = await db.execute(evidence_query)
        evidence_rows = result.all()

        response["evidence"] = [
            {
                "id": str(idea.id),
                "problem_statement": idea.problem_statement,
                "context": idea.context,
                "sentiment": idea.sentiment,
                "sentiment_score": idea.sentiment_score,
                "quality_score": idea.quality_score,
                "similarity_score": membership.similarity_score,
                "extracted_at": idea.extracted_at.isoformat(),
            }
            for membership, idea in evidence_rows
        ]

    logger.info(f"Retrieved cluster {cluster_id}: {cluster.label}")

    return response


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
    # Fetch source cluster
    query = select(Cluster).where(Cluster.id == cluster_id)
    result = await db.execute(query)
    source_cluster = result.scalar_one_or_none()

    if not source_cluster:
        raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")

    source_keywords = set(source_cluster.keywords)

    # Fetch all other clusters
    query = select(Cluster).where(Cluster.id != cluster_id)
    result = await db.execute(query)
    all_clusters = result.scalars().all()

    # Calculate similarity based on keyword overlap
    similar_clusters = []
    for cluster in all_clusters:
        cluster_keywords = set(cluster.keywords)

        # Jaccard similarity: intersection / union
        intersection = len(source_keywords & cluster_keywords)
        union = len(source_keywords | cluster_keywords)
        similarity_score = intersection / union if union > 0 else 0.0

        if similarity_score > 0:
            similar_clusters.append(
                {
                    "id": str(cluster.id),
                    "label": cluster.label,
                    "keywords": cluster.keywords,
                    "idea_count": cluster.idea_count,
                    "quality_score": cluster.quality_score,
                    "similarity_score": similarity_score,
                }
            )

    # Sort by similarity and limit
    similar_clusters.sort(key=lambda x: x["similarity_score"], reverse=True)
    similar_clusters = similar_clusters[:limit]

    logger.info(f"Found {len(similar_clusters)} similar clusters to {cluster_id}")

    return {
        "source_cluster": {
            "id": str(source_cluster.id),
            "label": source_cluster.label,
            "keywords": source_cluster.keywords,
        },
        "similar_clusters": similar_clusters,
    }


@router.get("/trending/list")
async def get_trending_clusters(
    limit: int = Query(10, ge=1, le=50, description="Number of clusters"),
    min_trend_score: float = Query(0.5, ge=0.0, le=1.0, description="Minimum trend score"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get currently trending clusters (high recent growth).

    Returns clusters sorted by trend score.
    """
    # Query trending clusters
    query = (
        select(Cluster)
        .where(Cluster.trend_score >= min_trend_score)
        .order_by(desc(Cluster.trend_score))
        .limit(limit)
    )

    result = await db.execute(query)
    clusters = result.scalars().all()

    logger.info(f"Retrieved {len(clusters)} trending clusters")

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
            for cluster in clusters
        ]
    }
