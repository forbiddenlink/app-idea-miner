# GitHub Copilot Instructions for App-Idea Miner

## Project Overview
App-Idea Miner is an intelligent opportunity detection platform that discovers, clusters, and analyzes "I wish there was an app..." posts from web sources. The system uses ML-powered clustering (HDBSCAN + TF-IDF) to surface validated app opportunities backed by real user evidence.

**Status:** Planning phase complete (52,000+ words of documentation). Implementation pending - bootstrap infrastructure first.

## Architecture at a Glance

```
[Data Sources] → [Celery Worker] → [PostgreSQL] → [FastAPI] → [React UI]
                        ↓              ↑
                    [Redis Cache/Queue]
```

**Tech Stack:**
- Package Manager: UV 0.5+ (10-100x faster than pip, native monorepo support)
- Backend: Python 3.12, FastAPI 0.115+, SQLAlchemy 2.0+, Celery 5.4+
- Database: PostgreSQL 16 (JSONB, full-text search), Redis 7
- DB Driver: asyncpg 0.30+ (8x faster than psycopg2, async-native)
- ML: scikit-learn, HDBSCAN, VADER sentiment, TF-IDF vectorization
- Frontend: React 18, Vite 6, TypeScript, Tailwind CSS, Framer Motion
- Infra: Docker Compose, Alembic migrations
- Linting: Ruff 0.8+ (100x faster than Black+Flake8)

## Critical Workflows

### Setup & Development
```bash
make dev          # Start all services (docker-compose up + seed data)
make migrate      # Run Alembic migrations
make seed         # Load sample_posts.json (100+ test ideas)
make test         # Run tests with coverage (target: 85%+)
make shell-api    # Enter API container for debugging
make cluster      # Trigger clustering manually
```

**Environment:** All services run via Docker Compose. No code should assume host execution. Use `docker-compose.yml` service names for inter-service communication (e.g., `postgresql` not `localhost`).

### Implementation Order (CRITICAL)
Follow [docs/CHECKLIST.md](../docs/CHECKLIST.md) phases sequentially:
1. **Phase -1 (4 hours):** Modern Tooling Setup - UV package manager, service layer, async SQLAlchemy, Ruff
2. **Phase 0 (Days 1-2):** Bootstrap - `docker-compose.yml`, Dockerfiles, Makefile, base API/worker
3. **Phase 1 (Days 3-4):** Data foundation - Database models, deduplication, RSS fetching
4. **Phase 2 (Days 5-6):** Processing - NLP extraction, sentiment analysis
5. **Phase 3 (Days 7-9):** Clustering - HDBSCAN implementation, keyword extraction
6. **Phase 4 (Days 10-11):** API - REST endpoints, WebSocket real-time updates
7. **Phase 5 (Days 12-14):** UI - React dashboard, cluster explorer
8. **Phase 6 (Days 15-16):** Polish - Tests, docs, bug fixes

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

### Database Patterns (SQLAlchemy 2.0 Async)
- **Models:** Define in `packages/core/models.py` (SQLAlchemy ORM)
- **Async Engine:** Use `create_async_engine` with `postgresql+asyncpg://` connection string
- **Session Config:** `expire_on_commit=False` to prevent lazy loading issues
- **Connection Pooling:** `pool_size=10`, `max_overflow=20`, `pool_recycle=1800`
- **Migrations:** Alembic-managed. Never modify DB directly. Create migration: `alembic revision --autogenerate -m "description"`
- **Schema:** See [docs/SCHEMA.md](../docs/SCHEMA.md) - 4 tables: `raw_posts`, `idea_candidates`, `clusters`, `cluster_memberships`
- **Deduplication:** URL hash (SHA256) + fuzzy title matching. See `packages/core/dedupe.py`
- **JSONB Usage:** `raw_posts.metadata` for flexible data (upvotes, tags, custom fields)

### Background Tasks (Celery)
- **Task organization:** `apps/worker/tasks/ingestion.py`, `processing.py`, `clustering.py`
- **Scheduling:** Celery Beat for periodic tasks (e.g., fetch RSS every 30 min)
- **Redis broker:** `redis://redis:6379/0` (service name `redis` in Docker)
- **Monitoring:** Flower UI available at `http://localhost:5555`
- **Error handling:** Tasks must be idempotent and log to stdout (captured by Docker)

### Clustering Algorithm (HDBSCAN)
See [docs/CLUSTERING.md](../docs/CLUSTERING.md) for full details:
- **Vectorization:** TF-IDF with 500 features, 1-3 grams, min_df=2, max_df=0.85
- **HDBSCAN config:** min_cluster_size=3, min_samples=2, metric='cosine'
- **Keyword extraction:** Top 10 TF-IDF terms per cluster
- **Quality scoring:** Silhouette score + avg sentiment + evidence diversity
- **No placeholder logic:** Clustering must produce real results from sample data

### Frontend Conventions (React)
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
