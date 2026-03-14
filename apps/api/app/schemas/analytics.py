"""Pydantic response schemas for analytics endpoints."""

from __future__ import annotations

from pydantic import BaseModel


class AnalyticsOverview(BaseModel):
    """Overview counts and averages."""

    total_posts: int
    total_ideas: int
    total_clusters: int
    avg_cluster_size: float
    avg_sentiment: float


class AnalyticsTrending(BaseModel):
    """Recent activity metrics."""

    hot_clusters: int
    new_ideas_today: int
    new_clusters_this_week: int


class DomainCount(BaseModel):
    """A single domain entry in the summary."""

    domain: str
    count: int


class AnalyticsSummaryResponse(BaseModel):
    """Response for GET /api/v1/analytics/summary."""

    overview: AnalyticsOverview
    trending: AnalyticsTrending
    sentiment_distribution: dict[str, int]
    top_domains: list[DomainCount]
    updated_at: str


class TrendDataPoint(BaseModel):
    """A single data point in a trend series."""

    date: str | None = None
    value: int
    avg_sentiment: float | None = None


class TrendsResponse(BaseModel):
    """Response for GET /api/v1/analytics/trends."""

    metric: str
    interval: str
    start_date: str
    end_date: str
    data_points: list[TrendDataPoint]


class DomainBreakdownItem(BaseModel):
    """A domain in the breakdown response."""

    name: str
    idea_count: int
    avg_sentiment: float | None = None
    percentage: float


class DomainsResponse(BaseModel):
    """Response for GET /api/v1/analytics/domains."""

    domains: list[DomainBreakdownItem]
    total_ideas: int
