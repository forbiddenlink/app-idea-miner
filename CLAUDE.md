# App-Idea Miner

Opportunity-detection platform: ingests "I wish there was an app..." posts from RSS feeds
(and Reddit via `asyncpraw`), clusters them with HDBSCAN + TF-IDF, and scores clusters by
evidence and quality. FastAPI backend, Celery workers, React frontend, Postgres + Redis.

## Stack

- Backend: Python 3.12, FastAPI, SQLAlchemy 2.0 (async) + asyncpg, Alembic migrations,
  Celery 5 (Redis broker/backend), scikit-learn + HDBSCAN + VADER + NLTK for NLP/clustering
- Frontend (`apps/web/`): React 18, TypeScript, Vite 6, Tailwind CSS 3, TanStack Query,
  React Context (`AuthContext`, `ToastContext`) for global state, React Router, Recharts,
  Playwright for E2E
- Package manager: uv for Python (`uv.lock`, `pyproject.toml`, uv workspace across
  `apps/api`, `apps/worker`, `packages/core`); pnpm for the web app
  (`apps/web/pnpm-lock.yaml`, `packageManager: pnpm@10.34.5`)
- Lint/format: Ruff + mypy (Python), ESLint (web, `--max-warnings 0`)
- Infra: Docker Compose (postgres, redis, api, worker, celery_beat, flower), Railway
  (`railway.toml`), Vercel (`vercel.json`, `api/` serverless entrypoint)

## Commands

Root (`Makefile`, run from repo root):
- `make dev` - start all services via docker-compose and seed data
- `make down` / `make logs` / `make logs-api` / `make logs-worker`
- `make migrate` / `make migration name=<x>` / `make db-reset` / `make db-shell`
- `make seed` / `make ingest` / `make cluster` / `make clean-data`
- `make test` / `make test-coverage` / `make test-file path=tests/test_x.py`
- `make lint` / `make format` (Ruff) / `make typecheck-baseline` (mypy, advisory)
- `make check` - lint + test + web-test + web-build
- `make security` (python-security + web-security), `make python-security` (`uv run pip-audit`)
- `make stats` / `make backup` / `make clean`

Web (`cd apps/web`):
- `pnpm dev` / `pnpm run build` / `pnpm run preview`
- `pnpm lint`, `pnpm test`, `pnpm run test:coverage`, `pnpm run test:e2e` (Playwright)

## Layout

- `apps/api/app/` - FastAPI app: `core/` (auth utilities), `routers/`, `schemas/` (Pydantic),
  `services/`, `config.py` (settings)
- `apps/worker/tasks/` - Celery tasks: `ingestion.py`, `processing.py`, `clustering.py`,
  `saved_search_alerts.py`
- `apps/web/src/` - `components/`, `contexts/` (AuthContext), `hooks/`, `pages/`, `services/`
  (typed API client), `types/`
- `packages/core/` - shared Python: models, clustering, NLP, dedupe
- `migrations/` - Alembic versions
- `tests/` - pytest integration tests
- `data/sample_posts.json` - seed data
- `docs/` - `ARCHITECTURE.md`, `API_SPEC.md`, `SCHEMA.md`, `CLUSTERING.md`, `DEPLOYMENT.md`,
  `TESTING.md`, `MONITORING.md`
- `infra/` - Dockerfiles, postgres init
- `thoughts/` - continuity ledger workspace

## Conventions

- Auth: API key (`X-API-Key` header, server-to-server) or JWT bearer (user sessions).
- Migrations always through Alembic, never raw DDL (`make migration name=...`).
- Docker inter-service URLs use compose service names, not `localhost` - the Postgres
  service is named `postgres` (matches `.env.example`'s `DATABASE_URL` and the README's
  config example).
- Tests marked `@pytest.mark.requires_db` skip locally without a live Postgres at
  `DATABASE_URL`; they always run in CI (Postgres 16 service container).

## Testing

Backend: pytest + pytest-asyncio, `testpaths = ["tests"]`, coverage is opt-in
(`make test-coverage` or `pytest --cov=apps --cov=packages`). Frontend: Vitest (unit),
Playwright (`apps/web/e2e/`, including an API-contract spec runnable against a real API with
`E2E_REAL_API=1`).

## Environment variables

In `.env.example`: `DATABASE_URL`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`,
`REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`, `CELERY_WORKERS`, `API_HOST`,
`API_PORT`, `API_WORKERS`, `CORS_ORIGINS`, `LOG_LEVEL`, `API_KEY`, `VITE_API_URL`,
`VITE_API_KEY`, `RSS_FEEDS`, `FETCH_INTERVAL_HOURS`, `MIN_CLUSTER_SIZE`, `MAX_FEATURES`,
`RECLUSTER_THRESHOLD`, `SECRET_KEY`, `NOTION_API_KEY`, `NOTION_IDEAS_DB_ID`,
`NOTION_MIN_QUALITY` (Notion sink is optional and fails open if `NOTION_API_KEY` is empty).

Used in source but missing from `.env.example`: `ANTHROPIC_API_KEY`, `REDDIT_CLIENT_ID`,
`REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT`, `PRODUCT_HUNT_TOKEN`, `APPSTORE_APP_IDS`,
`APPSTORE_COUNTRY`, `COMPETITOR_LIST_EXTRA`, `WEEKLY_DIGEST_SIZE`, `UPSTASH_REDIS_URL`,
`DB_DISABLE_POOL`, `ENV`, `VERCEL`.

## Gotchas

- Root has both `pyproject.toml`/`uv.lock` and a `requirements.txt`; verify which one a given
  deploy target (Railway vs Vercel serverless) actually installs from before editing deps.
- `pyproject.toml` author email is a placeholder (`elizabeth@example.com`), not a real contact.
