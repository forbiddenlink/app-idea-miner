"""
Shared database configuration for both API and Worker.
"""

import os
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


def _normalize_for_asyncpg(url: str) -> str:
    """
    Make a libpq-style connection string safe for the asyncpg driver.

    Neon/managed Postgres often issue URLs like
    `postgresql://.../db?sslmode=require&channel_binding=require`. asyncpg
    rejects `sslmode`/`channel_binding` as query params, so rewrite them:
    force the `postgresql+asyncpg://` scheme, rename `sslmode` -> `ssl`, and
    drop `channel_binding`. Guarded: URLs that don't carry those params are
    returned byte-for-byte unchanged, so an already-clean URL is untouched.
    """
    if "sslmode" not in url and "channel_binding" not in url:
        return url
    parts = urlsplit(url)
    scheme = "postgresql+asyncpg" if parts.scheme in ("postgres", "postgresql") else parts.scheme
    pairs = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        if key == "channel_binding":
            continue
        pairs.append(("ssl", value) if key == "sslmode" else (key, value))
    return urlunsplit((scheme, parts.netloc, parts.path, urlencode(pairs), parts.fragment))


# Get database URL from environment
DATABASE_URL = _normalize_for_asyncpg(
    os.getenv(
        "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@postgres:5432/appideas"
    )
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_recycle=1800,
    pool_pre_ping=True,
    echo=False,
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


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
