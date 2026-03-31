"""Pydantic schemas for bookmarks API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from apps.api.app.schemas.common import PaginationInfo
from apps.api.app.schemas.ideas import IdeaSummary


class BookmarkClusterSummary(BaseModel):
    id: str
    label: str
    description: str | None = None
    keywords: list[str]
    idea_count: int
    avg_sentiment: float | None = None
    quality_score: float | None = None
    trend_score: float | None = None
    created_at: str | None = None
    updated_at: str | None = None


class BookmarkItem(BaseModel):
    item_type: Literal["cluster", "idea"]
    item_id: str
    scope_key: str
    created_at: str
    cluster: BookmarkClusterSummary | None = None
    idea: IdeaSummary | None = None


class BookmarkListResponse(BaseModel):
    bookmarks: list[BookmarkItem]
    pagination: PaginationInfo


class BookmarkCreateRequest(BaseModel):
    item_type: Literal["cluster", "idea"]
    item_id: str = Field(min_length=1)


class BookmarkMutationResponse(BaseModel):
    success: bool
    message: str


class BookmarkClearResponse(BaseModel):
    success: bool
    deleted: int
