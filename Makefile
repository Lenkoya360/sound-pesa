# Sound Pesa Platform Makefile
# Provides convenient commands for development, testing, and deployment

.PHONY: help setup dev build start stop restart clean logs test deploy health

# Default target
help: ## Show this help message
	@echo "Sound Pesa Platform - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Environment Variables:"
	@echo "  ENV=development|staging|production (default: development)"
	@echo "  COMPOSE_FILE=docker-compose.dev.yml (auto-selected based on ENV)"

# Variables
ENV ?= development
ifeq ($(ENV),production)
	COMPOSE_FILE = docker-compose.yml
else ifeq ($(ENV),staging)
	COMPOSE_FILE = docker-compose.prod.yml
else
	COMPOSE_FILE = docker-compose.dev.yml
endif

DOCKER_COMPOSE = docker compose -f $(COMPOSE_FILE)

# Setup and Installation
setup: ## Set up the development environment
	@echo "🚀 Setting up Sound Pesa development environment..."
	@chmod +x scripts/*.sh
	@./scripts/dev-setup.sh

setup-env: ## Create environment files from examples
	@echo "📝 Creating environment files..."
	@cp -n .env.example .env || true
	@cp -n packages/api/.env.example packages/api/.env || true
	@cp -n packages/web/.env.example packages/web/.env.local || true
	@cp -n packages/app/.env.example packages/app/.env || true
	@echo "✅ Environment files created. Please update them with your configuration."

# Development Commands
dev: ## Start development environment
	@echo "🔧 Starting development environment..."
	$(DOCKER_COMPOSE) up -d
	@echo "✅ Development environment started!"
	@echo "📱 Web App: http://localhost:3000"
	@echo "🔧 API: http://localhost:8000"
	@echo "📊 Grafana: http://localhost:3001"

dev-build: ## Build and start development environment
	@echo "🔨 Building and starting development environment..."
	$(DOCKER_COMPOSE) up -d --build

dev-logs: ## Show development logs
	$(DOCKER_COMPOSE) logs -f

dev-shell: ## Open shell in API container
	$(DOCKER_COMPOSE) exec api bash

# Service Management
start: ## Start all services
	@echo "▶️ Starting Sound Pesa services..."
	$(DOCKER_COMPOSE) start

stop: ## Stop all services
	@echo "⏹️ Stopping Sound Pesa services..."
	$(DOCKER_COMPOSE) stop

restart: ## Restart all services
	@echo "🔄 Restarting Sound Pesa services..."
	$(DOCKER_COMPOSE) restart

status: ## Show service status
	@echo "📊 Service Status:"
	$(DOCKER_COMPOSE) ps

# Individual Service Commands
api: ## Start only API service
	$(DOCKER_COMPOSE) up -d postgres redis vault api

web: ## Start only web application
	$(DOCKER_COMPOSE) up -d web

app: ## Start only mobile app development server
	$(DOCKER_COMPOSE) up -d app

app-local: ## Start mobile app locally (without Docker)
	@echo "📱 Starting mobile app locally..."
	@cd packages/app && npx expo start

db: ## Start only database services
	$(DOCKER_COMPOSE) up -d postgres redis vault

blockchain: ## Start blockchain nodes
	$(DOCKER_COMPOSE) -f docker-compose.blockchain.yml up -d

monitoring: ## Start monitoring services
	$(DOCKER_COMPOSE) up -d prometheus grafana loki promtail alertmanager

# Database Commands
db-migrate: ## Run database migrations
	@echo "🗄️ Running database migrations..."
	$(DOCKER_COMPOSE) exec api python manage.py migrate

db-seed: ## Seed database with test data
	@echo "🌱 Seeding database with test data..."
	@chmod +x scripts/db-seed.sh
	@./scripts/db-seed.sh development

db-reset: ## Reset database (WARNING: Destroys all data)
	@echo "⚠️ This will destroy all database data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(DOCKER_COMPOSE) stop api; \
		$(DOCKER_COMPOSE) exec postgres psql -U soundpesa -c "DROP DATABASE IF EXISTS soundpesa;"; \
		$(DOCKER_COMPOSE) exec postgres psql -U soundpesa -c "CREATE DATABASE soundpesa;"; \
		$(DOCKER_COMPOSE) start api; \
		sleep 5; \
		$(DOCKER_COMPOSE) exec api python manage.py migrate; \
		echo "✅ Database reset complete"; \
	else \
		echo "❌ Database reset cancelled"; \
	fi

db-shell: ## Open database shell
	$(DOCKER_COMPOSE) exec postgres psql -U soundpesa -d soundpesa

db-backup: ## Create database backup
	@echo "💾 Creating database backup..."
	@mkdir -p backups
	$(DOCKER_COMPOSE) exec postgres pg_dump -U soundpesa soundpesa > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Backup created in backups/ directory"

# Build Commands
build: ## Build all Docker images
	@echo "🔨 Building Docker images..."
	$(DOCKER_COMPOSE) build

build-api: ## Build only API image
	$(DOCKER_COMPOSE) build api

build-web: ## Build only web image
	$(DOCKER_COMPOSE) build web

build-app: ## Build only mobile app image
	$(DOCKER_COMPOSE) build app

build-nginx: ## Build only nginx image
	$(DOCKER_COMPOSE) build nginx

# Testing Commands
test: ## Run all tests
	@echo "🧪 Running all tests..."
	@./scripts/run-tests.sh

test-api: ## Run API tests
	@echo "🧪 Running API tests..."
	$(DOCKER_COMPOSE) exec api python manage.py test

test-web: ## Run web application tests
	@echo "🧪 Running web tests..."
	$(DOCKER_COMPOSE) exec web npm test

test-app: ## Run mobile app tests
	@echo "🧪 Running mobile app tests..."
	$(DOCKER_COMPOSE) exec app npm test

test-integration: ## Run integration tests
	@echo "🧪 Running integration tests..."
	@chmod +x scripts/integration-tests.sh
	@./scripts/integration-tests.sh

# Health and Monitoring
health: ## Check system health
	@echo "🏥 Checking system health..."
	@chmod +x scripts/health-check.sh
	@./scripts/health-check.sh

health-report: ## Generate detailed health report
	@echo "📋 Generating health report..."
	@chmod +x scripts/health-check.sh
	@./scripts/health-check.sh --report

logs: ## Show logs for all services
	$(DOCKER_COMPOSE) logs -f

logs-api: ## Show API logs
	$(DOCKER_COMPOSE) logs -f api

logs-web: ## Show web application logs
	$(DOCKER_COMPOSE) logs -f web

logs-app: ## Show mobile app logs
	$(DOCKER_COMPOSE) logs -f app

logs-db: ## Show database logs
	$(DOCKER_COMPOSE) logs -f postgres

logs-nginx: ## Show nginx logs
	$(DOCKER_COMPOSE) logs -f nginx

logs-celery: ## Show celery worker logs
	$(DOCKER_COMPOSE) logs -f celery-worker

# Utility Commands
clean: ## Clean up Docker resources
	@echo "🧹 Cleaning up Docker resources..."
	$(DOCKER_COMPOSE) down --remove-orphans
	docker image prune -f
	docker volume prune -f
	docker network prune -f
	@echo "✅ Cleanup complete"

clean-all: ## Clean up everything including volumes (WARNING: Destroys all data)
	@echo "⚠️ This will destroy all data including databases!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(DOCKER_COMPOSE) down -v --remove-orphans; \
		docker image prune -a -f; \
		docker volume prune -f; \
		docker network prune -f; \
		echo "✅ Complete cleanup finished"; \
	else \
		echo "❌ Cleanup cancelled"; \
	fi

ps: ## Show running containers
	$(DOCKER_COMPOSE) ps

top: ## Show container resource usage
	docker stats --no-stream

# Configuration Management
validate-config: ## Validate environment configuration
	@echo "✅ Validating configuration for $(ENV) environment..."
	@chmod +x scripts/validate-config.sh
	@./scripts/validate-config.sh $(ENV)

validate-config-report: ## Generate configuration validation report
	@echo "📋 Generating configuration validation report..."
	@chmod +x scripts/validate-config.sh
	@./scripts/validate-config.sh $(ENV) --report

# Deployment Commands
deploy-staging: ## Deploy to staging environment
	@echo "🚀 Deploying to staging..."
	@chmod +x scripts/deploy-staging.sh
	@./scripts/deploy-staging.sh

deploy-prod: ## Deploy to production environment
	@echo "🚀 Deploying to production..."
	@chmod +x scripts/deploy-prod.sh
	@./scripts/deploy-prod.sh

# Development Helpers
shell-api: ## Open Django shell
	$(DOCKER_COMPOSE) exec api python manage.py shell

shell-db: ## Open database shell
	$(DOCKER_COMPOSE) exec postgres psql -U soundpesa -d soundpesa

shell-redis: ## Open Redis CLI
	$(DOCKER_COMPOSE) exec redis redis-cli

create-superuser: ## Create Django superuser
	$(DOCKER_COMPOSE) exec api python manage.py createsuperuser

collect-static: ## Collect static files
	$(DOCKER_COMPOSE) exec api python manage.py collectstatic --noinput

# Package Management
install-api: ## Install API dependencies
	$(DOCKER_COMPOSE) exec api pip install -r requirements.txt

install-web: ## Install web dependencies
	$(DOCKER_COMPOSE) exec web npm install

install-app: ## Install mobile app dependencies
	$(DOCKER_COMPOSE) exec app npm install

install-shared: ## Install shared package dependencies
	$(DOCKER_COMPOSE) exec web sh -c "cd ../shared && npm install && npm run build"

# Blockchain Commands (when blockchain compose is used)
bitcoin-cli: ## Access Bitcoin CLI
	docker compose -f docker-compose.blockchain.yml exec bitcoin-core bitcoin-cli getblockchaininfo

eth-status: ## Check Ethereum node status
	curl -X POST -H "Content-Type: application/json" --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' http://localhost:8545

cardano-status: ## Check Cardano node status
	docker compose -f docker-compose.blockchain.yml exec cardano-node cardano-cli query tip --mainnet

polkadot-status: ## Check Polkadot node status
	docker compose -f docker-compose.blockchain.yml exec polkadot polkadot --version

# Monitoring Commands
prometheus: ## Open Prometheus UI
	@echo "📊 Opening Prometheus at http://localhost:9090"
	@command -v open >/dev/null 2>&1 && open http://localhost:9090 || echo "Visit http://localhost:9090"

grafana: ## Open Grafana dashboard
	@echo "📈 Opening Grafana at http://localhost:3001 (admin/admin)"
	@command -v open >/dev/null 2>&1 && open http://localhost:3001 || echo "Visit http://localhost:3001"

mailhog: ## Open Mailhog UI (development only)
	@echo "📧 Opening Mailhog at http://localhost:8025"
	@command -v open >/dev/null 2>&1 && open http://localhost:8025 || echo "Visit http://localhost:8025"

# Celery Management
celery-status: ## Check Celery worker status
	$(DOCKER_COMPOSE) exec celery-worker celery -A sound_pesa inspect active

celery-purge: ## Purge all Celery tasks
	$(DOCKER_COMPOSE) exec celery-worker celery -A sound_pesa purge

celery-flower: ## Start Celery Flower monitoring
	$(DOCKER_COMPOSE) exec celery-worker celery -A sound_pesa flower --port=5555

# Security Commands
vault-status: ## Check Vault status
	$(DOCKER_COMPOSE) exec vault vault status

vault-unseal: ## Unseal Vault (if needed)
	$(DOCKER_COMPOSE) exec vault vault operator unseal

# Quick Access URLs
urls: ## Show all application URLs
	@echo "🌐 Sound Pesa Application URLs:"
	@echo "  Web Application:     http://localhost:3000"
	@echo "  API Documentation:  http://localhost:8000/api/docs/"
	@echo "  Admin Panel:        http://localhost:8000/admin/"
	@echo "  Grafana Dashboard:  http://localhost:3001 (admin/admin)"
	@echo "  Prometheus:         http://localhost:9090"
	@echo "  Mailhog (Dev):      http://localhost:8025"
	@echo "  Vault UI:           http://localhost:8200"

# Environment-specific commands
dev-env: ENV=development
staging-env: ENV=staging
production-env: ENV=production

# Docker System Commands
docker-prune: ## Prune Docker system
	docker system prune -f

docker-prune-all: ## Prune Docker system including volumes
	docker system prune -a --volumes -f

docker-images: ## List Docker images
	docker images

docker-volumes: ## List Docker volumes
	docker volume ls

docker-networks: ## List Docker networks
	docker network ls

# Performance and Debugging
perf-test: ## Run performance tests
	@echo "🚀 Running performance tests..."
	@chmod +x scripts/performance-tests.sh
	@./scripts/performance-tests.sh

debug-api: ## Start API in debug mode
	$(DOCKER_COMPOSE) exec api python manage.py runserver 0.0.0.0:8000 --settings=sound_pesa.settings.debug

debug-web: ## Start web in debug mode
	$(DOCKER_COMPOSE) exec web npm run dev

# Backup and Restore
backup-all: ## Create full system backup
	@echo "💾 Creating full system backup..."
	@chmod +x scripts/backup-system.sh
	@./scripts/backup-system.sh

restore-backup: ## Restore from backup
	@echo "🔄 Restoring from backup..."
	@chmod +x scripts/restore-backup.sh
	@./scripts/restore-backup.sh

# SSL/TLS Management (for production)
ssl-cert: ## Generate SSL certificates
	@echo "🔒 Generating SSL certificates..."
	@chmod +x scripts/generate-ssl.sh
	@./scripts/generate-ssl.sh

ssl-renew: ## Renew SSL certificates
	@echo "🔄 Renewing SSL certificates..."
	@chmod +x scripts/renew-ssl.sh
	@./scripts/renew-ssl.sh

# Aliases for common commands
up: dev ## Alias for dev
down: stop ## Alias for stop
rebuild: clean build dev ## Clean, build, and start
fresh: clean-all setup dev ## Complete fresh setup
reset: db-reset ## Alias for db-reset

# Default target when no command is specified
.DEFAULT_GOAL := help