# Bwenge OS Makefile

.PHONY: help build up down logs clean test lint format

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build all Docker images
	docker-compose build

up: ## Start all services
	docker-compose up -d

up-dev: ## Start all services in development mode with volume mounts
	docker-compose -f docker-compose.dev.yml up -d

down: ## Stop all services
	docker-compose down

down-dev: ## Stop development services
	docker-compose -f docker-compose.dev.yml down

logs: ## Show logs for all services
	docker-compose logs -f

clean: ## Clean up Docker resources
	docker-compose down -v
	docker system prune -f

test: ## Run all tests
	@echo "Running unit tests..."
	python -m pytest tests/unit/ -v
	@echo "Running integration tests..."
	python -m pytest tests/integration/ -v

test-unit: ## Run unit tests only
	python -m pytest tests/unit/ -v --cov=services --cov=libs

test-integration: ## Run integration tests only
	python -m pytest tests/integration/ -v

test-e2e: ## Run end-to-end tests
	python -m pytest tests/integration/test_end_to_end.py -v

test-performance: ## Run performance tests
	k6 run tests/performance/load-test.js

lint: ## Run linting
	@echo "Running linting..."
	black --check .
	isort --check-only .
	flake8 .
	mypy services/ libs/ --ignore-missing-imports

format: ## Format code
	@echo "Formatting code..."
	black .
	isort .

security-scan: ## Run security scans
	@echo "Running security scans..."
	bandit -r services/ libs/
	safety check

dev-setup: ## Set up development environment
	cp .env.example .env
	@echo "Please edit .env file with your configuration"

migrate: ## Run database migrations
	docker-compose exec postgres psql -U bwenge -d bwenge -f /docker-entrypoint-initdb.d/init-db.sql

reset-db: ## Reset database
	docker-compose down postgres
	docker volume rm bwenge_postgres_data
	docker-compose up -d postgres
	sleep 5
	make migrate

health: ## Check service health
	@echo "Checking service health..."
	@curl -s http://localhost:8000/health || echo "API Gateway: DOWN"
	@curl -s http://localhost:8001/health || echo "Auth Service: DOWN"
	@curl -s http://localhost:8002/health || echo "Ingest Service: DOWN"
	@curl -s http://localhost:8003/health || echo "Persona Service: DOWN"
	@curl -s http://localhost:8004/health || echo "Chat Service: DOWN"
	@curl -s http://localhost:8005/health || echo "3D Service: DOWN"
	@curl -s http://localhost:8006/health || echo "Analytics Service: DOWN"
	@curl -s http://localhost:8007/health || echo "Payments Service: DOWN"

install-deps: ## Install development dependencies
	pip install -r requirements.txt
	pip install pytest pytest-asyncio testcontainers black isort flake8 mypy

docs: ## Generate API documentation
	@echo "Generating API documentation..."
	python -c "from docs.api_documentation import generate_api_documentation; print(generate_api_documentation())" > docs/API.md

tracing-up: ## Start Jaeger tracing infrastructure
	docker-compose -f deploy/jaeger/docker-compose.jaeger.yml up -d

tracing-down: ## Stop Jaeger tracing infrastructure
	docker-compose -f deploy/jaeger/docker-compose.jaeger.yml down

smoke-test: ## Run smoke tests against deployment
	python scripts/smoke-tests.py --url http://localhost:8000

smoke-test-comprehensive: ## Run comprehensive smoke tests
	python scripts/smoke-tests.py --url http://localhost:8000 --comprehensive

backup: ## Backup database
	docker-compose exec postgres pg_dump -U bwenge bwenge > backup_$(shell date +%Y%m%d_%H%M%S).sql

restore: ## Restore database from backup (usage: make restore BACKUP=backup_file.sql)
	docker-compose exec -T postgres psql -U bwenge -d bwenge < $(BACKUP)

ci-setup: ## Setup CI environment
	@echo "Setting up CI environment..."
	cp .env.example .env.ci
	echo "OPENAI_API_KEY=test-key" >> .env.ci
	echo "JWT_SECRET=test-jwt-secret-for-ci" >> .env.ci
