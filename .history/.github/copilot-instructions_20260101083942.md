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
- **HDBSCAN config:** min_cluster_size=3, min_samples=2, metric='cosine'
- **Keyword extraction:** Top 10 TF-IDF terms per cluster
- **Quality scoring:** Silhouette score + avg sentiment + evidence diversity
- **No placeholder logic:** Clustering must produce real results from sample data

### Frontend Conventions (React + TypeScript)
- **Path Alias:** Use `@/` for `src/` imports (configured in `vite.config.ts`)
  - ✅ `import { Cluster } from '@/types'`
  - ❌ `import { Cluster } from '../../../types'`
- **Component Pattern:** Functional components with TypeScript interfaces
  ```tsx
  interface ClusterCardProps {
    cluster: Cluster
  }
  export const ClusterCard: React.FC<ClusterCardProps> = ({ cluster }) => { ... }
  ```
- **State Management:**
  - **Server State:** TanStack Query (React Query) - all API calls
  - **URL State:** React Router `useSearchParams()` for filters
  - **Local State:** `useState()` for UI-only state
  - **localStorage:** Custom hooks like `useFavorites()` for persistence
- **API Calls:** Centralized in `apps/web/src/services/api.ts`
  ```tsx
  import { getCluster } from '@/services/api'
  const { data, isLoading } = useQuery({
    queryKey: ['cluster', id],
    queryFn: () => getCluster(id)
  })
  ```
- **Styling:** Tailwind CSS utility classes only (no CSS-in-JS or styled-components)
  - Glassmorphism pattern: `bg-slate-800/80 backdrop-blur-sm border border-slate-700/50`
  - Colors: `primary-*`, `success-*`, `warning-*`, `danger-*`, `slate-*`
- **Animations:** Framer Motion for all transitions
  ```tsx
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    whileHover={{ y: -4 }}
  >
  ```
- **Icons:** `@heroicons/react/24/outline` (outline) and `/24/solid` (filled)
- **Forms:** Controlled components with React Hook Form (future) or direct state

### Backend Conventions (FastAPI + SQLAlchemy)
- **State management:** Zustand for global state (avoid prop drilling)
- **Data fetching:** React Query for API calls, caching, real-time updates
- **Styling:** Tailwind CSS only. No CSS-in-JS or styled-components
- **Dark theme:** Default UI theme (see [docs/PLAN.md](../docs/PLAN.md) design section)
- **Components:** Headless UI for accessible primitives, Heroicons for icons
- **Animations:** Framer Motion for transitions, cluster visualizations

### Testing Requirements
- **Coverage target:** 85%+ (enforced in CI after Phase 6)
- **Unit tests:** `tests/unit/` for business logic (clustering, NLP, dedupe)
- **Integration tests:** `tests/integration/` for API endpoints
- **E2E tests:** `tests/e2e/` for critical user flows (load data → cluster → view UI)
- **Test data:** Use `data/sample_posts.json` (100+ ideas) - never mock clustering results

## Key Files Reference

| File | Purpose | When to Read |
|------|---------|-------------|
| [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) | Tech stack justification, data flow | Before Phase 0 |
| [docs/SCHEMA.md](../docs/SCHEMA.md) | Complete DB design, indexes, queries | Before Phase 1 |
| [docs/API_SPEC.md](../docs/API_SPEC.md) | 25+ endpoints, WebSocket spec | Before Phase 4 |
| [docs/CLUSTERING.md](../docs/CLUSTERING.md) | HDBSCAN parameters, keyword extraction | Before Phase 3 |
| [docs/CHECKLIST.md](../docs/CHECKLIST.md) | 200+ implementation tasks | Daily reference |
| [README.md](../README.md) | Quick start, commands, troubleshooting | Setup issues |

## Common Pitfalls to Avoid

1. **Docker networking:** Use service names (`postgresql`, `redis`), not `localhost`
2. **Migrations:** Never skip Alembic - always generate migrations for schema changes
3. **Sample data dependency:** MVP must work with `data/sample_posts.json` - no API keys required
4. **Clustering parameters:** Don't change HDBSCAN config without updating docs
5. **No placeholder functions:** Every component must run end-to-end (see [docs/PLAN.md](../docs/PLAN.md) Phase 0 requirements)
6. **Environment variables:** Never commit `.env` - use `.env.example` as template

## Decision Rationale

**Why Celery over RQ?** More mature, Flower monitoring, advanced routing, better for multi-worker scaling.

**Why HDBSCAN?** Auto-detects cluster count (unlike K-means), handles noise, density-based (better for variable-size idea groups).

**Why monorepo?** Shared models between API/Worker, simplified dependency management, single Docker Compose setup.

**Why no authentication in MVP?** Focus on core clustering value first. Auth is Phase 2 (see [docs/PLAN.md](../docs/PLAN.md) future enhancements).

## When Stuck

1. Check [docs/CHECKLIST.md](../docs/CHECKLIST.md) for your current phase
2. Review [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) for component interactions
3. Examine `data/sample_posts.json` structure for expected input format
4. Read [docs/CLUSTERING.md](../docs/CLUSTERING.md) for ML algorithm details
5. Verify Docker services: `docker-compose ps` (all should be "Up")

## Design Philosophy

**Build for demonstration:** MVP must impress in 5 minutes. Beautiful UI + real insights from sample data.

**Evidence-based:** Every cluster shows real user quotes with source links. No synthetic/mock data in UI.

**Developer-friendly:** `make dev` is the only command needed. 85%+ test coverage. Clear error messages.

**Scalability-ready:** Architecture supports horizontal scaling (stateless API, queue-based processing), but optimize for single-machine MVP first.

---

*Last updated: December 31, 2025 - Planning phase complete, implementation starting with Phase 0*
