.PHONY: help dev down logs logs-api logs-worker logs-web migrate migration db-reset db-shell seed ingest cluster check test test-coverage test-file lint format typecheck-baseline security python-security web-security web-test web-build shell-api shell-worker stats backup clean clean-data

help: ## Show this help message
	@echo "App-Idea Miner - Development Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Core Commands
dev: ## Start all services (docker-compose up + seed data)
	docker-compose up -d
	@echo "Waiting for services to be healthy..."
	@sleep 10
	@echo "Services started! 🚀"
	@echo "  - API: http://localhost:8000"
	@echo "  - API Docs: http://localhost:8000/docs"
	@echo "  - Flower: http://localhost:5555"
	@echo "  - PostgreSQL: localhost:5432"
	@echo "  - Redis: localhost:6379"

down: ## Stop all services
	docker-compose down

logs: ## View logs (all services)
	docker-compose logs -f

logs-api: ## View API logs
	docker-compose logs -f api

logs-worker: ## View worker logs
	docker-compose logs -f worker

logs-web: ## View web UI logs (when implemented)
	@echo "Web UI not yet implemented"

# Database Commands
migrate: ## Run pending migrations
	docker-compose exec api uv run alembic upgrade head

migration: ## Create new migration (usage: make migration name=add_user_table)
	docker-compose exec api uv run alembic revision --autogenerate -m "$(name)"

db-reset: ## Reset database (WARNING: deletes all data)
	@echo "⚠️  WARNING: This will delete all data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		docker-compose up -d postgres redis; \
		sleep 5; \
		make migrate; \
	fi

db-shell: ## Open database shell
	docker-compose exec postgres psql -U postgres -d appideas

# Data Commands
seed: ## Load sample data
	docker-compose exec api sh -lc 'curl -sS -X POST -H "X-API-Key: $${API_KEY:-dev-api-key}" http://localhost:8000/api/v1/posts/seed'

ingest: ## Trigger ingestion manually
	docker-compose exec api sh -lc 'curl -sS -X POST -H "X-API-Key: $${API_KEY:-dev-api-key}" http://localhost:8000/api/v1/jobs/ingest'

cluster: ## Run clustering
	docker-compose exec api sh -lc 'curl -sS -X POST -H "X-API-Key: $${API_KEY:-dev-api-key}" http://localhost:8000/api/v1/jobs/recluster'

# Testing Commands
check: lint test web-test web-build ## Run backend lint/tests plus web tests/build

test: ## Run all tests
	uv run pytest

test-coverage: ## Run tests with coverage report
	uv run pytest --cov=apps --cov=packages --cov-report=html --cov-report=term-missing

test-file: ## Run specific test file (usage: make test-file path=tests/test_clustering.py)
	uv run pytest $(path) -v

# Code Quality Commands
lint: ## Lint code with Ruff
	uv run ruff check apps packages

format: ## Format code with Ruff
	uv run ruff format apps packages

typecheck-baseline: ## Run Python typecheck baseline (currently advisory)
	uv run mypy apps packages

security: python-security web-security ## Run Python audit plus high-severity web audit

python-security: ## Audit Python dependencies
	uv run pip-audit

web-security: ## Audit web dependencies at high severity
	cd apps/web && pnpm audit --audit-level high

web-test: ## Run web unit tests
	cd apps/web && pnpm test

web-build: ## Build web app
	cd apps/web && pnpm run build

# Utility Commands
shell-api: ## Enter API container shell
	docker-compose exec api /bin/bash

shell-worker: ## Enter worker container shell
	docker-compose exec worker /bin/bash

stats: ## View cluster sizes
	docker-compose exec postgres psql -U postgres -d appideas -c "SELECT label, idea_count FROM clusters ORDER BY idea_count DESC LIMIT 10;"

backup: ## Backup database
	@mkdir -p backups
	docker-compose exec postgres pg_dump -U postgres appideas > backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "Backup created in backups/"

clean: ## Full cleanup (containers, volumes, cache)
	docker-compose down -v
	rm -rf .venv __pycache__ .pytest_cache .coverage htmlcov
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

clean-data: ## Clear all data (keep containers)
	docker-compose exec postgres psql -U postgres -d appideas -c "TRUNCATE raw_posts, idea_candidates, clusters, cluster_memberships RESTART IDENTITY CASCADE;"
	@echo "Data cleared!"
