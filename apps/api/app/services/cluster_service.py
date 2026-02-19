"""
Cluster service - Business logic for cluster operations.

Handles cluster retrieval, scoring, similarity search, and evidence gathering.
"""

from typing import Any
from uuid import UUID

from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.utils import escape_like_pattern
from packages.core.models import Cluster, ClusterMembership, IdeaCandidate


class ClusterService:
    """Service for cluster-related business logic."""

    def __init__(self, db: AsyncSession):
        """
        Initialize cluster service.

        Args:
            db: Async database session
        """
        self.db = db

    async def get_all_clusters(
        self,
        sort_by: str = "size",
        order: str = "desc",
        limit: int = 20,
        offset: int = 0,
        min_size: int | None = None,
        q: str | None = None,
        domain: str | None = None,
    ) -> dict[str, Any]:
        """
        Retrieve clusters with filtering and pagination.

        Args:
            sort_by: Field to sort by (size, sentiment, trend, quality, created_at)
            order: Sort order (asc, desc)
            limit: Maximum results to return
            offset: Pagination offset
            min_size: Minimum cluster size filter
            q: Free-text search across label/description/keywords
            domain: Domain filter (not implemented yet in model but kept for API compat)

        Returns:
            Dict containing 'clusters' list and 'pagination' info
        """
        # Build query
        query = select(Cluster)

        # Apply filters
        if min_size is not None:
            query = query.where(Cluster.idea_count >= min_size)
        if q:
            escaped_q = escape_like_pattern(q.strip())
            search_term = f"%{escaped_q}%"
            keyword_text = func.coalesce(
                func.array_to_string(Cluster.keywords, " "), ""
            )
            query = query.where(
                or_(
                    Cluster.label.ilike(search_term),
                    Cluster.description.ilike(search_term),
                    keyword_text.ilike(search_term),
                )
            )

        # Apply sorting
        sort_field_map = {
            "size": Cluster.idea_count,
            "quality": Cluster.quality_score,
            "trend": Cluster.trend_score,
            "sentiment": Cluster.avg_sentiment,
            "created_at": Cluster.created_at,
        }

        # Default to size if invalid sort_by (though API validation should catch this)
        sort_field = sort_field_map.get(sort_by, Cluster.idea_count)

        if order == "desc":
            query = query.order_by(desc(sort_field))
        else:
            query = query.order_by(sort_field)

        # Get total count
        count_query = select(func.count()).select_from(Cluster)
        if min_size is not None:
            count_query = count_query.where(Cluster.idea_count >= min_size)
        if q:
            escaped_q = escape_like_pattern(q.strip())
            search_term = f"%{escaped_q}%"
            keyword_text = func.coalesce(
                func.array_to_string(Cluster.keywords, " "), ""
            )
            count_query = count_query.where(
                or_(
                    Cluster.label.ilike(search_term),
                    Cluster.description.ilike(search_term),
                    keyword_text.ilike(search_term),
                )
            )

        result = await self.db.execute(count_query)
        total = result.scalar_one()

        # Apply pagination
        query = query.limit(limit).offset(offset)

        # Execute query
        result = await self.db.execute(query)
        clusters = result.scalars().all()

        return {
            "clusters": clusters,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total,
            },
        }

    async def get_cluster_by_id(
        self, cluster_id: UUID, include_evidence: bool = True, evidence_limit: int = 5
    ) -> dict[str, Any] | None:
        """
        Get detailed cluster information.

        Args:
            cluster_id: Cluster UUID
            include_evidence: Whether to include representative ideas
            evidence_limit: Maximum evidence items to return

        Returns:
            Cluster model with optional 'evidence' list, or None if not found
        """
        # Fetch cluster
        query = select(Cluster).where(Cluster.id == cluster_id)
        result = await self.db.execute(query)
        cluster = result.scalar_one_or_none()

        if not cluster:
            return None

        # Convert to dict to allow attaching evidence
        # Note: In a real Pydantic world, we might return the ORM object and let response model handle it,
        # but here we follow the existing pattern of returning a dict/structure for the router.
        # Actually, let's return a construct that the router can easily digest.

        # Taking a slight divergence from the router's manual dict construction to keep it cleaner.
        # We will return the ORM object and let the router format it, OR return a rich dict.
        # Given the router logic, it constructs a specific response shape. Let's return that shape.

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

            result = await self.db.execute(evidence_query)
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

        return response

    async def get_trending_clusters(
        self, limit: int = 10, min_trend_score: float = 0.5
    ) -> list[Cluster]:
        """
        Get clusters with high recent growth.

        Args:
            limit: Number of clusters to return
            min_trend_score: Minimum trend score filter

        Returns:
            List of trending clusters
        """
        query = (
            select(Cluster)
            .where(Cluster.trend_score >= min_trend_score)
            .order_by(desc(Cluster.trend_score))
            .limit(limit)
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def find_similar_clusters(
        self, cluster_id: UUID, limit: int = 5
    ) -> dict[str, Any] | None:
        """
        Find clusters similar to the given cluster.

        Uses keyword overlap (Jaccard similarity) until pgvector is implemented.

        Args:
            cluster_id: Source cluster UUID
            limit: Number of similar clusters to return

        Returns:
            Dict with 'source_cluster' and 'similar_clusters' list, or None if source not found
        """
        # Fetch source cluster
        query = select(Cluster).where(Cluster.id == cluster_id)
        result = await self.db.execute(query)
        source_cluster = result.scalar_one_or_none()

        if not source_cluster:
            return None

        # Strategy 1: Vector Search (Preferred)
        if source_cluster.cluster_vector is not None:
            # Cosine distance: 0 = identical, 2 = opposite
            # We want smallest distance.
            distance_expr = Cluster.cluster_vector.cosine_distance(
                source_cluster.cluster_vector
            )

            query = (
                select(Cluster, distance_expr.label("distance"))
                .where(Cluster.id != cluster_id)
                .where(Cluster.cluster_vector.is_not(None))
                .order_by(distance_expr)
                .limit(limit)
            )

            result = await self.db.execute(query)
            rows = result.all()

            similar_clusters = []
            for cluster, distance in rows:
                # Convert distance to similarity score (approximate)
                similarity_score = 1 - distance if distance <= 1 else 0

                similar_clusters.append(
                    {
                        "id": str(cluster.id),
                        "label": cluster.label,
                        "keywords": cluster.keywords,
                        "idea_count": cluster.idea_count,
                        "quality_score": cluster.quality_score,
                        "similarity_score": float(similarity_score),
                    }
                )

            return {
                "source_cluster": {
                    "id": str(source_cluster.id),
                    "label": source_cluster.label,
                    "keywords": source_cluster.keywords,
                },
                "similar_clusters": similar_clusters,
            }

        # Strategy 2: Keyword Jaccard Fallback (Legacy)
        source_keywords = set(source_cluster.keywords)

        # Fetch all other clusters
        query = select(Cluster).where(Cluster.id != cluster_id)
        result = await self.db.execute(query)
        all_clusters = result.scalars().all()

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

        return {
            "source_cluster": {
                "id": str(source_cluster.id),
                "label": source_cluster.label,
                "keywords": source_cluster.keywords,
            },
            "similar_clusters": similar_clusters,
        }
