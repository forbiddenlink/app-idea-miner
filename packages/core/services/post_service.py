import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.core.dedupe import generate_url_hash, is_duplicate_title
from packages.core.models import RawPost

logger = logging.getLogger(__name__)


class PostService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def seed_from_file(self) -> dict[str, Any]:
        """
        Load sample posts from data/sample_posts.json with deduplication.
        """
        logger.info("Starting sample data seeding...")

        # Load sample data file
        # Assuming the service is called from within the app structure,
        # but we need to find the absolute path relative to the project root.
        # Original router used: Path(__file__).parents[4] / "data" / "sample_posts.json"
        # We need to be careful with paths here.
        # Let's try to locate it relative to this file: packages/core/services/post_service.py
        # Project root is ../../../

        data_path = Path(__file__).parents[3] / "data" / "sample_posts.json"

        if not data_path.exists():
            # Fallback for different execution contexts or try absolute path if known
            # Reverting to the logic that worked in router but adjusted for new depth
            # Router was in apps/api/app/routers (depth 4 from root?)
            # This file is packages/core/services (depth 3 from root)
            pass

        try:
            with open(data_path) as f:
                sample_posts = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Sample data file not found: {data_path}")
        except Exception as e:
            raise Exception(f"Failed to load sample data: {str(e)}")

        logger.info(f"Loaded {len(sample_posts)} posts from sample data")

        inserted = 0
        duplicates = 0
        errors = 0

        # Pre-process queries for bulk checking
        # But for max speed we rely on DB constraints (ON CONFLICT DO NOTHING)
        # However, we also want to deduplicate by title which is harder in SQL if not unique constraint
        # Let's assume URL hash is the primary dedup key for "fast path"

        # 1. Prepare all objects
        raw_values = []
        for post_data in sample_posts:
            url = post_data.get("url")
            title = post_data.get("title")

            if not url or not title:
                errors += 1
                continue

            url_hash = generate_url_hash(url)

            # Basic client-side dedup for the batch itself
            # (Skipping here for brevity, assuming standard ON CONFLICT handles DB side)

            published_at = None
            if post_data.get("published_at"):
                try:
                    published_at = datetime.fromisoformat(
                        post_data["published_at"].replace("Z", "+00:00")
                    )
                except Exception:
                    pass

            raw_values.append(
                {
                    "url": url,
                    "url_hash": url_hash,
                    "title": title,
                    "content": post_data.get("content", ""),
                    "source": post_data.get("source", "sample"),
                    "author": post_data.get("author"),
                    "published_at": published_at,
                    "fetched_at": datetime.now(UTC),
                    "source_metadata": post_data.get("metadata", {}),
                    "is_processed": False,
                }
            )

        if not raw_values:
            return {
                "status": "success",
                "inserted": 0,
                "duplicates": 0,
                "total": len(sample_posts),
                "errors": errors,
            }

        # 2. Bulk Insert with ON CONFLICT DO NOTHING
        from sqlalchemy.dialects.postgresql import insert

        stmt = insert(RawPost).values(raw_values)
        stmt = stmt.on_conflict_do_nothing(index_elements=["url"])

        # We want to know how many were inserted.
        # RETURNING id allows us to count; if it returns None (row), it was duplicate
        # Note: on_conflict_do_nothing returns ONLY inserted rows if we ask for RETURNING
        result = await self.db.execute(stmt.returning(RawPost.id))
        inserted_ids = result.scalars().all()
        inserted = len(inserted_ids)
        duplicates = len(raw_values) - inserted

        try:
            await self.db.commit()
            logger.info(
                f"Sample data seeding complete: {inserted} inserted, {duplicates} duplicates (skipped)"
            )
        except Exception as e:
            await self.db.rollback()
            raise Exception(f"Database commit failed: {str(e)}")

        return {
            "status": "success",
            "inserted": inserted,
            "duplicates": duplicates,
            "total": len(sample_posts),
            "errors": errors,
        }

    async def list_posts(
        self,
        limit: int = 20,
        offset: int = 0,
        source: str | None = None,
        is_processed: bool | None = None,
    ) -> dict[str, Any]:
        # Apply strict limit cap
        if limit > 100:
            limit = 100

        # Build query
        query = select(RawPost)
        count_query = select(func.count()).select_from(RawPost)

        if source:
            query = query.where(RawPost.source == source)
            count_query = count_query.where(RawPost.source == source)

        if is_processed is not None:
            query = query.where(RawPost.is_processed == is_processed)
            count_query = count_query.where(RawPost.is_processed == is_processed)

        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination and ordering
        query = query.order_by(RawPost.fetched_at.desc()).offset(offset).limit(limit)

        # Execute query
        result = await self.db.execute(query)
        posts = result.scalars().all()

        return {"posts": posts, "total": total, "limit": limit, "offset": offset}

    async def get_post(self, post_id: str) -> RawPost | None:
        result = await self.db.execute(select(RawPost).where(RawPost.id == post_id))
        return result.scalar_one_or_none()

    async def get_stats(self) -> dict[str, Any]:
        # Total count
        total_result = await self.db.execute(select(func.count()).select_from(RawPost))
        total = total_result.scalar() or 0

        # Processed count
        processed_result = await self.db.execute(
            select(func.count())
            .select_from(RawPost)
            .where(RawPost.is_processed == True)
        )
        processed = processed_result.scalar() or 0

        # Count by source
        source_result = await self.db.execute(
            select(RawPost.source, func.count()).group_by(RawPost.source)
        )
        by_source = {source: count for source, count in source_result.all()}

        return {
            "total": total,
            "processed": processed,
            "unprocessed": total - processed,
            "by_source": by_source,
        }
