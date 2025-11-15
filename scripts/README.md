# Scripts Directory

This directory contains automation scripts for development, testing, auditing, and deployment.

---

## 📁 Script Categories

### 🚀 Startup & Development

#### `dev-all.ps1`

**Purpose:** Start all ZiggyAI services (frontend + backend)  
**Usage:** `.\scripts\dev-all.ps1`  
**What it does:**

- Starts backend FastAPI server
- Starts frontend Next.js dev server
- Opens new terminal windows for each service

**Requirements:**

- Node.js 18+
- Python 3.11+
- Poetry installed

---

#### `preflight.ps1`

**Purpose:** Pre-deployment environment checks  
**Usage:** `.\scripts\preflight.ps1`  
**What it does:**

- Verifies all dependencies installed
- Checks environment variables
- Validates configuration files
- Tests database connections
- Ensures ports are available

**When to use:** Before deploying or starting development

---

### 🧪 Testing & Quality

#### `ui_audit.spec.ts`

**Purpose:** Playwright UI audit specification  
**Usage:** `npm run audit:fe:ui` (from frontend directory)  
**What it does:**

- Tests all frontend routes
- Captures screenshots
- Validates data rendering
- Checks for console errors
- Measures performance

**Output:** `frontend/artifacts/ui/`

---

#### `run_code_health.ps1`

**Purpose:** Run complete code health checks  
**Usage:** `.\scripts\run_code_health.ps1`  
**What it does:**

- Frontend type checking
- Backend type checking
- Linting (ESLint + Ruff)
- Security scanning (Bandit)
- Dead code detection (Vulture)
- Generates health report

**Output:** `CODE_HEALTH_REPORT.md`

---

#### `setup_ui_audit.ps1`

**Purpose:** Setup UI audit dependencies  
**Usage:** `.\scripts\setup_ui_audit.ps1`  
**What it does:**

- Installs Playwright
- Installs Lighthouse
- Installs Axe-core
- Configures audit tools

**When to use:** First-time setup or after clean install

---

#### `run_lighthouse.ps1`

**Purpose:** Run Lighthouse performance audits  
**Usage:** `.\scripts\run_lighthouse.ps1`  
**What it does:**

- Starts dev server if not running
- Runs Lighthouse on all routes
- Generates performance reports
- Captures metrics

**Output:** `frontend/artifacts/ui/lh_*.json`

---

### 🗄️ Database & Data

#### `dev_db_check.ps1`

**Purpose:** Verify database health  
**Usage:** `.\scripts\dev_db_check.ps1`  
**What it does:**

- Checks database connection
- Verifies schema migrations
- Tests query performance
- Validates data integrity

**When to use:** After migrations or when debugging DB issues

---

#### `seed-dev.ps1`

**Purpose:** Seed development database  
**Usage:** `.\scripts\seed-dev.ps1`  
**What it does:**

- Creates sample users
- Generates mock market data
- Populates test portfolios
- Seeds news articles

**When to use:** Fresh database or testing

---

### 🧹 Maintenance

#### `dev_clean_env.ps1`

**Purpose:** Clean development environment  
**Usage:** `.\scripts\dev_clean_env.ps1`  
**What it does:**

- Removes `node_modules/`
- Removes `.venv/`
- Clears build artifacts
- Resets caches
- Cleans test results

**When to use:** Before fresh install or when deps are broken

---

### 📊 Documentation & Analysis

#### `scan_repo.ps1`

**Purpose:** Scan repository structure  
**Usage:** `.\scripts\scan_repo.ps1`  
**What it does:**

- Lists all files and directories
- Analyzes code organization
- Identifies potential issues
- Generates structure report

**Output:** Console output + optional JSON

---

#### `export_frontend_routes.ps1`

**Purpose:** Export all frontend routes  
**Usage:** `.\scripts\export_frontend_routes.ps1`  
**What it does:**

- Scans `frontend/src/app/`
- Extracts all route definitions
- Generates route map
- Identifies dynamic routes

**Output:** `tools/out/frontend-routes.json`

---

#### `export_backend_routes.ps1`

**Purpose:** Export all backend API routes  
**Usage:** `.\scripts\export_backend_routes.ps1`  
**What it does:**

- Scans FastAPI routers
- Extracts endpoint definitions
- Maps HTTP methods
- Documents parameters

**Output:** `tools/out/backend-routes.json`

---

#### `build_indexes.ps1`

**Purpose:** Build search indexes  
**Usage:** `.\scripts\build_indexes.ps1`  
**What it does:**

- Indexes code for search
- Generates symbol tables
- Creates dependency graphs
- Updates documentation indexes

---

### 🎨 Blueprint & Visualization

#### `render_blueprint.ps1`

**Purpose:** Render system blueprint  
**Usage:** `.\scripts\render_blueprint.ps1`  
**What it does:**

- Generates architecture diagrams
- Creates flow charts
- Renders component relationships
- Produces visual documentation

**Output:** `docs/blueprints/`

---

#### `run_blueprint_full.ps1`

**Purpose:** Full blueprint generation  
**Usage:** `.\scripts\run_blueprint_full.ps1`  
**What it does:**

- Runs complete blueprint pipeline
- Analyzes entire codebase
- Generates all diagrams
- Creates comprehensive docs

**Output:** `docs/blueprints/full/`

---

### 🐍 Python Utilities

#### `generate_ui_report.py`

**Purpose:** Generate UI health report  
**Usage:** `python scripts/generate_ui_report.py`  
**What it does:**

- Aggregates UI audit results
- Analyzes screenshots
- Identifies UI issues
- Generates markdown report

**Output:** `UI_HEALTH_REPORT.md`

---

#### `verify_endpoints.py`

**Purpose:** Verify API endpoint coverage  
**Usage:** `python scripts/verify_endpoints.py`  
**What it does:**

- Compares frontend API calls to backend routes
- Identifies missing endpoints
- Detects unused routes
- Validates request/response contracts

**Output:** Console warnings + optional report

---

#### `detect_duplicates.py`

**Purpose:** Detect code duplication  
**Usage:** `python scripts/detect_duplicates.py`  
**What it does:**

- Scans for duplicate code blocks
- Identifies similar functions
- Suggests refactoring opportunities
- Generates duplication report

**Output:** `reports/duplicates.json`

---

#### `validate_code_health_system.py`

**Purpose:** Validate code health infrastructure  
**Usage:** `python scripts/validate_code_health_system.py`  
**What it does:**

- Checks all audit tools installed
- Verifies configuration files
- Tests audit pipelines
- Ensures reporting works

**Output:** Validation report

---

## 📝 Common Workflows

### Starting Development

```powershell
# Option 1: All services
.\scripts\dev-all.ps1

# Option 2: Individual services
cd frontend && npm run dev
cd backend && poetry run uvicorn app.main:app --reload
```

### Running Quality Checks

```powershell
# Quick check
.\scripts\run_code_health.ps1

# Full audit
cd frontend && npm run audit:fe:all
cd backend && make audit-backend-full
```

### Fresh Start

```powershell
# Clean everything
.\scripts\dev_clean_env.ps1

# Reinstall
cd frontend && npm install
cd backend && poetry install

# Seed database
.\scripts\seed-dev.ps1
```

### Pre-Deployment

```powershell
# Run preflight checks
.\scripts\preflight.ps1

# Build and test
cd frontend && npm run build && npm run test
cd backend && poetry run pytest
```

---

## 🔧 Configuration

Most scripts read configuration from:

- `.env` files (root, frontend, backend)
- `package.json` (frontend)
- `pyproject.toml` (backend)
- `Makefile` (build system)

---

## 📚 Dependencies

### Required Tools

- **PowerShell 5.1+** or **PowerShell Core 7+**
- **Node.js 18+** with npm
- **Python 3.11+** with Poetry
- **Git** for version control

### Optional Tools

- **Docker** for containerization
- **Make** for Makefile commands
- **Playwright** for E2E testing
- **Lighthouse** for performance audits

---

## 🐛 Troubleshooting

### Script Won't Run

```powershell
# Check execution policy
Get-ExecutionPolicy

# Set if needed (as admin)
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Dependencies Missing

```powershell
# Verify installations
node --version
python --version
poetry --version

# Install missing tools
choco install nodejs python poetry
```

### Port Conflicts

```powershell
# Kill process on port 3000
npx kill-port 3000

# Kill process on port 8000
npx kill-port 8000
```

---

## 📖 Additional Resources

- **Main README:** `../README.md`
- **Repository Analysis:** `../REPOSITORY_ANALYSIS.md`
- **Cleanup Guide:** `../CLEANUP_CHECKLIST.md`
- **Makefile:** `../Makefile` (alternative to scripts)

---

## 🤝 Contributing

When adding new scripts:

1. **Name clearly** - Use descriptive names
2. **Document purpose** - Add header comments
3. **Update this README** - Document the script
4. **Test thoroughly** - Verify on clean environment
5. **Handle errors** - Add error checking
6. **Provide output** - Clear success/failure messages

---

**Last Updated:** 2025-11-09  
**Maintained by:** ZiggyAI Development Team
