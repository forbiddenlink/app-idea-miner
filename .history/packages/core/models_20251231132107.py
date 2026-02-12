"""
SQLAlchemy ORM models for App-Idea Miner.
These models are shared between API and Worker services.
"""

import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class RawPost(Base):
    """
    Raw posts fetched from data sources (RSS feeds, APIs, sample data).
    Stores original, unprocessed content before extraction.
    """

    __tablename__ = "raw_posts"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Core fields
    url = Column(String, unique=True, nullable=False, index=True)
    url_hash = Column(String(64), nullable=False, index=True)  # SHA-256 hash for deduplication
    title = Column(Text, nullable=False)
    content = Column(Text)

    # Source metadata
    source = Column(String(50), nullable=False, index=True)  # 'hackernews', 'sample', 'rss_feed'
    author = Column(String(255))
    published_at = Column(DateTime(timezone=True))
    fetched_at = Column(DateTime(timezone=True), nullable=False, default=func.now())

    # Flexible metadata (JSONB for extensibility)
    source_metadata = Column(JSONB, default={})  # domain, tags, upvotes, etc.

    # Processing state
    language = Column(String(10), default="en")
    raw_sentiment = Column(Float)  # Quick sentiment score (-1 to 1)
    is_processed = Column(Boolean, default=False, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Relationships
    ideas = relationship("IdeaCandidate", back_populates="raw_post", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index(
            "idx_raw_posts_is_processed_false",
            "is_processed",
            postgresql_where=(is_processed == False),
        ),
        Index("idx_raw_posts_metadata", "metadata", postgresql_using="gin"),
        Index("idx_raw_posts_published_at_desc", published_at.desc()),
    )

    def __repr__(self):
        return f"<RawPost(id={self.id}, title='{self.title[:50]}...', source={self.source})>"


class IdeaCandidate(Base):
    """
    Extracted and normalized user needs from raw posts.
    Represents a single actionable app idea with quality scoring.
    """

    __tablename__ = "idea_candidates"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key
    raw_post_id = Column(
        UUID(as_uuid=True),
        ForeignKey("raw_posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Core content
    problem_statement = Column(Text, nullable=False)  # The extracted need
    context = Column(Text)  # Surrounding sentences for context

    # Sentiment analysis
    sentiment = Column(String(20), nullable=False, index=True)  # 'positive', 'neutral', 'negative'
    sentiment_score = Column(Float, nullable=False)  # -1 to 1 (VADER compound score)
    emotions = Column(JSONB, default={})  # {"frustration": 0.8, "urgency": 0.6}

    # Classification
    domain = Column(String(100), index=True)  # e.g., 'productivity', 'health'
    features_mentioned = Column(ARRAY(Text))  # ['AI', 'calendar', 'notifications']

    # Quality metrics
    quality_score = Column(
        Float, nullable=False, index=True
    )  # 0 to 1 (specificity + actionability)
    is_valid = Column(Boolean, default=True, index=True)  # False if flagged as spam/noise

    # Timestamps
    extracted_at = Column(DateTime(timezone=True), default=func.now())
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Relationships
    raw_post = relationship("RawPost", back_populates="ideas")
    cluster_memberships = relationship(
        "ClusterMembership", back_populates="idea", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_idea_candidates_quality_score_desc", quality_score.desc()),
        Index("idx_idea_candidates_is_valid_true", "is_valid", postgresql_where=(is_valid == True)),
        Index(
            "idx_idea_candidates_problem_statement_fts",
            "problem_statement",
            postgresql_using="gin",
            postgresql_ops={"problem_statement": "gin_trgm_ops"},
        ),
    )

    def __repr__(self):
        return f"<IdeaCandidate(id={self.id}, problem='{self.problem_statement[:50]}...', quality={self.quality_score:.2f})>"


class Cluster(Base):
    """
    Grouped opportunities discovered through ML clustering.
    Represents a validated app opportunity with aggregated metadata.
    """

    __tablename__ = "clusters"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Core metadata
    label = Column(String(255), nullable=False)  # "Book Reading & Progress Tracking"
    description = Column(Text)  # Auto-generated or manual
    keywords = Column(ARRAY(Text), nullable=False)  # Top 10: ['reading', 'books', ...]

    # Aggregated metrics
    idea_count = Column(Integer, nullable=False, default=0, index=True)
    avg_sentiment = Column(Float)  # Average across ideas
    quality_score = Column(Float, index=True)  # Average quality of ideas
    trend_score = Column(Float, default=0.0, index=True)  # Temporal growth metric

    # Optional: Vector for similarity search (if using pgvector extension)
    # cluster_vector = Column(Vector(500))  # Uncomment if using pgvector

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Relationships
    memberships = relationship(
        "ClusterMembership", back_populates="cluster", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_clusters_idea_count_desc", idea_count.desc()),
        Index("idx_clusters_trend_score_desc", trend_score.desc()),
    )

    def __repr__(self):
        return f"<Cluster(id={self.id}, label='{self.label}', ideas={self.idea_count})>"


class ClusterMembership(Base):
    """
    Many-to-many relationship between ideas and clusters.
    Tracks which ideas belong to which clusters with similarity scores.
    """

    __tablename__ = "cluster_memberships"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    cluster_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clusters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    idea_id = Column(
        UUID(as_uuid=True),
        ForeignKey("idea_candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Membership metadata
    similarity_score = Column(Float, nullable=False)  # Cosine similarity to cluster centroid
    is_representative = Column(Boolean, default=False, index=True)  # Top 5 evidence examples

    # Timestamp
    assigned_at = Column(DateTime(timezone=True), default=func.now())

    # Relationships
    cluster = relationship("Cluster", back_populates="memberships")
    idea = relationship("IdeaCandidate", back_populates="cluster_memberships")

    # Constraints
    __table_args__ = (
        Index(
            "idx_cluster_memberships_is_representative",
            "cluster_id",
            "is_representative",
            postgresql_where=(is_representative == True),
        ),
        Index("uq_cluster_idea", "cluster_id", "idea_id", unique=True),
    )

    def __repr__(self):
        return f"<ClusterMembership(cluster={self.cluster_id}, idea={self.idea_id}, score={self.similarity_score:.2f})>"
