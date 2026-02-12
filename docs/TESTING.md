# Testing Strategy & Guide

## Overview

This document outlines the testing approach for App-Idea Miner, including unit tests, integration tests, and end-to-end testing strategies.

---

## Testing Philosophy

**Current Status:** MVP with manual testing
**Target:** 85%+ code coverage with automated tests

### Testing Pyramid

```
           /\
          /  \  E2E Tests (5%)
         /    \  Critical user flows
        /------\
       /        \  Integration Tests (25%)
      /  API     \  Endpoint testing
     /   Tests    \
    /--------------\
   /                \  Unit Tests (70%)
  /  Core Logic     \  Clustering, NLP, Utils
 /                   \
/______________________\
```

---

## Test Environment Setup

### Prerequisites

```bash
# Install development dependencies
pip install pytest pytest-cov pytest-asyncio httpx faker

# Or using UV (recommended)
uv add --dev pytest pytest-cov pytest-asyncio httpx faker
```

### Configuration

**pytest.ini:**
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --cov=packages/core
    --cov=apps/api/app
    --cov-report=term-missing
    --cov-report=html
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
```

### Frontend E2E (Playwright)

From `apps/web`:

```bash
# Install browser once
npm run test:e2e:install

# Run UI E2E suite (mocked API flows)
npm run test:e2e

# Run real backend API contract checks (requires API running)
E2E_REAL_API=1 E2E_API_BASE_URL=http://127.0.0.1:8000 E2E_API_KEY=dev-api-key npm run test:e2e:real-api
```

Notes:
- `test:e2e` includes mocked, deterministic UI flow tests.
- `test:e2e:real-api` validates live API response contracts and input validation.
- Real API checks live in `apps/web/e2e/api-contract.spec.ts` and are skipped unless `E2E_REAL_API=1`.

### Directory Structure

```
tests/
├── conftest.py              # Shared fixtures
├── unit/                    # Unit tests
│   ├── test_clustering.py
│   ├── test_nlp.py
│   ├── test_dedupe.py
│   └── test_utils.py
├── integration/             # Integration tests
│   ├── test_api_clusters.py
│   ├── test_api_ideas.py
│   ├── test_api_analytics.py
│   └── test_database.py
└── e2e/                     # End-to-end tests
    ├── test_ingestion_flow.py
    ├── test_clustering_flow.py
    └── test_ui_flow.py
```

---

## Unit Tests

### Clustering Tests

**File:** `tests/unit/test_clustering.py`

```python
import pytest
import numpy as np
from packages.core.clustering import ClusterEngine

class TestClusterEngine:
    """Test clustering algorithm and keyword extraction"""

    @pytest.fixture
    def sample_texts(self):
        """Sample idea texts for testing"""
        return [
            "I need an app for tracking my daily expenses and budget",
            "Would love a budget tracking tool with AI insights",
            "Why isn't there an expense manager with receipt scanning",
            "I wish there was a reading progress tracker for books",
            "Need an app to track what books I've read this year",
        ]

    @pytest.fixture
    def cluster_engine(self):
        """Create cluster engine instance"""
        return ClusterEngine()

    def test_vectorization(self, cluster_engine, sample_texts):
        """Test TF-IDF vectorization"""
        vectors = cluster_engine.vectorizer.fit_transform(sample_texts)

        assert vectors.shape[0] == len(sample_texts)
        assert vectors.shape[1] > 0  # Should have features
        assert vectors.shape[1] <= 500  # Max features limit

    def test_clustering_groups_similar_ideas(self, cluster_engine, sample_texts):
        """Test that similar ideas are clustered together"""
        result = cluster_engine.cluster_ideas(sample_texts)

        # Should create at least 2 clusters (budget and reading)
        unique_labels = set(result.labels)
        assert len(unique_labels) >= 2

        # First 3 texts (budget) should be in same cluster
        assert result.labels[0] == result.labels[1] == result.labels[2]

        # Last 2 texts (reading) should be in same cluster
        assert result.labels[3] == result.labels[4]

    def test_keyword_extraction(self, cluster_engine, sample_texts):
        """Test keyword extraction from clusters"""
        result = cluster_engine.cluster_ideas(sample_texts)
        keywords = cluster_engine.extract_keywords(result)

        # Should extract keywords for each cluster
        assert len(keywords) > 0

        # Keywords should be relevant
        budget_cluster_keywords = None
        for cluster_id, kw_list in keywords.items():
            if any('budget' in kw or 'expense' in kw for kw, score in kw_list):
                budget_cluster_keywords = [kw for kw, score in kw_list]
                break

        assert budget_cluster_keywords is not None
        assert 'budget' in budget_cluster_keywords or 'expense' in budget_cluster_keywords

    def test_handles_noise_points(self, cluster_engine):
        """Test that outliers are labeled as noise"""
        diverse_texts = [
            "I need a budget app",
            "I need a budget tool",
            "I want a completely unrelated quantum physics calculator",
        ]

        result = cluster_engine.cluster_ideas(diverse_texts)

        # Quantum physics idea should be noise (-1)
        assert -1 in result.labels

    def test_quality_scoring(self, cluster_engine):
        """Test cluster quality score calculation"""
        cluster_data = {
            'idea_count': 10,
            'avg_sentiment': 0.5,
            'avg_quality_score': 0.8,
            'trend_score': 0.7
        }

        score = cluster_engine.score_cluster(cluster_data)

        assert 0 <= score <= 1
        assert isinstance(score, float)
```

### NLP Tests

**File:** `tests/unit/test_nlp.py`

```python
import pytest
from packages.core.nlp import TextProcessor

class TestTextProcessor:
    """Test NLP text processing and sentiment analysis"""

    @pytest.fixture
    def text_processor(self):
        """Create text processor instance"""
        return TextProcessor()

    def test_extract_need_statements(self, text_processor):
        """Test extraction of need statements"""
        text = """
        I love this product! I wish there was an app for tracking my workouts.
        Also, why isn't there a meal planning tool with AI suggestions?
        """

        statements = text_processor.extract_need_statements(text)

        assert len(statements) >= 2
        assert any('workout' in s['statement'].lower() for s in statements)
        assert any('meal planning' in s['statement'].lower() for s in statements)

    def test_sentiment_analysis_positive(self, text_processor):
        """Test sentiment analysis for positive text"""
        text = "I love this idea! It would be amazing and super helpful!"

        result = text_processor.analyze_sentiment(text)

        assert result['label'] == 'positive'
        assert result['score'] > 0
        assert 0 <= result['positive'] <= 1

    def test_sentiment_analysis_negative(self, text_processor):
        """Test sentiment analysis for negative text"""
        text = "This is terrible. I hate how frustrating this is. Awful experience."

        result = text_processor.analyze_sentiment(text)

        assert result['label'] == 'negative'
        assert result['score'] < 0
        assert result['emotions']['frustration'] > 0.5

    def test_sentiment_analysis_neutral(self, text_processor):
        """Test sentiment analysis for neutral text"""
        text = "I need an app for tracking expenses."

        result = text_processor.analyze_sentiment(text)

        assert result['label'] in ['neutral', 'positive']
        assert -0.1 <= result['score'] <= 0.1

    def test_quality_score_calculation(self, text_processor):
        """Test quality scoring"""
        high_quality = "I need a mobile app for tracking daily water intake with reminders and progress charts"
        low_quality = "app"

        score_high = text_processor.calculate_quality_score(high_quality)
        score_low = text_processor.calculate_quality_score(low_quality)

        assert score_high > score_low
        assert 0 <= score_high <= 1
        assert 0 <= score_low <= 1
```

### Deduplication Tests

**File:** `tests/unit/test_dedupe.py`

```python
import pytest
from packages.core.dedupe import Deduplicator

class TestDeduplicator:
    """Test URL and title deduplication logic"""

    @pytest.fixture
    def deduplicator(self):
        """Create deduplicator instance"""
        return Deduplicator()

    def test_url_canonicalization(self, deduplicator):
        """Test URL normalization"""
        url1 = "https://example.com/post?utm_source=twitter&id=123"
        url2 = "https://example.com/post?id=123"

        hash1 = deduplicator.generate_url_hash(url1)
        hash2 = deduplicator.generate_url_hash(url2)

        # Should generate same hash (tracking params removed)
        assert hash1 == hash2

    def test_url_hash_uniqueness(self, deduplicator):
        """Test that different URLs get different hashes"""
        url1 = "https://example.com/post1"
        url2 = "https://example.com/post2"

        hash1 = deduplicator.generate_url_hash(url1)
        hash2 = deduplicator.generate_url_hash(url2)

        assert hash1 != hash2

    def test_duplicate_title_detection(self, deduplicator):
        """Test fuzzy title matching"""
        title1 = "I wish there was an app for budget tracking"
        title2 = "I wish there was an app for budget tracking!"  # Different punctuation
        title3 = "I need a completely different app"

        # Similar titles should be duplicates
        assert deduplicator.is_duplicate_title(title1, title2, threshold=0.85)

        # Different titles should not be duplicates
        assert not deduplicator.is_duplicate_title(title1, title3, threshold=0.85)

    def test_threshold_sensitivity(self, deduplicator):
        """Test threshold affects matching"""
        title1 = "I need a budget app"
        title2 = "I need a budget application"

        # High threshold: should match
        assert deduplicator.is_duplicate_title(title1, title2, threshold=0.7)

        # Very high threshold: might not match
        # (depends on exact similarity ratio)
```

---

## Integration Tests

### API Tests

**File:** `tests/integration/test_api_clusters.py`

```python
import pytest
from fastapi.testclient import TestClient
from apps.api.app.main import app

@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)

class TestClustersAPI:
    """Test cluster API endpoints"""

    def test_list_clusters(self, client):
        """Test GET /api/v1/clusters"""
        response = client.get("/api/v1/clusters")

        assert response.status_code == 200
        data = response.json()
        assert 'clusters' in data
        assert isinstance(data['clusters'], list)

    def test_list_clusters_pagination(self, client):
        """Test pagination parameters"""
        response = client.get("/api/v1/clusters?limit=5&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert len(data['clusters']) <= 5
        assert 'pagination' in data

    def test_list_clusters_sorting(self, client):
        """Test sorting by different fields"""
        response = client.get("/api/v1/clusters?sort_by=size&order=desc")

        assert response.status_code == 200
        clusters = response.json()['clusters']

        # Verify descending order by size
        if len(clusters) > 1:
            assert clusters[0]['idea_count'] >= clusters[-1]['idea_count']

    def test_get_cluster_by_id(self, client):
        """Test GET /api/v1/clusters/{id}"""
        # First get list to get a valid ID
        list_response = client.get("/api/v1/clusters")
        clusters = list_response.json()['clusters']

        if clusters:
            cluster_id = clusters[0]['id']
            response = client.get(f"/api/v1/clusters/{cluster_id}")

            assert response.status_code == 200
            data = response.json()
            assert data['id'] == cluster_id
            assert 'keywords' in data
            assert 'evidence' in data

    def test_get_cluster_invalid_id(self, client):
        """Test 404 for invalid cluster ID"""
        response = client.get("/api/v1/clusters/invalid-uuid-12345")

        assert response.status_code in [404, 422]  # 404 or validation error
```

**File:** `tests/integration/test_api_analytics.py`

```python
import pytest
from fastapi.testclient import TestClient
from apps.api.app.main import app

@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)

class TestAnalyticsAPI:
    """Test analytics API endpoints"""

    def test_analytics_summary(self, client):
        """Test GET /api/v1/analytics/summary"""
        response = client.get("/api/v1/analytics/summary")

        assert response.status_code == 200
        data = response.json()

        assert 'overview' in data
        assert 'total_posts' in data['overview']
        assert 'total_ideas' in data['overview']
        assert 'total_clusters' in data['overview']

        # Verify data types
        assert isinstance(data['overview']['total_posts'], int)
        assert isinstance(data['overview']['avg_sentiment'], (int, float))

    def test_analytics_trends(self, client):
        """Test GET /api/v1/analytics/trends"""
        response = client.get("/api/v1/analytics/trends?metric=ideas&interval=day")

        assert response.status_code == 200
        data = response.json()

        assert 'data_points' in data
        assert isinstance(data['data_points'], list)

        # Verify data point structure
        if data['data_points']:
            point = data['data_points'][0]
            assert 'date' in point
            assert 'value' in point

    def test_analytics_domains(self, client):
        """Test GET /api/v1/analytics/domains"""
        response = client.get("/api/v1/analytics/domains")

        assert response.status_code == 200
        data = response.json()

        assert 'domains' in data
        assert isinstance(data['domains'], list)

        # Verify domain structure
        if data['domains']:
            domain = data['domains'][0]
            assert 'name' in domain
            assert 'idea_count' in domain
```

---

## End-to-End Tests

### Complete Pipeline Test

**File:** `tests/e2e/test_ingestion_flow.py`

```python
import pytest
import time
from fastapi.testclient import TestClient
from apps.api.app.main import app

@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)

@pytest.mark.e2e
@pytest.mark.slow
class TestIngestionFlow:
    """Test complete ingestion pipeline"""

    def test_seed_to_clusters_pipeline(self, client):
        """Test: Seed data → Process → Cluster → View in API"""

        # Step 1: Seed data
        seed_response = client.post("/api/v1/posts/seed")
        assert seed_response.status_code == 200

        # Step 2: Wait for processing
        time.sleep(5)

        # Step 3: Verify posts created
        posts_response = client.get("/api/v1/posts/stats/summary")
        assert posts_response.status_code == 200
        posts_data = posts_response.json()
        assert posts_data['total'] > 0

        # Step 4: Trigger clustering
        cluster_response = client.post("/api/v1/jobs/recluster")
        assert cluster_response.status_code in [200, 201]

        # Step 5: Wait for clustering
        time.sleep(10)

        # Step 6: Verify clusters created
        clusters_response = client.get("/api/v1/clusters")
        assert clusters_response.status_code == 200
        clusters_data = clusters_response.json()
        assert len(clusters_data['clusters']) > 0

        # Step 7: Verify cluster has evidence
        cluster_id = clusters_data['clusters'][0]['id']
        detail_response = client.get(f"/api/v1/clusters/{cluster_id}")
        assert detail_response.status_code == 200
        detail_data = detail_response.json()
        assert 'evidence' in detail_data
        assert len(detail_data['evidence']) > 0
```

---

## Running Tests

### Run All Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov

# Run specific test file
pytest tests/unit/test_clustering.py

# Run specific test
pytest tests/unit/test_clustering.py::TestClusterEngine::test_vectorization

# Run by marker
pytest -m unit        # Only unit tests
pytest -m integration # Only integration tests
pytest -m e2e         # Only end-to-end tests
```

### Coverage Report

```bash
# Generate HTML coverage report
pytest --cov --cov-report=html

# Open report
open htmlcov/index.html  # macOS
```

### Continuous Integration

**GitHub Actions workflow example:**

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install uv
          uv sync

      - name: Run tests
        run: |
          pytest --cov --cov-report=xml
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost/test_db
          REDIS_URL: redis://localhost:6379/0

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

---

## Manual Testing

### Smoke Tests

**Run after each deployment:**

1. **Health Check:**
   ```bash
   curl http://localhost:8000/health
   # Expect: {"status": "healthy"}
   ```

2. **List Clusters:**
   ```bash
   curl http://localhost:8000/api/v1/clusters | jq
   # Expect: JSON with clusters array
   ```

3. **UI Access:**
   - Open http://localhost:3000
   - Verify dashboard loads
   - Check no console errors

### User Acceptance Testing

**Test user flows:**

1. **View Dashboard:**
   - Open http://localhost:3000
   - Verify stats cards show numbers
   - Verify cluster grid displays
   - Click cluster → detail page loads

2. **Filter Clusters:**
   - Navigate to /clusters
   - Change sort order
   - Adjust min size filter
   - Verify results update

3. **Search Ideas:**
   - Navigate to /ideas (Coming Soon)
   - Enter search term
   - Verify results

4. **View Analytics:**
   - Navigate to /analytics
   - Verify charts render
   - Toggle metric (ideas/clusters)
   - Verify chart updates

---

## Test Data

### Sample Data

**Use existing:** `data/sample_posts.json` (20 posts)

**Generate additional:**

```python
# tests/fixtures/generate_test_data.py
from faker import Faker
import json

fake = Faker()

def generate_test_posts(count=100):
    """Generate test posts for testing"""
    posts = []
    domains = ['productivity', 'health', 'finance', 'social', 'entertainment']

    for i in range(count):
        post = {
            "url": f"https://example.com/post/{i}",
            "title": f"I wish there was an app for {fake.bs()}",
            "content": fake.paragraph(nb_sentences=5),
            "source": fake.random_element(['hackernews', 'reddit', 'twitter']),
            "author": fake.user_name(),
            "published_at": fake.date_time_this_year().isoformat(),
            "metadata": {
                "domain": fake.random_element(domains),
                "upvotes": fake.random_int(1, 100)
            }
        }
        posts.append(post)

    return posts

if __name__ == '__main__':
    posts = generate_test_posts(100)
    with open('data/test_posts_large.json', 'w') as f:
        json.dump(posts, f, indent=2)
```

---

## Coverage Goals

**Current:** 0% (manual testing only)
**Target:** 85%+

**Priority by module:**

| Module | Target Coverage | Priority |
|--------|----------------|----------|
| `packages/core/clustering.py` | 90%+ | HIGH |
| `packages/core/nlp.py` | 85%+ | HIGH |
| `packages/core/dedupe.py` | 90%+ | HIGH |
| `apps/api/app/routes/*.py` | 80%+ | MEDIUM |
| `apps/worker/tasks/*.py` | 70%+ | MEDIUM |
| `packages/core/utils.py` | 75%+ | LOW |

---

## Performance Testing

### Load Testing (Future)

**Using Locust:**

```python
# locustfile.py
from locust import HttpUser, task, between

class AppIdeaMinerUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def list_clusters(self):
        self.client.get("/api/v1/clusters")

    @task(2)
    def get_analytics(self):
        self.client.get("/api/v1/analytics/summary")

    @task(1)
    def get_cluster_detail(self):
        # Get random cluster
        response = self.client.get("/api/v1/clusters?limit=1")
        if response.status_code == 200:
            clusters = response.json()['clusters']
            if clusters:
                cluster_id = clusters[0]['id']
                self.client.get(f"/api/v1/clusters/{cluster_id}")

# Run: locust -f locustfile.py --host=http://localhost:8000
```

---

## Known Issues & Limitations

1. **No Database Transactions:** Tests don't rollback changes (use test database)
2. **Async Tests:** Requires pytest-asyncio plugin
3. **Celery Tasks:** Harder to test (mock task calls)
4. **UI Tests:** No Playwright/Cypress setup yet

---

## Future Improvements

1. **Add Playwright for UI testing**
2. **Increase coverage to 90%+**
3. **Add mutation testing (Mutmut)**
4. **Performance benchmarks**
5. **Visual regression testing**
6. **Load testing with Locust**

---

**This testing strategy ensures reliability while keeping the MVP focused on core functionality.** 🧪
