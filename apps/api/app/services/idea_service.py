"""
Idea service - Business logic for idea candidates.

Handles idea retrieval, searching, and statistics.
"""

from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from packages.core.models import IdeaCandidate


class IdeaService:
    """Service for idea-related business logic."""

    def __init__(self, db: AsyncSession):
        """
        Initialize idea service.

        Args:
            db: Async database session
        """
        self.db = db

    async def get_ideas(
        self,
        limit: int = 20,
        offset: int = 0,
        domain: str | None = None,
        sentiment: str | None = None,
        min_quality: float | None = None,
        q: str | None = None,
        sort_by: str = "quality",
        order: str = "desc",
    ) -> dict[str, Any]:
        """
        List idea candidates with filtering and pagination.

        Args:
            limit: Maximum results per page
            offset: Pagination offset
            domain: Filter by domain
            sentiment: Filter by sentiment
            min_quality: Minimum quality score
            q: Optional keyword search
            sort_by: quality, date, or sentiment
            order: asc or desc

        Returns:
            Dict with 'ideas' list and 'pagination' info
        """
        # Build query
        stmt = select(IdeaCandidate).options(selectinload(IdeaCandidate.raw_post))

        # Apply filters
        if domain:
            stmt = stmt.where(IdeaCandidate.domain == domain)
        if sentiment:
            stmt = stmt.where(IdeaCandidate.sentiment == sentiment)
        if min_quality is not None:
            stmt = stmt.where(IdeaCandidate.quality_score >= min_quality)
        if q and q.strip():
            pattern = f"%{q.strip()}%"
            search_filter = or_(
                IdeaCandidate.problem_statement.ilike(pattern),
                IdeaCandidate.context.ilike(pattern),
            )
            stmt = stmt.where(search_filter)

        # Sort by requested field with deterministic tiebreakers
        sort_column_map = {
            "quality": IdeaCandidate.quality_score,
            "date": IdeaCandidate.extracted_at,
            "sentiment": IdeaCandidate.sentiment_score,
        }
        sort_column = sort_column_map.get(sort_by, IdeaCandidate.quality_score)
        primary_sort = sort_column.asc() if order == "asc" else sort_column.desc()
        if sort_by == "date":
            stmt = stmt.order_by(primary_sort, IdeaCandidate.quality_score.desc())
        elif sort_by == "sentiment":
            stmt = stmt.order_by(
                primary_sort,
                IdeaCandidate.quality_score.desc(),
                IdeaCandidate.extracted_at.desc(),
            )
        else:
            stmt = stmt.order_by(primary_sort, IdeaCandidate.extracted_at.desc())

        # Get total count
        count_stmt = select(func.count()).select_from(IdeaCandidate)
        if domain:
            count_stmt = count_stmt.where(IdeaCandidate.domain == domain)
        if sentiment:
            count_stmt = count_stmt.where(IdeaCandidate.sentiment == sentiment)
        if min_quality is not None:
            count_stmt = count_stmt.where(IdeaCandidate.quality_score >= min_quality)
        if q and q.strip():
            pattern = f"%{q.strip()}%"
            count_stmt = count_stmt.where(
                or_(
                    IdeaCandidate.problem_statement.ilike(pattern),
                    IdeaCandidate.context.ilike(pattern),
                )
            )

        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)

        # Execute query
        result = await self.db.execute(stmt)
        ideas = result.scalars().all()

        return {
            "ideas": ideas,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total,
            },
        }

    async def get_idea_by_id(self, idea_id: UUID) -> IdeaCandidate | None:
        """
        Get a single idea by ID with full details.

        Args:
            idea_id: UUID of the idea

        Returns:
            IdeaCandidate or None if not found
        """
        stmt = (
            select(IdeaCandidate)
            .where(IdeaCandidate.id == idea_id)
            .options(selectinload(IdeaCandidate.raw_post))
        )

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def search_ideas(
        self,
        q: str,
        limit: int = 20,
        offset: int = 0,
        query_vector: list[float] | None = None,
    ) -> dict[str, Any]:
        """
        Search ideas by keyword or semantic vector.

        Args:
            q: Search text (used for keyword highlight/logging)
            limit: Maximum results
            offset: Pagination offset
            query_vector: Optional embedding vector for semantic search

        Returns:
            Dict with matching results and pagination
        """
        # Strategy 1: Semantic Search (if vector provided)
        if query_vector:
            distance_expr = IdeaCandidate.idea_vector.cosine_distance(query_vector)
            stmt = (
                select(IdeaCandidate, distance_expr.label("distance"))
                .where(IdeaCandidate.idea_vector.is_not(None))
                .order_by(distance_expr)
                .limit(limit)
                .offset(offset)
            )

            result = await self.db.execute(stmt)
            rows = result.all()

            # Format results with similarity score
            results = []
            for idea, distance in rows:
                # Approximate similarity
                similarity = 1 - distance if distance <= 1 else 0
                # Attach temporary score (not on model)
                idea.similarity_score = float(similarity)
                results.append(idea)

            # For count, we might just estimate or query all
            # (Vector search usually limits recall, so 'total' is fuzzy)
            total = len(results)  # Simplified, usually you don't count all vectors
            has_more = False

        else:
            # Strategy 2: Keyword Search (Legacy)
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
            count_result = await self.db.execute(count_stmt)
            total = count_result.scalar_one()

            # Apply pagination
            stmt = stmt.limit(limit).offset(offset)

            # Execute
            result = await self.db.execute(stmt)
            results = result.scalars().all()
            has_more = offset + limit < total

        return {
            "query": q,
            "results": results,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": has_more,
            },
        }

    async def get_ideas_stats(self) -> dict[str, Any]:
        """
        Get statistics about idea candidates.

        Returns:
            Dict with total count, breakdowns by domain/sentiment, and average quality
        """
        # Total ideas
        total_stmt = select(func.count()).select_from(IdeaCandidate)
        total_result = await self.db.execute(total_stmt)
        total = total_result.scalar_one()

        # By domain
        domain_stmt = (
            select(IdeaCandidate.domain, func.count(IdeaCandidate.id).label("count"))
            .group_by(IdeaCandidate.domain)
            .order_by(func.count(IdeaCandidate.id).desc())
        )

        domain_result = await self.db.execute(domain_stmt)
        by_domain = {row.domain: row.count for row in domain_result.fetchall()}

        # By sentiment
        sentiment_stmt = select(
            IdeaCandidate.sentiment, func.count(IdeaCandidate.id).label("count")
        ).group_by(IdeaCandidate.sentiment)

        sentiment_result = await self.db.execute(sentiment_stmt)
        by_sentiment = {row.sentiment: row.count for row in sentiment_result.fetchall()}

        # Average quality score
        avg_quality_stmt = select(func.avg(IdeaCandidate.quality_score))
        avg_quality_result = await self.db.execute(avg_quality_stmt)
        avg_quality = avg_quality_result.scalar_one()

        return {
            "total": total,
            "by_domain": by_domain,
            "by_sentiment": by_sentiment,
            "avg_quality_score": float(avg_quality) if avg_quality else 0.0,
        }
