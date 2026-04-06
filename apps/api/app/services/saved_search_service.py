"""Service layer for user saved searches."""

from __future__ import annotations

from typing import Any, cast
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.core.models import SavedSearch


class SavedSearchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _user_uuid(user_id: str) -> UUID:
        return UUID(user_id)

    @staticmethod
    def _serialize(saved_search: SavedSearch) -> dict[str, Any]:
        return {
            "id": str(saved_search.id),
            "name": saved_search.name,
            "query_params": saved_search.query_params or {},
            "alert_enabled": bool(saved_search.alert_enabled),
            "alert_frequency": saved_search.alert_frequency,
            "webhook_url": saved_search.webhook_url,
            "webhook_type": saved_search.webhook_type,
            "last_alert_at": saved_search.last_alert_at.isoformat()
            if saved_search.last_alert_at
            else None,
            "created_at": saved_search.created_at.isoformat(),
            "updated_at": saved_search.updated_at.isoformat(),
        }

    async def list_saved_searches(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        user_uuid = self._user_uuid(user_id)

        count_stmt = (
            select(func.count())
            .select_from(SavedSearch)
            .where(SavedSearch.user_id == user_uuid)
        )
        total = (await self.db.execute(count_stmt)).scalar_one()

        query = (
            select(SavedSearch)
            .where(SavedSearch.user_id == user_uuid)
            .order_by(SavedSearch.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = (await self.db.execute(query)).scalars().all()

        return {
            "saved_searches": [self._serialize(row) for row in rows],
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total,
            },
        }

    async def create_saved_search(
        self,
        user_id: str,
        name: str,
        query_params: dict[str, Any] | None,
        alert_enabled: bool,
        alert_frequency: str,
        webhook_url: str | None = None,
        webhook_type: str | None = None,
    ) -> dict[str, Any]:
        user_uuid = self._user_uuid(user_id)

        saved_search = SavedSearch(
            user_id=user_uuid,
            name=name.strip(),
            query_params=query_params or {},
            alert_enabled=alert_enabled,
            alert_frequency=alert_frequency,
            webhook_url=webhook_url,
            webhook_type=webhook_type,
        )
        self.db.add(saved_search)
        await self.db.flush()
        await self.db.refresh(saved_search)
        return self._serialize(saved_search)

    async def update_saved_search(
        self,
        user_id: str,
        saved_search_id: UUID,
        name: str | None,
        query_params: dict[str, Any] | None,
        alert_enabled: bool | None,
        alert_frequency: str | None,
        webhook_url: str | None = None,
        webhook_type: str | None = None,
    ) -> dict[str, Any] | None:
        user_uuid = self._user_uuid(user_id)

        stmt = select(SavedSearch).where(
            SavedSearch.id == saved_search_id,
            SavedSearch.user_id == user_uuid,
        )
        saved_search = (await self.db.execute(stmt)).scalar_one_or_none()
        if not saved_search:
            return None

        saved_search_any = cast(Any, saved_search)

        if name is not None:
            saved_search_any.name = name.strip()
        if query_params is not None:
            saved_search_any.query_params = query_params
        if alert_enabled is not None:
            saved_search_any.alert_enabled = alert_enabled
        if alert_frequency is not None:
            saved_search_any.alert_frequency = alert_frequency
        if webhook_url is not None:
            saved_search_any.webhook_url = webhook_url if webhook_url else None
        if webhook_type is not None:
            saved_search_any.webhook_type = webhook_type if webhook_type else None

        await self.db.flush()
        await self.db.refresh(saved_search)
        return self._serialize(saved_search)

    async def delete_saved_search(self, user_id: str, saved_search_id: UUID) -> bool:
        user_uuid = self._user_uuid(user_id)
        result = await self.db.execute(
            delete(SavedSearch).where(
                SavedSearch.id == saved_search_id,
                SavedSearch.user_id == user_uuid,
            )
        )
        rowcount = getattr(result, "rowcount", 0) or 0
        return rowcount > 0
