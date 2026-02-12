# Deployment Guide

## Overview

This guide covers deploying App-Idea Miner from local development to production environments.

---

## Table of Contents

1. [Local Development](#local-development)
2. [Production Deployment](#production-deployment)
3. [Environment Variables](#environment-variables)
4. [Database Setup](#database-setup)
5. [Monitoring & Maintenance](#monitoring--maintenance)
6. [Troubleshooting](#troubleshooting)

---

## Local Development

### Prerequisites

- **Docker Desktop** 4.0+ (includes Docker Compose V2)
- **UV Package Manager** 0.5+ (optional, for local Python dev)
- **Node.js** 18+ (for frontend development)
- **Make** (comes with macOS/Linux)
- **4GB RAM** minimum
- **2GB disk space**

### Quick Start

```bash
# Clone repository
git clone https://github.com/yourusername/app-idea-miner.git
cd app-idea-miner

# Copy environment file
cp .env.example .env

# Start all services
make dev

# Load sample data
make seed
```

### Access Points

| Service | URL | Description |
|---------|-----|-------------|
| **Web UI** | http://localhost:3000 | React frontend |
| **API** | http://localhost:8000 | FastAPI backend |
| **API Docs** | http://localhost:8000/docs | Swagger UI |
| **Flower** | http://localhost:5555 | Celery monitoring |
| **PostgreSQL** | localhost:5432 | Database |
| **Redis** | localhost:6379 | Cache & queue |

### Development Workflow

```bash
# Start services
make dev

# View logs
make logs

# Run migrations
make migrate

# Enter API shell
make shell-api

# Run tests
make test

# Stop services
make down

# Full cleanup
make clean
```

---

## Production Deployment

### Option 1: Docker Compose (Single Server)

**Recommended for:** Small to medium deployments, up to 1000 users

#### Setup Steps

1. **Provision Server:**
   - Ubuntu 22.04 LTS
   - 8GB RAM minimum
   - 50GB disk space
   - Open ports: 80, 443, 22

2. **Install Docker:**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   ```

3. **Clone Repository:**
   ```bash
   git clone https://github.com/yourusername/app-idea-miner.git
   cd app-idea-miner
   ```

4. **Configure Environment:**
   ```bash
   cp .env.example .env.production
   nano .env.production
   ```

   **Key changes for production:**
   ```bash
   # Use strong passwords
   POSTGRES_PASSWORD=your_strong_password

   # Production URLs
   API_HOST=api.yourdomain.com
   VITE_API_URL=https://api.yourdomain.com

   # Logging
   LOG_LEVEL=info

   # CORS
   CORS_ORIGINS=https://yourdomain.com
   ```

5. **Build and Start:**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

6. **Run Migrations:**
   ```bash
   docker-compose exec api alembic upgrade head
   ```

7. **Setup Nginx Reverse Proxy:**
   ```nginx
   # /etc/nginx/sites-available/app-idea-miner
   server {
       listen 80;
       server_name yourdomain.com;

       location / {
           proxy_pass http://localhost:3000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }

   server {
       listen 80;
       server_name api.yourdomain.com;

       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

8. **Setup SSL (Let's Encrypt):**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com -d api.yourdomain.com
   ```

9. **Setup Automatic Backups:**
   ```bash
   # Add to crontab
   0 2 * * * /opt/app-idea-miner/scripts/backup.sh
   ```

### Option 2: Kubernetes (Scalable)

**Recommended for:** Large deployments, multi-region, high availability

#### Prerequisites

- Kubernetes cluster (EKS, GKE, AKS)
- kubectl configured
- Helm 3.x

#### Deployment Steps

1. **Create Namespace:**
   ```bash
   kubectl create namespace app-idea-miner
   ```

2. **Deploy PostgreSQL:**
   ```bash
   helm install postgres bitnami/postgresql \
     --namespace app-idea-miner \
     --set postgresqlPassword=your_password \
     --set postgresqlDatabase=appideas \
     --set persistence.size=50Gi
   ```

3. **Deploy Redis:**
   ```bash
   helm install redis bitnami/redis \
     --namespace app-idea-miner \
     --set auth.password=your_password \
     --set master.persistence.size=10Gi
   ```

4. **Create ConfigMap:**
   ```yaml
   # k8s/configmap.yaml
   apiVersion: v1
   kind: ConfigMap
   metadata:
     name: app-config
     namespace: app-idea-miner
   data:
     DATABASE_URL: postgresql://postgres:password@postgres:5432/appideas
     REDIS_URL: redis://:password@redis-master:6379/0
     LOG_LEVEL: info
   ```

5. **Deploy API:**
   ```yaml
   # k8s/api-deployment.yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: api
     namespace: app-idea-miner
   spec:
     replicas: 3
     selector:
       matchLabels:
         app: api
     template:
       metadata:
         labels:
           app: api
       spec:
         containers:
         - name: api
           image: your-registry/app-idea-miner-api:latest
           ports:
           - containerPort: 8000
           envFrom:
           - configMapRef:
               name: app-config
           resources:
             requests:
               cpu: 500m
               memory: 1Gi
             limits:
               cpu: 2000m
               memory: 4Gi
           livenessProbe:
             httpGet:
               path: /health
               port: 8000
             initialDelaySeconds: 30
             periodSeconds: 10
           readinessProbe:
             httpGet:
               path: /health
               port: 8000
             initialDelaySeconds: 10
             periodSeconds: 5
   ```

6. **Deploy Worker:**
   ```yaml
   # k8s/worker-deployment.yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: worker
     namespace: app-idea-miner
   spec:
     replicas: 2
     selector:
       matchLabels:
         app: worker
     template:
       metadata:
         labels:
           app: worker
       spec:
         containers:
         - name: worker
           image: your-registry/app-idea-miner-worker:latest
           envFrom:
           - configMapRef:
               name: app-config
           resources:
             requests:
               cpu: 1000m
               memory: 2Gi
             limits:
               cpu: 4000m
               memory: 8Gi
   ```

7. **Create Ingress:**
   ```yaml
   # k8s/ingress.yaml
   apiVersion: networking.k8s.io/v1
   kind: Ingress
   metadata:
     name: app-ingress
     namespace: app-idea-miner
     annotations:
       cert-manager.io/cluster-issuer: letsencrypt-prod
       nginx.ingress.kubernetes.io/ssl-redirect: "true"
   spec:
     ingressClassName: nginx
     tls:
     - hosts:
       - api.yourdomain.com
       secretName: api-tls
     rules:
     - host: api.yourdomain.com
       http:
         paths:
         - path: /
           pathType: Prefix
           backend:
             service:
               name: api
               port:
                 number: 8000
   ```

8. **Apply Manifests:**
   ```bash
   kubectl apply -f k8s/
   ```

9. **Verify Deployment:**
   ```bash
   kubectl get pods -n app-idea-miner
   kubectl logs -f deployment/api -n app-idea-miner
   ```

---

## Environment Variables

### Required Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname
POSTGRES_USER=postgres
POSTGRES_PASSWORD=strong_password_here
POSTGRES_DB=appideas

# Redis
REDIS_URL=redis://host:6379/0

# API
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
SECRET_KEY=your_secret_key_here  # Generate: openssl rand -hex 32
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Worker
CELERY_BROKER_URL=redis://host:6379/0
CELERY_RESULT_BACKEND=redis://host:6379/1
CELERY_WORKERS=2

# Web UI
VITE_API_URL=https://api.yourdomain.com
VITE_WS_URL=wss://api.yourdomain.com

# Logging
LOG_LEVEL=info  # debug, info, warning, error
LOG_FORMAT=json  # json or text

# Data Sources
RSS_FEEDS=https://hnrss.org/newest
FETCH_INTERVAL_HOURS=6

# Clustering
MIN_CLUSTER_SIZE=3
MAX_FEATURES=500
RECLUSTER_THRESHOLD=100
MIN_QUALITY_SCORE=0.3

# Performance
CACHE_TTL=300  # 5 minutes
RATE_LIMIT=100  # requests per minute
```

### Optional Variables

```bash
# Authentication (future)
JWT_SECRET_KEY=your_jwt_secret
JWT_ALGORITHM=HS256
JWT_EXPIRATION=3600

# Monitoring
SENTRY_DSN=https://your-sentry-dsn
PROMETHEUS_ENABLED=true

# Email (future)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

---

## Database Setup

### Initial Setup

```bash
# Create database (if not using Docker)
psql -U postgres
CREATE DATABASE appideas;
\q

# Run migrations
docker-compose exec api alembic upgrade head

# Verify tables
docker-compose exec postgres psql -U postgres -d appideas -c "\dt"
```

### Migrations

```bash
# Create new migration
docker-compose exec api alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec api alembic upgrade head

# Rollback
docker-compose exec api alembic downgrade -1

# View history
docker-compose exec api alembic history
```

### Backup & Restore

**Backup:**
```bash
# Backup to file
docker-compose exec postgres pg_dump -U postgres appideas > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup with Docker
docker-compose exec postgres pg_dump -U postgres -F c -b -v -f /tmp/backup.dump appideas
docker cp app-idea-miner-postgres:/tmp/backup.dump ./backup.dump
```

**Restore:**
```bash
# Restore from SQL file
docker-compose exec -T postgres psql -U postgres appideas < backup.sql

# Restore from dump file
docker cp backup.dump app-idea-miner-postgres:/tmp/backup.dump
docker-compose exec postgres pg_restore -U postgres -d appideas -v /tmp/backup.dump
```

**Automated Backups:**
```bash
# scripts/backup.sh
#!/bin/bash
BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="appideas_$TIMESTAMP.sql"

docker-compose exec -T postgres pg_dump -U postgres appideas > "$BACKUP_DIR/$FILENAME"

# Compress
gzip "$BACKUP_DIR/$FILENAME"

# Delete backups older than 7 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "Backup completed: $FILENAME.gz"
```

### Database Maintenance

```bash
# Vacuum database
docker-compose exec postgres psql -U postgres -d appideas -c "VACUUM ANALYZE;"

# Check database size
docker-compose exec postgres psql -U postgres -d appideas -c "SELECT pg_size_pretty(pg_database_size('appideas'));"

# Check table sizes
docker-compose exec postgres psql -U postgres -d appideas -c "
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

---

## Monitoring & Maintenance

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Detailed health with services
curl http://localhost:8000/health | jq
```

### Prometheus Metrics

```bash
# View metrics
curl http://localhost:8000/metrics

# Expected metrics:
# - app_posts_total
# - app_ideas_total
# - app_clusters_total
# - app_version
```

### Flower (Celery Monitoring)

Access: http://localhost:5555

**Features:**
- View active tasks
- Monitor worker status
- Check queue lengths
- View task history
- Retry failed tasks

### Log Management

**View logs:**
```bash
# All services
make logs

# Specific service
docker-compose logs -f api
docker-compose logs -f worker
docker-compose logs -f postgres

# Last 100 lines
docker-compose logs --tail=100 api
```

**Log to file:**
```bash
docker-compose logs -f api > logs/api_$(date +%Y%m%d).log
```

### Alerting (Future)

**Setup with Prometheus + Alertmanager:**

```yaml
# prometheus/alert.rules.yml
groups:
- name: app-idea-miner
  rules:
  - alert: HighErrorRate
    expr: rate(api_requests_total{status=~"5.."}[5m]) > 0.1
    for: 5m
    annotations:
      summary: "High error rate detected"

  - alert: WorkerDown
    expr: up{job="worker"} == 0
    for: 5m
    annotations:
      summary: "Worker is down"

  - alert: DatabaseConnectionFailure
    expr: app_database_up == 0
    for: 1m
    annotations:
      summary: "Cannot connect to database"
```

---

## Troubleshooting

### Services Won't Start

**Issue:** Ports already in use

```bash
# Check what's using ports
lsof -i :8000  # API
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :3000  # Web UI

# Kill process or change ports in .env
```

**Issue:** Out of memory

```bash
# Check Docker memory
docker stats

# Increase Docker memory limit in Docker Desktop settings
# Or add resource limits in docker-compose.yml
```

### Database Connection Errors

**Issue:** Connection refused

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

**Issue:** Authentication failed

```bash
# Verify credentials in .env
cat .env | grep POSTGRES

# Reset password
docker-compose exec postgres psql -U postgres
ALTER USER postgres PASSWORD 'new_password';
\q
```

### Worker Not Processing Tasks

**Issue:** Celery worker not connected

```bash
# Check worker logs
docker-compose logs worker

# Check Redis connection
docker-compose exec worker redis-cli -h redis ping

# Restart worker
docker-compose restart worker
```

**Issue:** Tasks stuck in queue

```bash
# Check queue length
docker-compose exec worker celery -A apps.worker.celery_app inspect active

# Purge queue (WARNING: deletes all tasks)
docker-compose exec worker celery -A apps.worker.celery_app purge
```

### API Performance Issues

**Issue:** Slow responses

```bash
# Check API logs for slow queries
docker-compose logs api | grep "slow query"

# Check database performance
docker-compose exec postgres psql -U postgres -d appideas -c "
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity
WHERE state = 'active' AND now() - pg_stat_activity.query_start > interval '5 seconds';
"

# Enable query logging (temporary)
docker-compose exec postgres psql -U postgres -c "ALTER SYSTEM SET log_min_duration_statement = 1000;"
docker-compose restart postgres
```

**Issue:** High memory usage

```bash
# Check container memory
docker stats app-idea-miner-api

# Check Python memory profile
docker-compose exec api python -m memory_profiler app/main.py
```

### Frontend Build Errors

**Issue:** Vite build fails

```bash
# Clear node_modules
cd apps/web
rm -rf node_modules package-lock.json
npm install

# Clear Vite cache
rm -rf .vite

# Rebuild
npm run build
```

**Issue:** TypeScript errors

```bash
# Check TypeScript config
cd apps/web
npx tsc --noEmit

# Fix common issues
npm install --save-dev @types/node @types/react @types/react-dom
```

---

## Production Checklist

### Before Deployment

- [ ] Update all passwords to strong values
- [ ] Configure CORS for production domain
- [ ] Setup SSL/TLS certificates
- [ ] Configure environment variables
- [ ] Test database migrations
- [ ] Setup automated backups
- [ ] Configure logging (JSON format)
- [ ] Setup monitoring (Prometheus + Grafana)
- [ ] Configure alerting rules
- [ ] Test API endpoints
- [ ] Test UI on production URL
- [ ] Setup DNS records
- [ ] Configure firewall rules
- [ ] Document access credentials (in secrets manager)

### After Deployment

- [ ] Verify all services running
- [ ] Check health endpoints
- [ ] Monitor logs for errors
- [ ] Test critical user flows
- [ ] Check metrics dashboard
- [ ] Verify backups working
- [ ] Test alerting (trigger test alert)
- [ ] Document deployment date and version
- [ ] Update team on access URLs
- [ ] Schedule maintenance windows

---

## Performance Optimization

### Database Optimization

```sql
-- Add indexes for frequently queried columns
CREATE INDEX CONCURRENTLY idx_raw_posts_processed ON raw_posts(is_processed) WHERE is_processed = false;
CREATE INDEX CONCURRENTLY idx_clusters_trend ON clusters(trend_score DESC);
CREATE INDEX CONCURRENTLY idx_ideas_quality ON idea_candidates(quality_score DESC);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM clusters ORDER BY trend_score DESC LIMIT 10;

-- Enable query plan caching
ALTER SYSTEM SET plan_cache_mode = 'force_generic_plan';
```

### Redis Optimization

```bash
# Enable persistence
docker-compose exec redis redis-cli CONFIG SET save "900 1 300 10 60 10000"

# Check memory usage
docker-compose exec redis redis-cli INFO memory

# Set max memory and eviction policy
docker-compose exec redis redis-cli CONFIG SET maxmemory 2gb
docker-compose exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### API Optimization

```python
# Use connection pooling (already configured)
# Add response compression
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Enable HTTP/2
# Use Uvicorn with --http h11 flag

# Add caching headers
from fastapi import Response
@app.get("/api/v1/clusters")
async def list_clusters(response: Response):
    response.headers["Cache-Control"] = "public, max-age=300"
    ...
```

---

## Security Best Practices

1. **Use strong passwords** for all services
2. **Enable SSL/TLS** for all connections
3. **Restrict database access** to API only
4. **Use secrets manager** (AWS Secrets Manager, HashiCorp Vault)
5. **Enable rate limiting** on API
6. **Setup firewall rules** (only expose 80, 443)
7. **Regular security updates** for Docker images
8. **Monitor for vulnerabilities** (Snyk, Trivy)
9. **Audit logs** for suspicious activity
10. **Backup encryption** for sensitive data

---

**This deployment guide ensures App-Idea Miner runs reliably in production.** 🚀
