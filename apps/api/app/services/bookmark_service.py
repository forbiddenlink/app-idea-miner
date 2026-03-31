"""Bookmark service for saved ideas and clusters."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from packages.core.models import Bookmark, Cluster, IdeaCandidate


class BookmarkService:
    """Business logic for persisted bookmarks."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _user_uuid(user_id: str) -> UUID:
        return UUID(user_id)

    @staticmethod
    def _serialize_cluster(cluster: Cluster | None) -> dict[str, Any] | None:
        if not cluster:
            return None
        return {
            "id": str(cluster.id),
            "label": cluster.label,
            "description": cluster.description,
            "keywords": cluster.keywords,
            "idea_count": cluster.idea_count,
            "avg_sentiment": cluster.avg_sentiment,
            "quality_score": cluster.quality_score,
            "trend_score": cluster.trend_score,
            "created_at": cluster.created_at.isoformat()
            if cluster.created_at
            else None,
            "updated_at": cluster.updated_at.isoformat()
            if cluster.updated_at
            else None,
        }

    @staticmethod
    def _serialize_idea(idea: IdeaCandidate | None) -> dict[str, Any] | None:
        if not idea:
            return None

        raw_post = None
        if idea.raw_post:
            published_at = (
                idea.raw_post.published_at.isoformat()
                if idea.raw_post.published_at
                else None
            )
            raw_post = {
                "id": str(idea.raw_post.id),
                "url": idea.raw_post.url,
                "title": idea.raw_post.title,
                "source": idea.raw_post.source,
                "published_at": published_at,
            }

        extracted_at = idea.extracted_at.isoformat() if idea.extracted_at else None
        return {
            "id": str(idea.id),
            "problem_statement": idea.problem_statement,
            "context": idea.context,
            "domain": idea.domain,
            "sentiment": idea.sentiment,
            "sentiment_score": idea.sentiment_score,
            "emotions": idea.emotions,
            "quality_score": idea.quality_score,
            "features_mentioned": idea.features_mentioned,
            "extracted_at": extracted_at,
            "raw_post": raw_post,
        }

    @classmethod
    def _serialize_bookmark(
        cls,
        bookmark: Bookmark,
        clusters_map: dict[UUID, Cluster],
        ideas_map: dict[UUID, IdeaCandidate],
    ) -> dict[str, Any]:
        cluster_payload = None
        idea_payload = None
        if bookmark.item_type == "cluster":
            cluster_payload = cls._serialize_cluster(clusters_map.get(bookmark.item_id))
        elif bookmark.item_type == "idea":
            idea_payload = cls._serialize_idea(ideas_map.get(bookmark.item_id))

        return {
            "item_type": bookmark.item_type,
            "item_id": str(bookmark.item_id),
            "scope_key": str(bookmark.user_id),
            "created_at": bookmark.created_at.isoformat(),
            "cluster": cluster_payload,
            "idea": idea_payload,
        }

    async def list_bookmarks(
        self,
        user_id: str,
        item_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        user_uuid = self._user_uuid(user_id)

        stmt = select(Bookmark).where(Bookmark.user_id == user_uuid)
        count_stmt = (
            select(func.count())
            .select_from(Bookmark)
            .where(Bookmark.user_id == user_uuid)
        )

        if item_type:
            stmt = stmt.where(Bookmark.item_type == item_type)
            count_stmt = count_stmt.where(Bookmark.item_type == item_type)

        stmt = stmt.order_by(Bookmark.created_at.desc()).offset(offset).limit(limit)

        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        result = await self.db.execute(stmt)
        bookmarks = result.scalars().all()

        cluster_ids = [b.item_id for b in bookmarks if b.item_type == "cluster"]
        idea_ids = [b.item_id for b in bookmarks if b.item_type == "idea"]

        clusters_map: dict[UUID, Cluster] = {}
        ideas_map: dict[UUID, IdeaCandidate] = {}

        if cluster_ids:
            clusters_result = await self.db.execute(
                select(Cluster).where(Cluster.id.in_(cluster_ids))
            )
            clusters_map = {
                cluster.id: cluster for cluster in clusters_result.scalars()
            }

        if idea_ids:
            ideas_result = await self.db.execute(
                select(IdeaCandidate)
                .where(IdeaCandidate.id.in_(idea_ids))
                .options(selectinload(IdeaCandidate.raw_post))
            )
            ideas_map = {idea.id: idea for idea in ideas_result.scalars()}

        formatted = [
            self._serialize_bookmark(bookmark, clusters_map, ideas_map)
            for bookmark in bookmarks
        ]

        return {
            "bookmarks": formatted,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total,
            },
        }

    async def upsert_bookmark(
        self,
        user_id: str,
        item_type: str,
        item_id: UUID,
    ) -> Bookmark:
        user_uuid = self._user_uuid(user_id)

        if item_type not in {"cluster", "idea"}:
            raise ValueError("Invalid item_type")

        if item_type == "cluster":
            exists_stmt = select(Cluster.id).where(Cluster.id == item_id)
        else:
            exists_stmt = select(IdeaCandidate.id).where(IdeaCandidate.id == item_id)

        exists_result = await self.db.execute(exists_stmt)
        if not exists_result.scalar_one_or_none():
            raise ValueError(f"{item_type} not found")

        existing_result = await self.db.execute(
            select(Bookmark).where(
                Bookmark.user_id == user_uuid,
                Bookmark.item_type == item_type,
                Bookmark.item_id == item_id,
            )
        )
        existing = existing_result.scalar_one_or_none()
        if existing:
            return existing

        bookmark = Bookmark(
            user_id=user_uuid,
            item_type=item_type,
            item_id=item_id,
        )
        self.db.add(bookmark)
        await self.db.flush()
        return bookmark

    async def remove_bookmark(
        self,
        user_id: str,
        item_type: str,
        item_id: UUID,
    ) -> bool:
        user_uuid = self._user_uuid(user_id)
        result = await self.db.execute(
            delete(Bookmark).where(
                Bookmark.user_id == user_uuid,
                Bookmark.item_type == item_type,
                Bookmark.item_id == item_id,
            )
        )
        return (result.rowcount or 0) > 0

    async def clear_bookmarks(
        self,
        user_id: str,
        item_type: str | None = None,
    ) -> int:
        user_uuid = self._user_uuid(user_id)
        stmt = delete(Bookmark).where(Bookmark.user_id == user_uuid)
        if item_type:
            stmt = stmt.where(Bookmark.item_type == item_type)
        result = await self.db.execute(stmt)
        return result.rowcount or 0
