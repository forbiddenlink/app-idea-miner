# API Specification

## Base URL
- **Local Development:** `http://localhost:8000`
- **Production:** `https://api.app-idea-miner.com` (future)

## API Version
Current: `v1`

All endpoints are prefixed with `/api/v1` unless otherwise noted.

---

## Authentication

**MVP:** No authentication required (local development)

**Future:** JWT Bearer tokens
```http
Authorization: Bearer <token>
```

---

## Response Format

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "metadata": {
    "timestamp": "2025-12-31T10:00:00Z",
    "request_id": "req_abc123"
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid cluster ID format",
    "details": {
      "field": "cluster_id",
      "issue": "Must be a valid UUID"
    }
  },
  "metadata": {
    "timestamp": "2025-12-31T10:00:00Z",
    "request_id": "req_abc123"
  }
}
```

### HTTP Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `404` - Not Found
- `429` - Rate Limit Exceeded
- `500` - Internal Server Error

---

## Endpoints

## 1. Clusters

### GET `/api/v1/clusters`

**Description:** List all clusters with pagination and sorting

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sort_by` | string | `size` | Sort field: `size`, `sentiment`, `trend`, `quality`, `created_at` |
| `order` | string | `desc` | Sort order: `asc`, `desc` |
| `limit` | integer | `20` | Results per page (max 100) |
| `offset` | integer | `0` | Pagination offset |
| `domain` | string | - | Filter by domain |
| `min_size` | integer | - | Minimum idea count |

**Example Request:**
```bash
GET /api/v1/clusters?sort_by=trend&limit=10&min_size=5
```

**Example Response:**
```json
{
  "success": true,
  "data": {
    "clusters": [
      {
        "id": "770e8400-e29b-41d4-a716-446655440002",
        "label": "Book Reading & Progress Tracking",
        "description": "Apps for tracking reading habits, book progress, and getting recommendations",
        "keywords": ["reading", "books", "progress", "tracking", "habits"],
        "idea_count": 23,
        "avg_sentiment": 0.58,
        "quality_score": 0.76,
        "trend_score": 0.82,
        "created_at": "2025-12-30T14:00:00Z",
        "updated_at": "2025-12-31T09:10:00Z"
      }
    ],
    "pagination": {
      "total": 45,
      "limit": 10,
      "offset": 0,
      "has_more": true
    }
  }
}
```

---

### GET `/api/v1/clusters/{cluster_id}`

**Description:** Get detailed information about a specific cluster including evidence

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `cluster_id` | UUID | Yes | Cluster identifier |

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `include_evidence` | boolean | `true` | Include representative ideas |
| `evidence_limit` | integer | `5` | Number of evidence items (max 20) |

**Example Request:**
```bash
GET /api/v1/clusters/770e8400-e29b-41d4-a716-446655440002?evidence_limit=3
```

**Example Response:**
```json
{
  "success": true,
  "data": {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "label": "Book Reading & Progress Tracking",
    "description": "Apps for tracking reading habits...",
    "keywords": ["reading", "books", "progress", "tracking", "habits"],
    "idea_count": 23,
    "avg_sentiment": 0.58,
    "quality_score": 0.76,
    "trend_score": 0.82,
    "evidence": [
      {
        "id": "660e8400-e29b-41d4-a716-446655440001",
        "problem_statement": "track book reading habits with progress analytics",
        "sentiment": "positive",
        "sentiment_score": 0.65,
        "quality_score": 0.82,
        "source_url": "https://news.ycombinator.com/item?id=123456",
        "published_at": "2025-12-25T10:30:00Z",
        "similarity_score": 0.89
      }
    ],
    "timeline": [
      {
        "date": "2025-12-25",
        "ideas_added": 3
      },
      {
        "date": "2025-12-26",
        "ideas_added": 5
      }
    ],
    "created_at": "2025-12-30T14:00:00Z",
    "updated_at": "2025-12-31T09:10:00Z"
  }
}
```

---

### GET `/api/v1/clusters/{cluster_id}/similar`

**Description:** Find clusters similar to the given cluster

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `cluster_id` | UUID | Yes | Source cluster identifier |

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | `5` | Number of similar clusters |

**Example Response:**
```json
{
  "success": true,
  "data": {
    "similar_clusters": [
      {
        "id": "880e8400-e29b-41d4-a716-446655440003",
        "label": "Personal Library Management",
        "similarity_score": 0.78,
        "idea_count": 15,
        "keywords": ["library", "books", "organize", "catalog"]
      }
    ]
  }
}
```

---

### GET `/api/v1/clusters/trending`

**Description:** Get currently trending clusters (high recent growth)

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | `10` | Number of clusters |
| `days` | integer | `7` | Time window for trend calculation |

**Example Response:**
```json
{
  "success": true,
  "data": {
    "trending": [
      {
        "id": "990e8400-e29b-41d4-a716-446655440004",
        "label": "AI-Powered Budgeting",
        "idea_count": 18,
        "trend_score": 0.95,
        "growth_rate": 2.3,
        "keywords": ["AI", "budget", "finance", "automation"]
      }
    ]
  }
}
```

---

## 2. Ideas

### GET `/api/v1/ideas`

**Description:** Browse all idea candidates with filtering

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cluster_id` | UUID | - | Filter by cluster |
| `sentiment` | string | - | Filter: `positive`, `neutral`, `negative` |
| `domain` | string | - | Filter by domain |
| `min_quality` | float | - | Minimum quality score (0-1) |
| `limit` | integer | `20` | Results per page |
| `offset` | integer | `0` | Pagination offset |

**Example Request:**
```bash
GET /api/v1/ideas?sentiment=positive&min_quality=0.7&limit=10
```

**Example Response:**
```json
{
  "success": true,
  "data": {
    "ideas": [
      {
        "id": "660e8400-e29b-41d4-a716-446655440001",
        "problem_statement": "track book reading habits with progress analytics",
        "sentiment": "positive",
        "sentiment_score": 0.65,
        "quality_score": 0.82,
        "domain": "productivity",
        "features_mentioned": ["progress tracking", "analytics"],
        "cluster": {
          "id": "770e8400-e29b-41d4-a716-446655440002",
          "label": "Book Reading & Progress Tracking"
        },
        "source": {
          "url": "https://news.ycombinator.com/item?id=123456",
          "title": "I wish there was an app...",
          "published_at": "2025-12-25T10:30:00Z"
        },
        "extracted_at": "2025-12-31T09:05:00Z"
      }
    ],
    "pagination": {
      "total": 342,
      "limit": 10,
      "offset": 0,
      "has_more": true
    }
  }
}
```

---

### GET `/api/v1/ideas/{idea_id}`

**Description:** Get detailed information about a specific idea

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `idea_id` | UUID | Yes | Idea identifier |

**Example Response:**
```json
{
  "success": true,
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "problem_statement": "track book reading habits with progress analytics",
    "context": "I read a lot but forget what I've read. I wish there was an app...",
    "sentiment": "positive",
    "sentiment_score": 0.65,
    "emotions": {
      "hope": 0.7,
      "frustration": 0.3
    },
    "domain": "productivity",
    "features_mentioned": ["progress tracking", "analytics", "recommendations"],
    "quality_score": 0.82,
    "cluster": {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "label": "Book Reading & Progress Tracking"
    },
    "source": {
      "url": "https://news.ycombinator.com/item?id=123456",
      "title": "I wish there was an app for tracking my book reading habits",
      "author": "johndoe",
      "published_at": "2025-12-25T10:30:00Z"
    },
    "extracted_at": "2025-12-31T09:05:00Z"
  }
}
```

---

### GET `/api/v1/ideas/search`

**Description:** Full-text search across all ideas

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `q` | string | Yes | Search query |
| `limit` | integer | `20` | Results per page |
| `offset` | integer | `0` | Pagination offset |

**Example Request:**
```bash
GET /api/v1/ideas/search?q=budget%20tracking&limit=10
```

**Example Response:**
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": "...",
        "problem_statement": "automated budget tracking with AI insights",
        "relevance_score": 0.95,
        "sentiment": "positive",
        "cluster": { ... }
      }
    ],
    "query": "budget tracking",
    "total_results": 42
  }
}
```

---

## 3. Analytics

### GET `/api/v1/analytics/summary`

**Description:** Dashboard summary statistics

**Example Request:**
```bash
GET /api/v1/analytics/summary
```

**Example Response:**
```json
{
  "success": true,
  "data": {
    "overview": {
      "total_posts": 1243,
      "total_ideas": 856,
      "total_clusters": 47,
      "avg_cluster_size": 18.2,
      "avg_sentiment": 0.42
    },
    "trending": {
      "hot_clusters": 3,
      "new_ideas_today": 23,
      "new_clusters_this_week": 2
    },
    "sentiment_distribution": {
      "positive": 456,
      "neutral": 298,
      "negative": 102
    },
    "top_domains": [
      {"domain": "productivity", "count": 234},
      {"domain": "health", "count": 156},
      {"domain": "finance", "count": 132}
    ],
    "updated_at": "2025-12-31T10:00:00Z"
  }
}
```

---

### GET `/api/v1/analytics/trends`

**Description:** Time-series data for charts

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `metric` | string | `ideas` | Metric: `ideas`, `clusters`, `posts` |
| `interval` | string | `day` | Interval: `hour`, `day`, `week`, `month` |
| `start_date` | string | `-30d` | Start date (ISO 8601 or relative) |
| `end_date` | string | `now` | End date |

**Example Request:**
```bash
GET /api/v1/analytics/trends?metric=ideas&interval=day&start_date=2025-12-01
```

**Example Response:**
```json
{
  "success": true,
  "data": {
    "metric": "ideas",
    "interval": "day",
    "data_points": [
      {"date": "2025-12-01", "value": 23, "avg_sentiment": 0.45},
      {"date": "2025-12-02", "value": 31, "avg_sentiment": 0.52},
      {"date": "2025-12-03", "value": 28, "avg_sentiment": 0.48}
    ]
  }
}
```

---

### GET `/api/v1/analytics/domains`

**Description:** Domain/category breakdown

**Example Response:**
```json
{
  "success": true,
  "data": {
    "domains": [
      {
        "name": "productivity",
        "idea_count": 234,
        "cluster_count": 12,
        "avg_sentiment": 0.56,
        "percentage": 27.3
      },
      {
        "name": "health",
        "idea_count": 156,
        "cluster_count": 8,
        "avg_sentiment": 0.61,
        "percentage": 18.2
      }
    ],
    "total_ideas": 856
  }
}
```

---

## 4. Jobs (Background Tasks)

### POST `/api/v1/jobs/ingest`

**Description:** Trigger a new ingestion job

**Request Body:**
```json
{
  "source": "hackernews",  // Optional: specific source
  "force": false            // Force re-fetch even if recent
}
```

**Example Response:**
```json
{
  "success": true,
  "data": {
    "job_id": "job_abc123",
    "status": "queued",
    "estimated_duration": "30s",
    "created_at": "2025-12-31T10:00:00Z"
  }
}
```

---

### GET `/api/v1/jobs/{job_id}`

**Description:** Check job status

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `job_id` | string | Yes | Job identifier |

**Example Response:**
```json
{
  "success": true,
  "data": {
    "job_id": "job_abc123",
    "status": "completed",  // queued, running, completed, failed
    "progress": {
      "current": 100,
      "total": 100,
      "percentage": 100
    },
    "result": {
      "posts_fetched": 45,
      "posts_new": 12,
      "ideas_extracted": 18
    },
    "started_at": "2025-12-31T10:00:00Z",
    "completed_at": "2025-12-31T10:00:32Z",
    "duration_seconds": 32
  }
}
```

---

### POST `/api/v1/jobs/recluster`

**Description:** Trigger re-clustering of all ideas

**Request Body:**
```json
{
  "force": true,           // Re-cluster even if recent
  "min_cluster_size": 3    // Optional: override default
}
```

**Example Response:**
```json
{
  "success": true,
  "data": {
    "job_id": "job_xyz789",
    "status": "queued",
    "estimated_duration": "60s"
  }
}
```

---

### POST `/api/v1/posts/seed`

**Description:** Load sample data from `data/sample_posts.json`

**Example Response:**
```json
{
  "success": true,
  "data": {
    "posts_loaded": 100,
    "ideas_extracted": 87,
    "clusters_created": 12,
    "duration_seconds": 15
  }
}
```

---

## 5. Health & System

### GET `/health`

**Description:** System health check

**Example Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-12-31T10:00:00Z",
  "services": {
    "database": {
      "status": "up",
      "latency_ms": 2
    },
    "redis": {
      "status": "up",
      "latency_ms": 1
    },
    "worker": {
      "status": "up",
      "active_tasks": 2,
      "queue_length": 5
    }
  }
}
```

---

### GET `/metrics`

**Description:** Prometheus-style metrics

**Example Response:**
```
# HELP api_requests_total Total API requests
# TYPE api_requests_total counter
api_requests_total{method="GET",endpoint="/api/v1/clusters",status="200"} 1234

# HELP api_request_duration_seconds API request duration
# TYPE api_request_duration_seconds histogram
api_request_duration_seconds_bucket{le="0.1"} 950
api_request_duration_seconds_bucket{le="0.5"} 1200

# HELP clusters_total Total number of clusters
# TYPE clusters_total gauge
clusters_total 47

# HELP ideas_total Total number of ideas
# TYPE ideas_total gauge
ideas_total 856
```

---

## 6. WebSocket (Real-Time Updates)

### WebSocket Endpoint: `ws://localhost:8000/ws/updates`

**Description:** Real-time event stream for dashboard updates

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/updates');

ws.onopen = () => {
  console.log('Connected to updates stream');
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Event:', message);
};
```

**Event Types:**

**1. New Cluster Created**
```json
{
  "event": "cluster_created",
  "data": {
    "cluster_id": "...",
    "label": "New Opportunity",
    "idea_count": 5,
    "timestamp": "2025-12-31T10:00:00Z"
  }
}
```

**2. Cluster Updated**
```json
{
  "event": "cluster_updated",
  "data": {
    "cluster_id": "...",
    "changes": {
      "idea_count": 25,
      "trend_score": 0.85
    },
    "timestamp": "2025-12-31T10:00:00Z"
  }
}
```

**3. New Ideas Added**
```json
{
  "event": "ideas_added",
  "data": {
    "count": 3,
    "sentiment_breakdown": {
      "positive": 2,
      "neutral": 1
    },
    "timestamp": "2025-12-31T10:00:00Z"
  }
}
```

**4. Ingestion Job Status**
```json
{
  "event": "job_status",
  "data": {
    "job_id": "job_abc123",
    "status": "completed",
    "result": { ... }
  }
}
```

---

## Rate Limiting

**MVP Limits:**
- 100 requests per minute per IP
- 10 concurrent WebSocket connections per IP

**Headers:**
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1735639200
```

**Rate Limit Exceeded Response:**
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please try again in 30 seconds.",
    "retry_after": 30
  }
}
```

---

## CORS Configuration

**Allowed Origins (MVP):**
- `http://localhost:3000` (Vite dev server)
- `http://localhost:5173` (Alternate Vite port)

**Allowed Methods:**
- `GET`, `POST`, `PUT`, `DELETE`, `OPTIONS`

**Allowed Headers:**
- `Content-Type`, `Authorization`, `X-Requested-With`

---

## API Documentation

**Interactive Docs:** `http://localhost:8000/docs` (Swagger UI)

**OpenAPI JSON:** `http://localhost:8000/openapi.json`

**ReDoc:** `http://localhost:8000/redoc` (Alternative docs UI)

---

## Error Codes Reference

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request parameters |
| `NOT_FOUND` | 404 | Resource not found |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |
| `SERVICE_UNAVAILABLE` | 503 | Database or Redis down |

---

## Example Client (TypeScript)

```typescript
// src/services/api.ts
import axios from 'axios';

const client = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for error handling
client.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 429) {
      // Handle rate limiting
      const retryAfter = error.response.headers['x-ratelimit-reset'];
      // Show notification
    }
    throw error;
  }
);

// Cluster service
export const clusterService = {
  getAll: (params?: ClusterQueryParams) =>
    client.get<ClusterListResponse>('/clusters', { params }),
  
  getById: (id: string, includeEvidence = true) =>
    client.get<ClusterDetailResponse>(`/clusters/${id}`, {
      params: { include_evidence: includeEvidence },
    }),
  
  getTrending: (limit = 10) =>
    client.get<TrendingResponse>('/clusters/trending', {
      params: { limit },
    }),
};

// WebSocket helper
export function connectToUpdates(onMessage: (data: any) => void) {
  const ws = new WebSocket('ws://localhost:8000/ws/updates');
  
  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    onMessage(message);
  };
  
  return ws;
}
```

---

This API is designed to be **intuitive, well-documented, and performant**. Every endpoint includes examples and clear response formats. 🚀
