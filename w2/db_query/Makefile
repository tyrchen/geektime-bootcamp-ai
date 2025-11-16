.PHONY: help install dev backend frontend test lint format clean db-migrate db-upgrade db-downgrade

# Variables
BACKEND_DIR = backend
FRONTEND_DIR = frontend
PYTHON = python3.12
UV = uv
NPM = npm

# Colors for output
BLUE = \033[0;34m
GREEN = \033[0;32m
YELLOW = \033[0;33m
NC = \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)Database Query Tool - Makefile Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# Installation
install: install-backend install-frontend ## Install all dependencies

install-backend: ## Install backend dependencies (including dev dependencies)
	@echo "$(BLUE)Installing backend dependencies...$(NC)"
	cd $(BACKEND_DIR) && $(UV) sync --extra dev

install-frontend: ## Install frontend dependencies
	@echo "$(BLUE)Installing frontend dependencies...$(NC)"
	cd $(FRONTEND_DIR) && $(NPM) install

# Development servers
dev: dev-backend dev-frontend ## Start both backend and frontend (in parallel)

dev-backend: ## Start backend development server
	@echo "$(BLUE)Starting backend server on http://localhost:8000$(NC)"
	cd $(BACKEND_DIR) && $(UV) run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Start frontend development server
	@echo "$(BLUE)Starting frontend server on http://localhost:5173$(NC)"
	cd $(FRONTEND_DIR) && $(NPM) run dev

# Backend commands
backend: dev-backend ## Alias for dev-backend

backend-shell: ## Open Python shell with app context
	cd $(BACKEND_DIR) && $(UV) run python -c "from app import *; import IPython; IPython.embed()"

backend-check: ## Check backend code with mypy and ruff
	@echo "$(BLUE)Running type checks...$(NC)"
	cd $(BACKEND_DIR) && $(UV) run mypy app
	@echo "$(BLUE)Running lint checks...$(NC)"
	cd $(BACKEND_DIR) && $(UV) run ruff check app

# Frontend commands
frontend: dev-frontend ## Alias for dev-frontend

frontend-build: ## Build frontend for production
	@echo "$(BLUE)Building frontend...$(NC)"
	cd $(FRONTEND_DIR) && $(NPM) run build

frontend-preview: ## Preview production build
	cd $(FRONTEND_DIR) && $(NPM) run preview

# Testing
test: test-backend test-frontend ## Run all tests

test-backend: ## Run backend tests
	@echo "$(BLUE)Running backend tests...$(NC)"
	cd $(BACKEND_DIR) && $(UV) run pytest -v

test-backend-coverage: ## Run backend tests with coverage
	@echo "$(BLUE)Running backend tests with coverage...$(NC)"
	cd $(BACKEND_DIR) && $(UV) run pytest --cov=app --cov-report=html --cov-report=term

test-frontend: ## Run frontend tests
	@echo "$(BLUE)Running frontend tests...$(NC)"
	cd $(FRONTEND_DIR) && $(NPM) test

# Code quality
lint: lint-backend lint-frontend ## Run all linters

lint-backend: ## Lint backend code
	@echo "$(BLUE)Linting backend...$(NC)"
	cd $(BACKEND_DIR) && $(UV) run ruff check app tests

lint-frontend: ## Lint frontend code
	@echo "$(BLUE)Linting frontend...$(NC)"
	cd $(FRONTEND_DIR) && $(NPM) run lint

format: format-backend format-frontend ## Format all code

format-backend: ## Format backend code
	@echo "$(BLUE)Formatting backend...$(NC)"
	cd $(BACKEND_DIR) && $(UV) run ruff format app tests

format-frontend: ## Format frontend code
	@echo "$(BLUE)Formatting frontend...$(NC)"
	cd $(FRONTEND_DIR) && $(NPM) run lint -- --fix || true

# Database migrations
db-migrate: ## Create a new database migration (use MESSAGE="description")
	@if [ -z "$(MESSAGE)" ]; then \
		echo "$(YELLOW)Usage: make db-migrate MESSAGE=\"your migration message\"$(NC)"; \
		exit 1; \
	fi
	cd $(BACKEND_DIR) && $(UV) run alembic revision --autogenerate -m "$(MESSAGE)"

db-upgrade: ## Apply database migrations
	@echo "$(BLUE)Applying database migrations...$(NC)"
	cd $(BACKEND_DIR) && $(UV) run alembic upgrade head

db-downgrade: ## Rollback database migration (use REVISION=previous)
	@if [ -z "$(REVISION)" ]; then \
		echo "$(YELLOW)Usage: make db-downgrade REVISION=previous$(NC)"; \
		exit 1; \
	fi
	cd $(BACKEND_DIR) && $(UV) run alembic downgrade $(REVISION)

db-history: ## Show migration history
	cd $(BACKEND_DIR) && $(UV) run alembic history

db-current: ## Show current database revision
	cd $(BACKEND_DIR) && $(UV) run alembic current

# Cleanup
clean: clean-backend clean-frontend ## Clean all build artifacts

clean-backend: ## Clean backend artifacts
	@echo "$(BLUE)Cleaning backend...$(NC)"
	cd $(BACKEND_DIR) && \
		find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true && \
		find . -type f -name "*.pyc" -delete && \
		find . -type f -name "*.pyo" -delete && \
		find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true && \
		rm -rf .pytest_cache htmlcov .coverage dist build

clean-frontend: ## Clean frontend artifacts
	@echo "$(BLUE)Cleaning frontend...$(NC)"
	cd $(FRONTEND_DIR) && \
		rm -rf node_modules dist .vite

clean-db: ## Clean SQLite database (WARNING: deletes all data)
	@echo "$(YELLOW)WARNING: This will delete the SQLite database!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		rm -f ~/.db_query/db_query.db; \
		echo "$(GREEN)Database deleted$(NC)"; \
	else \
		echo "$(BLUE)Cancelled$(NC)"; \
	fi

# Setup
setup: install db-upgrade ## Initial setup: install dependencies and run migrations
	@echo "$(GREEN)Setup complete!$(NC)"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Copy backend/.env.example to backend/.env and add your OPENAI_API_KEY"
	@echo "  2. Run 'make dev' to start both servers"
	@echo "  3. Open http://localhost:5173 in your browser"

# Health checks
health: ## Check if backend is running
	@curl -s http://localhost:8000/health | python3 -m json.tool || echo "$(YELLOW)Backend is not running$(NC)"

# API documentation
docs: ## Open API documentation in browser
	@echo "$(BLUE)Opening API docs...$(NC)"
	@open http://localhost:8000/docs || xdg-open http://localhost:8000/docs || echo "Please open http://localhost:8000/docs manually"

# Update dependencies
update-backend: ## Update backend dependencies to latest versions
	cd $(BACKEND_DIR) && $(UV) sync --upgrade

update-frontend: ## Update frontend dependencies to latest versions
	cd $(FRONTEND_DIR) && $(NPM) update

update: update-backend update-frontend ## Update all dependencies

# Development workflow shortcuts
check: lint test ## Run lint and tests

ci: install lint test ## Run CI checks (install, lint, test)
