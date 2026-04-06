"""add webhook fields to saved_searches

Revision ID: f4a5b6c7d8e9
Revises: e3f4a5b6c7d8
Create Date: 2026-04-06 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f4a5b6c7d8e9"
down_revision: str | Sequence[str] | None = "e3f4a5b6c7d8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add webhook configuration fields to saved_searches."""
    op.add_column(
        "saved_searches",
        sa.Column("webhook_url", sa.String(500), nullable=True),
    )
    op.add_column(
        "saved_searches",
        sa.Column(
            "webhook_type",
            sa.String(20),
            nullable=True,
        ),
    )
    op.add_column(
        "saved_searches",
        sa.Column(
            "last_alert_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    # Add check constraint for webhook_type values
    op.create_check_constraint(
        "ck_saved_searches_webhook_type",
        "saved_searches",
        "webhook_type IN ('slack', 'discord', 'generic') OR webhook_type IS NULL",
    )


def downgrade() -> None:
    """Remove webhook fields."""
    op.drop_constraint(
        "ck_saved_searches_webhook_type", "saved_searches", type_="check"
    )
    op.drop_column("saved_searches", "last_alert_at")
    op.drop_column("saved_searches", "webhook_type")
    op.drop_column("saved_searches", "webhook_url")
