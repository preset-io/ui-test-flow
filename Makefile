# UITestFlow Makefile - Common development commands
.PHONY: help install install-dev setup clean lint format test test-unit test-integration test-e2e test-cov docker-build docker-up docker-down docker-logs db-migrate db-upgrade db-downgrade pre-commit run serve

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Default target
.DEFAULT_GOAL := help

# Python and pip executables
PYTHON := python3
PIP := pip3
VENV := .venv
VENV_BIN := $(VENV)/bin
PYTHON_VENV := $(VENV_BIN)/python
PIP_VENV := $(VENV_BIN)/pip

# Project directories
SRC_DIR := uitestflow
TEST_DIR := tests
DOCS_DIR := docs

help: ## Show this help message
	@echo "$(BLUE)UITestFlow Development Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

# Installation targets
install: ## Install production dependencies
	@echo "$(BLUE)Installing production dependencies...$(NC)"
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)Production dependencies installed successfully$(NC)"

install-dev: ## Install development dependencies
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	$(PIP) install -r requirements-dev.txt
	@echo "$(GREEN)Development dependencies installed successfully$(NC)"

setup: ## Setup development environment (venv + dependencies + pre-commit + playwright)
	@echo "$(BLUE)Setting up development environment...$(NC)"
	$(PYTHON) -m venv $(VENV)
	$(PIP_VENV) install --upgrade pip setuptools wheel
	$(PIP_VENV) install -r requirements-dev.txt
	$(VENV_BIN)/pre-commit install
	$(VENV_BIN)/playwright install chromium firefox webkit
	@echo "$(GREEN)Development environment setup complete!$(NC)"
	@echo "$(YELLOW)Activate virtual environment with: source $(VENV)/bin/activate$(NC)"

# Cleaning targets
clean: ## Clean build artifacts, cache files, and temporary files
	@echo "$(BLUE)Cleaning build artifacts and cache...$(NC)"
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .eggs/
	find . -type d -name '__pycache__' -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.pyo' -delete
	find . -type f -name '*~' -delete
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf logs/*.log
	@echo "$(GREEN)Cleanup complete$(NC)"

clean-all: clean ## Clean everything including virtual environment
	@echo "$(BLUE)Cleaning virtual environment...$(NC)"
	rm -rf $(VENV)
	rm -rf artifacts/
	@echo "$(GREEN)Full cleanup complete$(NC)"

# Code quality targets
lint: ## Run all linters (ruff, mypy)
	@echo "$(BLUE)Running linters...$(NC)"
	ruff check $(SRC_DIR) $(TEST_DIR)
	mypy $(SRC_DIR)
	@echo "$(GREEN)Linting complete$(NC)"

lint-fix: ## Run linters with auto-fix
	@echo "$(BLUE)Running linters with auto-fix...$(NC)"
	ruff check --fix $(SRC_DIR) $(TEST_DIR)
	@echo "$(GREEN)Auto-fix complete$(NC)"

format: ## Format code with black and ruff
	@echo "$(BLUE)Formatting code...$(NC)"
	black $(SRC_DIR) $(TEST_DIR)
	ruff format $(SRC_DIR) $(TEST_DIR)
	@echo "$(GREEN)Code formatting complete$(NC)"

format-check: ## Check code formatting without making changes
	@echo "$(BLUE)Checking code formatting...$(NC)"
	black --check $(SRC_DIR) $(TEST_DIR)
	ruff format --check $(SRC_DIR) $(TEST_DIR)

# Testing targets
test: ## Run all tests
	@echo "$(BLUE)Running all tests...$(NC)"
	pytest

test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(NC)"
	pytest -m unit -v

test-integration: ## Run integration tests only
	@echo "$(BLUE)Running integration tests...$(NC)"
	pytest -m integration -v

test-e2e: ## Run end-to-end tests only
	@echo "$(BLUE)Running end-to-end tests...$(NC)"
	pytest -m e2e -v

test-cov: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	pytest --cov=$(SRC_DIR) --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)Coverage report generated at htmlcov/index.html$(NC)"

test-watch: ## Run tests in watch mode (requires pytest-watch)
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	ptw -- -v

# Docker targets
docker-build: ## Build Docker images
	@echo "$(BLUE)Building Docker images...$(NC)"
	docker-compose build
	@echo "$(GREEN)Docker images built successfully$(NC)"

docker-build-prod: ## Build production Docker image
	@echo "$(BLUE)Building production Docker image...$(NC)"
	docker build --target production -t uitestflow:latest .
	@echo "$(GREEN)Production image built successfully$(NC)"

docker-up: ## Start all Docker services
	@echo "$(BLUE)Starting Docker services...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)Docker services started$(NC)"
	@echo "$(YELLOW)Web UI: http://localhost:8018$(NC)"
	@echo "$(YELLOW)Flower (Celery): http://localhost:5555$(NC)"
	@echo "$(YELLOW)MinIO Console: http://localhost:9001$(NC)"

docker-up-db: ## Start only database services (PostgreSQL + Redis)
	@echo "$(BLUE)Starting database services...$(NC)"
	./scripts/start-db.sh

setup-local-db: ## Setup UITestFlow database on local PostgreSQL installation
	@echo "$(BLUE)Setting up local PostgreSQL database...$(NC)"
	./scripts/setup-local-db.sh

docker-down: ## Stop all Docker services
	@echo "$(BLUE)Stopping Docker services...$(NC)"
	docker-compose down
	@echo "$(GREEN)Docker services stopped$(NC)"

docker-down-volumes: ## Stop Docker services and remove volumes
	@echo "$(BLUE)Stopping Docker services and removing volumes...$(NC)"
	docker-compose down -v
	@echo "$(GREEN)Docker services stopped and volumes removed$(NC)"

docker-logs: ## View Docker logs
	docker-compose logs -f

docker-restart: docker-down docker-up ## Restart all Docker services

docker-shell: ## Open shell in app container
	docker-compose exec app /bin/bash

docker-shell-db: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U uitest -d uitest

# Database targets
db-migrate: ## Create new database migration
	@echo "$(BLUE)Creating database migration...$(NC)"
	alembic revision --autogenerate -m "$(message)"
	@echo "$(GREEN)Migration created$(NC)"

db-upgrade: ## Upgrade database to latest version
	@echo "$(BLUE)Upgrading database...$(NC)"
	alembic upgrade head
	@echo "$(GREEN)Database upgraded$(NC)"

db-downgrade: ## Downgrade database by one version
	@echo "$(BLUE)Downgrading database...$(NC)"
	alembic downgrade -1
	@echo "$(GREEN)Database downgraded$(NC)"

db-reset: ## Reset database (WARNING: destroys all data)
	@echo "$(RED)WARNING: This will destroy all data!$(NC)"
	@read -p "Are you sure? (y/N): " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		alembic downgrade base; \
		alembic upgrade head; \
		echo "$(GREEN)Database reset complete$(NC)"; \
	else \
		echo "$(YELLOW)Aborted$(NC)"; \
	fi

# Pre-commit targets
pre-commit: ## Run pre-commit hooks on all files
	@echo "$(BLUE)Running pre-commit hooks...$(NC)"
	pre-commit run --all-files

pre-commit-update: ## Update pre-commit hooks to latest versions
	@echo "$(BLUE)Updating pre-commit hooks...$(NC)"
	pre-commit autoupdate

# Running targets
run: ## Run the CLI
	@echo "$(BLUE)Running UITestFlow CLI...$(NC)"
	uitestflow --help

serve: ## Start the FastAPI web server (development mode with auto-reload)
	@echo "$(BLUE)Starting UITestFlow web server...$(NC)"
	@echo "$(YELLOW)Development mode with auto-reload$(NC)"
	uitestflow serve --reload

serve-prod: ## Start the FastAPI web server (production mode)
	@echo "$(BLUE)Starting UITestFlow web server (production)...$(NC)"
	uitestflow serve --host 0.0.0.0 --port 8018 --workers 4

tui: ## Launch the Terminal User Interface (TUI) dashboard
	@echo "$(BLUE)Launching UITestFlow TUI dashboard...$(NC)"
	uitestflow tui

ui-dev: serve ## Alias for 'make serve' - Start UI in development mode

ui-build: ## Build production React bundle (placeholder - requires React setup)
	@echo "$(BLUE)Building production React bundle...$(NC)"
	@echo "$(YELLOW)Note: React UI setup not yet complete$(NC)"
	@if [ -d "uitestflow/ui" ]; then \
		cd uitestflow/ui && npm run build; \
	else \
		echo "$(YELLOW)React UI directory not found. Run 'make ui-setup' first.$(NC)"; \
	fi

ui-setup: ## Setup React development environment (placeholder)
	@echo "$(BLUE)Setting up React development environment...$(NC)"
	@echo "$(YELLOW)Note: React UI setup coming soon$(NC)"
	@echo "Creating UI directory structure..."
	@mkdir -p uitestflow/ui
	@echo "$(GREEN)UI directory created$(NC)"
	@echo "$(YELLOW)Next steps: Initialize React app with Vite$(NC)"

ui-install: ## Install UI dependencies (placeholder - requires React setup)
	@echo "$(BLUE)Installing UI dependencies...$(NC)"
	@if [ -d "uitestflow/ui" ]; then \
		cd uitestflow/ui && npm install; \
	else \
		echo "$(YELLOW)React UI directory not found. Run 'make ui-setup' first.$(NC)"; \
	fi

worker: ## Run Celery worker
	@echo "$(BLUE)Starting Celery worker...$(NC)"
	celery -A uitestflow.worker.tasks worker --loglevel=info

flower: ## Run Flower (Celery monitoring)
	@echo "$(BLUE)Starting Flower...$(NC)"
	celery -A uitestflow.worker.tasks flower --port=5555

# Build targets
build: ## Build the Python package
	@echo "$(BLUE)Building package...$(NC)"
	python -m build
	@echo "$(GREEN)Package built successfully$(NC)"

install-package: build ## Install the package locally
	@echo "$(BLUE)Installing package locally...$(NC)"
	pip install -e .
	@echo "$(GREEN)Package installed$(NC)"

# Playwright targets
playwright-install: ## Install Playwright browsers
	@echo "$(BLUE)Installing Playwright browsers...$(NC)"
	playwright install chromium firefox webkit
	@echo "$(GREEN)Playwright browsers installed$(NC)"

playwright-update: ## Update Playwright to latest version
	@echo "$(BLUE)Updating Playwright...$(NC)"
	pip install --upgrade playwright
	playwright install chromium firefox webkit
	@echo "$(GREEN)Playwright updated$(NC)"

# Documentation targets
docs-serve: ## Serve documentation locally
	@echo "$(BLUE)Serving documentation...$(NC)"
	mkdocs serve

docs-build: ## Build documentation
	@echo "$(BLUE)Building documentation...$(NC)"
	mkdocs build
	@echo "$(GREEN)Documentation built$(NC)"

# CI/CD targets
ci: lint format-check test ## Run CI checks locally
	@echo "$(GREEN)All CI checks passed!$(NC)"

# Version info
version: ## Show version information
	@echo "$(BLUE)UITestFlow Version Information$(NC)"
	@echo "Python: $(shell $(PYTHON) --version)"
	@echo "Pip: $(shell $(PIP) --version | cut -d' ' -f2)"
	@echo "Playwright: $(shell playwright --version 2>/dev/null || echo 'Not installed')"
	@echo "Docker: $(shell docker --version 2>/dev/null || echo 'Not installed')"
	@echo "Docker Compose: $(shell docker-compose --version 2>/dev/null || echo 'Not installed')"

# Quick start
quickstart: setup docker-up ## Quick start: setup environment and start services
	@echo "$(GREEN)UITestFlow is ready!$(NC)"
	@echo "$(YELLOW)Web UI: http://localhost:8018$(NC)"
	@echo "$(YELLOW)Run 'make help' to see all available commands$(NC)"
