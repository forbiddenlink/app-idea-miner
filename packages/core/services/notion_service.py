"""
Notion service for syncing top-quality idea clusters to the "Ideas Pipeline" database.

Idempotent: queries the data source by the "Source ID" property before writing, so
re-runs PATCH the existing page instead of creating a duplicate.

No-ops (fail open) when NOTION_API_KEY / NOTION_IDEAS_DB_ID are not configured, so a
missing Notion setup never breaks a clustering run.
"""

import logging
import os
from datetime import UTC, datetime
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class NotionService:
    """Service for pushing clusters to the Notion Ideas Pipeline data source."""

    NOTION_VERSION = "2025-09-03"
    API_BASE = "https://api.notion.com/v1"
    REQUEST_TIMEOUT = 10.0

    def __init__(
        self,
        api_key: str | None = None,
        data_source_id: str | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("NOTION_API_KEY")
        self.data_source_id = (
            data_source_id
            if data_source_id is not None
            else os.getenv("NOTION_IDEAS_DB_ID")
        )
        self.enabled = bool(self.api_key and self.data_source_id)

        if not self.enabled:
            logger.warning(
                "NOTION_API_KEY or NOTION_IDEAS_DB_ID not set. Notion sink disabled."
            )

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Notion-Version": self.NOTION_VERSION,
            "Content-Type": "application/json",
        }

    async def push_cluster(self, cluster: Any) -> bool:
        """
        Push a single cluster to the Notion Ideas Pipeline database.

        Queries for an existing page by "Source ID" first (idempotency key), then
        PATCHes it if found, or POSTs a new page otherwise.

        Args:
            cluster: A Cluster model instance (label, description, keywords, id)

        Returns:
            True if the page was created or updated, False otherwise (including no-op
            when the Notion sink is not configured).
        """
        if not self.enabled:
            logger.info(
                f"Notion sink disabled - skipping push for cluster {getattr(cluster, 'id', 'unknown')}"
            )
            return False

        source_id = str(cluster.id)

        try:
            existing_page_id = await self._find_existing_page(source_id)
            properties = self._build_properties(cluster)

            async with httpx.AsyncClient(timeout=self.REQUEST_TIMEOUT) as client:
                if existing_page_id:
                    response = await client.patch(
                        f"{self.API_BASE}/pages/{existing_page_id}",
                        headers=self._headers(),
                        json={"properties": properties},
                    )
                else:
                    response = await client.post(
                        f"{self.API_BASE}/pages",
                        headers=self._headers(),
                        json={
                            "parent": {"data_source_id": self.data_source_id},
                            "properties": properties,
                        },
                    )

                if response.status_code in (200, 201):
                    logger.info(f"Notion push succeeded for cluster {source_id}")
                    return True
                else:
                    logger.error(
                        f"Notion push failed for cluster {source_id}: "
                        f"{response.status_code} - {response.text}"
                    )
                    return False

        except Exception as e:
            logger.error(f"Notion push error for cluster {source_id}: {e}")
            return False

    async def _find_existing_page(self, source_id: str) -> str | None:
        """
        Query the data source for a page whose "Source ID" matches this cluster.

        Args:
            source_id: str(cluster.id), the idempotency key

        Returns:
            The existing page id, or None if no match was found (or the query failed).
        """
        query_payload = {
            "filter": {
                "property": "Source ID",
                "rich_text": {"equals": source_id},
            }
        }

        async with httpx.AsyncClient(timeout=self.REQUEST_TIMEOUT) as client:
            response = await client.post(
                f"{self.API_BASE}/data_sources/{self.data_source_id}/query",
                headers=self._headers(),
                json=query_payload,
            )

            if response.status_code != 200:
                logger.warning(
                    f"Notion idempotency query failed: "
                    f"{response.status_code} - {response.text}"
                )
                return None

            results = response.json().get("results", [])
            return results[0]["id"] if results else None

    def _build_properties(self, cluster: Any) -> dict[str, Any]:
        """
        Map a Cluster to Notion page properties.

        Only sets the fields the miner owns (Idea, Notes, Context, Status, Date Added,
        Source ID). Potential Revenue/Confidence/Complexity/Skill Fit/Stack are left
        untouched for manual curation.
        """
        keywords = ", ".join(cluster.keywords or [])
        description = cluster.description or ""
        notes = f"{description}\nKeywords: {keywords}\n[auto-mined by app-idea-miner]"

        today = datetime.now(UTC).date().isoformat()

        return {
            "Idea": {"title": [{"text": {"content": cluster.label}}]},
            "Notes": {"rich_text": [{"text": {"content": notes}}]},
            "Context": {"select": {"name": "Personal"}},
            "Status": {"select": {"name": "Idea"}},
            "Date Added": {"date": {"start": today}},
            "Source ID": {"rich_text": [{"text": {"content": str(cluster.id)}}]},
        }
