"""
Opportunity scoring API endpoints.

Provides market validation scores for clusters based on
demand, sentiment, quality, trends, and evidence diversity.
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
from apps.api.app.schemas.opportunities import (
    OpportunityDetailResponse,
    OpportunityListResponse,
)
from apps.api.app.services.opportunity_service import OpportunityService

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["opportunities"],
    dependencies=[Depends(get_api_key), Depends(RateLimiter(times=100, seconds=60))],
)


@router.get("", response_model=OpportunityListResponse)
async def list_opportunities(
    limit: int = Query(DEFAULT_PAGE_LIMIT, ge=1, le=MAX_PAGE_LIMIT),
    offset: int = Query(0, ge=0),
    min_score: int = Query(0, ge=0, le=100),
    sort_by: str = Query("score", pattern="^(score|demand|trend)$"),
    db: AsyncSession = Depends(get_db),
):
    """
    List all clusters ranked by opportunity score.

    The opportunity score (0-100) evaluates market validation based on:
    - Demand (30%): Number of ideas expressing this need
    - Sentiment (20%): Average user sentiment
    - Quality (25%): Quality of extracted ideas
    - Trend (15%): Growth momentum
    - Diversity (10%): Cross-domain evidence
    """
    try:
        service = OpportunityService(db)
        return await service.get_all_opportunities(
            limit=limit,
            offset=offset,
            min_score=min_score,
            sort_by=sort_by,
        )
    except OperationalError as e:
        logger.error(f"Database error listing opportunities: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail="Database unavailable")


@router.get("/{cluster_id}", response_model=OpportunityDetailResponse)
async def get_opportunity(
    cluster_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed opportunity score for a specific cluster.

    Returns score breakdown with grade (A-F) and verdict.
    """
    try:
        service = OpportunityService(db)
        result = await service.get_cluster_opportunity(cluster_id)

        if not result:
            raise HTTPException(status_code=404, detail="Cluster not found")

        return result
    except HTTPException:
        raise
    except OperationalError as e:
        logger.error(
            f"Database error fetching opportunity {cluster_id}: {e}", exc_info=True
        )
        raise HTTPException(status_code=503, detail="Database unavailable")
