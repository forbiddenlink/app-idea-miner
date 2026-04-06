"""Pydantic response schemas for idea endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from apps.api.app.schemas.common import PaginationInfo


class IdeaRawPostSummary(BaseModel):
    """Minimal raw post info embedded in idea list responses."""

    id: str
    url: str
    title: str
    source: str
    published_at: str | None = None


class IdeaRawPostDetail(BaseModel):
    """Full raw post info embedded in idea detail responses."""

    id: str
    url: str
    title: str
    content: str | None = None
    source: str
    author: str | None = None
    published_at: str | None = None
    fetched_at: str | None = None
    source_metadata: dict[str, Any] | None = None


class IdeaSummary(BaseModel):
    """Idea as returned in list endpoints."""

    id: str
    problem_statement: str
    context: str | None = None
    domain: str | None = None
    sentiment: str
    sentiment_score: float
    emotions: dict[str, Any] | None = None
    quality_score: float
    features_mentioned: list[str] | None = None
    competitors_mentioned: list[str] | None = None
    aspect_sentiments: dict[str, float] | None = None
    urgency_level: str | None = None
    extracted_at: str | None = None
    raw_post: IdeaRawPostSummary | None = None


class IdeaListResponse(BaseModel):
    """Response for GET /api/v1/ideas."""

    ideas: list[IdeaSummary]
    pagination: PaginationInfo


class IdeaDetailResponse(BaseModel):
    """Response for GET /api/v1/ideas/{idea_id}."""

    id: str
    problem_statement: str
    context: str | None = None
    domain: str | None = None
    sentiment: str
    sentiment_score: float
    emotions: dict[str, Any] | None = None
    quality_score: float
    features_mentioned: list[str] | None = None
    competitors_mentioned: list[str] | None = None
    aspect_sentiments: dict[str, float] | None = None
    urgency_level: str | None = None
    extracted_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    raw_post: IdeaRawPostDetail | None = None


class IdeaSearchRawPost(BaseModel):
    """Minimal raw post info in search results."""

    url: str
    title: str
    source: str


class IdeaSearchItem(BaseModel):
    """Idea as returned in search results."""

    id: str
    problem_statement: str
    domain: str | None = None
    sentiment: str
    quality_score: float
    extracted_at: str | None = None
    raw_post: IdeaSearchRawPost | None = None


class IdeaSearchResponse(BaseModel):
    """Response for GET /api/v1/ideas/search/query."""

    query: str
    results: list[IdeaSearchItem]
    pagination: PaginationInfo


class IdeaStatsResponse(BaseModel):
    """Response for GET /api/v1/ideas/stats/summary."""

    total: int
    by_domain: dict[str, int]
    by_sentiment: dict[str, int]
    avg_quality_score: float


class SimilarIdeaItem(BaseModel):
    """Idea with similarity score."""

    id: str
    problem_statement: str
    context: str | None = None
    domain: str | None = None
    sentiment: str
    sentiment_score: float
    quality_score: float
    features_mentioned: list[str] | None = None
    extracted_at: str | None = None
    similarity: float
    raw_post: IdeaRawPostSummary | None = None


class SimilarIdeasResponse(BaseModel):
    """Response for GET /api/v1/ideas/{id}/similar."""

    source_idea_id: str
    similar_ideas: list[SimilarIdeaItem]
    total: int
