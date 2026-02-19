"""
Celery tasks for clustering app ideas.

This module contains tasks for running the clustering algorithm on extracted ideas,
creating cluster records, and managing cluster memberships.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

from sqlalchemy import delete, select

from apps.worker.celery_app import celery_app
from packages.core.cache import invalidate_analytics_cache, invalidate_clusters_cache
from packages.core.clustering import cluster_ideas as run_clustering_algorithm
from packages.core.clustering import get_cluster_engine
from packages.core.database import AsyncSessionLocal
from packages.core.models import Cluster, ClusterMembership, IdeaCandidate

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="apps.worker.tasks.clustering.run_clustering",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=3,
)
def run_clustering(
    self,
    min_quality: float = 0.3,
    min_cluster_size: int = 3,
    recreate_clusters: bool = True,
) -> dict[str, Any]:
    """
    Run clustering algorithm on all valid idea candidates.

    This is the main clustering task that:
    1. Fetches all valid ideas with quality > threshold
    2. Runs HDBSCAN clustering algorithm
    3. Creates Cluster records with metadata
    4. Creates ClusterMembership records
    5. Marks top 5 ideas per cluster as representative

    Args:
        min_quality: Minimum quality score for ideas to include
        min_cluster_size: Minimum cluster size for HDBSCAN
        recreate_clusters: If True, delete existing clusters first

    Returns:
        Dictionary with clustering statistics
    """
    logger.info(
        f"Starting clustering task with min_quality={min_quality}, min_cluster_size={min_cluster_size}"
    )

    # Run async logic with a fresh event loop to avoid conflicts
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(
            _run_clustering_async(min_quality, min_cluster_size, recreate_clusters)
        )
    finally:
        loop.close()

    logger.info(f"Clustering task complete: {result}")
    return result


async def _run_clustering_async(
    min_quality: float, min_cluster_size: int, recreate_clusters: bool
) -> dict[str, Any]:
    """Async implementation of clustering task."""

    async with AsyncSessionLocal() as session:
        try:
            # Step 1: Delete existing clusters if requested
            if recreate_clusters:
                logger.info("Deleting existing clusters...")
                await session.execute(delete(ClusterMembership))
                await session.execute(delete(Cluster))
                await session.commit()

            # Step 2: Fetch valid ideas
            logger.info(f"Fetching ideas with quality >= {min_quality}...")
            stmt = (
                select(IdeaCandidate)
                .where(
                    IdeaCandidate.is_valid == True,
                    IdeaCandidate.quality_score >= min_quality,
                )
                .order_by(IdeaCandidate.quality_score.desc())
            )

            result = await session.execute(stmt)
            ideas = result.scalars().all()

            if not ideas:
                logger.warning("No valid ideas found to cluster")
                return {
                    "ideas_fetched": 0,
                    "clusters_created": 0,
                    "memberships_created": 0,
                    "noise_ideas": 0,
                }

            logger.info(f"Fetched {len(ideas)} valid ideas for clustering")

            # Step 3: Run clustering
            texts = [idea.problem_statement for idea in ideas]
            idea_ids = [idea.id for idea in ideas]

            logger.info("Running clustering algorithm...")
            cluster_result = run_clustering_algorithm(
                texts, min_cluster_size=min_cluster_size
            )

            logger.info(
                f"Clustering complete: {cluster_result.n_clusters} clusters, "
                f"{cluster_result.n_noise} noise points"
            )

            # Step 4: Create Cluster records
            clusters_created = 0
            memberships_created = 0

            for cluster_id in range(cluster_result.n_clusters):
                # Get ideas in this cluster
                cluster_mask = cluster_result.labels == cluster_id
                cluster_idea_indices = [
                    i for i, is_in_cluster in enumerate(cluster_mask) if is_in_cluster
                ]
                cluster_ideas = [ideas[i] for i in cluster_idea_indices]

                if not cluster_ideas:
                    continue

                # Calculate cluster metadata
                idea_count = len(cluster_ideas)
                avg_sentiment = (
                    sum(idea.sentiment_score for idea in cluster_ideas) / idea_count
                )
                avg_quality = (
                    sum(idea.quality_score for idea in cluster_ideas) / idea_count
                )

                # Calculate trend score
                timestamps = [idea.extracted_at for idea in cluster_ideas]
                engine = get_cluster_engine()
                trend_score = engine.calculate_trend_score(timestamps, window_days=7)

                # Calculate overall score
                quality_score = engine.score_cluster(
                    size=idea_count,
                    avg_sentiment=avg_sentiment,
                    avg_quality=avg_quality,
                    trend_score=trend_score,
                )

                # Get keywords for this cluster
                keywords = cluster_result.keywords.get(cluster_id, [])
                keyword_list = [kw[0] for kw in keywords]

                # Generate label
                label = engine.generate_cluster_label(keywords)

                # Create Cluster record
                cluster = Cluster(
                    label=label,
                    description=f"Cluster of {idea_count} related app ideas",
                    keywords=keyword_list,
                    idea_count=idea_count,
                    avg_sentiment=avg_sentiment,
                    quality_score=quality_score,
                    trend_score=trend_score,
                )
                session.add(cluster)
                await session.flush()  # Get cluster ID

                clusters_created += 1
                logger.debug(
                    f"Created cluster {cluster_id}: {label} ({idea_count} ideas)"
                )

                # Create ClusterMembership records
                # Sort ideas by quality to identify representative ones
                sorted_cluster_ideas = sorted(
                    zip(cluster_idea_indices, cluster_ideas),
                    key=lambda x: x[1].quality_score,
                    reverse=True,
                )

                for rank, (idx, idea) in enumerate(sorted_cluster_ideas):
                    # Calculate similarity score (use HDBSCAN probability if available)
                    similarity_score = (
                        float(cluster_result.probabilities[idx])
                        if cluster_result.probabilities is not None
                        else 0.9
                    )

                    # Mark top 5 as representative
                    is_representative = rank < 5

                    membership = ClusterMembership(
                        cluster_id=cluster.id,
                        idea_id=idea.id,
                        similarity_score=similarity_score,
                        is_representative=is_representative,
                    )
                    session.add(membership)
                    memberships_created += 1

            # Commit all changes
            await session.commit()

            # Invalidate caches after successful clustering with retry
            cache_invalidated = False
            for attempt in range(3):
                try:
                    await invalidate_clusters_cache()
                    await invalidate_analytics_cache()
                    logger.info("Caches invalidated after clustering")
                    cache_invalidated = True
                    break
                except Exception as cache_error:
                    logger.warning(
                        f"Cache invalidation attempt {attempt + 1}/3 failed: {cache_error}"
                    )
                    if attempt < 2:
                        await asyncio.sleep(1 * (attempt + 1))  # Backoff: 1s, 2s

            if not cache_invalidated:
                logger.error(
                    "Failed to invalidate caches after 3 attempts. "
                    "Users may see stale data until cache TTL expires."
                )

            return {
                "ideas_fetched": len(ideas),
                "clusters_created": clusters_created,
                "memberships_created": memberships_created,
                "noise_ideas": int(
                    cluster_result.n_noise
                ),  # Convert numpy int to Python int
            }

        except Exception as e:
            logger.error(f"Clustering task failed: {e}", exc_info=True)
            await session.rollback()
            raise


@celery_app.task(name="apps.worker.tasks.clustering.recluster_all")
def recluster_all(min_quality: float = 0.3) -> dict[str, Any]:
    """
    Force re-clustering of all ideas.

    This task deletes all existing clusters and re-runs clustering from scratch.
    Useful when clustering parameters change or to refresh stale clusters.

    Args:
        min_quality: Minimum quality score threshold

    Returns:
        Clustering statistics
    """
    logger.info("Reclustering all ideas...")
    return run_clustering(min_quality=min_quality, recreate_clusters=True)


@celery_app.task(name="apps.worker.tasks.clustering.update_cluster_trends")
def update_cluster_trends() -> dict[str, Any]:
    """
    Update trend scores for existing clusters.

    Recalculates trend scores based on recent idea additions without
    re-running the full clustering algorithm.

    Returns:
        Update statistics
    """
    logger.info("Updating cluster trend scores...")
    result = asyncio.run(_update_cluster_trends_async())
    logger.info(f"Trend update complete: {result}")
    return result


async def _update_cluster_trends_async() -> dict[str, Any]:
    """Async implementation of trend update."""

    async with AsyncSessionLocal() as session:
        try:
            # Fetch all clusters with their ideas
            stmt = select(Cluster)
            result = await session.execute(stmt)
            clusters = result.scalars().all()

            updated_count = 0
            engine = get_cluster_engine()

            for cluster in clusters:
                # Fetch cluster ideas with timestamps
                membership_stmt = select(ClusterMembership).where(
                    ClusterMembership.cluster_id == cluster.id
                )
                membership_result = await session.execute(membership_stmt)
                memberships = membership_result.scalars().all()

                # Get idea timestamps
                idea_ids = [m.idea_id for m in memberships]
                idea_stmt = select(IdeaCandidate).where(IdeaCandidate.id.in_(idea_ids))
                idea_result = await session.execute(idea_stmt)
                ideas = idea_result.scalars().all()

                timestamps = [idea.extracted_at for idea in ideas]

                # Calculate new trend score
                new_trend_score = engine.calculate_trend_score(
                    timestamps, window_days=7
                )

                # Update cluster
                cluster.trend_score = new_trend_score
                cluster.updated_at = datetime.utcnow()
                updated_count += 1

            await session.commit()

            return {"clusters_updated": updated_count}

        except Exception as e:
            logger.error(f"Trend update failed: {e}", exc_info=True)
            await session.rollback()
            raise
