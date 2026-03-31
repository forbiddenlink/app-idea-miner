"""add bookmarks table

Revision ID: 9e4a8f2b8d11
Revises: f6e39222109b
Create Date: 2026-03-18 22:08:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9e4a8f2b8d11"
down_revision: str | Sequence[str] | None = "f6e39222109b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "bookmarks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("scope_key", sa.String(length=64), nullable=False),
        sa.Column("item_type", sa.String(length=20), nullable=False),
        sa.Column("item_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "item_type IN ('cluster', 'idea')", name="ck_bookmarks_item_type"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_bookmarks_scope_created_desc",
        "bookmarks",
        ["scope_key", sa.literal_column("created_at DESC")],
        unique=False,
    )
    op.create_index("ix_bookmarks_item_id", "bookmarks", ["item_id"], unique=False)
    op.create_index("ix_bookmarks_item_type", "bookmarks", ["item_type"], unique=False)
    op.create_index("ix_bookmarks_scope_key", "bookmarks", ["scope_key"], unique=False)
    op.create_index(
        "uq_bookmarks_scope_item",
        "bookmarks",
        ["scope_key", "item_type", "item_id"],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("uq_bookmarks_scope_item", table_name="bookmarks")
    op.drop_index("ix_bookmarks_scope_key", table_name="bookmarks")
    op.drop_index("ix_bookmarks_item_type", table_name="bookmarks")
    op.drop_index("ix_bookmarks_item_id", table_name="bookmarks")
    op.drop_index("idx_bookmarks_scope_created_desc", table_name="bookmarks")
    op.drop_table("bookmarks")
