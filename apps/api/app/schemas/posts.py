"""Pydantic response schemas for post endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from apps.api.app.schemas.common import PaginationInfo


class PostSummary(BaseModel):
    """Post as returned in list endpoints."""

    id: str
    url: str
    title: str
    source: str
    author: str | None = None
    published_at: str | None = None
    fetched_at: str | None = None
    is_processed: bool
    metadata: dict[str, Any] | None = None


class PostListResponse(BaseModel):
    """Response for GET /api/v1/posts."""

    posts: list[PostSummary]
    pagination: PaginationInfo


class PostDetailResponse(BaseModel):
    """Response for GET /api/v1/posts/{post_id}."""

    id: str
    url: str
    url_hash: str
    title: str
    content: str | None = None
    source: str
    author: str | None = None
    published_at: str | None = None
    fetched_at: str | None = None
    metadata: dict[str, Any] | None = None
    is_processed: bool
    created_at: str | None = None
    updated_at: str | None = None


class SeedResponse(BaseModel):
    """Response for POST /api/v1/posts/seed."""

    inserted: int
    duplicates: int
    total: int
    errors: int | None = None


class PostStatsResponse(BaseModel):
    """Response for GET /api/v1/posts/stats/summary."""

    total: int
    processed: int
    unprocessed: int
    by_source: dict[str, int]
