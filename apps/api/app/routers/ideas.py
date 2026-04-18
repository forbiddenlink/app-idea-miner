"""
API endpoints for idea candidates.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.constants import DEFAULT_PAGE_LIMIT, MAX_PAGE_LIMIT
from apps.api.app.core.rate_limit import RateLimiter
from apps.api.app.core.security import get_api_key
from apps.api.app.database import get_db
from apps.api.app.schemas.ideas import (
    IdeaDetailResponse,
    IdeaListResponse,
    IdeaSearchResponse,
    IdeaStatsResponse,
    SimilarIdeasResponse,
)
from apps.api.app.services.idea_service import IdeaService
from packages.core.services.similarity_service import SimilarityService

router = APIRouter(
    tags=["ideas"],
    dependencies=[Depends(get_api_key), Depends(RateLimiter(times=100, seconds=60))],
)
logger = logging.getLogger(__name__)


@router.get("", response_model=IdeaListResponse)
async def list_ideas(
    limit: int = Query(DEFAULT_PAGE_LIMIT, ge=1, le=MAX_PAGE_LIMIT),
    offset: int = Query(0, ge=0),
    domain: str | None = None,
    sentiment: str | None = None,
    min_quality: float | None = Query(None, ge=0.0, le=1.0),
    q: str | None = Query(None, min_length=2),
    competitor: str | None = Query(
        None, min_length=2, description="Filter by competitor mentioned"
    ),
    sort_by: str = Query("quality", pattern="^(quality|date|sentiment)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
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
        q: Optional keyword search query
        competitor: Filter by competitor mentioned (e.g., notion, slack, todoist)
        sort_by: Sort field (quality, date, sentiment)
        order: Sort direction (asc, desc)
        db: Database session

    Returns:
        Dict with ideas list and pagination metadata
    """
    try:
        service = IdeaService(db)
        result = await service.get_ideas(
            limit=limit,
            offset=offset,
            domain=domain,
            sentiment=sentiment,
            min_quality=min_quality,
            q=q,
            competitor=competitor,
            sort_by=sort_by,
            order=order,
        )

        ideas = result["ideas"]

        # Format response
        ideas_data = [
            {
                "id": str(idea.id),
                "problem_statement": idea.problem_statement,
                "context": idea.context,
                "domain": idea.domain,
                "sentiment": idea.sentiment,
                "sentiment_score": idea.sentiment_score,
                "emotions": idea.emotions,
                "quality_score": idea.quality_score,
                "features_mentioned": idea.features_mentioned,
                "competitors_mentioned": idea.competitors_mentioned,
                "aspect_sentiments": idea.aspect_sentiments,
                "urgency_level": idea.urgency_level,
                "extracted_at": idea.extracted_at.isoformat()
                if idea.extracted_at
                else None,
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
            "pagination": result["pagination"],
        }

    except OperationalError as e:
        logger.error(f"Database connection error listing ideas: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail="Database unavailable")


@router.get("/{idea_id}", response_model=IdeaDetailResponse)
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
        service = IdeaService(db)
        idea = await service.get_idea_by_id(idea_id)

        if not idea:
            raise HTTPException(status_code=404, detail="Idea not found")

        return {
            "id": str(idea.id),
            "problem_statement": idea.problem_statement,
            "context": idea.context,
            "domain": idea.domain,
            "sentiment": idea.sentiment,
            "sentiment_score": idea.sentiment_score,
            "emotions": idea.emotions,
            "quality_score": idea.quality_score,
            "features_mentioned": idea.features_mentioned,
            "competitors_mentioned": idea.competitors_mentioned,
            "aspect_sentiments": idea.aspect_sentiments,
            "urgency_level": idea.urgency_level,
            "extracted_at": idea.extracted_at.isoformat()
            if idea.extracted_at
            else None,
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
    except OperationalError as e:
        logger.error(
            f"Database connection error fetching idea {idea_id}: {e}", exc_info=True
        )
        raise HTTPException(status_code=503, detail="Database unavailable")


@router.get("/{idea_id}/similar", response_model=SimilarIdeasResponse)
async def get_similar_ideas(
    idea_id: UUID,
    limit: int = Query(10, ge=1, le=50),
    min_similarity: float = Query(0.7, ge=0.0, le=1.0),
    db: AsyncSession = Depends(get_db),
):
    """
    Find ideas similar to the given idea using vector similarity.

    Uses cosine similarity on embeddings to find semantically similar ideas.

    Args:
        idea_id: UUID of the source idea
        limit: Maximum number of similar ideas (max 50)
        min_similarity: Minimum similarity score (0-1)
        db: Database session

    Returns:
        List of similar ideas with similarity scores
    """
    try:
        service = SimilarityService(db)
        similar = await service.find_similar_ideas(
            idea_id=idea_id,
            limit=limit,
            min_similarity=min_similarity,
        )

        # Format response
        similar_data = [
            {
                "id": str(item["idea"].id),
                "problem_statement": item["idea"].problem_statement,
                "context": item["idea"].context,
                "domain": item["idea"].domain,
                "sentiment": item["idea"].sentiment,
                "sentiment_score": item["idea"].sentiment_score,
                "quality_score": item["idea"].quality_score,
                "features_mentioned": item["idea"].features_mentioned,
                "extracted_at": item["idea"].extracted_at.isoformat()
                if item["idea"].extracted_at
                else None,
                "similarity": item["similarity"],
                "raw_post": {
                    "id": str(item["idea"].raw_post.id),
                    "url": item["idea"].raw_post.url,
                    "title": item["idea"].raw_post.title,
                    "source": item["idea"].raw_post.source,
                    "published_at": item["idea"].raw_post.published_at.isoformat()
                    if item["idea"].raw_post.published_at
                    else None,
                }
                if item["idea"].raw_post
                else None,
            }
            for item in similar
        ]

        return {
            "source_idea_id": str(idea_id),
            "similar_ideas": similar_data,
            "total": len(similar_data),
        }

    except OperationalError as e:
        logger.error(
            f"Database connection error finding similar ideas: {e}", exc_info=True
        )
        raise HTTPException(status_code=503, detail="Database unavailable")


@router.get("/search/query", response_model=IdeaSearchResponse)
async def search_ideas(
    q: str = Query(..., min_length=2),
    limit: int = Query(DEFAULT_PAGE_LIMIT, ge=1, le=MAX_PAGE_LIMIT),
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
        service = IdeaService(db)
        result = await service.search_ideas(q=q, limit=limit, offset=offset)

        ideas = result["results"]

        # Format response
        ideas_data = [
            {
                "id": str(idea.id),
                "problem_statement": idea.problem_statement,
                "domain": idea.domain,
                "sentiment": idea.sentiment,
                "quality_score": idea.quality_score,
                "extracted_at": idea.extracted_at.isoformat()
                if idea.extracted_at
                else None,
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
            "query": result["query"],
            "results": ideas_data,
            "pagination": result["pagination"],
        }

    except OperationalError as e:
        logger.error(f"Database connection error searching ideas: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail="Database unavailable")


@router.get("/stats/summary", response_model=IdeaStatsResponse)
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
        service = IdeaService(db)
        return await service.get_ideas_stats()

    except OperationalError as e:
        logger.error(
            f"Database connection error fetching ideas stats: {e}", exc_info=True
        )
        raise HTTPException(status_code=503, detail="Database unavailable")
