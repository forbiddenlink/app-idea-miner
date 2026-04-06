"""API endpoints for user saved searches."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.auth import get_current_user_id
from apps.api.app.core.constants import DEFAULT_PAGE_LIMIT, MAX_PAGE_LIMIT
from apps.api.app.core.rate_limit import RateLimiter
from apps.api.app.core.security import get_api_key
from apps.api.app.database import get_db
from apps.api.app.schemas.saved_searches import (
    SavedSearchCreateRequest,
    SavedSearchListResponse,
    SavedSearchMutationResponse,
    SavedSearchUpdateRequest,
    WebhookTestRequest,
    WebhookTestResponse,
)
from apps.api.app.services.saved_search_service import SavedSearchService
from packages.core.services.notification_service import NotificationService

router = APIRouter(
    tags=["saved-searches"],
    dependencies=[Depends(get_api_key), Depends(RateLimiter(times=100, seconds=60))],
)


@router.get("", response_model=SavedSearchListResponse)
async def list_saved_searches(
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_LIMIT)] = DEFAULT_PAGE_LIMIT,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    service = SavedSearchService(db)
    return await service.list_saved_searches(
        user_id=user_id, limit=limit, offset=offset
    )


@router.post(
    "",
    response_model=SavedSearchMutationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_saved_search(
    payload: SavedSearchCreateRequest,
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = SavedSearchService(db)
    saved_search = await service.create_saved_search(
        user_id=user_id,
        name=payload.name,
        query_params=payload.query_params,
        alert_enabled=payload.alert_enabled,
        alert_frequency=payload.alert_frequency,
        webhook_url=payload.webhook_url,
        webhook_type=payload.webhook_type,
    )
    return {
        "success": True,
        "message": "Saved search created",
        "saved_search": saved_search,
    }


@router.patch(
    "/{saved_search_id}",
    response_model=SavedSearchMutationResponse,
    responses={404: {"description": "Saved search not found"}},
)
async def update_saved_search(
    saved_search_id: UUID,
    payload: SavedSearchUpdateRequest,
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = SavedSearchService(db)
    saved_search = await service.update_saved_search(
        user_id=user_id,
        saved_search_id=saved_search_id,
        name=payload.name,
        query_params=payload.query_params,
        alert_enabled=payload.alert_enabled,
        alert_frequency=payload.alert_frequency,
        webhook_url=payload.webhook_url,
        webhook_type=payload.webhook_type,
    )
    if not saved_search:
        raise HTTPException(status_code=404, detail="Saved search not found")
    return {
        "success": True,
        "message": "Saved search updated",
        "saved_search": saved_search,
    }


@router.delete(
    "/{saved_search_id}",
    response_model=SavedSearchMutationResponse,
    responses={404: {"description": "Saved search not found"}},
)
async def delete_saved_search(
    saved_search_id: UUID,
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = SavedSearchService(db)
    removed = await service.delete_saved_search(
        user_id=user_id, saved_search_id=saved_search_id
    )
    if not removed:
        raise HTTPException(status_code=404, detail="Saved search not found")
    return {"success": True, "message": "Saved search deleted"}


@router.post("/test-webhook", response_model=WebhookTestResponse)
async def test_webhook(
    payload: WebhookTestRequest,
    _user_id: Annotated[str, Depends(get_current_user_id)],
):
    """
    Send a test notification to verify webhook configuration.

    Sends a sample notification to the provided webhook URL.
    """
    notification_service = NotificationService()
    result = await notification_service.test_webhook(
        webhook_url=payload.webhook_url,
        webhook_type=payload.webhook_type,
    )
    return result
