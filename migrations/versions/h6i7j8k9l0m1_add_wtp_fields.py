"""add willingness-to-pay fields to idea_candidates

Revision ID: h6i7j8k9l0m1
Revises: g5h6i7j8k9l0
Create Date: 2026-07-30 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "h6i7j8k9l0m1"
down_revision: str | Sequence[str] | None = "g5h6i7j8k9l0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add wtp_score + has_wtp_signal to idea_candidates."""
    op.add_column(
        "idea_candidates",
        sa.Column("wtp_score", sa.Float(), nullable=True, server_default="0.0"),
    )
    op.add_column(
        "idea_candidates",
        sa.Column(
            "has_wtp_signal",
            sa.Boolean(),
            nullable=True,
            server_default=sa.false(),
        ),
    )
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_idea_candidates_has_wtp_signal
        ON idea_candidates (has_wtp_signal)
    """)


def downgrade() -> None:
    """Remove willingness-to-pay fields."""
    op.drop_index("idx_idea_candidates_has_wtp_signal", table_name="idea_candidates")
    op.drop_column("idea_candidates", "has_wtp_signal")
    op.drop_column("idea_candidates", "wtp_score")
