"""API endpoints for persisted bookmarks."""

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
from apps.api.app.schemas.bookmarks import (
    BookmarkClearResponse,
    BookmarkCreateRequest,
    BookmarkListResponse,
    BookmarkMutationResponse,
)
from apps.api.app.services.bookmark_service import BookmarkService

router = APIRouter(
    tags=["bookmarks"],
    dependencies=[Depends(get_api_key), Depends(RateLimiter(times=100, seconds=60))],
)


@router.get("", response_model=BookmarkListResponse)
async def list_bookmarks(
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    item_type: Annotated[str | None, Query(pattern="^(cluster|idea)$")] = None,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_LIMIT)] = DEFAULT_PAGE_LIMIT,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    service = BookmarkService(db)
    return await service.list_bookmarks(
        user_id=user_id,
        item_type=item_type,
        limit=limit,
        offset=offset,
    )


@router.post(
    "",
    response_model=BookmarkMutationResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Invalid request"},
        404: {"description": "Item not found"},
    },
)
async def create_bookmark(
    payload: BookmarkCreateRequest,
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = BookmarkService(db)
    try:
        await service.upsert_bookmark(
            user_id=user_id,
            item_type=payload.item_type,
            item_id=UUID(payload.item_id),
        )
    except ValueError as exc:
        message = str(exc)
        if message.endswith("not found"):
            raise HTTPException(status_code=404, detail=message) from exc
        raise HTTPException(status_code=400, detail=message) from exc

    return {"success": True, "message": "Bookmark saved"}


@router.delete(
    "/{item_type}/{item_id}",
    response_model=BookmarkMutationResponse,
    responses={400: {"description": "Invalid item_type"}},
)
async def delete_bookmark(
    item_type: str,
    item_id: UUID,
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if item_type not in {"cluster", "idea"}:
        raise HTTPException(status_code=400, detail="Invalid item_type")

    service = BookmarkService(db)
    removed = await service.remove_bookmark(
        user_id=user_id,
        item_type=item_type,
        item_id=item_id,
    )
    return {
        "success": True,
        "message": "Bookmark removed" if removed else "Bookmark was already absent",
    }


@router.delete("", response_model=BookmarkClearResponse)
async def clear_bookmarks(
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    item_type: Annotated[str | None, Query(pattern="^(cluster|idea)$")] = None,
):
    service = BookmarkService(db)
    deleted = await service.clear_bookmarks(user_id=user_id, item_type=item_type)
    return {"success": True, "deleted": deleted}
