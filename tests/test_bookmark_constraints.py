from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from apps.api.app.core.auth import get_password_hash
from packages.core.models import Bookmark, User

pytestmark = pytest.mark.requires_db


@pytest.mark.asyncio
async def test_bookmark_requires_valid_user_fk(db_session):
    bookmark = Bookmark(
        user_id=uuid4(),
        item_type="cluster",
        item_id=uuid4(),
    )
    db_session.add(bookmark)

    with pytest.raises(IntegrityError):
        await db_session.commit()

    await db_session.rollback()


@pytest.mark.asyncio
async def test_bookmark_unique_per_user_item(db_session):
    user = User(
        email="constraints-unique@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    item_id = uuid4()
    first = Bookmark(user_id=user.id, item_type="cluster", item_id=item_id)
    duplicate = Bookmark(user_id=user.id, item_type="cluster", item_id=item_id)
    db_session.add_all([first, duplicate])

    with pytest.raises(IntegrityError):
        await db_session.commit()

    await db_session.rollback()


@pytest.mark.asyncio
async def test_bookmark_same_item_allowed_for_different_users(db_session):
    user_a = User(
        email="constraints-user-a@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True,
    )
    user_b = User(
        email="constraints-user-b@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True,
    )
    db_session.add_all([user_a, user_b])
    await db_session.flush()

    shared_item_id = uuid4()
    db_session.add_all(
        [
            Bookmark(user_id=user_a.id, item_type="cluster", item_id=shared_item_id),
            Bookmark(user_id=user_b.id, item_type="cluster", item_id=shared_item_id),
        ]
    )
    await db_session.commit()

    count_stmt = select(func.count()).select_from(Bookmark)
    count = (await db_session.execute(count_stmt)).scalar_one()
    assert count == 2


@pytest.mark.asyncio
async def test_bookmark_deleted_when_user_deleted(db_session):
    user = User(
        email="constraints-cascade@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    bookmark = Bookmark(
        user_id=user.id,
        item_type="idea",
        item_id=uuid4(),
    )
    db_session.add(bookmark)
    await db_session.commit()

    await db_session.delete(user)
    await db_session.commit()

    bookmark_exists = await db_session.scalar(
        select(Bookmark.id).where(Bookmark.id == bookmark.id)
    )
    assert bookmark_exists is None
