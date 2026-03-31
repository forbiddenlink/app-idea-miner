import asyncio
import os
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from packages.core.models import Base

# Database URLs
# Main DB for admin tasks (create/drop test db)
ADMIN_DATABASE_URL = os.getenv(
    "ADMIN_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres",
)
# Test DB
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/appideas_test",
)


def pytest_configure(config):
    """Register custom marks."""
    config.addinivalue_line(
        "markers", "requires_db: mark test as requiring a live PostgreSQL connection"
    )


async def _check_db_available() -> bool:
    """Return True if PostgreSQL is reachable."""
    try:
        engine = create_async_engine(ADMIN_DATABASE_URL, poolclass=NullPool)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        await engine.dispose()
        return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def event_loop():
    """
    Create an instance of the default event loop for each test case.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


async def create_test_database():
    """Create the test database and enable extensions."""
    # Connect to admin DB to create test DB
    engine = create_async_engine(ADMIN_DATABASE_URL, isolation_level="AUTOCOMMIT")
    async with engine.connect() as conn:
        # Check if test DB exists
        # Terminate connections to allow drop
        await conn.execute(text("DROP DATABASE IF EXISTS appideas_test WITH (FORCE)"))
        # Use template0 to avoid inheriting host-specific collation drift from template1.
        await conn.execute(text("CREATE DATABASE appideas_test TEMPLATE template0"))
    await engine.dispose()

    # Connect to Test DB to enable extensions
    test_engine = create_async_engine(TEST_DATABASE_URL)
    async with test_engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
    await test_engine.dispose()


async def drop_test_database():
    """Drop the test database."""
    engine = create_async_engine(ADMIN_DATABASE_URL, isolation_level="AUTOCOMMIT")
    async with engine.connect() as conn:
        await conn.execute(text("DROP DATABASE IF EXISTS appideas_test WITH (FORCE)"))
    await engine.dispose()


@pytest.fixture(scope="session")
async def db_engine():
    """
    Session-scoped database engine.
    Creates DB and tables once per session.
    Skips automatically when PostgreSQL is not reachable.
    """
    if not await _check_db_available():
        pytest.skip(
            "PostgreSQL not available – set ADMIN_DATABASE_URL to enable integration tests"
        )

    await create_test_database()

    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()
    await drop_test_database()


@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Function-scoped session.
    Rolls back transaction after each test to ensure isolation.
    """
    connection = await db_engine.connect()
    transaction = await connection.begin()

    session_maker = async_sessionmaker(
        bind=connection,
        expire_on_commit=False,
    )
    session = session_maker()

    yield session

    await session.close()
    await transaction.rollback()
    await connection.close()


@pytest.fixture(scope="function")
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """
    Test client with DB session override.
    """
    # Lazy import to avoid loading app/redis for unit tests that don't use this fixture
    from apps.api.app.database import get_db
    from apps.api.app.main import app

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
