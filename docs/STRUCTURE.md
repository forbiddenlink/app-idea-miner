# Project Structure

## Current State (Planning Complete)

```
app-idea-miner/
├── 📄 README.md                          ✅ Comprehensive guide (15K+ words)
├── 📄 .env.example                       ⏳ To be created
├── 📄 .gitignore                         ⏳ To be created
├── 📄 docker-compose.yml                 ⏳ To be created
├── 📄 Makefile                           ⏳ To be created
│
├── 📂 .github/
│   └── 📂 instructions/
│       └── 📄 codacy.instructions.md     ✅ Code quality config
│
├── 📂 apps/                              ✅ Created
│   ├── 📂 api/                           ✅ Created (empty)
│   │   ├── 📂 app/                       ⏳ FastAPI application
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 main.py                # FastAPI app entry
│   │   │   ├── 📄 config.py              # Settings from env
│   │   │   ├── 📄 database.py            # DB connection
│   │   │   ├── 📄 dependencies.py        # DI containers
│   │   │   │
│   │   │   ├── 📂 models/                # SQLAlchemy ORM
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 base.py
│   │   │   │   ├── 📄 post.py
│   │   │   │   ├── 📄 idea.py
│   │   │   │   └── 📄 cluster.py
│   │   │   │
│   │   │   ├── 📂 schemas/               # Pydantic models
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 cluster.py
│   │   │   │   ├── 📄 idea.py
│   │   │   │   └── 📄 analytics.py
│   │   │   │
│   │   │   ├── 📂 routes/                # API endpoints
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 clusters.py        # Cluster endpoints
│   │   │   │   ├── 📄 ideas.py           # Idea endpoints
│   │   │   │   ├── 📄 analytics.py       # Analytics endpoints
│   │   │   │   ├── 📄 jobs.py            # Job management
│   │   │   │   └── 📄 health.py          # Health checks
│   │   │   │
│   │   │   ├── 📂 services/              # Business logic
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 cluster_service.py
│   │   │   │   ├── 📄 idea_service.py
│   │   │   │   └── 📄 analytics_service.py
│   │   │   │
│   │   │   └── 📂 websocket/             # Real-time
│   │   │       ├── 📄 __init__.py
│   │   │       └── 📄 updates.py
│   │   │
│   │   ├── 📂 tests/                     ⏳ API tests
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 conftest.py
│   │   │   ├── 📄 test_clusters.py
│   │   │   ├── 📄 test_ideas.py
│   │   │   └── 📄 test_health.py
│   │   │
│   │   ├── 📄 Dockerfile                 ⏳ API container
│   │   ├── 📄 requirements.txt           ⏳ Python deps
│   │   └── 📄 pytest.ini                 ⏳ Test config
│   │
│   ├── 📂 worker/                        ✅ Created (empty)
│   │   ├── 📄 __init__.py                ⏳ Package init
│   │   ├── 📄 celery_app.py              ⏳ Celery instance
│   │   ├── 📄 config.py                  ⏳ Worker settings
│   │   │
│   │   ├── 📂 tasks/                     ⏳ Background tasks
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 ingestion.py           # Fetch posts
│   │   │   ├── 📄 processing.py          # Extract ideas
│   │   │   ├── 📄 clustering.py          # Run clustering
│   │   │   └── 📄 maintenance.py         # Cleanup jobs
│   │   │
│   │   ├── 📂 tests/                     ⏳ Worker tests
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 conftest.py
│   │   │   └── 📄 test_tasks.py
│   │   │
│   │   ├── 📄 Dockerfile                 ⏳ Worker container
│   │   └── 📄 requirements.txt           ⏳ Python deps
│   │
│   └── 📂 web/                           ✅ Created (empty)
│       ├── 📂 public/                    ⏳ Static assets
│       │   ├── 📄 favicon.ico
│       │   └── 📄 logo.svg
│       │
│       ├── 📂 src/                       ⏳ React source
│       │   ├── 📄 main.tsx               # Entry point
│       │   ├── 📄 App.tsx                # Root component
│       │   ├── 📄 index.css              # Global styles
│       │   │
│       │   ├── 📂 components/            # Reusable components
│       │   │   ├── 📄 Navbar.tsx
│       │   │   ├── 📄 ClusterCard.tsx
│       │   │   ├── 📄 IdeaCard.tsx
│       │   │   ├── 📄 StatCard.tsx
│       │   │   ├── 📄 SearchBar.tsx
│       │   │   ├── 📄 FilterSidebar.tsx
│       │   │   └── 📂 charts/
│       │   │       ├── 📄 TrendChart.tsx
│       │   │       ├── 📄 SentimentPie.tsx
│       │   │       └── 📄 TimelineChart.tsx
│       │   │
│       │   ├── 📂 pages/                 # Route pages
│       │   │   ├── 📄 Dashboard.tsx
│       │   │   ├── 📄 ClusterExplorer.tsx
│       │   │   ├── 📄 ClusterDetail.tsx
│       │   │   ├── 📄 IdeaBrowser.tsx
│       │   │   └── 📄 Analytics.tsx
│       │   │
│       │   ├── 📂 hooks/                 # Custom hooks
│       │   │   ├── 📄 useClusters.ts
│       │   │   ├── 📄 useIdeas.ts
│       │   │   ├── 📄 useWebSocket.ts
│       │   │   └── 📄 useAnalytics.ts
│       │   │
│       │   ├── 📂 services/              # API client
│       │   │   ├── 📄 api.ts             # Axios instance
│       │   │   ├── 📄 clusterService.ts
│       │   │   ├── 📄 ideaService.ts
│       │   │   └── 📄 analyticsService.ts
│       │   │
│       │   ├── 📂 store/                 # State management
│       │   │   └── 📄 appStore.ts        # Zustand store
│       │   │
│       │   └── 📂 types/                 # TypeScript types
│       │       ├── 📄 Cluster.ts
│       │       ├── 📄 Idea.ts
│       │       └── 📄 Analytics.ts
│       │
│       ├── 📄 index.html                 ⏳ HTML template
│       ├── 📄 package.json               ⏳ Node dependencies
│       ├── 📄 tsconfig.json              ⏳ TypeScript config
│       ├── 📄 vite.config.ts             ⏳ Vite config
│       ├── 📄 tailwind.config.js         ⏳ Tailwind config
│       ├── 📄 postcss.config.js          ⏳ PostCSS config
│       └── 📄 .eslintrc.json             ⏳ ESLint config
│
├── 📂 packages/                          ✅ Created
│   └── 📂 core/                          ✅ Created (empty)
│       ├── 📄 __init__.py                ⏳ Package init
│       ├── 📄 models.py                  ⏳ Shared SQLAlchemy models
│       ├── 📄 clustering.py              ⏳ Clustering engine
│       ├── 📄 nlp.py                     ⏳ Text processing
│       ├── 📄 dedupe.py                  ⏳ Deduplication logic
│       ├── 📄 utils.py                   ⏳ Utility functions
│       └── 📄 requirements.txt           ⏳ Shared dependencies
│
├── 📂 infra/                             ✅ Created (empty)
│   ├── 📄 docker-compose.yml             ⏳ Service orchestration
│   ├── 📄 Dockerfile.api                 ⏳ API image
│   ├── 📄 Dockerfile.worker              ⏳ Worker image
│   ├── 📄 .dockerignore                  ⏳ Docker ignore
│   │
│   ├── 📂 postgres/                      ⏳ PostgreSQL config
│   │   └── 📄 init.sql                   # Initial schema
│   │
│   ├── 📂 nginx/                         ⏳ Nginx (future)
│   │   └── 📄 nginx.conf
│   │
│   └── 📂 scripts/                       ⏳ Deployment scripts
│       ├── 📄 backup.sh
│       └── 📄 restore.sh
│
├── 📂 migrations/                        ✅ Created (empty)
│   ├── 📄 env.py                         ⏳ Alembic env
│   ├── 📄 script.py.mako                 ⏳ Migration template
│   ├── 📄 alembic.ini                    ⏳ Alembic config
│   │
│   └── 📂 versions/                      ⏳ Migration files
│       └── 📄 001_initial_schema.py      # First migration
│
├── 📂 data/                              ✅ Created (empty)
│   ├── 📄 sample_posts.json              ⏳ 100+ curated ideas
│   │
│   └── 📂 fixtures/                      ⏳ Test data
│       ├── 📄 posts_hackernews.json
│       └── 📄 posts_producthunt.json
│
├── 📂 docs/                              ✅ Created
│   ├── 📄 PLAN.md                        ✅ 16-day development plan
│   ├── 📄 ARCHITECTURE.md                ✅ System architecture
│   ├── 📄 SCHEMA.md                      ✅ Database design
│   ├── 📄 API_SPEC.md                    ✅ API reference
│   ├── 📄 CLUSTERING.md                  ✅ ML algorithm deep dive
│   ├── 📄 RESEARCH.md                    ✅ Competitive analysis
│   ├── 📄 SUMMARY.md                     ✅ Planning summary
│   ├── 📄 STRUCTURE.md                   ✅ This file
│   │
│   ├── 📄 DATA_SOURCES.md                ⏳ Adding new sources
│   ├── 📄 DEPLOYMENT.md                  ⏳ Production guide
│   ├── 📄 TESTING.md                     ⏳ Testing strategy
│   ├── 📄 CONTRIBUTING.md                ⏳ Contribution guide
│   │
│   └── 📂 assets/                        ⏳ Screenshots
│       ├── 📄 dashboard.png
│       ├── 📄 cluster-detail.png
│       └── 📄 analytics.png
│
└── 📂 tests/                             ✅ Created (empty)
    ├── 📄 __init__.py                    ⏳ Package init
    ├── 📄 conftest.py                    ⏳ Pytest config
    │
    ├── 📂 unit/                          ⏳ Unit tests
    │   ├── 📄 test_clustering.py
    │   ├── 📄 test_nlp.py
    │   ├── 📄 test_dedupe.py
    │   └── 📄 test_utils.py
    │
    └── 📂 integration/                   ⏳ Integration tests
        ├── 📄 test_ingestion_flow.py
        ├── 📄 test_processing_flow.py
        └── 📄 test_clustering_flow.py
```

---

## Legend

- ✅ **Created** - Directory or file exists
- ⏳ **To Be Created** - Planned for implementation
- 📂 **Directory**
- 📄 **File**

---

## Statistics

### Current State (Planning Phase)
- **Directories Created:** 7
- **Documentation Files:** 8 (52,000+ words)
- **Total Lines of Planning:** ~3,500
- **Estimated Final Lines of Code:** ~15,000

### After Implementation (Phase 0-6)
- **Total Files:** ~150+
- **Python Files:** ~45
- **TypeScript/React Files:** ~40
- **Config/Docker Files:** ~20
- **Test Files:** ~30
- **Documentation:** ~15

---

## File Counts by Component

| Component | Files | Lines (Est.) |
|-----------|-------|--------------|
| API (FastAPI) | ~15 | ~2,500 |
| Worker (Celery) | ~8 | ~1,200 |
| Core Package | ~6 | ~1,800 |
| Web UI (React) | ~40 | ~6,000 |
| Tests | ~30 | ~2,000 |
| Infrastructure | ~10 | ~500 |
| Migrations | ~3 | ~400 |
| Documentation | ~15 | ~600 |
| **Total** | **~127** | **~15,000** |

---

## Next Steps for Implementation

### Phase 0: Bootstrap (Days 1-2)
Create all files marked with ⏳ in:
- `infra/` - Docker setup
- `.env.example` - Configuration template
- `Makefile` - Development commands
- `requirements.txt` files
- `package.json` - Node dependencies

### Phase 1: Foundation (Days 3-4)
- Database models (`packages/core/models.py`)
- Alembic migrations (`migrations/versions/`)
- Basic API structure (`apps/api/app/`)
- Basic worker structure (`apps/worker/`)

### Phase 2-6: Feature Implementation
Follow [PLAN.md](PLAN.md) for detailed phase breakdown.

---

## Quick Reference

### Key Entry Points
- **API:** `apps/api/app/main.py`
- **Worker:** `apps/worker/celery_app.py`
- **Web UI:** `apps/web/src/App.tsx`
- **Core Logic:** `packages/core/`

### Key Configuration Files
- **Environment:** `.env` (from `.env.example`)
- **Docker:** `docker-compose.yml`
- **Database:** `migrations/env.py`
- **API:** `apps/api/app/config.py`
- **Worker:** `apps/worker/config.py`

### Key Documentation
- **Getting Started:** [README.md](../README.md)
- **Development Plan:** [PLAN.md](PLAN.md)
- **Architecture:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **API Reference:** [API_SPEC.md](API_SPEC.md)

---

This structure is designed to be:
- 🏗️ **Modular:** Clear separation of concerns
- 📚 **Documented:** README for every component
- 🧪 **Testable:** Tests alongside code
- 🚀 **Scalable:** Ready for growth
- 🛠️ **Maintainable:** Consistent patterns

**Ready to implement!** 💻
