"""
FastAPI dependency injection.
Provides database sessions and other dependencies to route handlers.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.config import Settings, get_settings
from apps.api.app.database import AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session.
    Ensures proper session lifecycle management with automatic cleanup.

    Usage in routes:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            items = await db.execute(select(Item))
            return items.scalars().all()
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


def get_settings_dependency() -> Settings:
    """
    Dependency that provides application settings.

    Usage in routes:
        @app.get("/config")
        async def get_config(settings: Settings = Depends(get_settings_dependency)):
            return {"log_level": settings.LOG_LEVEL}
    """
    return get_settings()
