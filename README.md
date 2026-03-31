# App-Idea Miner

> Discover validated app opportunities from real user needs

An intelligent opportunity detection platform that automatically collects, clusters, and analyzes "I wish there was an app..." posts from across the web — giving you evidence-backed insights on what people actually want built.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![PostgreSQL 16](https://img.shields.io/badge/postgresql-16-blue.svg)](https://www.postgresql.org/)
[![Redis 7](https://img.shields.io/badge/redis-7-red.svg)](https://redis.io/)
[![React 18](https://img.shields.io/badge/react-18-blue.svg)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.115-green.svg)](https://fastapi.tiangolo.com/)

---

## Status

**MVP complete** — all core phases shipped and security-hardened.

| Area                                                | Status      |
| --------------------------------------------------- | ----------- |
| Data ingestion pipeline                             | ✅ Complete |
| NLP extraction + sentiment                          | ✅ Complete |
| HDBSCAN clustering                                  | ✅ Complete |
| FastAPI backend (21+ endpoints)                     | ✅ Complete |
| React UI (5 pages, 30+ components)                  | ✅ Complete |
| JWT authentication + API key auth                   | ✅ Complete |
| User-owned bookmarks                                | ✅ Complete |
| Saved searches + alert scheduling                   | ✅ Complete |
| Redis caching                                       | ✅ Complete |
| Docker Compose orchestration                        | ✅ Complete |
| CI pipeline (GitHub Actions)                        | ✅ Complete |
| WCAG 2.2 accessibility                              | ✅ Complete |
| Security hardened (rate limiting, timing-safe auth) | ✅ Complete |

---

## Features

### Data Intelligence

- **Smart Ingestion:** Fetches posts from RSS feeds with URL-hash and content-fingerprint deduplication
- **AI-Powered Clustering:** Groups similar ideas using HDBSCAN + TF-IDF vectorization
- **Evidence-Based:** Every cluster backed by real user quotes with source links
- **Quality Scoring:** Automatic assessment of idea specificity and actionability (0–1 scale)

### Analytics & Insights

- **Dashboard:** Key metrics + top clusters at a glance
- **Trend Analysis:** Time-series charts showing idea growth
- **Domain Breakdown:** Categorized by productivity, health, finance, etc.
- **Sentiment Analysis:** VADER-based positive/negative distribution

### User Features

- **Authentication:** JWT login with email normalization and rate-limited endpoints
- **Bookmarks:** Authenticated, user-owned bookmarks persisted to the database
- **Saved Searches:** Save filter combinations with optional daily/weekly alert digests
- **Command Palette:** `Cmd+K` universal search across pages, clusters, and ideas
- **Context Menus:** Right-click on cards for copy, share, and export actions
- **Advanced Filtering:** Sort by size, quality, sentiment, or trend
- **Export:** CSV and JSON export from any view

### Infrastructure

- **Background Workers:** Celery task queues for ingestion, processing, clustering, and alerts
- **Async API:** FastAPI + asyncpg (8× faster than sync psycopg2)
- **Migrations:** Alembic-managed schema versions, never raw DDL
- **Monitoring:** Flower (Celery), Prometheus metrics endpoint

---

## Quick Start

### Prerequisites

- [UV](https://astral.sh/uv) 0.5+ — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Docker Desktop 4.0+ (with Compose V2)
- Make
- 4 GB RAM, 2 GB free disk

### Installation

```bash
git clone https://github.com/yourusername/app-idea-miner.git
cd app-idea-miner
cp .env.example .env
make dev
```

The following services start automatically:

| Service                 | URL                          |
| ----------------------- | ---------------------------- |
| Web UI                  | <http://localhost:3000>      |
| API                     | <http://localhost:8000>      |
| API Docs (Swagger)      | <http://localhost:8000/docs> |
| Flower (Celery monitor) | <http://localhost:5555>      |
| PostgreSQL              | localhost:5432               |
| Redis                   | localhost:6379               |

### First Run

```bash
# Seed sample data (20 curated app ideas)
make seed

# Wait ~30 seconds for the worker to process and cluster

# Open the UI
open http://localhost:3000
```

You should see 10–15 clusters with evidence links and quality scores.

---

## Architecture

```
┌─────────────────────────────────────────┐
│              Data Sources               │
│  RSS Feeds · Sample Data · (Future APIs)│
└──────────────────┬──────────────────────┘
                   │
                   ▼
         ┌──────────────────┐
         │  Celery Worker   │
         │  Ingestion ·     │
         │  Processing ·    │
         │  Clustering ·    │
         │  Alert Digests   │
         └────────┬─────────┘
                  │
         ┌────────▼─────────┐
         │   PostgreSQL 16  │
         │   Redis 7        │
         └────────┬─────────┘
                  │
         ┌────────▼─────────┐        ┌──────────────────┐
         │    FastAPI       │◄───────│  React + Vite    │
         │  REST · Auth ·   │        │  TypeScript UI   │
         │  API Key Gate    │        └──────────────────┘
         └──────────────────┘
```

### Tech Stack

| Layer    | Technology                                                    |
| -------- | ------------------------------------------------------------- |
| API      | Python 3.12, FastAPI 0.115, SQLAlchemy 2.0 (async), asyncpg   |
| Auth     | JWT (python-jose), passlib/bcrypt, per-route rate limiting    |
| Workers  | Celery 5.4, Redis 7 (broker + result backend)                 |
| ML       | scikit-learn (TF-IDF), HDBSCAN, VADER sentiment, NLTK         |
| Database | PostgreSQL 16 (JSONB, full-text search), Alembic migrations   |
| Frontend | React 18, TypeScript 5, Vite 6, Tailwind CSS 3, Framer Motion |
| State    | TanStack Query 5, Zustand 4                                   |
| Testing  | pytest + pytest-asyncio, Vitest, Playwright                   |
| Tooling  | UV (packages), Ruff (lint/format), mypy (types)               |
| Infra    | Docker Compose, GitHub Actions CI                             |

---

## Project Structure

```
app-idea-miner/
├── apps/
│   ├── api/                    # FastAPI backend
│   │   └── app/
│   │       ├── core/           # Auth utilities
│   │       ├── routers/        # Endpoints (clusters, ideas, bookmarks, auth, …)
│   │       ├── schemas/        # Pydantic request/response schemas
│   │       └── services/       # Business logic layer
│   ├── worker/                 # Celery background tasks
│   │   └── tasks/
│   │       ├── ingestion.py
│   │       ├── processing.py
│   │       ├── clustering.py
│   │       └── saved_search_alerts.py
│   └── web/                    # React frontend
│       └── src/
│           ├── components/     # Reusable UI components
│           ├── contexts/       # AuthContext
│           ├── hooks/          # useFavorites, useKeyboard, …
│           ├── pages/          # Dashboard, ClusterExplorer, Ideas, Saved, Settings, Login
│           ├── services/       # Typed API client
│           └── types/          # Shared TypeScript interfaces
├── packages/
│   └── core/                   # Shared Python (models, clustering, NLP, dedupe)
├── migrations/                 # Alembic versions
├── tests/                      # pytest integration tests
├── data/
│   └── sample_posts.json       # Seed data (20 curated ideas)
├── docs/                       # Architecture, API spec, schema, deployment
├── infra/                      # Dockerfiles, postgres init
├── Makefile                    # Dev commands
└── docker-compose.yml
```

---

## Configuration

Copy `.env.example` to `.env` and adjust as needed:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgresql:5432/appideas
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=appideas

# Redis
REDIS_URL=redis://redis:6379/0

# Auth
SECRET_KEY=your-secret-key-here

# API
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000

# Worker
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1

# Frontend
VITE_API_URL=http://localhost:8000

# Data Sources
RSS_FEEDS=https://hnrss.org/newest
FETCH_INTERVAL_HOURS=6

# Clustering
MIN_CLUSTER_SIZE=3
MAX_FEATURES=500
```

> All Docker inter-service URLs use service names (`postgresql`, `redis`), not `localhost`.

---

## Development Commands

### Services

```bash
make dev          # Start all services
make down         # Stop all services
make logs         # Tail all logs
make logs-api     # Tail API logs only
make logs-worker  # Tail worker logs only
```

### Database

```bash
make migrate                          # Run pending migrations
make migration name=add_column_x      # Generate new migration
make db-reset                         # Drop and recreate (loses data)
make db-shell                         # psql shell
```

### Data

```bash
make seed         # Load sample_posts.json
make ingest       # Trigger ingestion task manually
make cluster      # Run clustering task manually
make clean-data   # Truncate all data tables
```

### Testing

```bash
make test                                        # All tests
make test-coverage                               # With HTML coverage report
make test-file path=tests/test_api_auth.py       # Single file
cd apps/web && npm test                          # Frontend unit tests
cd apps/web && npm run test:e2e                  # Playwright E2E tests
```

> Tests marked `@pytest.mark.requires_db` are skipped locally unless `DATABASE_URL` points to a live Postgres instance. They always run in CI (GitHub Actions provides a Postgres service).

### Code Quality

```bash
make lint         # Ruff linter
make format       # Ruff auto-format
cd apps/web && npm run lint    # ESLint (0 warnings policy)
cd apps/web && npm run build   # TypeScript + Vite build check
```

---

## API Overview

Full reference: [`docs/API_SPEC.md`](docs/API_SPEC.md)

Authentication options:

- **API Key:** `X-API-Key: <key>` header (server-to-server)
- **JWT Bearer:** `Authorization: Bearer <token>` (user sessions)

Key endpoints:

```
GET  /api/v1/clusters           List clusters (sort, filter, paginate)
GET  /api/v1/clusters/{id}      Cluster detail with evidence
GET  /api/v1/ideas              List ideas (search, filter)
GET  /api/v1/analytics/summary  Aggregated platform metrics

POST /api/v1/auth/register      Create account
POST /api/v1/auth/login         Exchange credentials for JWT
GET  /api/v1/auth/me            Current user info

GET  /api/v1/bookmarks          User's saved bookmarks
POST /api/v1/bookmarks          Bookmark a cluster or idea
DELETE /api/v1/bookmarks/{id}   Remove bookmark

GET  /api/v1/saved-searches     User's saved searches
POST /api/v1/saved-searches     Create saved search with alert options
DELETE /api/v1/saved-searches/{id}

POST /api/v1/jobs/ingest        Trigger ingestion
POST /api/v1/jobs/cluster       Trigger clustering
GET  /health                    Health check
GET  /metrics                   Prometheus metrics
```

---

## How It Works

### 1. Ingestion

Posts are fetched from RSS feeds on a configurable schedule. Each post is deduplicated using a SHA-256 URL hash and fuzzy title matching before being stored.

### 2. Processing

Each post is run through:

- **Idea extraction:** pattern matching for "I wish there was an app…" phrases
- **Sentiment analysis:** VADER scores (compound, positive, negative, neutral)
- **Domain tagging:** productivity, health, finance, etc.
- **Quality scoring:** specificity × actionability → 0–1 float

### 3. Clustering

Ideas are grouped using:

1. **TF-IDF vectorization** (500 features, 1–3 grams, L2-normalized)
2. **HDBSCAN** (min_cluster_size=2, euclidean distance) — auto-detects cluster count and handles noise
3. **Keyword extraction:** top-10 TF-IDF terms per cluster
4. **Quality scoring:** silhouette score + average sentiment + source diversity

See [`docs/CLUSTERING.md`](docs/CLUSTERING.md) for the full algorithm breakdown.

---

## Testing

```bash
# Backend
make test                     # All tests (DB tests skip without live Postgres)
make test-coverage            # HTML report at htmlcov/index.html

# Frontend
cd apps/web
npm test                      # Vitest unit tests
npm run test:coverage         # With coverage
npm run test:e2e              # Playwright smoke + flow tests
```

CI runs both suites on every push. The backend job provides a Postgres 16 service container so all tests (including `requires_db`) execute in CI.

---

## Deployment

See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for full instructions.

The project ships with:

- `railway.toml` for [Railway](https://railway.app) deployment
- `vercel.json` for Vercel (frontend)
- `api/` directory with a serverless-ready entrypoint

---

## Documentation

| File                                           | Contents                             |
| ---------------------------------------------- | ------------------------------------ |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | System design decisions              |
| [`docs/API_SPEC.md`](docs/API_SPEC.md)         | Full API reference (21+ endpoints)   |
| [`docs/SCHEMA.md`](docs/SCHEMA.md)             | Database schema and relationships    |
| [`docs/CLUSTERING.md`](docs/CLUSTERING.md)     | HDBSCAN algorithm deep dive          |
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)     | Production deployment guide          |
| [`docs/TESTING.md`](docs/TESTING.md)           | Testing strategy and patterns        |
| [`docs/MONITORING.md`](docs/MONITORING.md)     | Metrics, alerting, and observability |

---

## Contributing

1. Fork the repo and create a feature branch
2. Run `make dev` to start the stack
3. Write tests for new behavior
4. Ensure `make lint` and `make test` pass
5. Open a pull request

---

## License

[MIT](LICENSE)
