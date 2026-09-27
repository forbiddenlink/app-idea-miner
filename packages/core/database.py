"""
Shared database configuration for both API and Worker.
"""

import os
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool


def _normalize_for_asyncpg(url: str) -> tuple[str, dict]:
    """
    Make a libpq-style connection string safe for the asyncpg driver.

    Neon/managed Postgres issue URLs like
    `postgresql://.../db?sslmode=require&channel_binding=require`. asyncpg does
    not accept `sslmode`/`channel_binding` as query params, and forwarding the
    raw `sslmode` value is fragile (asyncpg validates the string against a
    fixed list). So when those params are present we STRIP all SSL-related
    query params from the URL, force the `postgresql+asyncpg://` scheme, and
    request TLS unambiguously via ``connect_args={"ssl": True}`` (asyncpg's
    default verified SSL context — what Neon needs).

    Guarded: URLs without `sslmode`/`channel_binding` are returned byte-for-byte
    unchanged with no connect_args, so an already-clean URL (e.g. the working
    prod value) is untouched.
    """
    parts = urlsplit(url)
    query = parse_qsl(parts.query, keep_blank_values=True)
    ssl_keys = {"sslmode", "channel_binding", "ssl"}
    if not (ssl_keys & {key for key, _ in query}):
        return url, {}
    scheme = (
        "postgresql+asyncpg"
        if parts.scheme in ("postgres", "postgresql")
        else parts.scheme
    )
    pairs = [(key, value) for key, value in query if key not in ssl_keys]
    clean = urlunsplit(
        (scheme, parts.netloc, parts.path, urlencode(pairs), parts.fragment)
    )
    return clean, {"ssl": True}


# Get database URL from environment
DATABASE_URL, _connect_args = _normalize_for_asyncpg(
    os.getenv(
        "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@postgres:5432/appideas"
    )
)

# Create async engine.
# One-shot runners (e.g. the GH Actions cron) invoke several Celery tasks in
# sequence, each in its own asyncio.run() loop. A shared connection pool binds
# its connections to the first loop and raises "Event loop is closed" on the
# next task, so those contexts set DB_DISABLE_POOL=1 to use NullPool (a fresh
# connection per use). Long-lived services (API) keep the pool.
if os.getenv("DB_DISABLE_POOL"):
    engine = create_async_engine(
        DATABASE_URL,
        poolclass=NullPool,
        pool_pre_ping=True,
        echo=False,
        connect_args=_connect_args,
    )
else:
    engine = create_async_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_recycle=1800,
        pool_pre_ping=True,
        echo=False,
        connect_args=_connect_args,
    )

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


def reset_engine_for_fork() -> None:
    """
    Discard this engine's pooled connections and internal asyncio primitives.

    `engine` is created once at import time, in the Celery master process
    before the prefork pool forks worker child processes. SQLAlchemy's async
    connection pool lazily creates its internal `asyncio.Lock`/`Event`
    objects bound to whichever event loop is running the first time a
    connection is checked out. A forked child process runs its own fresh
    event loop per task (`asyncio.run(...)` in `process_raw_posts`), so the
    first task on a newly started worker process reused the parent's
    inherited (loop-bound) pool and failed with
    "Future ... attached to a different loop" (or "Event loop is closed").

    Call this once, synchronously, from Celery's `worker_process_init`
    signal (see `apps/worker/celery_app.py`) so every worker child process
    starts with an empty pool and lazily creates loop-bound state against
    its own event loop on first use instead of the parent's.

    `close=False` skips synchronously closing any connections the parent
    process still had checked out (that would itself need the parent's now
    gone event loop); those connections are simply dropped, which is safe
    since the child process has no in-flight work yet.
    """
    engine.sync_engine.dispose(close=False)


async def get_db():
    """
    Dependency for FastAPI endpoints.

    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
