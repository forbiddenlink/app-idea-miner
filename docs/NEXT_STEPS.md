# App-Idea Miner — Next Steps & Improvement Roadmap

> Generated March 2026 after comprehensive codebase audit and Vercel deployment verification.

## Current Status

- **All 6 pages** render correctly on production (https://app-idea-miner.vercel.app)
- **22+ API endpoints** working on Vercel serverless
- **Security hardened**: Unique API key + SECRET_KEY set, ENV=production enabled
- **Zero console errors**, all linters pass (Ruff, ESLint, TypeScript)
- **26 security tests** pass (API auth, rate limiting, CORS, headers)

---

## Priority Matrix

| Area | P0 (Do Now) | P1 (Next Sprint) | P2 (Backlog) |
|------|-------------|-------------------|--------------|
| **Data Sources** | Enable real Reddit + PH credentials | HN API, Twitter/X | GitHub Discussions, Lemmy |
| **ML/Clustering** | Sentence embeddings, cluster labels | Semantic dedup, topic modeling | Incremental clustering, market signals |
| **Infrastructure** | Upstash Redis, DB connection pooling | Cache headers, compression | Read replicas, cursor pagination |
| **Features** | Pydantic schemas, user auth | Export, email alerts, rate limiting | Cluster comparison, WebSocket, CI/CD |
| **Testing** | Clustering/NLP/dedupe unit tests | Source connectors, cache tests | Frontend tests, E2E with Playwright |
| **Frontend** | Responsive design, loading states | API retry, keyboard nav, light mode audit | Virtual lists, PWA, animations |

---

## 1. Data Source Expansion

### Current State
Plugin architecture in `apps/worker/sources/` with `BaseSource` abstract class + 3 implementations (RSS, Reddit, ProductHunt). Reddit and ProductHunt fall back to mock data when credentials are missing.

### Recommendations

| Priority | Action | Complexity | Details |
|----------|--------|------------|---------|
| **P0** | Enable real Reddit credentials | Small | `RedditSource` is fully implemented with `asyncpraw`. Needs `REDDIT_CLIENT_ID` + `REDDIT_CLIENT_SECRET` env vars. Free tier: 60 req/min. |
| **P0** | Enable real ProductHunt credentials | Small | GraphQL integration complete. Needs `PRODUCT_HUNT_TOKEN` env var. API v2: 450 req/day. |
| **P1** | Add HackerNews API source | Small | Official HN API is free, no auth. Create `HackerNewsSource(BaseSource)`. Filter "Ask HN"/"Show HN" posts for app ideas. |
| **P1** | Add Twitter/X source | Medium | X API v2 Free tier: 1,500 tweets/month. Search: `"I wish there was an app" OR "someone should build"`. |
| **P1** | Add Indie Hackers source | Medium | Use RSS feed at `https://www.indiehackers.com/feed.xml` via existing `RSSSource`. |
| **P2** | Add GitHub Discussions source | Medium | GitHub GraphQL API to search issues/discussions for "feature request"/"app idea". |
| **P2** | Configure Celery Beat schedule | Small | `run_ingestion_cycle` task exists but no periodic schedule. Add to `celery_app.py`. |

---

## 2. ML/Clustering Improvements

### Current State
- TF-IDF (500 features, 1-3 grams, L2 normalized) → HDBSCAN clustering
- VADER sentiment + keyword-based emotion detection
- URL hash + fuzzy title deduplication (85% threshold)
- Cluster labels = top 3 keyword concatenation

### Recommendations

| Priority | Action | Complexity | Details |
|----------|--------|------------|---------|
| **P0** | Replace TF-IDF with sentence embeddings | Medium | Use `sentence-transformers/all-MiniLM-L6-v2` (80MB, 384-dim). `pgvector` already in dependencies. Keep TF-IDF for keyword extraction only. |
| **P0** | Improve cluster labeling | Small | Use most representative sentence (closest to centroid) or LLM-generated 3-5 word labels instead of "Photo + App + Stats". |
| **P1** | Add semantic deduplication | Medium | Embed all posts, flag pairs with cosine similarity > 0.92 as duplicates. Current dedup misses cross-source duplicates. |
| **P1** | Add topic modeling layer | Medium | BERTopic on top of clusters for hierarchical themes ("Health & Wellness", "Developer Tools"). |
| **P1** | Upgrade sentiment analysis | Small | Consider `cardiffnlp/twitter-roberta-base-sentiment` for better accuracy on social media text. |
| **P2** | Add market signal extraction | Medium | Extract: existing app mentions ("like X but for Y"), price willingness, market sizing hints. |
| **P2** | Implement incremental clustering | Large | Use `hdbscan.approximate_predict()` (already enabled with `prediction_data=True`) for scale. |

---

## 3. Infrastructure & Performance

### Current State
- Vercel serverless (Python lambda + static frontend)
- Redis caching layer exists but Redis not configured on Vercel
- PostgreSQL via asyncpg with pool_size=10 (too aggressive for serverless)

### Recommendations

| Priority | Action | Complexity | Details |
|----------|--------|------------|---------|
| **P0** | Add Upstash Redis | Small | Free tier: 10K commands/day. Caching layer already abstracted. Swap connection to Upstash REST SDK. |
| **P0** | Fix DB connection pooling for serverless | Small | Change `pool_size=10` to `NullPool` in `database.py` for serverless. Use external pooler (Neon/Supabase built-in). |
| **P1** | Add Cache-Control headers | Small | `Cache-Control: public, max-age=300, stale-while-revalidate=60` on read-only endpoints. |
| **P1** | Move background jobs off Vercel | Medium | Railway ($5/mo) for Celery worker, or Vercel Cron Functions (60s limit), or Inngest. |
| **P2** | Cursor-based pagination | Medium | Replace offset/limit with keyset pagination using `created_at + id` cursor. |

---

## 4. Missing Features

### Not completed from original checklist:
- WebSocket support, rate limiting integration, structured logging
- Unit tests for clustering/NLP/dedupe
- CI/CD pipeline, Pydantic schemas

### Recommendations

| Priority | Action | Complexity | Details |
|----------|--------|------------|---------|
| **P0** | Add Pydantic response schemas | Medium | No request validation or auto-docs. Define schemas in `apps/api/app/schemas/` for all 21+ endpoints. |
| **P0** | Add user authentication | Large | Single shared API key → JWT with roles. Consider Better Auth or Clerk. Unlocks per-user favorites/searches. |
| **P1** | Wire up export endpoints | Small | `ExportButton` component exists. Add `GET /api/v1/clusters/export?format=csv|json`. |
| **P1** | Apply rate limiting globally | Small | `RateLimiter` class exists but only in tests. Apply to all routes (100 req/min anon, 1000 auth). |
| **P2** | Add CI/CD with GitHub Actions | Small | Lint (Ruff) + test (pytest) + build (Vite) + deploy (Vercel). |
| **P2** | Cluster comparison view | Medium | Side-by-side comparison showing keyword overlaps, sentiment deltas. |

---

## 5. Testing Coverage (Currently 12%)

### Missing Coverage

| Priority | Area | Complexity | Details |
|----------|------|------------|---------|
| **P0** | Clustering engine | Medium | Test `cluster_ideas()`, keyword extraction, label generation, edge cases (empty/single doc). |
| **P0** | NLP processor | Medium | Test 12+ regex patterns, sentiment analysis, emotion detection, quality scoring. |
| **P0** | Deduplication | Small | Test URL canonicalization, hash generation, fuzzy title matching. |
| **P1** | Source connectors | Medium | Mock external APIs, test parsing logic, test mock fallback mode. |
| **P1** | Cache layer | Small | Test key generation, `@cached` decorator, invalidation, metrics. |
| **P2** | Frontend tests (Vitest) | Large | ClusterCard, Dashboard data, CommandPalette keyboard shortcuts. |
| **P2** | E2E tests (Playwright) | Large | Dashboard → Cluster → Evidence → Search flow. |

---

## 6. Frontend Improvements

### Recommendations

| Priority | Action | Complexity | Details |
|----------|--------|------------|---------|
| **P0** | Add responsive breakpoints | Medium | No mobile-specific styles found. Add responsive grid, collapsible nav, mobile menu. |
| **P0** | Verify loading states on all pages | Small | Dashboard has skeletons but verify Ideas, Opportunities, Analytics handle loading/error. |
| **P1** | Add API retry with backoff | Small | Only rate limit errors are caught. Add exponential backoff for 5xx, toast for user-visible errors. |
| **P1** | Light mode CSS audit | Medium | Colors tuned for dark mode. Audit contrast for glassmorphism effects in light mode. |
| **P2** | Virtualized lists | Medium | `@tanstack/react-virtual` for 100+ cluster/idea lists. |
| **P2** | PWA support | Small | Add `manifest.json` + service worker for offline static shell. |

---

## Top 5 Highest-Impact Quick Wins

1. **Enable real Reddit + ProductHunt credentials** — unlocks real data with zero code changes
2. **Add Upstash Redis** — makes caching work on Vercel serverless
3. **Write clustering/NLP/dedupe unit tests** — protects core business logic (biggest coverage gap)
4. **Sentence embeddings** — dramatically improves clustering quality
5. **Pydantic response schemas** — adds validation, auto-docs, type safety across all endpoints
