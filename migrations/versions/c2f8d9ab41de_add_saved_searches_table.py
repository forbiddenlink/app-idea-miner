"""add saved searches table

Revision ID: c2f8d9ab41de
Revises: b7d12e9a4f3c
Create Date: 2026-03-30 22:05:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c2f8d9ab41de"
down_revision: str | Sequence[str] | None = "b7d12e9a4f3c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "saved_searches",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("query_params", sa.JSON(), nullable=False),
        sa.Column(
            "alert_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "alert_frequency",
            sa.String(length=16),
            nullable=False,
            server_default="weekly",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "alert_frequency IN ('daily', 'weekly')",
            name="ck_saved_searches_alert_frequency",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_saved_searches_user_created_desc",
        "saved_searches",
        ["user_id", sa.literal_column("created_at DESC")],
        unique=False,
    )
    op.create_index(
        "ix_saved_searches_user_id", "saved_searches", ["user_id"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_saved_searches_user_id", table_name="saved_searches")
    op.drop_index("idx_saved_searches_user_created_desc", table_name="saved_searches")
    op.drop_table("saved_searches")
