"""
Opportunity scoring service.

Computes market validation scores for clusters based on
demand signals, sentiment, quality, trends, and evidence diversity.
"""

import logging
import math
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.core.models import Cluster, ClusterMembership, IdeaCandidate

logger = logging.getLogger(__name__)


def compute_opportunity_score(
    idea_count: int,
    avg_sentiment: float,
    quality_score: float,
    trend_score: float,
    unique_domains: int,
) -> dict:
    """
    Compute opportunity score (0-100) from cluster signals.

    Returns breakdown dict with total and component scores.
    """
    demand = min(30, round(math.log2(max(idea_count, 1) + 1) * 10))
    sentiment = round((max(min(avg_sentiment, 1.0), -1.0) + 1) / 2 * 20)
    quality = round(max(min(quality_score, 1.0), 0.0) * 25)
    trend = round(min(max(trend_score, 0.0), 1.0) * 15)
    diversity = min(10, unique_domains * 2)

    total = demand + sentiment + quality + trend + diversity

    # Determine grade
    if total >= 80:
        grade = "A"
        verdict = "Strong opportunity — high demand with quality signals"
    elif total >= 60:
        grade = "B"
        verdict = "Promising opportunity — worth further validation"
    elif total >= 40:
        grade = "C"
        verdict = "Moderate opportunity — needs more evidence"
    elif total >= 20:
        grade = "D"
        verdict = "Weak opportunity — limited signals detected"
    else:
        grade = "F"
        verdict = "Insufficient data to evaluate"

    return {
        "total": total,
        "grade": grade,
        "verdict": verdict,
        "breakdown": {
            "demand": {
                "score": demand,
                "max": 30,
                "description": f"{idea_count} ideas detected",
            },
            "sentiment": {
                "score": sentiment,
                "max": 20,
                "description": f"Avg sentiment: {avg_sentiment:.2f}",
            },
            "quality": {
                "score": quality,
                "max": 25,
                "description": f"Quality score: {quality_score:.2f}",
            },
            "trend": {
                "score": trend,
                "max": 15,
                "description": f"Trend score: {trend_score:.2f}",
            },
            "diversity": {
                "score": diversity,
                "max": 10,
                "description": f"{unique_domains} unique domain(s)",
            },
        },
    }


class OpportunityService:
    """Service for computing and retrieving opportunity scores."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_cluster_opportunity(self, cluster_id: UUID) -> dict | None:
        """Get opportunity score for a single cluster."""
        # Fetch cluster
        stmt = select(Cluster).where(Cluster.id == cluster_id)
        result = await self.db.execute(stmt)
        cluster = result.scalar_one_or_none()

        if not cluster:
            return None

        # Get unique domains for this cluster
        domain_stmt = (
            select(func.count(func.distinct(IdeaCandidate.domain)))
            .join(ClusterMembership, ClusterMembership.idea_id == IdeaCandidate.id)
            .where(ClusterMembership.cluster_id == cluster_id)
            .where(IdeaCandidate.domain.isnot(None))
        )
        domain_result = await self.db.execute(domain_stmt)
        unique_domains = domain_result.scalar_one() or 0

        score = compute_opportunity_score(
            idea_count=cluster.idea_count or 0,
            avg_sentiment=cluster.avg_sentiment or 0.0,
            quality_score=cluster.quality_score or 0.0,
            trend_score=cluster.trend_score or 0.0,
            unique_domains=unique_domains,
        )

        return {
            "cluster_id": str(cluster.id),
            "cluster_label": cluster.label,
            "opportunity_score": score,
        }

    async def get_all_opportunities(
        self,
        limit: int = 20,
        offset: int = 0,
        min_score: int = 0,
        sort_by: str = "score",
    ) -> dict:
        """Get opportunity scores for all clusters, ranked."""
        # Fetch all clusters
        stmt = select(Cluster).order_by(Cluster.idea_count.desc())
        result = await self.db.execute(stmt)
        clusters = result.scalars().all()

        # Get unique domains per cluster in one query
        domain_stmt = (
            select(
                ClusterMembership.cluster_id,
                func.count(func.distinct(IdeaCandidate.domain)).label("unique_domains"),
            )
            .join(IdeaCandidate, ClusterMembership.idea_id == IdeaCandidate.id)
            .where(IdeaCandidate.domain.isnot(None))
            .group_by(ClusterMembership.cluster_id)
        )
        domain_result = await self.db.execute(domain_stmt)
        domain_map = {row.cluster_id: row.unique_domains for row in domain_result}

        # Compute scores
        opportunities = []
        for cluster in clusters:
            unique_domains = domain_map.get(cluster.id, 0)
            score = compute_opportunity_score(
                idea_count=cluster.idea_count or 0,
                avg_sentiment=cluster.avg_sentiment or 0.0,
                quality_score=cluster.quality_score or 0.0,
                trend_score=cluster.trend_score or 0.0,
                unique_domains=unique_domains,
            )

            if score["total"] >= min_score:
                opportunities.append(
                    {
                        "cluster_id": str(cluster.id),
                        "cluster_label": cluster.label,
                        "keywords": cluster.keywords or [],
                        "idea_count": cluster.idea_count or 0,
                        "opportunity_score": score,
                    }
                )

        # Sort
        if sort_by == "score":
            opportunities.sort(
                key=lambda x: x["opportunity_score"]["total"], reverse=True
            )
        elif sort_by == "demand":
            opportunities.sort(key=lambda x: x["idea_count"], reverse=True)
        elif sort_by == "trend":
            opportunities.sort(
                key=lambda x: x["opportunity_score"]["breakdown"]["trend"]["score"],
                reverse=True,
            )

        total = len(opportunities)
        paginated = opportunities[offset : offset + limit]

        return {
            "opportunities": paginated,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total,
            },
        }
