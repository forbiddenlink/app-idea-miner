"""
Posts API endpoints for raw post management.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.database import get_db
from packages.core.dedupe import generate_url_hash, is_duplicate_title
from packages.core.models import RawPost

logger = logging.getLogger(__name__)

router = APIRouter(tags=["posts"])


@router.post("/seed", status_code=status.HTTP_201_CREATED)
async def seed_sample_data(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Load sample posts from data/sample_posts.json.

    Applies deduplication logic before inserting.
    Useful for development and demo purposes.

    Returns:
        dict: Statistics (inserted, duplicates, total, errors)
    """
    logger.info("Starting sample data seeding...")

    # Load sample data file
    data_path = Path(__file__).parents[4] / "data" / "sample_posts.json"

    if not data_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Sample data file not found: {data_path}"
        )

    try:
        with open(data_path) as f:
            sample_posts = json.load(f)
    except Exception as e:
        logger.error(f"Error loading sample data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load sample data: {str(e)}",
        )

    logger.info(f"Loaded {len(sample_posts)} posts from sample data")

    inserted = 0
    duplicates = 0
    errors = 0

    for post_data in sample_posts:
        try:
            url = post_data.get("url")
            title = post_data.get("title")

            if not url or not title:
                logger.warning("Skipping post with missing URL or title")
                errors += 1
                continue

            # Generate URL hash
            url_hash = generate_url_hash(url)

            # Check for URL hash duplicate
            result = await db.execute(select(RawPost).where(RawPost.url_hash == url_hash))
            if result.scalar_one_or_none():
                logger.debug(f"Duplicate URL hash: {url[:50]}...")
                duplicates += 1
                continue

            # Check for title duplicate (against recent posts)
            result = await db.execute(
                select(RawPost).order_by(RawPost.fetched_at.desc()).limit(1000)
            )
            recent_posts = result.scalars().all()

            is_dup = False
            for existing_post in recent_posts:
                if is_duplicate_title(title, existing_post.title):
                    logger.debug(f"Duplicate title: {title[:50]}...")
                    duplicates += 1
                    is_dup = True
                    break

            if is_dup:
                continue

            # Parse published_at
            published_at = None
            if post_data.get("published_at"):
                try:
                    published_at = datetime.fromisoformat(
                        post_data["published_at"].replace("Z", "+00:00")
                    )
                except Exception as e:
                    logger.warning(f"Error parsing date: {e}")

            # Create new post
            new_post = RawPost(
                url=url,
                url_hash=url_hash,
                title=title,
                content=post_data.get("content", ""),
                source=post_data.get("source", "sample"),
                author=post_data.get("author"),
                published_at=published_at,
                fetched_at=datetime.utcnow(),
                source_metadata=post_data.get("metadata", {}),
                is_processed=False,
            )

            db.add(new_post)
            inserted += 1
            logger.debug(f"Inserted post: {title[:50]}...")

        except Exception as e:
            logger.error(f"Error processing post: {e}", exc_info=True)
            errors += 1
            continue

    # Commit all inserts
    try:
        await db.commit()
        logger.info(f"Sample data seeding complete: {inserted} inserted, {duplicates} duplicates")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error committing sample data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database commit failed: {str(e)}",
        )

    return {
        "status": "success",
        "inserted": inserted,
        "duplicates": duplicates,
        "total": len(sample_posts),
        "errors": errors,
    }


@router.get("")
async def list_posts(
    limit: int = 20,
    offset: int = 0,
    source: str | None = None,
    is_processed: bool | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    List raw posts with pagination and filtering.

    Args:
        limit: Number of posts to return (max 100)
        offset: Number of posts to skip
        source: Filter by source (e.g., 'hackernews', 'reddit')
        is_processed: Filter by processing status
        db: Database session

    Returns:
        dict: Posts list with pagination metadata
    """
    # Validate limit
    if limit > 100:
        limit = 100

    # Build query
    query = select(RawPost)

    if source:
        query = query.where(RawPost.source == source)

    if is_processed is not None:
        query = query.where(RawPost.is_processed == is_processed)

    # Get total count
    count_query = select(func.count()).select_from(RawPost)
    if source:
        count_query = count_query.where(RawPost.source == source)
    if is_processed is not None:
        count_query = count_query.where(RawPost.is_processed == is_processed)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination and ordering
    query = query.order_by(RawPost.fetched_at.desc()).offset(offset).limit(limit)

    # Execute query
    result = await db.execute(query)
    posts = result.scalars().all()

    return {
        "posts": [
            {
                "id": str(post.id),
                "url": post.url,
                "title": post.title,
                "source": post.source,
                "author": post.author,
                "published_at": post.published_at.isoformat() if post.published_at else None,
                "fetched_at": post.fetched_at.isoformat() if post.fetched_at else None,
                "is_processed": post.is_processed,
                "metadata": post.source_metadata,
            }
            for post in posts
        ],
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total,
        },
    }


@router.get("/{post_id}")
async def get_post(
    post_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get a single post by ID.

    Args:
        post_id: UUID of the post
        db: Database session

    Returns:
        dict: Post details
    """
    result = await db.execute(select(RawPost).where(RawPost.id == post_id))
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with ID {post_id} not found"
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
async def get_stats(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Get statistics about raw posts.

    Returns:
        dict: Statistics (total, by source, processed vs unprocessed)
    """
    # Total count
    total_result = await db.execute(select(func.count()).select_from(RawPost))
    total = total_result.scalar()

    # Processed count
    processed_result = await db.execute(
        select(func.count()).select_from(RawPost).where(RawPost.is_processed == True)
    )
    processed = processed_result.scalar()

    # Count by source
    source_result = await db.execute(select(RawPost.source, func.count()).group_by(RawPost.source))
    by_source = {source: count for source, count in source_result.all()}

    return {
        "total": total,
        "processed": processed,
        "unprocessed": total - processed,
        "by_source": by_source,
    }
