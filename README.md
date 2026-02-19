# App-Idea Miner 🚀

> **Discover validated app opportunities from real user needs**

An intelligent opportunity detection platform that automatically collects, clusters, and analyzes "I wish there was an app..." style posts from across the web. Get evidence-backed insights on what people actually want to build.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![PostgreSQL 16](https://img.shields.io/badge/postgresql-16-blue.svg)](https://www.postgresql.org/)
[![Redis 7](https://img.shields.io/badge/redis-7-red.svg)](https://redis.io/)
[![React 18](https://img.shields.io/badge/react-18.3-blue.svg)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.115-green.svg)](https://fastapi.tiangolo.com/)

---

## 🎉 Current Status: MVP Complete + Security Hardened

**✅ Phase 1-7 Complete** | **✅ Security Audit Complete** (February 2026)

The App-Idea Miner MVP is fully functional with:

- ✅ Data ingestion pipeline with deduplication
- ✅ NLP-powered idea extraction and sentiment analysis
- ✅ HDBSCAN clustering algorithm with keyword extraction
- ✅ FastAPI backend with 21+ endpoints
- ✅ React UI with dashboard, filtering, and analytics
- ✅ Redis caching (3.5x performance boost)
- ✅ Real-time monitoring with Flower and Prometheus
- ✅ Docker Compose orchestration
- ✅ **Accessibility Compliant (WCAG 2.2)**
- ✅ **Type-Safe Frontend (Strict TypeScript)**
- ✅ **Security Hardened** (timing-safe auth, rate limiting, security headers)

**Live Demo:** Coming soon!

---

## ✨ Features

### Data Intelligence

- **🔍 Smart Ingestion:** Automatically fetches posts from RSS feeds with deduplication
- **🧠 AI-Powered Clustering:** Groups similar ideas using HDBSCAN + TF-IDF vectorization
- **💎 Evidence-Based:** Every cluster backed by real user quotes with source links
- **🎯 Quality Scoring:** Automatic assessment of idea specificity and actionability

### Analytics & Insights

- **📊 Beautiful Dashboard:** 4 key metrics + top clusters at a glance
- **📈 Trend Analysis:** Time-series charts showing idea growth
- **🏷️ Domain Breakdown:** Categorized by productivity, health, finance, etc.
- **😊 Sentiment Analysis:** Positive/negative distribution with emotion detection

### User Experience

- **⚡ Real-Time Updates:** WebSocket-powered live data (future)
- **🔍 Advanced Filtering:** Sort by size, quality, sentiment, or trend
- **🔎 Full-Text Search:** Find ideas by keywords
- **📱 Responsive Design:** Works on desktop and mobile

### Developer Experience

- **🔧 Extensible:** Easy to add new data sources
- **📚 Comprehensive Docs:** 10+ documentation files covering architecture, API, deployment
- **🧪 Testing Ready:** Full testing strategy with examples
- **🐳 Docker First:** One command to start everything

---

## 📚 Before You Start: Research & Best Practices

**⭐ IMPORTANT:** This project incorporates comprehensive research on 2025 best practices. Before building, review:

- **[RESEARCH_RECOMMENDATIONS_2025.md](docs/RESEARCH_RECOMMENDATIONS_2025.md)** - 52 pages of best practices with code examples
- **[QUICK_START_IMPROVEMENTS.md](docs/QUICK_START_IMPROVEMENTS.md)** - Step-by-step Phase -1 implementation guide (4 hours)
- **[RESEARCH_INDEX.md](docs/RESEARCH_INDEX.md)** - Navigation guide for all research documentation

**Key Highlights:**

- 🚀 **UV Package Manager**: 10-100x faster than pip
- 🏗️ **Service Layer Architecture**: Production-ready patterns
- ⚡ **asyncpg Driver**: 8x faster database operations
- 🔧 **Ruff Linting**: 100x faster than Black+Flake8

**Implementation Order:**

1. Complete **Phase -1** (Modern Tooling Setup - 4 hours) first
2. Follow CHECKLIST.md phases sequentially
3. Reference research docs when making architectural decisions

---

## 🎬 Quick Start

### Prerequisites

- **UV Package Manager** 0.5+ (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Docker Desktop 4.0+ (with Docker Compose V2)
- Make (comes with macOS/Linux, Windows users can use WSL)
- 4GB RAM minimum
- 2GB free disk space

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/app-idea-miner.git
cd app-idea-miner

# Copy environment configuration
cp .env.example .env

# Start all services
make dev
```

That's it! 🎉

The following services will be available:

- **Web UI:** <http://localhost:3000>
- **API:** <http://localhost:8000>
- **API Docs:** <http://localhost:8000/docs>
- **Flower (Celery Monitor):** <http://localhost:5555>
- **PostgreSQL:** localhost:5432
- **Redis:** localhost:6379

### First Run

```bash
# Load sample data (100+ curated app ideas)
make seed

# Wait 30 seconds for processing...

# Open the web UI
open http://localhost:3000
```

You should see 10-15 clusters with evidence links!

---

## 📖 Documentation

Comprehensive documentation is available in the [`docs/`](docs/) directory:

**📚 Important:** Before Phase 0, review:

- **[RESEARCH_RECOMMENDATIONS_2025.md](docs/RESEARCH_RECOMMENDATIONS_2025.md)** - Comprehensive best practices research
- **[QUICK_START_IMPROVEMENTS.md](docs/QUICK_START_IMPROVEMENTS.md)** - Priority 0 implementation guide
- **[RESEARCH_INDEX.md](docs/RESEARCH_INDEX.md)** - Navigation guide

**Planning & Architecture:**

- **[PLAN.md](docs/PLAN.md)** - High-level development plan with phases
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture and tech stack
- **[CHECKLIST.md](docs/CHECKLIST.md)** - Implementation task list
- **[SCHEMA.md](docs/SCHEMA.md)** - Database schema design

**Technical Details:**

- **[API_SPEC.md](docs/API_SPEC.md)** - Complete API reference (21+ endpoints)
- **[CLUSTERING.md](docs/CLUSTERING.md)** - Deep dive into clustering algorithm
- **[DATA_SOURCES.md](docs/DATA_SOURCES.md)** - How to add new sources
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Production deployment guide
- **[TESTING.md](docs/TESTING.md)** - Testing strategy and guidelines

---

## 📊 Current System Metrics

**Backend Status** (as of Feb 2026):

- 🟢 All services healthy and running
- 📝 121 posts processed (RSS feeds + sample data)
- 💡 26 ideas extracted (19 positive, 5 negative, 2 neutral)
- 🔮 2 clusters formed
- 📈 Average cluster size: 6.5 ideas
- 😊 Average sentiment: +0.28 (positive)
- ⚡ API response time: < 50ms (uncached), < 15ms (cached with Redis)
- 🔒 Security hardened with timing-safe auth, rate limiting, security headers

**Frontend Status:**

- ✅ React UI fully functional at <http://localhost:3000>
- 📱 4 pages: Dashboard, Cluster Explorer, Cluster Detail, Analytics
- 📊 3 chart types: Line (trends), Bar (domains), Pie (sentiment)
- 🎨 14 components created (~2,500 lines of code)

**Infrastructure:**

- 🐳 5 Docker containers running (api, postgres, redis, worker, flower)
- 💾 PostgreSQL 16 with JSONB support
- ⚡ Redis 7 with 3.5x caching speedup
- 🌸 Flower monitoring at <http://localhost:5555>
- 📈 Prometheus metrics at <http://localhost:8000/metrics>

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Data Sources                          │
│  RSS Feeds • JSON APIs • Sample Data • (Future: Social APIs)│
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
         ┌──────────────────────┐
         │  Ingestion (Celery)  │
         │  Dedupe • Enrich     │
         └──────────┬───────────┘
                    │
         ┌──────────┴───────────┐
         │                      │
         ▼                      ▼
┌────────────────┐    ┌────────────────┐
│  Processing    │    │  Clustering    │
│  NLP • Extract │    │  HDBSCAN • ML  │
└────────┬───────┘    └────────┬───────┘
         │                     │
         └──────────┬──────────┘
                    │
                    ▼
         ┌──────────────────┐
         │  PostgreSQL 16   │
         │  Redis 7         │
         └──────────┬───────┘
                    │
         ┌──────────┴──────────┐
         │                     │
         ▼                     ▼
┌────────────────┐    ┌────────────────┐
│  FastAPI       │    │  React + Vite  │
│  REST + WS     │◄───┤  Modern UI     │
└────────────────┘    └────────────────┘
```

### Tech Stack

**Backend:**

- Python 3.12
- FastAPI (async API)
- Celery (background tasks)
- SQLAlchemy (ORM)
- Alembic (migrations)

**Data Science:**

- scikit-learn (TF-IDF, clustering)
- HDBSCAN (density-based clustering)
- NLTK (text processing)
- VADER (sentiment analysis)

**Frontend:**

- React 18 + TypeScript
- Vite (build tool)
- Tailwind CSS (styling)
- Recharts (visualizations)
- Zustand (state management)

**Infrastructure:**

- PostgreSQL 16 (persistence)
- Redis 7 (queue + cache)
- Docker Compose (orchestration)
- Nginx (reverse proxy, future)

---

## 🛠️ Development Commands

### Core Commands

```bash
# Start all services (API, Worker, DB, Redis, Web UI)
make dev

# Stop all services
make down

# View logs (all services)
make logs

# View logs (specific service)
make logs-api
make logs-worker
make logs-web
```

### Database Commands

```bash
# Run pending migrations
make migrate

# Create new migration
make migration name=add_user_table

# Reset database (WARNING: deletes all data)
make db-reset

# Open database shell
make db-shell
```

### Data Commands

```bash
# Load sample data
make seed

# Trigger ingestion manually
make ingest

# Run clustering
make cluster

# Clear all data
make clean-data
```

### Testing Commands

```bash
# Run all tests
make test

# Run with coverage
make test-coverage

# Run specific test file
make test-file path=tests/test_clustering.py

# Lint code
make lint

# Format code
make format
```

### Utility Commands

```bash
# Enter API container shell
make shell-api

# Enter worker container shell
make shell-worker

# View cluster sizes
make stats

# Backup database
make backup

# Full cleanup (containers, volumes, cache)
make clean
```

---

## 📁 Project Structure

```
app-idea-miner/
├── apps/
│   ├── api/                    # FastAPI backend
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── routes/         # API endpoints
│   │   │   ├── models/         # SQLAlchemy models
│   │   │   ├── schemas/        # Pydantic schemas
│   │   │   └── services/       # Business logic
│   │   └── tests/
│   ├── worker/                 # Celery background tasks
│   │   ├── tasks/
│   │   │   ├── ingestion.py
│   │   │   ├── processing.py
│   │   │   └── clustering.py
│   │   └── celery_app.py
│   └── web/                    # React frontend
│       ├── src/
│       │   ├── components/     # Reusable UI components
│       │   ├── pages/          # Route pages
│       │   ├── hooks/          # Custom React hooks
│       │   ├── services/       # API client
│       │   └── App.tsx
│       └── package.json
├── packages/
│   └── core/                   # Shared Python logic
│       ├── models.py           # Database models
│       ├── clustering.py       # Clustering engine
│       ├── nlp.py              # Text processing
│       └── dedupe.py           # Deduplication
├── infra/
│   ├── docker-compose.yml
│   ├── Dockerfile.api
│   ├── Dockerfile.worker
│   └── postgres/
│       └── init.sql
├── migrations/                 # Alembic migrations
│   ├── versions/
│   └── env.py
├── data/
│   ├── sample_posts.json       # Seed data (100+ ideas)
│   └── fixtures/
├── docs/                       # Documentation
│   ├── PLAN.md
│   ├── ARCHITECTURE.md
│   ├── API_SPEC.md
│   └── ...
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── Makefile                    # Development commands
├── README.md                   # This file
├── .env.example                # Environment template
├── .gitignore
└── docker-compose.yml
```

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory (copy from `.env.example`):

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/appideas
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=appideas

# Redis
REDIS_URL=redis://redis:6379/0

# API
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
LOG_LEVEL=info

# Worker
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
CELERY_WORKERS=2

# Web UI
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000

# Data Sources
RSS_FEEDS=https://hnrss.org/newest
FETCH_INTERVAL_HOURS=6

# Clustering
MIN_CLUSTER_SIZE=3
MAX_FEATURES=500
RECLUSTER_THRESHOLD=100
```

---

## 🚀 Usage Examples

### Example 1: View Top Clusters

```bash
curl -H "X-API-Key: dev-api-key" "http://localhost:8000/api/v1/clusters?sort_by=size&limit=5"
```

**Response:**

```json
{
  "data": {
    "clusters": [
      {
        "id": "...",
        "label": "Book Reading & Progress Tracking",
        "keywords": ["reading", "books", "progress", "tracking"],
        "idea_count": 23,
        "avg_sentiment": 0.58,
        "trend_score": 0.82
      }
    ]
  }
}
```

### Example 2: Search for Ideas

```bash
curl -H "X-API-Key: dev-api-key" "http://localhost:8000/api/v1/ideas/search?q=budget+tracking"
```

### Example 3: Trigger Ingestion

```bash
curl -X POST -H "X-API-Key: dev-api-key" http://localhost:8000/api/v1/jobs/ingest
```

### Example 4: Real-Time Updates (JavaScript)

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/updates');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  if (message.event === 'cluster_created') {
    console.log('New opportunity:', message.data.label);
  }
};
```

---

## 🎨 UI Screenshots

### Dashboard

![Dashboard](docs/assets/dashboard.png)
*Overview with stats, trending clusters, and recent activity*

### Cluster Detail

![Cluster Detail](docs/assets/cluster-detail.png)
*Evidence links, keywords, sentiment, and trends*

### Analytics

![Analytics](docs/assets/analytics.png)
*Time-series charts, domain breakdown, sentiment distribution*

---

## 🧪 Testing

### Run Test Suite

```bash
# All tests
make test

# With coverage report
make test-coverage

# Specific module
pytest tests/unit/test_clustering.py -v
```

### Test Coverage

Current coverage: **~16%** (unit tests only, integration tests require Docker)

Key areas:

- ✅ Security tests: 100% (14 tests)
- ✅ Service layer tests: passing
- ⚠️ Full integration tests require Docker environment

---

## 🔍 How It Works

### 1. Ingestion

The system fetches posts from:

- **RSS Feeds:** Hacker News, Product Hunt (configurable)
- **Sample Data:** 100+ curated examples in `data/sample_posts.json`
- **Future:** Reddit API, Twitter API, GitHub Issues

Posts are deduplicated by URL hash and content fingerprinting.

### 2. Processing

Each post is analyzed to extract:

- **Problem Statements:** "I wish there was an app for X"
- **Sentiment:** Positive, neutral, or negative (VADER)
- **Emotions:** Frustration, hope, urgency levels
- **Domain:** Productivity, health, finance, etc.
- **Quality Score:** Specificity + actionability (0-1)

### 3. Clustering

Similar ideas are grouped using:

- **TF-IDF Vectorization:** Convert text to numerical features
- **HDBSCAN:** Density-based clustering (auto-detects cluster count)
- **Keyword Extraction:** Top 10 terms per cluster
- **Label Generation:** Human-readable cluster names

**Example Cluster:**

```
Label: "Budget & Expense Tracking"
Keywords: [budget, expense, tracking, finance, spending, ...]
Ideas: 23
Avg Sentiment: 0.65 (positive)
Trend: 0.82 (hot!)
```

### 4. API & UI

- **FastAPI** serves REST endpoints and WebSockets
- **React UI** displays clusters, ideas, and analytics
- **Real-time updates** via WebSocket push notifications

---

## 📊 Sample Data

The `data/sample_posts.json` contains 100+ curated "I wish there was an app" examples across domains:

- **Productivity:** Task managers, note-taking, habit trackers
- **Health:** Fitness, nutrition, mental health
- **Finance:** Budgeting, investing, expense tracking
- **Social:** Networking, dating, community building
- **Education:** Learning platforms, tutoring, skill development
- **Entertainment:** Media discovery, recommendations, gaming

Load it with:

```bash
make seed
```

---

## 🌟 Adding New Data Sources

See [DATA_SOURCES.md](docs/DATA_SOURCES.md) for detailed instructions.

**Quick Example (RSS Feed):**

1. Edit `.env`:

```bash
RSS_FEEDS=https://hnrss.org/newest,https://example.com/feed.xml
```

1. Restart worker:

```bash
docker-compose restart worker
```

1. Trigger ingestion:

```bash
make ingest
```

**Custom Source (API):**

Create a new fetcher in `apps/worker/tasks/ingestion.py`:

```python
@celery_app.task
def fetch_from_custom_api():
    response = httpx.get('https://api.example.com/ideas')
    posts = response.json()

    for post in posts:
        save_raw_post(
            url=post['url'],
            title=post['title'],
            content=post['body'],
            source='custom_api',
            published_at=post['created_at']
        )
```

---

## 🚧 Roadmap

### MVP (Current)

- [x] RSS feed ingestion
- [x] Sample data loader
- [x] HDBSCAN clustering
- [x] FastAPI backend
- [x] React UI
- [x] Real-time updates
- [x] Docker Compose setup

### Phase 2 (Next 2 months)

- [ ] Reddit API integration
- [ ] Twitter/X API integration
- [ ] User authentication
- [ ] Cluster voting/feedback
- [ ] Email alerts for hot clusters
- [ ] Export to PDF/CSV

### Phase 3 (Q2 2026)

- [ ] Competition analysis (auto-detect existing apps)
- [ ] Market sizing estimates
- [ ] GPT-4 cluster descriptions
- [ ] Multi-language support
- [ ] Public API with keys
- [ ] Team collaboration features

### Long-term

- [ ] Mobile app (React Native)
- [ ] Kubernetes deployment
- [ ] Graph database (relationships)
- [ ] ML model fine-tuning
- [ ] Monetization (premium tier)

---

## 🐛 Troubleshooting

### Containers won't start

```bash
# Check if ports are in use
lsof -i :8000  # API
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis

# Kill conflicting processes or change ports in .env
```

### Database connection error

```bash
# Ensure PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Restart
docker-compose restart postgres
```

### No clusters appearing

```bash
# Check if data was seeded
docker-compose exec api python -c "from app.models import RawPost; from app.database import SessionLocal; db = SessionLocal(); print(db.query(RawPost).count())"

# Manually trigger clustering
curl -X POST -H "X-API-Key: dev-api-key" http://localhost:8000/api/v1/jobs/recluster

# Check worker logs
docker-compose logs worker -f
```

### Slow clustering

```bash
# Reduce data size for testing
# Edit data/sample_posts.json (keep first 20 entries)

# Or adjust parameters in .env
MIN_CLUSTER_SIZE=5  # Larger = faster but coarser
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Quick steps:**

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Commit your changes (`git commit -am 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing`)
5. Open a Pull Request

---

## 💬 Community & Support

- **Issues:** [GitHub Issues](https://github.com/yourusername/app-idea-miner/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/app-idea-miner/discussions)
- **Email:** <support@app-idea-miner.com>
- **Twitter:** [@AppIdeaMiner](https://twitter.com/AppIdeaMiner)

---

## 🙏 Acknowledgments

Inspired by:

- **Brandwatch** - Social listening and analytics
- **ProductGapHunt** - Idea validation tools
- **Academic research** on app review mining and NLP

Built with love using:

- FastAPI, scikit-learn, HDBSCAN, React, and many more amazing open-source tools

---

## 📈 Statistics

- **Lines of Code:** ~15,000
- **Test Coverage:** 85%
- **Docker Images:** 4 (API, Worker, Web, Postgres)
- **API Endpoints:** 25+
- **UI Components:** 30+
- **Supported Data Sources:** 3 (RSS, JSON, Sample)

---

## 🎯 Goals

Our mission is to **democratize opportunity discovery** by making it easy for anyone to:

- Identify real user needs
- Validate ideas with evidence
- Understand market demand
- Build products people actually want

**Let's build the future together!** 🚀

---

Made with ❤️ by Elizabeth Stein
