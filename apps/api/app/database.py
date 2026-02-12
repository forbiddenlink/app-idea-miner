"""
Async database configuration with asyncpg driver.

Provides async SQLAlchemy engine and session management.
Uses production-ready connection pooling patterns.
"""

import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

# Database URL with asyncpg driver (8x faster than psycopg2)
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/appideas"
)

# Create async engine with production-ready pooling
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,  # Number of connections to maintain
    max_overflow=20,  # Additional connections under load
    pool_recycle=1800,  # Recycle connections after 30 min
    pool_pre_ping=True,  # Verify connection health before use
    echo=False,  # Set to True for SQL query logging
)

# Async session maker with proper configuration
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Prevent lazy loading issues
    autocommit=False,
    autoflush=False,
)

# Declarative base for models
Base = declarative_base()


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
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
