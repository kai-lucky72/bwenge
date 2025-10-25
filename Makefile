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

test: ## Run tests
	@echo "Running tests..."
	# Add test commands here

lint: ## Run linting
	@echo "Running linting..."
	# Add linting commands here

format: ## Format code
	@echo "Formatting code..."
	# Add formatting commands here

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
	pip install -r requirements-dev.txt


backup: ## Backup database
	docker-compose exec postgres pg_dump -U bwenge bwenge > backup_$(shell date +%Y%m%d_%H%M%S).sql


restore: ## Restore database from backup (usage: make restore BACKUP=backup_file.sql)
	docker-compose exec -T postgres psql -U bwenge -d bwenge < $(BACKUP)

