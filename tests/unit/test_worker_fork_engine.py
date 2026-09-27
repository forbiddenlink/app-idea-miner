"""
Regression test for the Celery worker cold-start "attached to a different
loop" bug (apps/worker/tasks/processing.py, first task on a fresh worker
process).

`packages.core.database.engine` is created once at import time, in the
Celery master process, before the prefork pool forks worker child
processes. SQLAlchemy's async connection pool lazily creates internal
asyncio primitives (locks/events) bound to whichever event loop is running
at first checkout. A forked child process runs its own event loop per task
(`asyncio.run(...)`), so the first task on a newly started worker process
reused the parent's loop-bound pool and raised RuntimeError ("attached to a
different loop" / "Event loop is closed").

Uses a dedicated engine created in this test module rather than the
process-wide `packages.core.database.engine` singleton, so disposing its
pool to reproduce/fix the bug can't affect the connection pool other tests
in this suite share.
"""

import asyncio
import os
from unittest.mock import patch

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from packages.core.database import reset_engine_for_fork

pytestmark = pytest.mark.requires_db

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/appideas_test",
)


@pytest.fixture
def dedicated_engine():
    """
    A standalone engine, mirroring packages.core.database's setup, that
    only this test module touches — safe to dispose without affecting the
    shared engine other tests in the suite use.
    """
    engine = create_async_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    yield engine
    engine.sync_engine.dispose(close=False)


async def _query_once(session_factory) -> None:
    async with session_factory() as session:
        await session.execute(text("SELECT 1"))


def test_cold_worker_first_task_succeeds_after_fork_reset(dedicated_engine):
    """
    A cold worker's first task must succeed with no retry once
    reset_engine_for_fork() (dispose(close=False)) has run — the
    worker_process_init fix.
    """
    session_factory = async_sessionmaker(
        dedicated_engine, class_=AsyncSession, expire_on_commit=False
    )

    # Simulate whatever event loop activity happened in the parent process
    # before Celery forked this worker (e.g. import-time engine creation
    # plus any startup checks).
    asyncio.run(_query_once(session_factory))

    # Simulate Celery's worker_process_init firing in the freshly forked
    # child process, before it picks up its first task. This is exactly
    # what packages.core.database.reset_engine_for_fork does to the real
    # shared engine.
    dedicated_engine.sync_engine.dispose(close=False)

    # Simulate the forked worker's first task, run in its own fresh loop
    # (mirrors `asyncio.run(_process_posts_async(...))` in
    # apps/worker/tasks/processing.py). This must succeed on the first
    # attempt, with no RuntimeError and no Celery retry.
    asyncio.run(_query_once(session_factory))


def test_reproduces_bug_without_the_fork_reset(dedicated_engine):
    """
    Sanity check that the failure this fix addresses is real: without
    disposing the pool between two separate asyncio.run() loops sharing
    the same engine, the second loop's first query raises.
    """
    session_factory = async_sessionmaker(
        dedicated_engine, class_=AsyncSession, expire_on_commit=False
    )

    asyncio.run(_query_once(session_factory))

    with pytest.raises(RuntimeError):
        asyncio.run(_query_once(session_factory))


def test_reset_engine_for_fork_disposes_the_shared_engine_pool():
    """
    packages.core.database.reset_engine_for_fork must be the function wired
    to Celery's worker_process_init (see apps/worker/celery_app.py) and
    must call dispose(close=False) on the real shared engine — checked here
    via a mock so this test never touches the shared engine's live
    connections (used by every other test in the suite).
    """
    with patch("packages.core.database.engine") as mock_engine:
        reset_engine_for_fork()
        mock_engine.sync_engine.dispose.assert_called_once_with(close=False)
