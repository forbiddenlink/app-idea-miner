# Monitoring & Observability Guide

## Overview

App-Idea Miner includes built-in monitoring capabilities for tracking system health, performance, and business metrics.

---

## Monitoring Stack

### Available Tools

| Tool | Purpose | Access URL | Status |
|------|---------|-----------|--------|
| **Flower** | Celery task monitoring | http://localhost:5555 | ✅ Active |
| **Prometheus** | Metrics endpoint | http://localhost:8000/metrics | ✅ Active |
| **Health Check** | Service status | http://localhost:8000/health | ✅ Active |
| **API Docs** | Interactive API testing | http://localhost:8000/docs | ✅ Active |

---

## 1. Flower - Celery Monitoring

### Overview

Flower is a real-time web-based monitoring tool for Celery. It provides visibility into:
- Active tasks and their status
- Worker health and availability
- Task history and results
- Queue lengths and task routing
- Task success/failure rates

### Access

**URL:** http://localhost:5555

**Features:**
- **Dashboard:** Overview of all workers and active tasks
- **Tasks:** Browse task history with filtering
- **Workers:** View worker status, registered tasks, and stats
- **Broker:** Monitor Redis connection and queue status
- **Monitor:** Real-time task execution view

### Key Screens

#### Dashboard
```
Workers: 1 active
- worker@hostname:
  - Status: Online
  - Active: 0 tasks
  - Processed: 234 tasks
  - Succeeded: 230
  - Failed: 4
```

#### Tasks View
- **Filter by:** Name, state (SUCCESS, FAILURE, PENDING, RETRY)
- **Sort by:** Started, received, runtime
- **Actions:** Revoke, terminate tasks

#### Workers View
- **Online workers:** Shows all connected workers
- **Registered tasks:** Lists available task functions
- **Stats:** Success/failure rates, average runtime

### Common Tasks

**Check worker status:**
```bash
# Via Flower UI: Workers tab

# Via command line:
docker-compose exec worker celery -A apps.worker.celery_app inspect active
docker-compose exec worker celery -A apps.worker.celery_app inspect stats
```

**View active tasks:**
```bash
# Via Flower UI: Monitor tab (real-time)

# Via command line:
docker-compose exec worker celery -A apps.worker.celery_app inspect active
```

**Retry failed task:**
```bash
# Via Flower UI: Tasks → Select task → Retry button

# Via API:
curl -X POST http://localhost:5555/api/task/retry/{task_id}
```

**Purge queue (clear all pending tasks):**
```bash
# WARNING: This deletes all pending tasks!
docker-compose exec worker celery -A apps.worker.celery_app purge
```

### Flower Configuration

**docker-compose.yml:**
```yaml
flower:
  image: mher/flower:2.0
  command: celery --broker=redis://redis:6379/0 flower --port=5555
  ports:
    - "5555:5555"
  environment:
    - CELERY_BROKER_URL=redis://redis:6379/0
    - CELERY_RESULT_BACKEND=redis://redis:6379/1
  depends_on:
    - redis
```

### Troubleshooting

**Issue:** Flower shows no workers

```bash
# Check worker is running
docker-compose ps worker

# Check worker logs
docker-compose logs worker

# Restart worker
docker-compose restart worker
```

**Issue:** Tasks stuck in PENDING

```bash
# Check Redis connection
docker-compose exec worker redis-cli -h redis ping

# Check worker can access tasks
docker-compose exec worker celery -A apps.worker.celery_app inspect registered
```

---

## 2. Prometheus Metrics

### Overview

App-Idea Miner exposes Prometheus-compatible metrics at `/metrics` endpoint. These metrics can be scraped by Prometheus and visualized in Grafana.

### Access

**URL:** http://localhost:8000/metrics

**Example Output:**
```prometheus
# HELP app_posts_total Total number of posts ingested
# TYPE app_posts_total gauge
app_posts_total 20

# HELP app_ideas_total Total number of valid ideas extracted
# TYPE app_ideas_total gauge
app_ideas_total 9

# HELP app_clusters_total Total number of opportunity clusters
# TYPE app_clusters_total gauge
app_clusters_total 3

# HELP app_version Application version info
# TYPE app_version gauge
app_version{version="1.0.0"} 1
```

### Available Metrics

#### Business Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `app_posts_total` | Gauge | Total posts in database |
| `app_ideas_total` | Gauge | Total valid ideas extracted |
| `app_clusters_total` | Gauge | Total opportunity clusters |
| `app_avg_sentiment` | Gauge | Average sentiment score (-1 to 1) |
| `app_avg_quality` | Gauge | Average idea quality score (0 to 1) |

#### System Metrics (Future)

| Metric | Type | Description |
|--------|------|-------------|
| `http_requests_total` | Counter | Total HTTP requests by endpoint |
| `http_request_duration_seconds` | Histogram | Request latency by endpoint |
| `database_connections_active` | Gauge | Active DB connections |
| `redis_cache_hits_total` | Counter | Cache hits |
| `redis_cache_misses_total` | Counter | Cache misses |
| `celery_tasks_total` | Counter | Tasks executed by status |
| `celery_task_duration_seconds` | Histogram | Task execution time |

### Testing Metrics

```bash
# View all metrics
curl http://localhost:8000/metrics

# View specific metric (filter with grep)
curl http://localhost:8000/metrics | grep app_posts_total

# Monitor metrics continuously
watch -n 5 'curl -s http://localhost:8000/metrics | grep "^app_"'
```

### Prometheus Integration (Future)

**prometheus.yml:**
```yaml
scrape_configs:
  - job_name: 'app-idea-miner'
    scrape_interval: 15s
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
```

**Docker Compose addition:**
```yaml
prometheus:
  image: prom/prometheus:latest
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
    - prometheus_data:/prometheus
  ports:
    - "9090:9090"
  command:
    - '--config.file=/etc/prometheus/prometheus.yml'
    - '--storage.tsdb.path=/prometheus'
```

### Grafana Dashboard (Future)

**Sample queries for Grafana:**

```promql
# Total Posts Over Time
rate(app_posts_total[5m])

# Ideas Extracted Per Hour
increase(app_ideas_total[1h])

# Clustering Rate
rate(app_clusters_total[30m])

# Sentiment Trend
app_avg_sentiment

# Quality Distribution
histogram_quantile(0.95, app_quality_score_bucket)
```

---

## 3. Health Check Endpoint

### Overview

The `/health` endpoint provides a comprehensive health check of all system components.

### Access

**URL:** http://localhost:8000/health

**Example Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-12-31T22:10:00Z",
  "services": {
    "database": {
      "status": "up",
      "latency_ms": 2.36
    },
    "redis": {
      "status": "up",
      "latency_ms": 0.26
    },
    "worker": {
      "status": "up",
      "active_tasks": 0,
      "registered_workers": 1
    }
  }
}
```

### Health Check Details

**Overall Status:**
- `healthy` - All services operational
- `degraded` - Some services down but core functionality works
- `unhealthy` - Critical services unavailable

**Service-Level Checks:**

**Database:**
- Attempts connection to PostgreSQL
- Measures query latency
- Status: `up` or `down`

**Redis:**
- Pings Redis server
- Measures response time
- Status: `up` or `down`

**Worker:**
- Checks Celery worker availability
- Counts active tasks
- Status: `up` or `down`

### Using Health Checks

**Manual Check:**
```bash
curl http://localhost:8000/health | jq
```

**Monitoring Script:**
```bash
# scripts/health_monitor.sh
#!/bin/bash
while true; do
  STATUS=$(curl -s http://localhost:8000/health | jq -r '.status')

  if [ "$STATUS" != "healthy" ]; then
    echo "[ALERT] System unhealthy: $STATUS"
    # Send alert (email, Slack, PagerDuty, etc.)
  else
    echo "[OK] System healthy"
  fi

  sleep 60
done
```

**Kubernetes Liveness Probe:**
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
  failureThreshold: 3
```

**Docker Healthcheck:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

---

## 4. Application Logs

### Log Locations

**Docker Compose:**
```bash
# View all logs
docker-compose logs

# View specific service
docker-compose logs -f api
docker-compose logs -f worker
docker-compose logs -f postgres

# Last 100 lines
docker-compose logs --tail=100 api

# Follow logs with timestamps
docker-compose logs -f -t api
```

**Log to Files:**
```bash
# Save logs to file
docker-compose logs api > logs/api_$(date +%Y%m%d).log
docker-compose logs worker > logs/worker_$(date +%Y%m%d).log

# Continuous logging
docker-compose logs -f api >> logs/api.log 2>&1 &
```

### Log Levels

| Level | Usage | Example |
|-------|-------|---------|
| **DEBUG** | Development, detailed tracing | "Database query: SELECT * FROM ..." |
| **INFO** | General informational messages | "Cluster created: id=abc123" |
| **WARNING** | Potential issues, non-critical | "Rate limit approaching: 90/100" |
| **ERROR** | Errors that don't crash the app | "Failed to fetch RSS feed: timeout" |
| **CRITICAL** | Severe errors, system down | "Database connection lost" |

### Structured Logging (Future)

**JSON Format:**
```json
{
  "timestamp": "2025-12-31T10:00:00Z",
  "level": "INFO",
  "service": "api",
  "message": "Cluster created",
  "cluster_id": "abc123",
  "idea_count": 5,
  "request_id": "req_xyz789"
}
```

**Implementation:**
```python
# apps/api/app/logging_config.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": "api",
            "message": record.getMessage(),
        }

        # Add extra fields
        if hasattr(record, 'cluster_id'):
            log_data['cluster_id'] = record.cluster_id

        return json.dumps(log_data)

# Apply formatter
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger = logging.getLogger("app")
logger.addHandler(handler)
```

### Log Aggregation (Future)

**ELK Stack (Elasticsearch + Logstash + Kibana):**
```yaml
# docker-compose.monitoring.yml
elasticsearch:
  image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
  environment:
    - discovery.type=single-node
  ports:
    - "9200:9200"

logstash:
  image: docker.elastic.co/logstash/logstash:8.11.0
  volumes:
    - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf

kibana:
  image: docker.elastic.co/kibana/kibana:8.11.0
  ports:
    - "5601:5601"
  environment:
    - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
```

---

## 5. Performance Monitoring

### API Performance

**Response Time Tracking:**
```bash
# Measure endpoint latency
time curl http://localhost:8000/api/v1/clusters

# With detailed timing
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/v1/clusters
```

**curl-format.txt:**
```
    time_namelookup:  %{time_namelookup}s\n
       time_connect:  %{time_connect}s\n
    time_appconnect:  %{time_appconnect}s\n
   time_pretransfer:  %{time_pretransfer}s\n
      time_redirect:  %{time_redirect}s\n
 time_starttransfer:  %{time_starttransfer}s\n
                    ----------\n
         time_total:  %{time_total}s\n
```

**Load Testing with Apache Bench:**
```bash
# 100 requests, 10 concurrent
ab -n 100 -c 10 http://localhost:8000/api/v1/clusters

# With authentication
ab -n 100 -c 10 -H "Authorization: Bearer token" http://localhost:8000/api/v1/clusters
```

### Database Performance

**Query Performance:**
```sql
-- Enable query logging
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log queries > 1s
SELECT pg_reload_conf();

-- View slow queries
SELECT
  pid,
  now() - pg_stat_activity.query_start AS duration,
  query
FROM pg_stat_activity
WHERE state = 'active' AND now() - pg_stat_activity.query_start > interval '5 seconds';

-- Index usage
SELECT
  schemaname,
  tablename,
  indexname,
  idx_scan,
  idx_tup_read,
  idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

**Connection Pool Monitoring:**
```sql
-- Active connections
SELECT count(*) FROM pg_stat_activity WHERE state = 'active';

-- Connection sources
SELECT
  application_name,
  state,
  count(*)
FROM pg_stat_activity
GROUP BY application_name, state;
```

### Redis Performance

**Monitor Redis:**
```bash
# Real-time stats
docker-compose exec redis redis-cli --stat

# Detailed info
docker-compose exec redis redis-cli INFO

# Memory usage
docker-compose exec redis redis-cli INFO memory

# Key space
docker-compose exec redis redis-cli INFO keyspace

# Cache hit rate
docker-compose exec redis redis-cli INFO stats | grep keyspace
```

**Cache Performance:**
```bash
# Monitor cache hits/misses
watch -n 1 'docker-compose exec redis redis-cli INFO stats | grep -E "keyspace_hits|keyspace_misses"'
```

---

## 6. Alerting (Future Setup)

### Alert Rules

**Prometheus Alertmanager:**
```yaml
# prometheus/alerts.yml
groups:
  - name: app-idea-miner
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        annotations:
          summary: "High error rate detected"
          description: "API error rate is {{ $value }} errors/sec"

      - alert: DatabaseDown
        expr: up{job="postgres"} == 0
        for: 1m
        annotations:
          summary: "Database is down"

      - alert: WorkerDown
        expr: celery_workers_online == 0
        for: 5m
        annotations:
          summary: "No Celery workers available"

      - alert: LowCacheHitRate
        expr: redis_cache_hit_rate < 0.5
        for: 10m
        annotations:
          summary: "Cache hit rate below 50%"
```

### Notification Channels

**Slack Integration:**
```yaml
# alertmanager.yml
route:
  receiver: 'slack-notifications'

receivers:
  - name: 'slack-notifications'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#alerts'
        title: 'App-Idea Miner Alert'
        text: '{{ .CommonAnnotations.summary }}'
```

**Email Notifications:**
```yaml
receivers:
  - name: 'email-notifications'
    email_configs:
      - to: 'alerts@yourdomain.com'
        from: 'monitoring@yourdomain.com'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'your_email@gmail.com'
        auth_password: 'your_app_password'
```

---

## 7. Monitoring Best Practices

### What to Monitor

**Golden Signals:**
1. **Latency:** API response times (p50, p95, p99)
2. **Traffic:** Requests per second
3. **Errors:** Error rate (5xx responses)
4. **Saturation:** Resource utilization (CPU, memory, disk)

**Business Metrics:**
- Posts ingested per hour
- Ideas extracted per hour
- Clusters created per day
- Average sentiment score
- Top domains by count

**System Metrics:**
- Database connection pool usage
- Redis memory usage
- Worker task queue length
- API cache hit rate

### Dashboard Layout

**Recommended Grafana Dashboard:**
```
┌─────────────────────────────────────┐
│  OVERVIEW                           │
│  ├─ Total Posts: 20                 │
│  ├─ Total Ideas: 9                  │
│  ├─ Total Clusters: 3               │
│  └─ Avg Sentiment: 0.26             │
├─────────────────────────────────────┤
│  API PERFORMANCE                    │
│  ├─ Request Rate (RPS): [Graph]    │
│  ├─ Response Time (p95): [Graph]   │
│  └─ Error Rate: [Graph]             │
├─────────────────────────────────────┤
│  WORKER STATUS                      │
│  ├─ Active Workers: 1               │
│  ├─ Queue Length: [Graph]           │
│  └─ Task Success Rate: [Graph]      │
├─────────────────────────────────────┤
│  SYSTEM RESOURCES                   │
│  ├─ CPU Usage: [Graph]              │
│  ├─ Memory Usage: [Graph]           │
│  └─ Disk I/O: [Graph]               │
└─────────────────────────────────────┘
```

### Retention Policies

**Logs:** 7 days for INFO, 30 days for WARN/ERROR
**Metrics:** 15s resolution for 7 days, 5m for 90 days, 1h forever
**Traces:** 24 hours for all, 7 days for errors

---

## 8. Troubleshooting with Monitoring

### Common Issues

**High API Latency:**
1. Check database query times (slow query log)
2. Check Redis hit rate (should be > 80%)
3. Check worker queue length (should be < 100)
4. Check system resources (CPU, memory)

**Tasks Not Processing:**
1. Check Flower - are workers online?
2. Check Redis - is broker accessible?
3. Check worker logs - any errors?
4. Check task definitions - are they registered?

**Database Connection Errors:**
1. Check health endpoint - database status
2. Check connection pool - how many active?
3. Check PostgreSQL logs - any crashes?
4. Check network - can API reach database?

---

**This monitoring setup provides comprehensive visibility into App-Idea Miner's health and performance.** 📊
