"""
Posts API endpoints for raw post management.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.rate_limit import RateLimiter
from apps.api.app.core.security import get_api_key
from apps.api.app.database import get_db
from packages.core.services.post_service import PostService

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["posts"],
    dependencies=[Depends(get_api_key), Depends(RateLimiter(times=100, seconds=60))],
)


def get_post_service(db: AsyncSession = Depends(get_db)) -> PostService:
    return PostService(db)


@router.post("/seed", status_code=status.HTTP_201_CREATED)
async def seed_sample_data(service: PostService = Depends(get_post_service)) -> dict:
    """
    Load sample posts from data/sample_posts.json.

    Applies deduplication logic before inserting.
    Useful for development and demo purposes.

    Returns:
        dict: Statistics (inserted, duplicates, total, errors)
    """
    try:
        return await service.seed_from_file()
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        # Return 500 but detail might be safe enough for now
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("")
async def list_posts(
    limit: int = 20,
    offset: int = 0,
    source: str | None = None,
    is_processed: bool | None = None,
    service: PostService = Depends(get_post_service),
) -> dict:
    """
    List raw posts with pagination and filtering.

    Args:
        limit: Number of posts to return (max 100)
        offset: Number of posts to skip
        source: Filter by source (e.g., 'hackernews', 'reddit')
        is_processed: Filter by processing status
        service: Post business logic service

    Returns:
        dict: Posts list with pagination metadata
    """
    result = await service.list_posts(limit, offset, source, is_processed)

    # Transform to API response format
    # The service returns ORM objects, we serialize here or Pydantic (using manual dict for now to match original)
    posts = [
        {
            "id": str(post.id),
            "url": post.url,
            "title": post.title,
            "source": post.source,
            "author": post.author,
            "published_at": post.published_at.isoformat()
            if post.published_at
            else None,
            "fetched_at": post.fetched_at.isoformat() if post.fetched_at else None,
            "is_processed": post.is_processed,
            "metadata": post.source_metadata,
        }
        for post in result["posts"]
    ]

    return {
        "posts": posts,
        "pagination": {
            "total": result["total"],
            "limit": result["limit"],
            "offset": result["offset"],
            "has_more": result["offset"] + result["limit"] < result["total"],
        },
    }


@router.get("/{post_id}")
async def get_post(
    post_id: str,
    service: PostService = Depends(get_post_service),
) -> dict:
    """
    Get a single post by ID.

    Args:
        post_id: UUID of the post
        service: Post business logic service

    Returns:
        dict: Post details
    """
    post = await service.get_post(post_id)

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with ID {post_id} not found",
        )

    return {
        "id": str(post.id),
        "url": post.url,
        "url_hash": post.url_hash,
        "title": post.title,
        "content": post.content,
        "source": post.source,
        "author": post.author,
        "published_at": post.published_at.isoformat() if post.published_at else None,
        "fetched_at": post.fetched_at.isoformat() if post.fetched_at else None,
        "metadata": post.source_metadata,
        "is_processed": post.is_processed,
        "created_at": post.created_at.isoformat() if post.created_at else None,
        "updated_at": post.updated_at.isoformat() if post.updated_at else None,
    }


@router.get("/stats/summary")
async def get_stats(service: PostService = Depends(get_post_service)) -> dict:
    """
    Get statistics about raw posts.

    Returns:
        dict: Statistics (total, by source, processed vs unprocessed)
    """
    return await service.get_stats()
