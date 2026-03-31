"""Pydantic schemas for saved searches API."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from apps.api.app.schemas.common import PaginationInfo

AlertFrequency = Literal["daily", "weekly"]


class SavedSearchItem(BaseModel):
    id: str
    name: str
    query_params: dict[str, Any]
    alert_enabled: bool
    alert_frequency: AlertFrequency
    created_at: str
    updated_at: str


class SavedSearchListResponse(BaseModel):
    saved_searches: list[SavedSearchItem]
    pagination: PaginationInfo


class SavedSearchCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    query_params: dict[str, Any] = Field(default_factory=dict)
    alert_enabled: bool = False
    alert_frequency: AlertFrequency = "weekly"


class SavedSearchUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    query_params: dict[str, Any] | None = None
    alert_enabled: bool | None = None
    alert_frequency: AlertFrequency | None = None


class SavedSearchMutationResponse(BaseModel):
    success: bool
    message: str
    saved_search: SavedSearchItem | None = None
