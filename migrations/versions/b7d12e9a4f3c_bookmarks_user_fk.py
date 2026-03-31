"""add user_id foreign key to bookmarks

Revision ID: b7d12e9a4f3c
Revises: a1b2c3d4e5f6
Create Date: 2026-03-30 21:45:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7d12e9a4f3c"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("bookmarks", sa.Column("user_id", sa.UUID(), nullable=True))

    # Backfill user_id from legacy scope_key where it already stores user UUID text.
    op.execute(
        """
        UPDATE bookmarks AS b
        SET user_id = u.id
        FROM users AS u
        WHERE b.scope_key = CAST(u.id AS TEXT)
        """
    )

    # Remove orphaned legacy rows that cannot be mapped to a real user.
    op.execute("DELETE FROM bookmarks WHERE user_id IS NULL")

    op.alter_column("bookmarks", "user_id", nullable=False)

    op.create_index("ix_bookmarks_user_id", "bookmarks", ["user_id"], unique=False)
    op.create_foreign_key(
        "fk_bookmarks_user_id_users",
        "bookmarks",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_index("uq_bookmarks_scope_item", table_name="bookmarks")
    op.drop_index("idx_bookmarks_scope_created_desc", table_name="bookmarks")

    op.create_index(
        "uq_bookmarks_user_item",
        "bookmarks",
        ["user_id", "item_type", "item_id"],
        unique=True,
    )
    op.create_index(
        "idx_bookmarks_user_created_desc",
        "bookmarks",
        ["user_id", sa.literal_column("created_at DESC")],
        unique=False,
    )

    op.drop_index("ix_bookmarks_scope_key", table_name="bookmarks")
    op.drop_column("bookmarks", "scope_key")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        "bookmarks", sa.Column("scope_key", sa.String(length=64), nullable=True)
    )

    op.execute(
        """
        UPDATE bookmarks
        SET scope_key = CAST(user_id AS TEXT)
        WHERE user_id IS NOT NULL
        """
    )

    op.execute("UPDATE bookmarks SET scope_key = 'default' WHERE scope_key IS NULL")
    op.alter_column("bookmarks", "scope_key", nullable=False)

    op.create_index("ix_bookmarks_scope_key", "bookmarks", ["scope_key"], unique=False)

    op.drop_index("idx_bookmarks_user_created_desc", table_name="bookmarks")
    op.drop_index("uq_bookmarks_user_item", table_name="bookmarks")

    op.create_index(
        "idx_bookmarks_scope_created_desc",
        "bookmarks",
        ["scope_key", sa.literal_column("created_at DESC")],
        unique=False,
    )
    op.create_index(
        "uq_bookmarks_scope_item",
        "bookmarks",
        ["scope_key", "item_type", "item_id"],
        unique=True,
    )

    op.drop_constraint("fk_bookmarks_user_id_users", "bookmarks", type_="foreignkey")
    op.drop_index("ix_bookmarks_user_id", table_name="bookmarks")
    op.drop_column("bookmarks", "user_id")
