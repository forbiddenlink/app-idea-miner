"""Fabricated mock posts must never reach the database.

Sources fall back to made-up posts (tagged source_metadata["mock"]=True) when
credentials are missing. The ingestion cycle has to refuse them, otherwise a
missing secret silently pollutes the clusters shown to users.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.worker.sources.base import BaseSource
from apps.worker.tasks import ingestion
from packages.core.models import RawPost


def _post(url: str, mock: bool) -> RawPost:
    return RawPost(
        source="test",
        url=url,
        url_hash=url,
        title="t",
        content="c",
        source_metadata={"mock": True} if mock else {},
    )


def _source(name: str, posts: list[RawPost], is_mock: bool) -> type[BaseSource]:
    async def fetch(self):
        return posts

    return type(name, (BaseSource,), {"fetch": fetch, "is_mock": is_mock})


@pytest.mark.asyncio
async def test_mock_source_is_skipped_and_counted_as_error():
    fake = _source("FakeMock", [_post("https://x/1", mock=True)], is_mock=True)
    session = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=session)
    ctx.__aexit__ = AsyncMock(return_value=False)
    saved = AsyncMock(return_value=True)

    stats = {"fetched": 0, "new": 0, "duplicates": 0, "errors": 0}
    with (
        patch.object(ingestion, "SOURCE_REGISTRY", [fake]),
        patch.object(ingestion, "AsyncSessionLocal", return_value=ctx),
        patch.object(ingestion, "_save_if_new", saved),
    ):
        await ingestion._run_ingestion_async(stats)

    saved.assert_not_called()
    assert stats["new"] == 0
    assert stats["errors"] == 1


@pytest.mark.asyncio
async def test_tagged_mock_posts_from_any_source_are_dropped():
    real = _post("https://x/real", mock=False)
    fake = _post("https://x/fake", mock=True)
    src = _source("Leaky", [real, fake], is_mock=False)
    session = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.begin_nested = MagicMock(
        return_value=MagicMock(
            __aenter__=AsyncMock(return_value=None),
            __aexit__=AsyncMock(return_value=False),
        )
    )
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=session)
    ctx.__aexit__ = AsyncMock(return_value=False)
    saved = AsyncMock(return_value=True)

    stats = {"fetched": 0, "new": 0, "duplicates": 0, "errors": 0}
    with (
        patch.object(ingestion, "SOURCE_REGISTRY", [src]),
        patch.object(ingestion, "AsyncSessionLocal", return_value=ctx),
        patch.object(ingestion, "_save_if_new", saved),
    ):
        await ingestion._run_ingestion_async(stats)

    assert [c.args[1].url for c in saved.call_args_list] == ["https://x/real"]
    assert stats["new"] == 1
