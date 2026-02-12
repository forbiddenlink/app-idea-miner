"""
Analytics API endpoints.

Provides aggregated statistics and trend data for the dashboard.
"""

import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.core.cache import cached_route
from packages.core.database import get_db
from packages.core.models import Cluster, IdeaCandidate, RawPost

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/summary")
@cached_route("analytics:summary", ttl=300)  # Cache for 5 minutes
async def get_analytics_summary(db: AsyncSession = Depends(get_db)):
    """
    Get dashboard summary statistics.

    Returns overview metrics: total posts, ideas, clusters, averages, distributions.
    Cached for 5 minutes.
    """
    # Total counts
    posts_count_query = select(func.count()).select_from(RawPost)
    ideas_count_query = (
        select(func.count()).select_from(IdeaCandidate).where(IdeaCandidate.is_valid == True)
    )
    clusters_count_query = select(func.count()).select_from(Cluster)

    posts_result = await db.execute(posts_count_query)
    ideas_result = await db.execute(ideas_count_query)
    clusters_result = await db.execute(clusters_count_query)

    total_posts = posts_result.scalar_one()
    total_ideas = ideas_result.scalar_one()
    total_clusters = clusters_result.scalar_one()

    # Averages
    avg_cluster_size_query = select(func.avg(Cluster.idea_count))
    avg_sentiment_query = select(func.avg(IdeaCandidate.sentiment_score)).where(
        IdeaCandidate.is_valid == True
    )

    avg_cluster_result = await db.execute(avg_cluster_size_query)
    avg_sentiment_result = await db.execute(avg_sentiment_query)

    avg_cluster_size = avg_cluster_result.scalar_one() or 0.0
    avg_sentiment = avg_sentiment_result.scalar_one() or 0.0

    # Recent activity (last 24 hours)
    now = datetime.now(UTC)
    yesterday = now - timedelta(hours=24)

    new_ideas_query = (
        select(func.count())
        .select_from(IdeaCandidate)
        .where(IdeaCandidate.extracted_at >= yesterday, IdeaCandidate.is_valid == True)
    )

    new_clusters_week_query = (
        select(func.count())
        .select_from(Cluster)
        .where(Cluster.created_at >= now - timedelta(days=7))
    )

    new_ideas_result = await db.execute(new_ideas_query)
    new_clusters_result = await db.execute(new_clusters_week_query)

    new_ideas_today = new_ideas_result.scalar_one()
    new_clusters_this_week = new_clusters_result.scalar_one()

    # Sentiment distribution
    sentiment_dist_query = (
        select(IdeaCandidate.sentiment, func.count())
        .where(IdeaCandidate.is_valid == True)
        .group_by(IdeaCandidate.sentiment)
    )

    sentiment_result = await db.execute(sentiment_dist_query)
    sentiment_rows = sentiment_result.all()

    sentiment_distribution = {sentiment: count for sentiment, count in sentiment_rows}

    # Top domains
    domain_query = (
        select(IdeaCandidate.domain, func.count().label("count"))
        .where(IdeaCandidate.is_valid == True)
        .group_by(IdeaCandidate.domain)
        .order_by(desc("count"))
        .limit(10)
    )

    domain_result = await db.execute(domain_query)
    domain_rows = domain_result.all()

    top_domains = [{"domain": domain or "other", "count": count} for domain, count in domain_rows]

    logger.info(
        f"Analytics summary: {total_posts} posts, {total_ideas} ideas, {total_clusters} clusters"
    )

    return {
        "overview": {
            "total_posts": total_posts,
            "total_ideas": total_ideas,
            "total_clusters": total_clusters,
            "avg_cluster_size": round(avg_cluster_size, 2),
            "avg_sentiment": round(avg_sentiment, 3),
        },
        "trending": {
            "hot_clusters": total_clusters,  # Can refine to count clusters with trend_score > threshold
            "new_ideas_today": new_ideas_today,
            "new_clusters_this_week": new_clusters_this_week,
        },
        "sentiment_distribution": sentiment_distribution,
        "top_domains": top_domains,
        "updated_at": now.isoformat(),
    }


@router.get("/trends")
async def get_analytics_trends(
    metric: str = Query("ideas", description="Metric to track: ideas, clusters, posts"),
    interval: str = Query("day", description="Time interval: hour, day, week, month"),
    start_date: str | None = Query(None, description="Start date (ISO 8601) or relative like -30d"),
    end_date: str | None = Query(None, description="End date (ISO 8601) or 'now'"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get time-series trend data for charts.

    Returns data points with counts and averages over time.
    """
    # Parse date range
    now = datetime.now(UTC)

    if start_date:
        if start_date.startswith("-"):
            # Relative date like "-30d"
            days = int(start_date[1:-1])
            start_dt = now - timedelta(days=days)
        else:
            start_dt = datetime.fromisoformat(start_date)
    else:
        start_dt = now - timedelta(days=30)  # Default 30 days

    if end_date and end_date != "now":
        end_dt = datetime.fromisoformat(end_date)
    else:
        end_dt = now

    # Determine table and timestamp field
    if metric == "ideas":
        table = IdeaCandidate
        timestamp_field = IdeaCandidate.extracted_at
        filter_condition = IdeaCandidate.is_valid == True
    elif metric == "clusters":
        table = Cluster
        timestamp_field = Cluster.created_at
        filter_condition = True  # No filter for clusters
    elif metric == "posts":
        table = RawPost
        timestamp_field = RawPost.fetched_at
        filter_condition = True
    else:
        raise HTTPException(status_code=400, detail=f"Invalid metric: {metric}")

    # Determine date truncation based on interval
    if interval == "hour":
        trunc_func = func.date_trunc("hour", timestamp_field)
    elif interval == "day":
        trunc_func = func.date_trunc("day", timestamp_field)
    elif interval == "week":
        trunc_func = func.date_trunc("week", timestamp_field)
    elif interval == "month":
        trunc_func = func.date_trunc("month", timestamp_field)
    else:
        raise HTTPException(status_code=400, detail=f"Invalid interval: {interval}")

    # Build query
    query = (
        select(trunc_func.label("date"), func.count().label("value"))
        .where(timestamp_field >= start_dt, timestamp_field <= end_dt, filter_condition)
        .group_by("date")
        .order_by("date")
    )

    # Add sentiment average for ideas
    if metric == "ideas":
        query = (
            select(
                trunc_func.label("date"),
                func.count().label("value"),
                func.avg(IdeaCandidate.sentiment_score).label("avg_sentiment"),
            )
            .where(
                timestamp_field >= start_dt,
                timestamp_field <= end_dt,
                IdeaCandidate.is_valid == True,
            )
            .group_by("date")
            .order_by("date")
        )

    result = await db.execute(query)
    rows = result.all()

    # Format data points
    if metric == "ideas" and len(rows) > 0 and len(rows[0]) == 3:
        data_points = [
            {
                "date": row[0].isoformat() if row[0] else None,
                "value": row[1],
                "avg_sentiment": round(row[2], 3) if row[2] else None,
            }
            for row in rows
        ]
    else:
        data_points = [
            {"date": row[0].isoformat() if row[0] else None, "value": row[1]} for row in rows
        ]

    logger.info(f"Trends for {metric} ({interval}): {len(data_points)} data points")

    return {
        "metric": metric,
        "interval": interval,
        "start_date": start_dt.isoformat(),
        "end_date": end_dt.isoformat(),
        "data_points": data_points,
    }


@router.get("/domains")
async def get_analytics_domains(db: AsyncSession = Depends(get_db)):
    """
    Get domain/category breakdown statistics.

    Returns ideas and clusters per domain with percentages.
    """
    # Total ideas
    total_ideas_query = (
        select(func.count()).select_from(IdeaCandidate).where(IdeaCandidate.is_valid == True)
    )
    total_result = await db.execute(total_ideas_query)
    total_ideas = total_result.scalar_one()

    # Ideas per domain
    domain_query = (
        select(
            IdeaCandidate.domain,
            func.count().label("idea_count"),
            func.avg(IdeaCandidate.sentiment_score).label("avg_sentiment"),
        )
        .where(IdeaCandidate.is_valid == True)
        .group_by(IdeaCandidate.domain)
        .order_by(desc("idea_count"))
    )

    domain_result = await db.execute(domain_query)
    domain_rows = domain_result.all()

    domains = [
        {
            "name": domain or "other",
            "idea_count": idea_count,
            "avg_sentiment": round(avg_sentiment, 3) if avg_sentiment else None,
            "percentage": round((idea_count / total_ideas) * 100, 1) if total_ideas > 0 else 0.0,
        }
        for domain, idea_count, avg_sentiment in domain_rows
    ]

    logger.info(f"Domain breakdown: {len(domains)} domains")

    return {"domains": domains, "total_ideas": total_ideas}
