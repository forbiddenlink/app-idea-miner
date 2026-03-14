"""Pydantic response schemas for cluster endpoints."""

from __future__ import annotations

from pydantic import BaseModel

from apps.api.app.schemas.common import PaginationInfo


class ClusterSummary(BaseModel):
    """Cluster summary returned in list endpoints."""

    id: str
    label: str
    description: str | None = None
    keywords: list[str]
    idea_count: int
    avg_sentiment: float | None = None
    quality_score: float | None = None
    trend_score: float | None = None
    created_at: str
    updated_at: str


class ClusterListResponse(BaseModel):
    """Response for GET /api/v1/clusters."""

    clusters: list[ClusterSummary]
    pagination: PaginationInfo


class ClusterEvidenceItem(BaseModel):
    """An idea included as evidence in a cluster detail response."""

    id: str
    problem_statement: str
    context: str | None = None
    sentiment: str
    sentiment_score: float
    quality_score: float
    similarity_score: float
    extracted_at: str


class ClusterDetailResponse(BaseModel):
    """Response for GET /api/v1/clusters/{cluster_id}."""

    id: str
    label: str
    description: str | None = None
    keywords: list[str]
    idea_count: int
    avg_sentiment: float | None = None
    quality_score: float | None = None
    trend_score: float | None = None
    created_at: str
    updated_at: str
    evidence: list[ClusterEvidenceItem] | None = None


class SimilarClusterItem(BaseModel):
    """A cluster returned in similarity results."""

    id: str
    label: str
    keywords: list[str]
    idea_count: int
    quality_score: float | None = None
    similarity_score: float


class SourceClusterInfo(BaseModel):
    """Minimal cluster info for the source cluster in similarity results."""

    id: str
    label: str
    keywords: list[str]


class SimilarClustersResponse(BaseModel):
    """Response for GET /api/v1/clusters/{cluster_id}/similar."""

    source_cluster: SourceClusterInfo
    similar_clusters: list[SimilarClusterItem]


class TrendingClusterItem(BaseModel):
    """A cluster in the trending list."""

    id: str
    label: str
    keywords: list[str]
    idea_count: int
    trend_score: float | None = None
    quality_score: float | None = None
    avg_sentiment: float | None = None


class TrendingClustersResponse(BaseModel):
    """Response for GET /api/v1/clusters/trending/list."""

    trending: list[TrendingClusterItem]
