"""Pydantic response schemas for job endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class JobQueuedResponse(BaseModel):
    """Response when a job is successfully queued."""

    job_id: str
    status: str
    estimated_duration: str
    message: str


class JobStatusResponse(BaseModel):
    """Response for job status check.

    ``result`` is populated on SUCCESS, ``error`` on FAILURE.
    """

    job_id: str
    status: str
    message: str
    result: Any = None
    error: str | None = None


class JobCancelResponse(BaseModel):
    """Response for job cancellation request."""

    job_id: str
    status: str
    message: str
