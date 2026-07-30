"""Pydantic response schemas for opportunity endpoints."""

from __future__ import annotations

from pydantic import BaseModel

from apps.api.app.schemas.common import PaginationInfo


class ScoreBreakdownItem(BaseModel):
    """A single component of the opportunity score."""

    score: int
    max: int
    description: str


class OpportunityScore(BaseModel):
    """Composite opportunity score with grade and breakdown."""

    total: int
    grade: str
    verdict: str
    breakdown: dict[str, ScoreBreakdownItem]


class CompetitorMention(BaseModel):
    """An incumbent named across a cluster's ideas — a market-gap signal."""

    name: str
    count: int


class OpportunityItem(BaseModel):
    """An opportunity in list results."""

    cluster_id: str
    cluster_label: str
    keywords: list[str]
    idea_count: int
    opportunity_score: OpportunityScore
    top_competitors: list[CompetitorMention] = []


class OpportunityListResponse(BaseModel):
    """Response for GET /api/v1/opportunities."""

    opportunities: list[OpportunityItem]
    pagination: PaginationInfo


class OpportunityDetailResponse(BaseModel):
    """Response for GET /api/v1/opportunities/{cluster_id}."""

    cluster_id: str
    cluster_label: str
    opportunity_score: OpportunityScore
    top_competitors: list[CompetitorMention] = []
