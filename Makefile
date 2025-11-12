# ================================
# ZiggyAI Code Health Audit System
# UI-First, then API approach
# ================================
# Works on Windows PowerShell with 'make' installed (choco install make)
# or you can run the same commands manually.

.SILENT:

PY=python
POETRY=poetry

# Colors for output
RED := \\033[0;31m
GREEN := \\033[0;32m  
YELLOW := \\033[1;33m
BLUE := \\033[0;34m
NC := \\033[0m # No Color

# Default target
help:
	echo "$(BLUE)🏥 ZiggyAI Code Health Audit System$(NC)"
	echo "$(YELLOW)Strategy: UI-First → API-Second$(NC)"
	echo ""
	echo "$(GREEN)📱 Frontend Audit Commands:$(NC)"
	echo "  make install-frontend-deps    Install frontend audit dependencies"
	echo "  make audit-frontend-quick     Type check + lint only"
	echo "  make audit-frontend-full      Complete frontend audit with UI tests"
	echo "  make audit-frontend-ui        Playwright visual audit + screenshots"
	echo "  make audit-frontend-perf      Lighthouse performance audit"
	echo ""
	echo "$(GREEN)🔧 Backend Audit Commands:$(NC)"
	echo "  make install-backend-deps     Install backend audit dependencies" 
	echo "  make audit-backend-quick      Syntax + type + security only"
	echo "  make audit-backend-full       Complete backend audit with API tests"
	echo "  make audit-backend-endpoints  API endpoint smoke tests"
	echo "  make audit-backend-fuzz       Schemathesis API fuzzing"
	echo ""
	echo "$(GREEN)🎯 Complete Audit Commands:$(NC)"
	echo "  make install-deps             Install all dependencies"
	echo "  make audit-all                Run complete audit (frontend + backend)"
	echo "  make audit-quick              Quick syntax/type checks only"
	echo "  make report                   Generate consolidated health report"
	echo ""
	echo "$(GREEN)🧹 Utility Commands:$(NC)"
	echo "  make clean                    Clean artifacts and reports"
	echo "  make dev-setup                Setup development environment"

# ==============================================================================
# DEPENDENCY INSTALLATION
# ==============================================================================

install-deps: install-frontend-deps install-backend-deps
	echo "$(GREEN)✅ All audit dependencies installed$(NC)"

install-frontend-deps:
	echo "$(BLUE)📦 Installing frontend audit dependencies...$(NC)"
	cd frontend && npm install
	echo "$(GREEN)✅ Frontend dependencies installed$(NC)"

install-backend-deps:
	echo "$(BLUE)📦 Installing backend audit dependencies...$(NC)"
	$(PY) -m pip install ruff mypy bandit vulture jscpd click schemathesis
	echo "$(GREEN)✅ Backend dependencies installed$(NC)"

# ==============================================================================
# FRONTEND AUDIT (PHASE 1 - PRIORITY)
# ==============================================================================

audit-frontend-quick:
	echo "$(BLUE)🔍 Quick Frontend Audit (Types + Lint)...$(NC)"
	cd frontend && npm run audit:fe:types
	cd frontend && npm run audit:fe:lint
	echo "$(GREEN)✅ Quick frontend audit complete$(NC)"

audit-frontend-full: audit-frontend-quick
	echo "$(BLUE)🔍 Full Frontend Audit...$(NC)"
	$(MAKE) audit-frontend-ui
	$(MAKE) audit-frontend-perf
	cd frontend && npm run audit:fe:dup || echo "Duplication check failed"
	cd frontend && npm run audit:fe:unused || echo "Unused code check failed"
	cd frontend && npm run audit:fe:report
	echo "$(GREEN)✅ Full frontend audit complete$(NC)"
	echo "$(YELLOW)📝 Check UI_HEALTH_REPORT.md for results$(NC)"

audit-frontend-ui:
	echo "$(BLUE)🔍 Frontend UI Audit (Playwright)...$(NC)"
	cd frontend && npm run audit:fe:ui || echo "UI audit failed"
	echo "$(GREEN)✅ UI audit complete - check artifacts/ui/ for screenshots$(NC)"

audit-frontend-perf:
	echo "$(BLUE)🔍 Frontend Performance Audit (Lighthouse)...$(NC)"
	cd frontend && npm run audit:fe:lighthouse || echo "Performance audit failed"
	echo "$(GREEN)✅ Performance audit complete$(NC)"

# ==============================================================================
# BACKEND AUDIT (PHASE 2 - SECOND)
# ==============================================================================

audit-backend-quick:
	echo "$(BLUE)🔍 Quick Backend Audit (Syntax + Types + Security)...$(NC)"
	cd backend && $(PY) -m ruff check . || echo "Ruff check failed"
	cd backend && $(PY) -m mypy . --ignore-missing-imports || echo "MyPy check failed"
	cd backend && $(PY) -m bandit -r . || echo "Bandit check failed"
	echo "$(GREEN)✅ Quick backend audit complete$(NC)"

audit-backend-full: audit-backend-quick
	echo "$(BLUE)🔍 Full Backend Audit...$(NC)"
	$(MAKE) audit-backend-endpoints
	$(MAKE) audit-backend-fuzz
	cd backend && $(PY) scripts/backend_health_audit.py || echo "Backend health audit failed"
	echo "$(GREEN)✅ Full backend audit complete$(NC)"
	echo "$(YELLOW)📝 Check API_HEALTH_REPORT.md for results$(NC)"

audit-backend-endpoints:
	echo "$(BLUE)🔍 Backend Endpoint Smoke Tests...$(NC)"
	cd backend && $(PY) tests/test_endpoints_smoke.py || echo "Endpoint tests failed"
	echo "$(GREEN)✅ Endpoint smoke tests complete$(NC)"

audit-backend-fuzz:
	echo "$(BLUE)🔍 Backend API Fuzzing (Schemathesis)...$(NC)"
	cd backend && $(PY) scripts/run_schemathesis.py || echo "API fuzzing failed"
	echo "$(GREEN)✅ API fuzzing complete$(NC)"

# ==============================================================================
# COMPLETE AUDIT WORKFLOWS
# ==============================================================================

audit-quick: audit-frontend-quick audit-backend-quick
	echo "$(GREEN)✅ Quick audit complete$(NC)"
	echo "$(YELLOW)💡 Run 'make audit-all' for comprehensive testing$(NC)"

audit-all: 
	echo "$(BLUE)🚀 Starting Complete Code Health Audit...$(NC)"
	echo "$(YELLOW)Phase 1: Frontend UI (Priority)$(NC)"
	$(MAKE) audit-frontend-full
	echo ""
	echo "$(YELLOW)Phase 2: Backend API (Secondary)$(NC)"  
	$(MAKE) audit-backend-full
	echo ""
	echo "$(YELLOW)Phase 3: Consolidated Report$(NC)"
	$(MAKE) report
	echo "$(GREEN)🎉 Complete audit finished!$(NC)"
	echo "$(YELLOW)📝 Check CODE_HEALTH_REPORT.md for consolidated results$(NC)"

# Frontend-first workflow (recommended)
audit-frontend-first: audit-frontend-full
	echo "$(GREEN)✅ Frontend audit complete$(NC)"
	echo "$(YELLOW)💡 Run 'make audit-backend-full' when frontend is clean$(NC)"

# ==============================================================================
# REPORTING
# ==============================================================================

report:
	echo "$(BLUE)📊 Generating consolidated health report...$(NC)"
	$(PY) scripts/generate_code_health_report.py
	echo "$(GREEN)✅ CODE_HEALTH_REPORT.md generated$(NC)"
	echo "$(YELLOW)📖 Open CODE_HEALTH_REPORT.md to see results$(NC)"

# ==============================================================================
# DEVELOPMENT SETUP
# ==============================================================================

dev-setup: install-deps
	echo "$(BLUE)🛠️ Setting up development environment...$(NC)"
	if not exist artifacts mkdir artifacts
	if not exist artifacts\\ui mkdir artifacts\\ui
	if not exist artifacts\\frontend mkdir artifacts\\frontend
	if not exist artifacts\\backend mkdir artifacts\\backend
	echo "$(GREEN)✅ Development environment ready$(NC)"
	echo "$(YELLOW)💡 Run 'make audit-all' to start health monitoring$(NC)"

# ==============================================================================
# UTILITIES
# ==============================================================================

clean:
	echo "$(BLUE)🧹 Cleaning artifacts and reports...$(NC)"
	if exist artifacts rmdir /s /q artifacts
	if exist UI_HEALTH_REPORT.md del UI_HEALTH_REPORT.md
	if exist API_HEALTH_REPORT.md del API_HEALTH_REPORT.md
	if exist CODE_HEALTH_REPORT.md del CODE_HEALTH_REPORT.md
	echo "$(GREEN)✅ Cleanup complete$(NC)"

# Development shortcuts
fe: audit-frontend-full
be: audit-backend-full
quick: audit-quick
all: audit-all

# CI/CD helpers
ci-frontend:
	$(MAKE) audit-frontend-quick
	echo "$(GREEN)✅ CI Frontend checks passed$(NC)"

ci-backend:
	$(MAKE) audit-backend-quick  
	echo "$(GREEN)✅ CI Backend checks passed$(NC)"

# ==============================================================================
# ORIGINAL COMMANDS (PRESERVED)
# ==============================================================================

install-backend:
	cd backend && $(POETRY) install

run-backend:
	cd backend && $(POETRY) run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

lint:
	cd backend && $(POETRY) run ruff check .
	cd backend && $(POETRY) run mypy app || true

test:
	cd backend && $(POETRY) run pytest -q

freeze:
	cd backend && $(POETRY) export -f requirements.txt --with dev --without-hashes -o requirements.txt

# --- Frontend Commands ---
install-frontend:
	cd frontend && npm install

run-frontend:
	cd frontend && npm run dev

build-frontend:
	cd frontend && npm run build

# --- Docker Commands ---
up:
	docker compose up --build

down:
	docker compose down

restart:
	docker compose down && docker compose up --build -d

# --- Utility / Maintenance ---
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf backend/.pytest_cache frontend/node_modules

status:
	docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# --- Default Target ---
help:
	@echo ""
	@echo "Ziggy Clean Makefile Commands:"
	@echo "  make install-backend     -> install Python deps (Poetry)"
	@echo "  make run-backend         -> run FastAPI dev server"
	@echo "  make install-frontend    -> install Node deps"
	@echo "  make run-frontend        -> run Vite dev server"
	@echo "  make up                  -> launch full Docker stack"
	@echo "  make down                -> stop Docker stack"
	@echo "  make freeze              -> export Poetry requirements"
	@echo "  make lint                -> run linters"
	@echo "  make test                -> run tests"
	@echo "  make status              -> show running containers"
	@echo ""

.PHONY: install-backend run-backend lint test freeze install-frontend run-frontend build-frontend up down restart clean status help
