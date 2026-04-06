"""
Similarity search service for ideas and clusters.

Uses pgvector cosine similarity for finding related content.
"""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from packages.core.models import Cluster, ClusterMembership, IdeaCandidate

logger = logging.getLogger(__name__)


class SimilarityService:
    """Service for finding similar ideas and clusters using vector embeddings."""

    def __init__(self, db: AsyncSession):
        """
        Initialize similarity service.

        Args:
            db: Async database session
        """
        self.db = db

    async def find_similar_ideas(
        self,
        idea_id: UUID,
        limit: int = 10,
        min_similarity: float = 0.7,
    ) -> list[dict]:
        """
        Find ideas similar to the given idea using cosine similarity.

        Args:
            idea_id: UUID of the source idea
            limit: Maximum number of similar ideas to return
            min_similarity: Minimum similarity score (0-1) to include

        Returns:
            List of dicts with 'idea' and 'similarity' keys, sorted by similarity
        """
        # Get source idea's embedding
        idea = await self.db.get(IdeaCandidate, idea_id)
        if not idea:
            logger.warning(f"Idea {idea_id} not found")
            return []

        if idea.idea_vector is None:
            logger.warning(f"Idea {idea_id} has no embedding vector")
            return []

        # Vector similarity query using cosine distance
        # Cosine distance = 1 - cosine_similarity, so we compute (1 - distance) for similarity
        distance_expr = IdeaCandidate.idea_vector.cosine_distance(idea.idea_vector)
        similarity_expr = (1 - distance_expr).label("similarity")

        stmt = (
            select(IdeaCandidate, similarity_expr)
            .where(IdeaCandidate.id != idea_id)
            .where(IdeaCandidate.idea_vector.is_not(None))
            .where(IdeaCandidate.is_valid == True)
            .options(selectinload(IdeaCandidate.raw_post))
            .order_by(distance_expr)
            .limit(limit * 2)  # Fetch extra to filter by min_similarity
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        # Filter by minimum similarity and format response
        similar_ideas = []
        for row_idea, similarity in rows:
            if similarity >= min_similarity:
                similar_ideas.append(
                    {
                        "idea": row_idea,
                        "similarity": float(similarity),
                    }
                )
            if len(similar_ideas) >= limit:
                break

        logger.debug(
            f"Found {len(similar_ideas)} similar ideas for idea {idea_id} "
            f"(min_similarity={min_similarity})"
        )

        return similar_ideas

    async def find_similar_ideas_by_text(
        self,
        query_vector: list[float],
        limit: int = 10,
        min_similarity: float = 0.5,
        exclude_ids: list[UUID] | None = None,
    ) -> list[dict]:
        """
        Find ideas similar to a query embedding.

        Useful for semantic search where the query is converted to an embedding.

        Args:
            query_vector: 384-dimensional embedding vector
            limit: Maximum number of results
            min_similarity: Minimum similarity score
            exclude_ids: Optional list of idea IDs to exclude

        Returns:
            List of dicts with 'idea' and 'similarity' keys
        """
        distance_expr = IdeaCandidate.idea_vector.cosine_distance(query_vector)
        similarity_expr = (1 - distance_expr).label("similarity")

        stmt = (
            select(IdeaCandidate, similarity_expr)
            .where(IdeaCandidate.idea_vector.is_not(None))
            .where(IdeaCandidate.is_valid == True)
            .options(selectinload(IdeaCandidate.raw_post))
            .order_by(distance_expr)
            .limit(limit * 2)
        )

        if exclude_ids:
            stmt = stmt.where(IdeaCandidate.id.not_in(exclude_ids))

        result = await self.db.execute(stmt)
        rows = result.all()

        similar_ideas = []
        for idea, similarity in rows:
            if similarity >= min_similarity:
                similar_ideas.append(
                    {
                        "idea": idea,
                        "similarity": float(similarity),
                    }
                )
            if len(similar_ideas) >= limit:
                break

        return similar_ideas

    async def find_similar_clusters(
        self,
        cluster_id: UUID,
        limit: int = 5,
        min_similarity: float = 0.6,
    ) -> list[dict]:
        """
        Find clusters similar to the given cluster using cosine similarity.

        Args:
            cluster_id: UUID of the source cluster
            limit: Maximum number of similar clusters to return
            min_similarity: Minimum similarity score (0-1) to include

        Returns:
            List of dicts with 'cluster' and 'similarity' keys
        """
        # Get source cluster's embedding
        cluster = await self.db.get(Cluster, cluster_id)
        if not cluster:
            logger.warning(f"Cluster {cluster_id} not found")
            return []

        if cluster.cluster_vector is None:
            logger.warning(f"Cluster {cluster_id} has no embedding vector")
            return []

        # Vector similarity query
        distance_expr = Cluster.cluster_vector.cosine_distance(cluster.cluster_vector)
        similarity_expr = (1 - distance_expr).label("similarity")

        stmt = (
            select(Cluster, similarity_expr)
            .where(Cluster.id != cluster_id)
            .where(Cluster.cluster_vector.is_not(None))
            .order_by(distance_expr)
            .limit(limit * 2)
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        similar_clusters = []
        for row_cluster, similarity in rows:
            if similarity >= min_similarity:
                similar_clusters.append(
                    {
                        "cluster": row_cluster,
                        "similarity": float(similarity),
                    }
                )
            if len(similar_clusters) >= limit:
                break

        logger.debug(
            f"Found {len(similar_clusters)} similar clusters for cluster {cluster_id}"
        )

        return similar_clusters

    async def find_ideas_in_cluster_similar_to(
        self,
        cluster_id: UUID,
        idea_id: UUID,
        limit: int = 10,
    ) -> list[dict]:
        """
        Find ideas within a specific cluster that are similar to a given idea.

        Useful for exploring related ideas within a topic cluster.

        Args:
            cluster_id: UUID of the cluster to search within
            idea_id: UUID of the reference idea
            limit: Maximum results

        Returns:
            List of similar ideas within the cluster
        """
        # Get the reference idea
        idea = await self.db.get(IdeaCandidate, idea_id)
        if not idea or idea.idea_vector is None:
            return []

        # Get idea IDs in this cluster
        membership_stmt = select(ClusterMembership.idea_id).where(
            ClusterMembership.cluster_id == cluster_id
        )
        membership_result = await self.db.execute(membership_stmt)
        cluster_idea_ids = [row[0] for row in membership_result.fetchall()]

        if not cluster_idea_ids:
            return []

        # Find similar ideas within cluster
        distance_expr = IdeaCandidate.idea_vector.cosine_distance(idea.idea_vector)
        similarity_expr = (1 - distance_expr).label("similarity")

        stmt = (
            select(IdeaCandidate, similarity_expr)
            .where(IdeaCandidate.id.in_(cluster_idea_ids))
            .where(IdeaCandidate.id != idea_id)
            .where(IdeaCandidate.idea_vector.is_not(None))
            .options(selectinload(IdeaCandidate.raw_post))
            .order_by(distance_expr)
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        return [
            {"idea": row_idea, "similarity": float(similarity)}
            for row_idea, similarity in rows
        ]
