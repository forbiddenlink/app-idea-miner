"""Common Pydantic response schemas shared across routers."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class PaginationInfo(BaseModel):
    """Pagination metadata returned with list responses."""

    total: int
    limit: int
    offset: int
    has_more: bool


class HealthServiceInfo(BaseModel):
    status: str
    message: str | None = None
    latency_ms: float | None = None
    error: str | None = None
    workers: int | None = None
    active_tasks: int | None = None

    model_config = ConfigDict(extra="allow")


class HealthResponse(BaseModel):
    """Response from /health endpoint."""

    status: str
    version: str
    environment: str
    timestamp: float
    services: dict[str, HealthServiceInfo]


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str
