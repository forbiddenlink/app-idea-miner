# GitHub Copilot Instructions for App-Idea Miner

## Project Overview
App-Idea Miner is an intelligent opportunity detection platform that discovers, clusters, and analyzes "I wish there was an app..." posts from web sources using ML-powered clustering (HDBSCAN + TF-IDF).

**Current Status:** MVP Complete through Phase 8E (all features implemented and tested)
- ✅ Backend: 21+ API endpoints, Celery workers, PostgreSQL + Redis
- ✅ Frontend: 5 pages, 30+ React components, modern glassmorphism UI
- ✅ Features: Favorites, Enhanced Tooltips, Filter Chips, Command Palette (Cmd+K), Context Menus

## Architecture at a Glance

```
[RSS/Sample Data] → [Celery Worker] → [PostgreSQL] → [FastAPI] → [React UI]
                         ↓               ↑              ↑
                    [Redis Cache/Queue]  └──────────────┘
```

**Tech Stack:**
- **Package Manager:** UV 0.5+ (10-100x faster than pip, native monorepo support)
- **Backend:** Python 3.12, FastAPI 0.115+, SQLAlchemy 2.0+ (async), Celery 5.4+
- **Database:** PostgreSQL 16 (JSONB, full-text search), Redis 7 (cache + queue)
- **DB Driver:** asyncpg 0.30+ (8x faster than psycopg2, async-native)
- **ML:** scikit-learn, HDBSCAN, VADER sentiment, TF-IDF vectorization
- **Frontend:** React 18, Vite 6, TypeScript 5, Tailwind CSS 3, Framer Motion 11
- **State:** TanStack Query 5 (React Query), Zustand 4 (future)
- **Infra:** Docker Compose, Alembic migrations
- **Linting:** Ruff 0.8+ (100x faster than Black+Flake8)

## Critical Workflows

### Essential Commands (Makefile)
```bash
make dev          # Start all services (postgres, redis, api, worker, flower)
make down         # Stop all services
make logs         # View all logs (Ctrl+C to exit)
make logs-api     # View API logs only
make logs-worker  # View Celery worker logs
make migrate      # Run Alembic migrations
make migration name="description"  # Create new migration
make seed         # Load sample_posts.json (20 curated ideas)
make test         # Run pytest with coverage (target: 85%+)
make lint         # Run Ruff linter
make format       # Auto-format with Ruff
make shell-api    # Enter API container for debugging
make cluster      # Manually trigger clustering job
```

**⚠️ CRITICAL:** All services run in Docker. Use service names for inter-service communication:
- Database: `postgresql:5432` (NOT localhost)
- Redis: `redis:6379` (NOT localhost)
- API from Web: Proxied via Vite to `http://localhost:8000`

### Frontend Development
```bash
cd apps/web
npm run dev       # Starts Vite dev server on port 3000
npm run build     # Production build
npm run preview   # Preview production build
npm run lint      # ESLint check
```

**Vite Proxy:** API requests to `/api/*` are proxied to `http://localhost:8000` (see `vite.config.ts`)

## Project-Specific Conventions

### Monorepo Structure
```
apps/api/          # FastAPI backend (routes, dependencies, config)
apps/worker/       # Celery tasks (ingestion, processing, clustering)
apps/web/          # React frontend (components, pages, hooks)
packages/core/     # Shared Python code (models, clustering, NLP, dedupe)
infra/             # Docker configs, postgres init scripts
migrations/        # Alembic versions (sequential 001_, 002_, etc.)
data/              # sample_posts.json, fixtures
docs/              # 11 comprehensive MD files (PLAN, ARCHITECTURE, etc.)
```

**Import Convention:** Core package is shared - use `from packages.core.models import RawPost` in both API and Worker.

### Database Patterns
- **Models:** Define in `packages/core/models.py` (SQLAlchemy ORM)
- **Migrations:** Alembic-managed. Never modify DB directly. Create migration: `alembic revision --autogenerate -m "description"`
- **Schema:** See [docs/SCHEMA.md](../docs/SCHEMA.md) - 4 tables: `raw_posts`, `idea_candidates`, `clusters`, `cluster_memberships`
- **Deduplication:** URL hash (SHA256) + fuzzy title matching. See `packages/core/dedupe.py`
- **JSONB Usage:** `raw_posts.metadata` for flexible data (upvotes, tags, custom fields)

### API Design (FastAPI)
- **No placeholders:** Every endpoint must work end-to-end with sample data
- **Pydantic schemas:** Define in `apps/api/app/schemas/` for request/response validation
- **Dependency injection:** Use `apps/api/app/dependencies.py` for DB sessions
- **Service layer:** Business logic in `apps/api/app/services/` - separates HTTP from domain logic
- **WebSocket:** Real-time cluster updates at `/ws` (see [docs/API_SPEC.md](../docs/API_SPEC.md))
- **Health checks:** `/health` endpoint returns service status + DB connection

### Backend Conventions (FastAPI + SQLAlchemy)
- **Service Layer Pattern:** Business logic in `apps/api/app/services/`, NOT in route handlers
  ```python
  # apps/api/app/services/cluster_service.py
  async def get_clusters(db: AsyncSession, filters: ClusterFilters):
      query = select(Cluster).options(...)
      return await db.execute(query)

  # apps/api/app/routers/clusters.py
  @router.get("/")
  async def list_clusters(db: AsyncSession = Depends(get_db)):
      return await cluster_service.get_clusters(db, filters)
  ```
- **Async Everywhere:** Use `async def` for all route handlers and DB operations
  ```python
  from sqlalchemy.ext.asyncio import AsyncSession

  async with AsyncSessionLocal() as session:
      result = await session.execute(select(Cluster))
  ```
- **Models:** Shared in `packages/core/models.py` (imported by API and Worker)
- **Router Organization:** One file per resource in `apps/api/app/routers/`
  - `clusters.py`, `ideas.py`, `posts.py`, `analytics.py`, `jobs.py`
- **Dependency Injection:** Use FastAPI `Depends()` for DB sessions, not global variables
  ```python
  from apps.api.app.dependencies import get_db

  async def endpoint(db: AsyncSession = Depends(get_db)): ...
  ```
- **Error Handling:** Raise `HTTPException` with appropriate status codes
  ```python
  from fastapi import HTTPException, status

  if not cluster:
      raise HTTPException(status_code=404, detail="Cluster not found")
  ```
- **Celery Tasks:** Use `send_task()` with string names to avoid circular imports
  ```python
  from apps.api.app.dependencies import celery_app

  job = celery_app.send_task('apps.worker.tasks.clustering.run_clustering')
  return {"job_id": job.id}
  ```

### Database Patterns (SQLAlchemy 2.0 Async)
- **Connection String:** Always use `postgresql+asyncpg://` driver
- **Session Config:** `expire_on_commit=False` to prevent lazy loading issues
  ```python
  AsyncSessionLocal = sessionmaker(
      engine, class_=AsyncSession, expire_on_commit=False
  )
  ```
- **Migrations:** NEVER modify DB directly. Always create Alembic migrations:
  ```bash
  make migration name="add_favorites_table"
  make migrate  # Apply migration
  ```
- **Relationships:** Use `selectinload()` for eager loading to avoid N+1 queries
  ```python
  stmt = select(Cluster).options(selectinload(Cluster.memberships))
  ```
- **JSONB Queries:** Use PostgreSQL JSONB operators for flexible metadata
  ```python
  # Query JSONB column
  stmt = select(RawPost).where(
      RawPost.source_metadata['upvotes'].astext.cast(Integer) > 10
  )
  ```

### Background Tasks (Celery)
- **Task Location:** `apps/worker/tasks/` organized by function
  - `ingestion.py` - Fetch posts from RSS/APIs
  - `processing.py` - Extract ideas, sentiment analysis
  - `clustering.py` - Run HDBSCAN clustering
- **Idempotency:** Tasks MUST be idempotent (safe to retry)
- **Error Handling:** Log errors to stdout (captured by Docker logs)
- **Monitoring:** Flower UI at `http://localhost:5555` shows task status
- **Shared Code:** Import from `packages/core/` for models, clustering, NLP
  ```python
  from packages.core.models import RawPost, Cluster
  from packages.core.clustering import ClusterEngine
  ```

### Clustering Algorithm (HDBSCAN)
See [docs/CLUSTERING.md](../docs/CLUSTERING.md) for full details:
- **Vectorization:** TF-IDF with 500 features, 1-3 grams, min_df=2, max_df=0.85
- **HDBSCAN config:** min_cluster_size=2, metric='euclidean' (L2-normalized TF-IDF)
- **Keyword extraction:** Top 10 TF-IDF terms per cluster
- **Quality scoring:** Silhouette score + avg sentiment + evidence diversity
- **Implementation:** `packages/core/clustering.py` - `ClusterEngine` class

## Key Files & Patterns

### Component Examples (Learn From These)
**EnhancedTooltip** (`apps/web/src/components/EnhancedTooltip.tsx`):
- Smart positioning with viewport edge detection
- 200ms hover delay (configurable)
- Framer Motion animations
- Metrics grid with icons and color coding
- Pattern: Wrap any element to add rich hover details

**CommandPalette** (`apps/web/src/components/CommandPalette.tsx`):
- Cmd+K keyboard shortcut (industry standard)
- Universal search across pages/clusters/ideas
- Recent searches stored in localStorage
- Headless UI Dialog with glassmorphism styling
- Pattern: Modal overlays with keyboard listeners

**ContextMenu** (`apps/web/src/components/ContextMenu.tsx`):
- Right-click context menus on cards
- Helper functions: `copyToClipboard`, `shareUrl`, `exportAsJson`
- Pre-built menus: `createClusterContextMenu()`, `createIdeaContextMenu()`
- Pattern: Wrap components to add right-click actions

### Custom Hooks (Reuse These)
- **useFavorites** (`apps/web/src/hooks/useFavorites.ts`): localStorage persistence for bookmarks
- **useFilterChips** (`apps/web/src/components/FilterChips.tsx`): Auto-format filter state to visual chips
- **useKeyboardShortcuts** (`apps/web/src/hooks/useKeyboardShortcuts.ts`): Global keyboard handlers

### API Route Pattern
```python
# apps/api/app/routers/clusters.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.app.dependencies import get_db
from apps.api.app.services import cluster_service

router = APIRouter(prefix="/api/v1/clusters", tags=["clusters"])

@router.get("/")
async def list_clusters(
    sort_by: str = Query("size", regex="^(size|sentiment|trend|quality)$"),
    order: str = Query("desc", regex="^(asc|desc)$"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """List all clusters with pagination and sorting."""
    return await cluster_service.get_clusters(db, sort_by, order, limit, offset)
```

## Common Pitfalls

1. **Docker networking:** Use service names (`postgresql`, `redis`), NOT `localhost`
2. **Async sessions:** Always use `async with` context managers for DB sessions
3. **Circular imports:** Worker tasks should use `send_task()` with string names
4. **Frontend imports:** Use `@/` alias, not relative paths (`../../../`)
5. **Migrations:** Run `make migration` BEFORE modifying models (auto-generates SQL)
6. **Component state:** Use React Query for server state, NOT useState for API data
7. **Styling:** Use Tailwind utilities only (avoid inline styles, `style=` prop triggers linter)
8. **Type safety:** Always define TypeScript interfaces for props and API responses

## Testing Patterns

### Frontend Tests (Future)
```tsx
// Use React Testing Library + Vitest
import { render, screen } from '@testing-library/react'
import { ClusterCard } from '@/components/ClusterCard'

test('renders cluster card with metrics', () => {
  render(<ClusterCard cluster={mockCluster} />)
  expect(screen.getByText('23 ideas')).toBeInTheDocument()
})
```

### Backend Tests
```python
# Use pytest with async support
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_list_clusters(client: AsyncClient):
    response = await client.get("/api/v1/clusters")
    assert response.status_code == 200
    assert len(response.json()["clusters"]) > 0
```

## Documentation Files (Read These)

**Must-Read Before Making Changes:**
- [CHECKLIST.md](../docs/CHECKLIST.md) - Implementation phases (Phases 1-8E complete)
- [ARCHITECTURE.md](../docs/ARCHITECTURE.md) - System design decisions
- [API_SPEC.md](../docs/API_SPEC.md) - All 21+ endpoints documented
- [SCHEMA.md](../docs/SCHEMA.md) - Database tables and relationships

**Reference When Needed:**
- [CLUSTERING.md](../docs/CLUSTERING.md) - HDBSCAN algorithm deep dive
- [PHASE_8E_COMPLETE.md](../docs/PHASE_8E_COMPLETE.md) - Latest features (Favorites, Tooltips, Command Palette, Context Menus)
- [README.md](../README.md) - Quick start, setup, troubleshooting

## Decision Rationale (The "Why")

**Why Celery over RQ?** More mature, Flower monitoring, advanced routing, better for multi-worker scaling.

**Why HDBSCAN?** Auto-detects cluster count (unlike K-means), handles noise, density-based (better for variable-size idea groups).

**Why monorepo?** Shared models between API/Worker, simplified dependency management, single Docker Compose setup.

**Why TanStack Query?** Industry standard for server state, built-in caching, automatic refetching, better than Redux for API data.

**Why glassmorphism?** Modern 2025 design trend, creates depth with backdrop blur, professional appearance.

---

**Last Updated:** January 1, 2026 - Phase 8E complete (all 5 quick wins implemented)
