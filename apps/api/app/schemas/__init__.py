"""Pydantic response schemas for the App-Idea Miner API."""

from apps.api.app.schemas.analytics import (
    AnalyticsSummaryResponse,
    DomainsResponse,
    TrendsResponse,
)
from apps.api.app.schemas.clusters import (
    ClusterDetailResponse,
    ClusterListResponse,
    SimilarClustersResponse,
    TrendingClustersResponse,
)
from apps.api.app.schemas.common import ErrorResponse, HealthResponse, PaginationInfo
from apps.api.app.schemas.ideas import (
    IdeaDetailResponse,
    IdeaListResponse,
    IdeaSearchResponse,
    IdeaStatsResponse,
)
from apps.api.app.schemas.opportunities import (
    OpportunityDetailResponse,
    OpportunityListResponse,
)
from apps.api.app.schemas.posts import (
    PostDetailResponse,
    PostListResponse,
    PostStatsResponse,
    SeedResponse,
)

__all__ = [
    "AnalyticsSummaryResponse",
    "ClusterDetailResponse",
    "ClusterListResponse",
    "DomainsResponse",
    "ErrorResponse",
    "HealthResponse",
    "IdeaDetailResponse",
    "IdeaListResponse",
    "IdeaSearchResponse",
    "IdeaStatsResponse",
    "OpportunityDetailResponse",
    "OpportunityListResponse",
    "PaginationInfo",
    "PostDetailResponse",
    "PostListResponse",
    "PostStatsResponse",
    "SeedResponse",
    "SimilarClustersResponse",
    "TrendingClustersResponse",
    "TrendsResponse",
]
