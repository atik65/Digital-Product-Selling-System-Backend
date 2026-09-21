.PHONY: help setup dev db-up db-down db-reset seed migration migrate rollback migrate-status lint format test docker-build docker-up docker-down docker-logs backup backup-list backup-restore

define HELP_TEXT
Usage: make [target]

Available targets:
  setup           Initial project setup (install dependencies, start db, run migrations)
  dev             Start FastAPI development server with hot-reload
  db-up           Start PostgreSQL container and apply pending migrations
  db-down         Stop PostgreSQL container
  db-reset        Reset database volume and reapply all migrations
  seed            Seed the database with initial users (admin/user) and sample products
  docker-build    Build Docker images for the stack
  docker-up       Start entire stack (DB + API) inside Docker
  docker-down     Stop all running Docker containers
  docker-logs     Follow logs from the Dockerized API container
  migration       Create a new migration (Usage: make migration m="description")
  migrate         Apply all pending migrations (alembic upgrade head)
  rollback        Rollback the most recent migration (downgrade -1)
  migrate-status  Show current database migration revision
  lint            Run ruff linter
  format          Run ruff formatter
  test            Run unit tests with pytest
  backup          Run database backup to Cloudflare R2
  backup-list     List available database backups in Cloudflare R2
  backup-restore  Restore database backup from Cloudflare R2 (Usage: make backup-restore key="backups/YYYY/MM/digital_product_selling_system_backup_YYYYMMDD_HHMMSS.sql.gz")
endef

help: ## Show this help message
	@$(info $(HELP_TEXT))
	@cd .

setup: ## Initial project setup (install dependencies, start db, run migrations)
	uv sync
	docker compose up -d --wait db
	uv run alembic upgrade head

dev: ## Start FastAPI development server with hot-reload
	uv run uvicorn app.main:app --reload

db-up: ## Start PostgreSQL container and apply pending migrations
	docker compose up -d --wait db
	uv run alembic upgrade head

db-down: ## Stop PostgreSQL container
	docker compose stop db

db-reset: ## Reset database volume and reapply all migrations
	docker compose down -v
	docker compose up -d --wait db
	uv run alembic upgrade head

seed: ## Seed database with initial users and sample products
	uv run python scripts/seed.py

docker-build: ## Build Docker images for the application stack
	docker compose build

docker-up: ## Start entire stack (DB + API) inside Docker
	docker compose up -d --build

docker-down: ## Stop all running Docker containers
	docker compose down

docker-logs: ## Follow logs from the Dockerized API container
	docker compose logs -f api

migration: ## Create a new migration (Usage: make migration m="description")
	uv run alembic revision --autogenerate -m "$(m)"

migrate: ## Apply all pending migrations
	uv run alembic upgrade head

rollback: ## Rollback the most recent migration (downgrade -1)
	uv run alembic downgrade -1

migrate-status: ## Show current database migration revision
	uv run alembic current

lint: ## Run ruff linter
	uv run ruff check .

format: ## Run ruff formatter
	uv run ruff format .

test: ## Run unit tests with pytest
	uv run pytest

postman: ## Generate Postman Collection v2.1.0 JSON file
	uv run python scripts/generate_postman_collection.py

backup: ## Run database backup to Cloudflare R2
	uv run python scripts/r2_backup.py backup

backup-list: ## List available database backups in Cloudflare R2
	uv run python scripts/r2_backup.py list

backup-restore: ## Restore database backup from Cloudflare R2 (Usage: make backup-restore key="path/to/file.sql.gz")
	@if [ -z "$(key)" ]; then echo "Error: 'key' parameter is required. Usage: make backup-restore key=\"backups/YYYY/MM/...sql.gz\""; exit 1; fi
	uv run python scripts/r2_backup.py restore $(key)


