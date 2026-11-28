"""Pydantic schemas for saved searches API."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator

from apps.api.app.schemas.common import PaginationInfo
from packages.core.services.notification_service import (
    WebhookUrlError,
    validate_webhook_url,
)

AlertFrequency = Literal["daily", "weekly"]
WebhookType = Literal["slack", "discord", "generic"]


def _check_webhook_url(value: str | None) -> str | None:
    """Reject SSRF-prone webhook URLs at save time (empty string clears it)."""
    if value:
        try:
            validate_webhook_url(value)
        except WebhookUrlError as exc:
            raise ValueError(str(exc)) from exc
    return value


class SavedSearchItem(BaseModel):
    id: str
    name: str
    query_params: dict[str, Any]
    alert_enabled: bool
    alert_frequency: AlertFrequency
    webhook_url: str | None = None
    webhook_type: WebhookType | None = None
    last_alert_at: str | None = None
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
    webhook_url: str | None = Field(default=None, max_length=500)
    webhook_type: WebhookType | None = None

    @field_validator("webhook_url")
    @classmethod
    def _validate_webhook_url(cls, value: str | None) -> str | None:
        return _check_webhook_url(value)


class SavedSearchUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    query_params: dict[str, Any] | None = None
    alert_enabled: bool | None = None
    alert_frequency: AlertFrequency | None = None
    webhook_url: str | None = Field(default=None, max_length=500)
    webhook_type: WebhookType | None = None

    @field_validator("webhook_url")
    @classmethod
    def _validate_webhook_url(cls, value: str | None) -> str | None:
        return _check_webhook_url(value)


class SavedSearchMutationResponse(BaseModel):
    success: bool
    message: str
    saved_search: SavedSearchItem | None = None


class WebhookTestRequest(BaseModel):
    webhook_url: str = Field(max_length=500)
    webhook_type: WebhookType

    @field_validator("webhook_url")
    @classmethod
    def _validate_webhook_url(cls, value: str | None) -> str | None:
        return _check_webhook_url(value)


class WebhookTestResponse(BaseModel):
    success: bool
    message: str
