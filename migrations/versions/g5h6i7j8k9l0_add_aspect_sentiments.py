"""Add aspect_sentiments and urgency_level fields.

Revision ID: g5h6i7j8k9l0
Revises: f4a5b6c7d8e9
Create Date: 2026-04-06

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "g5h6i7j8k9l0"
down_revision: str | None = "f4a5b6c7d8e9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add aspect_sentiments JSONB column
    op.add_column(
        "idea_candidates",
        sa.Column("aspect_sentiments", JSONB, nullable=True, default={}),
    )

    # Add urgency_level column
    op.add_column(
        "idea_candidates",
        sa.Column("urgency_level", sa.String(20), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("idea_candidates", "urgency_level")
    op.drop_column("idea_candidates", "aspect_sentiments")
