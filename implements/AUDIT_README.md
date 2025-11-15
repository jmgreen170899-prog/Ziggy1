# 🏥 ZiggyAI Code Health Audit System

**Strategy**: UI-First → API-Second  
**Goal**: Detect, diagnose, and fix user-facing issues before backend hardening

## 🚀 Quick Start

### Option 1: Using Make (Recommended)

```bash
# Setup everything
make dev-setup

# Run complete audit
make audit-all

# Check results
open CODE_HEALTH_REPORT.md
```

### Option 2: Using PowerShell (Windows)

```powershell
# Setup everything
.\audit.ps1 dev-setup

# Run complete audit
.\audit.ps1 audit-all

# Check results
notepad CODE_HEALTH_REPORT.md
```

### Option 3: Manual Commands

```bash
# Frontend (Phase 1 - Priority)
cd frontend
npm install
npm run audit:fe:types
npm run audit:fe:lint
npm run audit:fe:ui
npm run audit:fe:lighthouse
npm run audit:fe:report

# Backend (Phase 2 - Secondary)
cd ../backend
pip install ruff mypy bandit vulture jscpd schemathesis
python scripts/backend_health_audit.py

# Consolidated Report
cd ..
python scripts/generate_code_health_report.py
```

## 🎯 Audit Philosophy

### Phase 1: Frontend UI (First & Priority)

**Why First?** Users see UI issues immediately. Fix what's visible before what's hidden.

- **Strict Type & Lint**: Zero TypeScript errors, zero ESLint warnings
- **Route & Render Audit**: Every route loads, displays data, no console errors
- **Performance & A11y**: Lighthouse scores >70% performance, >80% accessibility
- **Duplication & Unused**: Clean codebase with minimal technical debt

### Phase 2: Backend API (Second)

**Why Second?** API issues are often hidden until they cause frontend failures.

- **Smoke Test All Routes**: Every endpoint returns <400 for valid requests
- **OpenAPI Fuzz**: Schemathesis validates all documented endpoints
- **Syntax/Type/Security**: Ruff, MyPy, Bandit pass cleanly
- **Dead Code & Duplication**: Minimal unused imports and duplicated logic
- **Health Endpoint**: `/paper/health` returns required fields with correct status codes

## 📊 Issue Priority System

### 🚨 P0 (Critical) - Fix Before Production

- Frontend routes completely broken
- Console errors in UI
- NaN/Infinity values displayed to users
- API endpoints returning 5xx errors
- Health endpoint failures

### ⚠️ P1 (High Priority) - Fix This Sprint

- Missing/empty data fields in UI
- Network errors in frontend
- Performance scores <70%
- Accessibility scores <80%
- High layout shift (CLS >0.1)
- API endpoints returning 4xx errors
- Type checking failures
- Security warnings

### 📝 P2 (Polish) - Technical Debt

- Code duplication
- Unused code/dependencies
- Slow load times (>5s)
- Minor performance optimizations

## 🛠️ Tools & Technologies

### Frontend Audit Stack

- **TypeScript**: Strict type checking with `tsconfig.strict.json`
- **ESLint**: Code quality and style enforcement
- **Playwright**: Visual UI testing with screenshots
- **Lighthouse**: Performance and accessibility auditing
- **jscpd**: Code duplication detection
- **knip/ts-prune/depcheck**: Unused code and dependency detection

### Backend Audit Stack

- **Ruff**: Fast Python linting and formatting
- **MyPy**: Static type checking
- **Bandit**: Security vulnerability scanning
- **Vulture**: Dead code detection
- **Schemathesis**: OpenAPI-based API fuzzing
- **Custom Smoke Tests**: Endpoint availability testing

## 📁 Artifacts & Reports

### Generated Reports

- `CODE_HEALTH_REPORT.md` - Consolidated P0/P1/P2 issues with action items
- `UI_HEALTH_REPORT.md` - Frontend-specific findings with screenshots
- `API_HEALTH_REPORT.md` - Backend-specific findings with endpoint analysis

### Artifacts Directory Structure

```
artifacts/
├── ui/
│   ├── ui_audit_results.json         # Playwright test results
│   ├── lighthouse_summary.json       # Performance scores
│   ├── <route>.png                   # Screenshots per route
│   └── playwright-report/            # Detailed test reports
├── frontend/
│   ├── jscpd-report.json            # Code duplication
│   └── knip-results.json            # Unused code
└── backend/
    ├── backend_audit_results.json   # Comprehensive audit
    ├── endpoints_failures.json      # API endpoint status
    ├── ruff_report.json             # Linting results
    ├── bandit_report.json           # Security findings
    └── schemathesis_report.json     # API fuzzing results
```

## 🔧 Available Commands

### Quick Commands

```bash
make audit-quick          # Fast type/lint checks only
make audit-frontend-quick # Frontend types + lint only
make audit-backend-quick  # Backend syntax + types + security only
```

### Full Audits

```bash
make audit-frontend-full  # Complete frontend audit with UI tests
make audit-backend-full   # Complete backend audit with API tests
make audit-all           # Full audit (frontend → backend → report)
```

### Individual Components

```bash
make audit-frontend-ui    # Playwright visual audit + screenshots
make audit-frontend-perf  # Lighthouse performance audit
make audit-backend-endpoints # API endpoint smoke tests
make audit-backend-fuzz   # Schemathesis API fuzzing
```

### Utilities

```bash
make dev-setup           # Install all dependencies + create directories
make clean              # Remove all artifacts and reports
make report             # Generate consolidated CODE_HEALTH_REPORT.md
make status             # Show current health status
```

### Shortcuts

```bash
make fe    # = audit-frontend-full
make be    # = audit-backend-full
make quick # = audit-quick
make all   # = audit-all
```

## 🎯 Acceptance Criteria

### ✅ Ready for Production When:

**Frontend (Phase 1)**

- [ ] Zero P0 issues (broken routes, console errors, NaN values)
- [ ] `audit:fe:types` and `audit:fe:lint` pass with zero warnings
- [ ] All routes load successfully with data-loaded selectors
- [ ] Performance scores >70% average across all routes
- [ ] Accessibility scores >80% average across all routes
- [ ] Screenshots show fully rendered data for every tab
- [ ] TTL badges properly indicate data freshness

**Backend (Phase 2)**

- [ ] Zero P0 issues (5xx errors, health endpoint failures)
- [ ] `ruff check`, `mypy`, and `bandit` pass cleanly
- [ ] All endpoints return <400 status codes for valid requests
- [ ] `/paper/health` returns 200 with required fields when active
- [ ] Returns 503 if engine running but no trades in 15m
- [ ] Returns 500 if strict isolation fails
- [ ] Schemathesis fuzzing shows no critical failures

**Integration**

- [ ] Frontend receives real-time data from backend
- [ ] WebSocket connections stable under load
- [ ] Error boundaries handle API failures gracefully
- [ ] No NaN/Infinity values reach the UI
- [ ] All data views show loading states and error states

## 🔄 Continuous Integration

### Pre-commit Hooks

```bash
# Add to .git/hooks/pre-commit
make audit-quick || exit 1
```

### GitHub Actions / CI Pipeline

```yaml
# Recommended CI workflow
- name: Frontend Health Check
  run: make ci-frontend

- name: Backend Health Check
  run: make ci-backend

- name: Generate Health Report
  run: make report

- name: Fail on P0 Issues
  run: |
    if grep -q "🔴 CRITICAL" CODE_HEALTH_REPORT.md; then
      echo "❌ P0 issues found - blocking deployment"
      exit 1
    fi
```

## 🚨 Troubleshooting

### Common Issues

**"UI audit failed"**

- Ensure frontend dev server is running (`npm run dev`)
- Check if port 3000 is available
- Verify Playwright is installed (`npx playwright install`)

**"API fuzzing failed"**

- Ensure backend server is running (`make run-backend`)
- Check if port 8000 is available
- Verify OpenAPI schema is accessible at `/openapi.json`

**"Permission denied"**

- On Windows: Run PowerShell as Administrator
- On Mac/Linux: Use `sudo` for global package installs

**"Command not found"**

- Install make: `choco install make` (Windows) or `brew install make` (Mac)
- Use PowerShell script alternative: `.\audit.ps1`
- Run commands manually from the Quick Start section

### Debug Mode

```bash
# Verbose output
make audit-all VERBOSE=1

# Individual component debugging
cd frontend && npm run audit:fe:ui -- --debug
cd backend && python scripts/backend_health_audit.py --verbose
```

## 🤝 Contributing

### Adding New Audit Checks

1. **Frontend**: Add to `frontend/scripts/ui_audit.spec.ts`
2. **Backend**: Add to `backend/scripts/backend_health_audit.py`
3. **Report**: Update `scripts/generate_code_health_report.py`
4. **Commands**: Add to `Makefile` and `audit.ps1`

### Audit Check Guidelines

- **Fast by default**: Quick checks should complete in <30s
- **Actionable output**: Every failure should suggest a fix
- **Priority classification**: Clearly mark P0/P1/P2 issues
- **Artifacts**: Save detailed results for investigation
- **Screenshots**: Visual evidence for UI issues

---

## 📚 Further Reading

- [Frontend Audit Deep Dive](frontend/scripts/README.md)
- [Backend Audit Deep Dive](backend/scripts/README.md)
- [Playwright UI Testing Guide](https://playwright.dev/docs/intro)
- [Lighthouse Performance Guide](https://developers.google.com/web/tools/lighthouse)
- [Schemathesis API Testing](https://schemathesis.readthedocs.io/)

**Remember**: Fix the frontend UI first, then harden the backend API. Users see the UI - they don't see your elegant API design until it works perfectly from their perspective.
