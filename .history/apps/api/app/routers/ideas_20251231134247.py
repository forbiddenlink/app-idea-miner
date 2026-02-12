"""
API endpoints for idea candidates.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.api.app.database import get_db
from packages.core.models import IdeaCandidate

router = APIRouter(tags=["ideas"])
logger = logging.getLogger(__name__)


@router.get("")
async def list_ideas(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    domain: str | None = None,
    sentiment: str | None = None,
    min_quality: float | None = Query(None, ge=0.0, le=1.0),
    db: AsyncSession = Depends(get_db),
):
    """
    List idea candidates with filtering and pagination.

    Args:
        limit: Maximum results per page (max 100)
        offset: Pagination offset
        domain: Filter by domain (productivity, health, finance, etc.)
        sentiment: Filter by sentiment (positive, neutral, negative)
        min_quality: Minimum quality score (0-1)
        db: Database session

    Returns:
        Dict with ideas list and pagination metadata
    """
    try:
        # Build query
        stmt = select(IdeaCandidate).options(selectinload(IdeaCandidate.raw_post))

        # Apply filters
        if domain:
            stmt = stmt.where(IdeaCandidate.domain == domain)
        if sentiment:
            stmt = stmt.where(IdeaCandidate.sentiment == sentiment)
        if min_quality is not None:
            stmt = stmt.where(IdeaCandidate.quality_score >= min_quality)

        # Order by quality and recency
        stmt = stmt.order_by(IdeaCandidate.quality_score.desc(), IdeaCandidate.extracted_at.desc())

        # Get total count
        count_stmt = select(func.count()).select_from(IdeaCandidate)
        if domain:
            count_stmt = count_stmt.where(IdeaCandidate.domain == domain)
        if sentiment:
            count_stmt = count_stmt.where(IdeaCandidate.sentiment == sentiment)
        if min_quality is not None:
            count_stmt = count_stmt.where(IdeaCandidate.quality_score >= min_quality)

        count_result = await db.execute(count_stmt)
        total = count_result.scalar_one()

        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)

        # Execute query
        result = await db.execute(stmt)
        ideas = result.scalars().all()

        # Format response
        ideas_data = [
            {
                "id": str(idea.id),
                "problem_statement": idea.problem_statement,
                "solution_hint": idea.solution_hint,
                "domain": idea.domain,
                "sentiment": idea.sentiment,
                "sentiment_score": idea.sentiment_score,
                "quality_score": idea.quality_score,
                "features_mentioned": idea.features_mentioned,
                "extracted_at": idea.extracted_at.isoformat() if idea.extracted_at else None,
                "raw_post": {
                    "id": str(idea.raw_post.id),
                    "url": idea.raw_post.url,
                    "title": idea.raw_post.title,
                    "source": idea.raw_post.source,
                    "published_at": idea.raw_post.published_at.isoformat()
                    if idea.raw_post.published_at
                    else None,
                }
                if idea.raw_post
                else None,
            }
            for idea in ideas
        ]

        return {
            "ideas": ideas_data,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total,
            },
        }

    except Exception as e:
        logger.error(f"Error listing ideas: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{idea_id}")
async def get_idea(
    idea_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a single idea by ID with full details.

    Args:
        idea_id: UUID of the idea
        db: Database session

    Returns:
        Idea details with raw post information
    """
    try:
        stmt = (
            select(IdeaCandidate)
            .where(IdeaCandidate.id == idea_id)
            .options(selectinload(IdeaCandidate.raw_post))
        )

        result = await db.execute(stmt)
        idea = result.scalar_one_or_none()

        if not idea:
            raise HTTPException(status_code=404, detail="Idea not found")

        return {
            "id": str(idea.id),
            "problem_statement": idea.problem_statement,
            "solution_hint": idea.solution_hint,
            "domain": idea.domain,
            "sentiment": idea.sentiment,
            "sentiment_score": idea.sentiment_score,
            "quality_score": idea.quality_score,
            "features_mentioned": idea.features_mentioned,
            "extracted_at": idea.extracted_at.isoformat() if idea.extracted_at else None,
            "created_at": idea.created_at.isoformat() if idea.created_at else None,
            "updated_at": idea.updated_at.isoformat() if idea.updated_at else None,
            "raw_post": {
                "id": str(idea.raw_post.id),
                "url": idea.raw_post.url,
                "title": idea.raw_post.title,
                "content": idea.raw_post.content,
                "source": idea.raw_post.source,
                "author": idea.raw_post.author,
                "published_at": idea.raw_post.published_at.isoformat()
                if idea.raw_post.published_at
                else None,
                "fetched_at": idea.raw_post.fetched_at.isoformat()
                if idea.raw_post.fetched_at
                else None,
                "source_metadata": idea.raw_post.source_metadata,
            }
            if idea.raw_post
            else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching idea {idea_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/search/query")
async def search_ideas(
    q: str = Query(..., min_length=2),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    Search ideas by keyword (case-insensitive).

    Args:
        q: Search query
        limit: Maximum results
        offset: Pagination offset
        db: Database session

    Returns:
        Matching ideas with pagination
    """
    try:
        # Simple case-insensitive search on problem_statement
        # For production, use PostgreSQL full-text search with ts_vector
        stmt = (
            select(IdeaCandidate)
            .where(IdeaCandidate.problem_statement.ilike(f"%{q}%"))
            .options(selectinload(IdeaCandidate.raw_post))
            .order_by(IdeaCandidate.quality_score.desc())
        )

        # Get total count
        count_stmt = (
            select(func.count())
            .select_from(IdeaCandidate)
            .where(IdeaCandidate.problem_statement.ilike(f"%{q}%"))
        )
        count_result = await db.execute(count_stmt)
        total = count_result.scalar_one()

        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)

        # Execute
        result = await db.execute(stmt)
        ideas = result.scalars().all()

        # Format response
        ideas_data = [
            {
                "id": str(idea.id),
                "problem_statement": idea.problem_statement,
                "domain": idea.domain,
                "sentiment": idea.sentiment,
                "quality_score": idea.quality_score,
                "extracted_at": idea.extracted_at.isoformat() if idea.extracted_at else None,
                "raw_post": {
                    "url": idea.raw_post.url,
                    "title": idea.raw_post.title,
                    "source": idea.raw_post.source,
                }
                if idea.raw_post
                else None,
            }
            for idea in ideas
        ]

        return {
            "query": q,
            "results": ideas_data,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total,
            },
        }

    except Exception as e:
        logger.error(f"Error searching ideas: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/stats/summary")
async def get_ideas_stats(
    db: AsyncSession = Depends(get_db),
):
    """
    Get statistics about idea candidates.

    Args:
        db: Database session

    Returns:
        Dict with various statistics
    """
    try:
        # Total ideas
        total_stmt = select(func.count()).select_from(IdeaCandidate)
        total_result = await db.execute(total_stmt)
        total = total_result.scalar_one()

        # By domain
        domain_stmt = (
            select(IdeaCandidate.domain, func.count(IdeaCandidate.id).label("count"))
            .group_by(IdeaCandidate.domain)
            .order_by(func.count(IdeaCandidate.id).desc())
        )

        domain_result = await db.execute(domain_stmt)
        by_domain = {row.domain: row.count for row in domain_result.fetchall()}

        # By sentiment
        sentiment_stmt = select(
            IdeaCandidate.sentiment, func.count(IdeaCandidate.id).label("count")
        ).group_by(IdeaCandidate.sentiment)

        sentiment_result = await db.execute(sentiment_stmt)
        by_sentiment = {row.sentiment: row.count for row in sentiment_result.fetchall()}

        # Average quality score
        avg_quality_stmt = select(func.avg(IdeaCandidate.quality_score))
        avg_quality_result = await db.execute(avg_quality_stmt)
        avg_quality = avg_quality_result.scalar_one()

        return {
            "total": total,
            "by_domain": by_domain,
            "by_sentiment": by_sentiment,
            "avg_quality_score": float(avg_quality) if avg_quality else 0.0,
        }

    except Exception as e:
        logger.error(f"Error fetching ideas stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
