"""
Async database configuration with asyncpg driver.

Provides async SQLAlchemy engine and session management.
Uses production-ready connection pooling patterns.

Supports lazy initialization for serverless environments (Vercel).
"""

import os
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

# Database URL with asyncpg driver (8x faster than psycopg2)
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/appideas"
)

# Check if we're in a serverless environment without a database
IS_SERVERLESS = os.getenv("VERCEL", "") == "1"
HAS_DATABASE = bool(os.getenv("DATABASE_URL"))

# Declarative base for models (always available)
Base = declarative_base()

# Lazy engine and session initialization for serverless
_engine = None
_session_local = None


@lru_cache(maxsize=1)
def get_engine():
    """Get or create async engine (lazy initialization)."""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            DATABASE_URL,
            pool_size=5 if IS_SERVERLESS else 10,
            max_overflow=10 if IS_SERVERLESS else 20,
            pool_recycle=300 if IS_SERVERLESS else 1800,  # Shorter for serverless
            pool_pre_ping=True,
            echo=False,
        )
    return _engine


def get_session_local():
    """Get or create async session maker (lazy initialization)."""
    global _session_local
    if _session_local is None:
        _session_local = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _session_local


# For backwards compatibility with existing imports
class _EngineProxy:
    """Proxy that lazily initializes the engine on first use."""

    async def dispose(self):
        if _engine is not None:
            await _engine.dispose()

    def __getattr__(self, name):
        return getattr(get_engine(), name)


engine = _EngineProxy()


def AsyncSessionLocal():
    """Get a session from the lazy-initialized session maker."""
    return get_session_local()()


async def get_db() -> AsyncSession:
    """
    Dependency function for FastAPI to get async database sessions.

    Usage in FastAPI route:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...

    Yields:
        AsyncSession: Database session with automatic cleanup
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        else:
            # Only commit if no exception occurred
            await session.commit()
        finally:
            await session.close()
