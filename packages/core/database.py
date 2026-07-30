"""
Shared database configuration for both API and Worker.
"""

import os
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


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
    if "sslmode" not in url and "channel_binding" not in url:
        return url, {}
    parts = urlsplit(url)
    scheme = "postgresql+asyncpg" if parts.scheme in ("postgres", "postgresql") else parts.scheme
    pairs = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key not in ("sslmode", "channel_binding", "ssl")
    ]
    clean = urlunsplit((scheme, parts.netloc, parts.path, urlencode(pairs), parts.fragment))
    return clean, {"ssl": True}


# Get database URL from environment
DATABASE_URL, _connect_args = _normalize_for_asyncpg(
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
    connect_args=_connect_args,
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
