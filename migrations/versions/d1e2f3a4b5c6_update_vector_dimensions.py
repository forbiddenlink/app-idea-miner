"""update vector dimensions to 384 for all-MiniLM-L6-v2

Revision ID: d1e2f3a4b5c6
Revises: c2f8d9ab41de
Create Date: 2026-04-06 10:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d1e2f3a4b5c6"
down_revision: str | Sequence[str] | None = "c2f8d9ab41de"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Update vector dimensions from 1536 to 384 for all-MiniLM-L6-v2 model."""
    # Drop existing vector data (incompatible dimensions)
    op.execute("UPDATE idea_candidates SET idea_vector = NULL")
    op.execute("UPDATE clusters SET cluster_vector = NULL")

    # Alter column types to use 384 dimensions
    op.execute("ALTER TABLE idea_candidates ALTER COLUMN idea_vector TYPE vector(384)")
    op.execute("ALTER TABLE clusters ALTER COLUMN cluster_vector TYPE vector(384)")

    # Create HNSW index for efficient similarity search on ideas
    # Parameters: m=16 (connections per layer), ef_construction=64 (build quality)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_idea_candidates_embedding_hnsw
        ON idea_candidates USING hnsw (idea_vector vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)

    # Create HNSW index for cluster similarity search
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_clusters_embedding_hnsw
        ON clusters USING hnsw (cluster_vector vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)


def downgrade() -> None:
    """Revert vector dimensions to 1536."""
    # Drop HNSW indexes
    op.execute("DROP INDEX IF EXISTS idx_idea_candidates_embedding_hnsw")
    op.execute("DROP INDEX IF EXISTS idx_clusters_embedding_hnsw")

    # Clear vector data
    op.execute("UPDATE idea_candidates SET idea_vector = NULL")
    op.execute("UPDATE clusters SET cluster_vector = NULL")

    # Revert to 1536 dimensions
    op.execute("ALTER TABLE idea_candidates ALTER COLUMN idea_vector TYPE vector(1536)")
    op.execute("ALTER TABLE clusters ALTER COLUMN cluster_vector TYPE vector(1536)")
