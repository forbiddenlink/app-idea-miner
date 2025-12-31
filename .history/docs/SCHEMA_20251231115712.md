# Database Schema Design

## Overview

The App-Idea Miner database uses **PostgreSQL 16** with a normalized relational schema optimized for both write-heavy ingestion and read-heavy analytics queries.

### Design Principles
1. **Normalization:** Reduce redundancy, maintain data integrity
2. **Indexing:** Fast lookups on frequently queried columns
3. **JSONB:** Flexible metadata without schema rigidity
4. **Audit Trail:** Track creation/update timestamps
5. **Soft Deletes:** Optional (can be added with `deleted_at` column)

---

## Entity Relationship Diagram

```
┌──────────────┐         ┌──────────────────┐
│  RawPost     │         │  IdeaCandidate   │
│──────────────│         │──────────────────│
│ id (PK)      │◄───────┐│ id (PK)          │
│ url (unique) │        ││ raw_post_id (FK) │
│ url_hash     │        ││ problem_stmt     │
│ title        │        ││ sentiment        │
│ content      │        ││ quality_score    │
│ source       │        │└──────────────────┘
│ published_at │        │         │
│ fetched_at   │        │         │
│ metadata     │        │         │
└──────────────┘        │         │
                        │         │
                        │         ▼
                        │ ┌──────────────────────┐
                        │ │  ClusterMembership   │
                        │ │──────────────────────│
                        │ │ cluster_id (FK)      │
                        │ │ idea_id (FK)         │
                        │ │ similarity_score     │
                        │ │ is_representative    │
                        │ └──────────────────────┘
                        │         │
                        │         │
                        │         ▼
                        │ ┌──────────────────────┐
                        │ │  Cluster             │
                        │ │──────────────────────│
                        │ │ id (PK)              │
                        │ │ label                │
                        │ │ description          │
                        │ │ keywords             │
                        │ │ idea_count           │
                        │ │ avg_sentiment        │
                        │ │ quality_score        │
                        │ │ created_at           │
                        └─┤ updated_at           │
                          └──────────────────────┘
```

---

## Table Definitions

### 1. `raw_posts`

**Purpose:** Store original, unprocessed posts from all sources

```sql
CREATE TABLE raw_posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url TEXT NOT NULL UNIQUE,
    url_hash VARCHAR(64) NOT NULL,  -- SHA256 hash for fast deduplication
    title TEXT NOT NULL,
    content TEXT,
    source VARCHAR(50) NOT NULL,     -- 'hackernews', 'sample', 'rss_feed'
    author VARCHAR(255),
    published_at TIMESTAMP WITH TIME ZONE,
    fetched_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',     -- Flexible: {domain, tags, upvotes, etc.}
    language VARCHAR(10) DEFAULT 'en',
    raw_sentiment FLOAT,             -- Quick sentiment (-1 to 1)
    is_processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_raw_posts_url_hash ON raw_posts(url_hash);
CREATE INDEX idx_raw_posts_source ON raw_posts(source);
CREATE INDEX idx_raw_posts_published_at ON raw_posts(published_at DESC);
CREATE INDEX idx_raw_posts_is_processed ON raw_posts(is_processed) WHERE is_processed = FALSE;
CREATE INDEX idx_raw_posts_metadata ON raw_posts USING GIN(metadata);  -- For JSONB queries
```

**Sample Row:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "url": "https://news.ycombinator.com/item?id=123456",
  "url_hash": "a3f5b...",
  "title": "I wish there was an app for tracking my book reading habits",
  "content": "Full post text...",
  "source": "hackernews",
  "author": "johndoe",
  "published_at": "2025-12-25T10:30:00Z",
  "fetched_at": "2025-12-31T09:00:00Z",
  "metadata": {
    "domain": "productivity",
    "upvotes": 42,
    "comment_count": 15
  },
  "language": "en",
  "raw_sentiment": 0.65,
  "is_processed": false
}
```

---

### 2. `idea_candidates`

**Purpose:** Extracted and normalized user needs from raw posts

```sql
CREATE TABLE idea_candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_post_id UUID NOT NULL REFERENCES raw_posts(id) ON DELETE CASCADE,
    problem_statement TEXT NOT NULL,  -- The core need: "track reading habits"
    context TEXT,                      -- Surrounding sentences for context
    sentiment VARCHAR(20) NOT NULL,    -- 'positive', 'neutral', 'negative'
    sentiment_score FLOAT NOT NULL,    -- -1 to 1 (VADER compound score)
    emotions JSONB DEFAULT '{}',       -- {"frustration": 0.8, "urgency": 0.6}
    domain VARCHAR(100),               -- e.g., 'productivity', 'health'
    features_mentioned TEXT[],         -- Array: ['AI', 'calendar', 'notifications']
    quality_score FLOAT NOT NULL,      -- 0 to 1 (specificity + actionability)
    is_valid BOOLEAN DEFAULT TRUE,     -- False if flagged as spam/noise
    extracted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_idea_candidates_raw_post_id ON idea_candidates(raw_post_id);
CREATE INDEX idx_idea_candidates_sentiment ON idea_candidates(sentiment);
CREATE INDEX idx_idea_candidates_quality_score ON idea_candidates(quality_score DESC);
CREATE INDEX idx_idea_candidates_is_valid ON idea_candidates(is_valid) WHERE is_valid = TRUE;
CREATE INDEX idx_idea_candidates_domain ON idea_candidates(domain);
CREATE INDEX idx_idea_candidates_problem_statement_fts ON idea_candidates 
    USING GIN(to_tsvector('english', problem_statement));  -- Full-text search
```

**Sample Row:**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "raw_post_id": "550e8400-e29b-41d4-a716-446655440000",
  "problem_statement": "track book reading habits with progress analytics",
  "context": "I read a lot but forget what I've read. I wish there was...",
  "sentiment": "positive",
  "sentiment_score": 0.65,
  "emotions": {
    "hope": 0.7,
    "frustration": 0.3
  },
  "domain": "productivity",
  "features_mentioned": ["progress tracking", "analytics", "recommendations"],
  "quality_score": 0.82,
  "is_valid": true,
  "extracted_at": "2025-12-31T09:05:00Z"
}
```

---

### 3. `clusters`

**Purpose:** Grouped opportunities with aggregated metadata

```sql
CREATE TABLE clusters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    label VARCHAR(255) NOT NULL,         -- "Book Reading Trackers"
    description TEXT,                     -- Auto-generated or manual
    keywords TEXT[] NOT NULL,             -- Top 10: ['reading', 'books', 'progress', ...]
    idea_count INTEGER NOT NULL DEFAULT 0,
    avg_sentiment FLOAT,                  -- Average across ideas
    quality_score FLOAT,                  -- Average quality of ideas
    trend_score FLOAT DEFAULT 0.0,        -- Temporal growth metric
    cluster_vector VECTOR(500),           -- For similarity search (pgvector extension)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_clusters_idea_count ON clusters(idea_count DESC);
CREATE INDEX idx_clusters_quality_score ON clusters(quality_score DESC);
CREATE INDEX idx_clusters_trend_score ON clusters(trend_score DESC);
CREATE INDEX idx_clusters_created_at ON clusters(created_at DESC);
```

**Sample Row:**
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "label": "Book Reading & Progress Tracking",
  "description": "Apps for tracking reading habits, book progress, and getting recommendations",
  "keywords": ["reading", "books", "progress", "tracking", "habits", "analytics", "recommendations", "library", "goals", "stats"],
  "idea_count": 23,
  "avg_sentiment": 0.58,
  "quality_score": 0.76,
  "trend_score": 0.82,
  "created_at": "2025-12-30T14:00:00Z",
  "updated_at": "2025-12-31T09:10:00Z"
}
```

---

### 4. `cluster_memberships`

**Purpose:** Many-to-many relationship between ideas and clusters

```sql
CREATE TABLE cluster_memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cluster_id UUID NOT NULL REFERENCES clusters(id) ON DELETE CASCADE,
    idea_id UUID NOT NULL REFERENCES idea_candidates(id) ON DELETE CASCADE,
    similarity_score FLOAT NOT NULL,      -- Cosine similarity to cluster centroid
    is_representative BOOLEAN DEFAULT FALSE,  -- Top 5 evidence examples
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(cluster_id, idea_id)
);

-- Indexes
CREATE INDEX idx_cluster_memberships_cluster_id ON cluster_memberships(cluster_id);
CREATE INDEX idx_cluster_memberships_idea_id ON cluster_memberships(idea_id);
CREATE INDEX idx_cluster_memberships_is_representative 
    ON cluster_memberships(cluster_id, is_representative) 
    WHERE is_representative = TRUE;
```

**Sample Row:**
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440003",
  "cluster_id": "770e8400-e29b-41d4-a716-446655440002",
  "idea_id": "660e8400-e29b-41d4-a716-446655440001",
  "similarity_score": 0.89,
  "is_representative": true,
  "assigned_at": "2025-12-31T09:10:00Z"
}
```

---

## Supporting Tables (Future)

### 5. `data_sources`

**Purpose:** Configurable ingestion sources

```sql
CREATE TABLE data_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    source_type VARCHAR(50) NOT NULL,  -- 'rss', 'api', 'sample'
    url TEXT,
    config JSONB DEFAULT '{}',          -- API keys, query params
    is_active BOOLEAN DEFAULT TRUE,
    last_fetched_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 6. `ingestion_jobs`

**Purpose:** Track ingestion job history

```sql
CREATE TABLE ingestion_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID REFERENCES data_sources(id),
    status VARCHAR(20) NOT NULL,        -- 'pending', 'running', 'completed', 'failed'
    posts_fetched INTEGER DEFAULT 0,
    posts_new INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);
```

### 7. `analytics_snapshots`

**Purpose:** Daily aggregated metrics for trend analysis

```sql
CREATE TABLE analytics_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    snapshot_date DATE NOT NULL UNIQUE,
    total_posts INTEGER NOT NULL,
    total_ideas INTEGER NOT NULL,
    total_clusters INTEGER NOT NULL,
    avg_cluster_size FLOAT,
    top_domains JSONB,                  -- {"productivity": 45, "health": 32, ...}
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## Migrations (Alembic)

### Initial Migration

**File:** `migrations/versions/001_initial_schema.py`

```python
"""Initial schema

Revision ID: 001
Create Date: 2025-12-31
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Create raw_posts table
    op.create_table(
        'raw_posts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('url_hash', sa.String(64), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('content', sa.Text()),
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('author', sa.String(255)),
        sa.Column('published_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('fetched_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), server_default='{}'),
        sa.Column('language', sa.String(10), server_default='en'),
        sa.Column('raw_sentiment', sa.Float()),
        sa.Column('is_processed', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now())
    )
    
    # Add constraints and indexes
    op.create_unique_constraint('uq_raw_posts_url', 'raw_posts', ['url'])
    op.create_index('idx_raw_posts_url_hash', 'raw_posts', ['url_hash'])
    op.create_index('idx_raw_posts_source', 'raw_posts', ['source'])
    # ... more indexes
    
    # Create other tables...

def downgrade():
    op.drop_table('raw_posts')
    # Drop other tables...
```

---

## Query Examples

### 1. Get Top Clusters with Evidence

```sql
SELECT 
    c.id,
    c.label,
    c.keywords,
    c.idea_count,
    c.avg_sentiment,
    (
        SELECT json_agg(
            json_build_object(
                'problem', ic.problem_statement,
                'sentiment', ic.sentiment,
                'url', rp.url
            )
        )
        FROM cluster_memberships cm
        JOIN idea_candidates ic ON cm.idea_id = ic.id
        JOIN raw_posts rp ON ic.raw_post_id = rp.id
        WHERE cm.cluster_id = c.id 
          AND cm.is_representative = TRUE
        LIMIT 5
    ) as evidence
FROM clusters c
ORDER BY c.idea_count DESC
LIMIT 10;
```

### 2. Search Ideas by Keyword

```sql
SELECT 
    ic.id,
    ic.problem_statement,
    ic.sentiment,
    rp.url,
    rp.published_at
FROM idea_candidates ic
JOIN raw_posts rp ON ic.raw_post_id = rp.id
WHERE to_tsvector('english', ic.problem_statement) @@ to_tsquery('english', 'budget & tracking')
ORDER BY ic.quality_score DESC
LIMIT 20;
```

### 3. Analytics: Ideas per Day

```sql
SELECT 
    DATE(created_at) as date,
    COUNT(*) as ideas_created,
    AVG(sentiment_score) as avg_sentiment
FROM idea_candidates
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

### 4. Find Similar Clusters

```sql
-- Requires pgvector extension
SELECT 
    c2.id,
    c2.label,
    c2.idea_count,
    (c1.cluster_vector <=> c2.cluster_vector) as distance
FROM clusters c1
CROSS JOIN clusters c2
WHERE c1.id = '770e8400-e29b-41d4-a716-446655440002'
  AND c2.id != c1.id
ORDER BY distance ASC
LIMIT 5;
```

---

## Performance Considerations

### Index Strategy
- **High cardinality columns:** Use B-tree (id, url_hash)
- **JSONB columns:** Use GIN indexes
- **Full-text search:** Use GIN with `to_tsvector`
- **Partial indexes:** For filtered queries (e.g., `is_processed = FALSE`)

### Query Optimization
- Use `EXPLAIN ANALYZE` to check query plans
- Avoid N+1 queries (use JOINs or eager loading)
- Paginate large result sets
- Use materialized views for complex analytics

### Maintenance
- Regular `VACUUM` and `ANALYZE`
- Monitor index usage: `pg_stat_user_indexes`
- Archive old data (soft delete or partition)

---

## Data Retention Policy

### MVP
- Keep all data indefinitely

### Future
- Archive raw posts > 1 year old
- Keep aggregated analytics forever
- Soft delete spam/invalid ideas

---

## Backup Strategy

### MVP (Local Dev)
- Docker volume persistence
- Manual exports: `pg_dump`

### Production (Future)
- Automated daily backups
- Point-in-time recovery (PITR)
- Offsite backup storage

---

This schema is designed to be **simple, scalable, and query-efficient** while maintaining flexibility for future enhancements. 🗄️
