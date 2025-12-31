# 🔬 Technology Decision Matrix

Quick reference for understanding trade-offs in research recommendations.

---

## 📦 Dependency Management

| Tool | Speed | Monorepo Support | Maturity | Learning Curve | Verdict |
|------|-------|------------------|----------|----------------|---------|
| **pip** | ⭐ | ❌ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ Too slow for 2025 |
| **Poetry** | ⭐⭐ | ⚠️ Via plugins | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⚠️ Slow, complex |
| **UV** ⭐ | ⭐⭐⭐⭐⭐ | ✅ Native | ⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ **Recommended** |

**Benchmarks:**
- Installing FastAPI deps: **pip: 45s** → **UV: 3s** (15x faster)
- Docker builds: **pip: 5min** → **UV: 30s** (10x faster)

**Migration Effort:** 30 minutes (follow QUICK_START_IMPROVEMENTS.md)

---

## 🧠 Clustering Algorithms

| Approach | Quality | Speed | Complexity | Use Case | Verdict |
|----------|---------|-------|------------|----------|---------|
| **TF-IDF + HDBSCAN** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | MVP, exact keywords | ✅ Start here |
| **BERTopic** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | Semantic similarity | ✅ Phase 2 |
| **LDA** | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | Legacy systems | ❌ Outdated |

**Quality Comparison (Topic Coherence Score):**
- TF-IDF + HDBSCAN: **0.45-0.55**
- BERTopic: **0.65-0.75** (+30-50% improvement)

**Recommendation:** Implement both with feature flag:
```python
USE_BERTOPIC = os.getenv("CLUSTERING_METHOD") == "bertopic"
```

**Migration Path:**
1. Launch MVP with TF-IDF (faster development)
2. Compute embeddings in background
3. A/B test BERTopic vs TF-IDF
4. Switch based on results

---

## 🗄️ Database: Async Drivers

| Driver | Speed | Maturity | Compatibility | Pool Support | Verdict |
|--------|-------|----------|---------------|--------------|---------|
| **psycopg2** (sync) | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ | ❌ Not async |
| **psycopg3** (async) | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ | ⚠️ Newer |
| **asyncpg** ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ | ✅ **Recommended** |

**Benchmarks (1000 queries):**
- psycopg2 (sync): **~2500ms**
- psycopg3 (async): **~800ms**
- asyncpg: **~300ms** (8x faster than sync!)

**Critical:** SQLAlchemy URL must be `postgresql+asyncpg://`

---

## 🏗️ Architecture Patterns

### API Structure

| Pattern | Testability | Maintainability | Performance | Complexity | Verdict |
|---------|-------------|-----------------|-------------|------------|---------|
| **Fat Controllers** | ⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐ | ❌ Anti-pattern |
| **Service Layer** ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ✅ **Recommended** |
| **CQRS** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⚠️ Overkill for MVP |

**Example: Testing Complexity**

```python
# Fat Controller (hard to test)
@router.get("/clusters")
async def get_clusters(db: Session):
    # 50 lines of business logic mixed with HTTP concerns
    # Must mock HTTP request/response to test
    pass

# Service Layer (easy to test)
class ClusterService:
    async def get_all(self): 
        # Pure business logic
        pass

# Test is simple
async def test_service():
    service = ClusterService(mock_db)
    result = await service.get_all()
    assert len(result) > 0
```

### WebSocket Scaling

| Approach | Multi-Worker | Complexity | Latency | Verdict |
|----------|--------------|------------|---------|---------|
| **In-Memory Dict** | ❌ | ⭐ | ⭐⭐⭐⭐⭐ | ❌ Single worker only |
| **Redis Pub/Sub** ⭐ | ✅ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ **Recommended** |
| **RabbitMQ** | ✅ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⚠️ Overkill |

**Recommendation:** Start with in-memory (MVP), add Redis pub/sub before scaling horizontally.

---

## 🐳 Docker Strategies

### Image Size

| Base Image | Size | Build Time | Security | Verdict |
|------------|------|------------|----------|---------|
| `python:3.12` | 1.02 GB | Fast | ⚠️ Many vulnerabilities | ❌ Too bloated |
| `python:3.12-slim` ⭐ | 160 MB | Fast | ✅ Minimal | ✅ **Recommended** |
| `python:3.12-alpine` | 55 MB | Slow* | ✅ Minimal | ⚠️ Compile issues |

*Alpine uses musl libc, causes issues with compiled Python packages (numpy, pandas)

### Build Strategy

| Pattern | Cache Efficiency | Rebuild Time | Complexity | Verdict |
|---------|------------------|--------------|------------|---------|
| **Single Stage** | ⭐⭐ | ⭐⭐ | ⭐ | ❌ Slow |
| **Multi-Stage** ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ✅ **Recommended** |

**Example Build Times (with UV):**
- First build: **~2 minutes**
- Code change (cached deps): **~10 seconds**
- Dependency change: **~30 seconds**

---

## 📊 Indexing Strategies (PostgreSQL)

### JSONB Indexes

| Index Type | Use Case | Speed | Storage | Verdict |
|------------|----------|-------|---------|---------|
| **GIN (default)** ⭐ | Containment (`@>`) | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ✅ **Recommended** |
| **GIN (jsonb_path_ops)** | Containment only | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⚠️ Limited queries |
| **Expression Index** | Single key | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ Specific keys |

**Recommendation:**
1. One GIN index on entire JSONB column (handles most queries)
2. Expression indexes for frequently queried keys

```sql
-- Covers 90% of queries
CREATE INDEX idx_metadata_gin ON raw_posts USING GIN (metadata);

-- For specific high-traffic query
CREATE INDEX idx_metadata_domain ON raw_posts ((metadata->>'domain'));
```

### Compression

| Algorithm | Speed | Compression Ratio | Verdict |
|-----------|-------|-------------------|---------|
| **pglz** (default) | ⭐⭐ | ⭐⭐⭐⭐ | ⚠️ Slow decompression |
| **lz4** ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ✅ **Recommended** |

**Impact:** 2x faster decompression, ~10% more storage

```sql
ALTER TABLE raw_posts ALTER COLUMN metadata SET COMPRESSION lz4;
```

---

## 🧪 Testing Frameworks

| Tool | Speed | Features | Async Support | Verdict |
|------|-------|----------|---------------|---------|
| **unittest** | ⭐⭐⭐ | ⭐⭐ | ⚠️ Manual | ❌ Outdated |
| **pytest** ⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ pytest-asyncio | ✅ **Recommended** |

**Extensions:**
- `pytest-asyncio` - Async test support
- `pytest-cov` - Coverage reports
- `pytest-xdist` - Parallel execution

```bash
# Run tests in parallel with coverage
pytest -n auto --cov=apps --cov=packages --cov-report=html
```

---

## 🎨 Frontend: Build Tools

| Tool | Dev Start Time | HMR Speed | Build Time | Bundle Size | Verdict |
|------|----------------|-----------|------------|-------------|---------|
| **Create React App** | 20-30s | ⭐⭐⭐ | 45s | Large | ❌ Deprecated |
| **Webpack** | 15s | ⭐⭐⭐ | 30s | Optimized | ⚠️ Complex |
| **Vite** ⭐ | <1s | ⭐⭐⭐⭐⭐ | 10s | Optimized | ✅ **Recommended** |

**Key Difference:** Vite uses ES modules in dev (no bundling), Rollup for prod

**Developer Experience:**
- **CRA:** Save file → wait 3s → see change
- **Vite:** Save file → instant update (<100ms)

---

## 🔧 Linting & Formatting

| Tool | Speed | Features | Config | Verdict |
|------|-------|----------|--------|---------|
| **Black + Flake8 + isort** | ⭐⭐ | ⭐⭐⭐⭐ | 3 files | ⚠️ Slow |
| **Ruff** ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 1 file | ✅ **Recommended** |

**Benchmarks (large codebase):**
- Black + Flake8 + isort: **~5 seconds**
- Ruff: **~0.05 seconds** (100x faster!)

**Configuration:**
```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP"]
```

One command: `ruff check --fix && ruff format`

---

## 📈 Decision Framework

### When to Choose X Over Y

**UV vs Poetry:**
- Choose UV if: Monorepo, want speed, willing to use new tool
- Choose Poetry if: Need mature ecosystem, conservative team
- **Recommendation:** UV (industry is moving this direction)

**BERTopic vs TF-IDF:**
- Choose BERTopic if: Quality critical, have compute resources
- Choose TF-IDF if: MVP speed critical, simple deployment
- **Recommendation:** Start TF-IDF, add BERTopic flag

**Service Layer vs Fat Controllers:**
- Choose Service Layer if: App will grow, team > 1 person
- Choose Fat Controllers if: Throwaway prototype
- **Recommendation:** Always service layer (takes 1 hour, saves weeks)

**Async vs Sync:**
- Choose Async if: I/O bound workload (API calls, DB queries)
- Choose Sync if: CPU bound workload (data processing)
- **Recommendation:** Async for API, sync for heavy ML tasks

---

## ⚖️ Effort vs Impact

```
High Impact, Low Effort (Do First)
├─ UV package manager         (30 min → 10x faster builds)
├─ PostgreSQL JSONB indexes   (10 min → 100x faster queries)
├─ Ruff linting               (15 min → 100x faster linting)
└─ Docker health checks       (30 min → prevents outages)

High Impact, Medium Effort (Priority 1)
├─ Service layer architecture (3 hours → maintainability)
├─ SQLAlchemy async patterns  (2 hours → prevents issues)
└─ WebSocket connection mgr   (2 hours → enables scaling)

High Impact, High Effort (Phase 2)
├─ BERTopic clustering        (8 hours → 30-50% quality)
├─ GitHub Actions CI/CD       (4 hours → automation)
└─ Observability stack        (8 hours → production insights)

Low Impact, Any Effort (Skip or Defer)
└─ Premature optimizations
```

---

## 🎯 MVP vs Production

| Feature | MVP (Week 1-2) | Production (Month 2-3) |
|---------|----------------|------------------------|
| **Dependency Mgmt** | UV ✅ | UV ✅ |
| **Architecture** | Service Layer ✅ | Service Layer ✅ |
| **Database** | Async + Indexes ✅ | + Read Replicas |
| **Clustering** | TF-IDF ✅ | + BERTopic |
| **Docker** | Health Checks ✅ | + Kubernetes |
| **WebSocket** | In-Memory ✅ | + Redis Pub/Sub |
| **Monitoring** | Logs ✅ | + Prometheus + Grafana |
| **CI/CD** | Manual ✅ | + GitHub Actions |
| **Testing** | 70% coverage ✅ | + 90% coverage |

---

## 🔥 Hot Takes (Opinionated)

**Don't Overthink:**
- ✅ Start with TF-IDF, add BERTopic later
- ✅ In-memory WebSocket for MVP is fine
- ✅ SQLite for tests, PostgreSQL for dev/prod

**Do From Day 1:**
- ✅ UV (saves hours over project lifetime)
- ✅ Service layer (harder to refactor later)
- ✅ Async database (sync → async refactor is painful)
- ✅ Health checks (5 minutes now vs hours debugging later)

**Never Do:**
- ❌ pip without lockfile (non-reproducible)
- ❌ Fat controllers (technical debt from day 1)
- ❌ Blocking I/O in async code (kills performance)
- ❌ No health checks in Docker (broken deploys)

---

## 📚 Further Reading

**When You Need Deep Dive:**
- UV: https://docs.astral.sh/uv/
- BERTopic: https://maartengr.github.io/BERTopic/
- SQLAlchemy 2.0: https://docs.sqlalchemy.org/en/20/
- FastAPI: https://fastapi.tiangolo.com/
- PostgreSQL JSONB: https://www.postgresql.org/docs/16/datatype-json.html

**When You're Stuck:**
- UV Issues: https://github.com/astral-sh/uv/issues
- FastAPI Discord: https://discord.gg/fastapi
- SQLAlchemy Discussions: https://github.com/sqlalchemy/sqlalchemy/discussions

---

**Last Updated:** December 31, 2025  
**Confidence Level:** Based on production experience + 2025 research
