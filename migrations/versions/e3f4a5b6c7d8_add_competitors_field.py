"""add competitors_mentioned field to idea_candidates

Revision ID: e3f4a5b6c7d8
Revises: d1e2f3a4b5c6
Create Date: 2026-04-06 11:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "e3f4a5b6c7d8"
down_revision: str | Sequence[str] | None = "d1e2f3a4b5c6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add competitors_mentioned field to idea_candidates."""
    # Add ARRAY column for competitor mentions
    op.add_column(
        "idea_candidates",
        sa.Column(
            "competitors_mentioned",
            postgresql.ARRAY(sa.Text()),
            nullable=True,
        ),
    )

    # Create GIN index for efficient array queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_idea_candidates_competitors
        ON idea_candidates USING gin (competitors_mentioned)
    """)


def downgrade() -> None:
    """Remove competitors_mentioned field."""
    op.drop_index("idx_idea_candidates_competitors", table_name="idea_candidates")
    op.drop_column("idea_candidates", "competitors_mentioned")
