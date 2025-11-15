# ZiggyAI Cleanup Checklist

**Generated:** 2025-11-09  
**Purpose:** Actionable checklist for cleaning up the repository  
**Status:** 🟡 Pending Review - DO NOT apply until approved

---

## 📋 Overview

This checklist identifies specific files and directories for cleanup. Each item includes:

- ✅ Safe to proceed
- ⚠️ Needs review before deletion
- 🔄 Should be moved/reorganized
- 📝 Needs documentation

**Review Process:**

1. Review each section
2. Confirm safety of proposed actions
3. Execute in phases
4. Verify after each phase

---

## 🗑️ Phase 1: Safe Deletions (Low Risk)

### Backup Files (3 files - 🗑️ DELETE)

Git history preserves old versions, so these backups are redundant.

```bash
# Files to delete:
frontend/src/app/crypto/page_old.tsx.backup
frontend/src/app/learning/page_old.tsx.backup
frontend/src/app/trading/page_old.tsx.backup
```

**Actions:**

```bash
cd /home/runner/work/ZiggyAI/ZiggyAI
rm frontend/src/app/crypto/page_old.tsx.backup
rm frontend/src/app/learning/page_old.tsx.backup
rm frontend/src/app/trading/page_old.tsx.backup
```

**Risk:** 🟢 Low - Git history contains old versions

---

## 🔄 Phase 2: Reorganization (Medium Risk)

### 2A. Root-Level Test Files (8 files - 🔄 MOVE)

These test files should be in the backend tests directory.

```bash
# Files to move:
test_decision_log.py          → backend/tests/decisions/test_decision_log.py
test_explain_server.py        → backend/tests/api/test_explain_server.py
test_news_websocket.py        → backend/tests/websocket/test_news_websocket.py
test_paper_import.py          → backend/tests/paper/test_paper_import.py
test_websocket.py             → backend/tests/websocket/test_websocket.py

# Utility scripts to keep but document:
check_data_freshness.py       → Keep at root (utility)
demo_audit.py                 → Keep at root (demo/docs)
paper_test_api.py            → Keep at root or move to backend/tests/paper/
```

**Actions:**

```bash
cd /home/runner/work/ZiggyAI/ZiggyAI

# Create test subdirectories if they don't exist
mkdir -p backend/tests/decisions
mkdir -p backend/tests/websocket
mkdir -p backend/tests/paper

# Move test files
mv test_decision_log.py backend/tests/decisions/
mv test_explain_server.py backend/tests/api/
mv test_news_websocket.py backend/tests/websocket/
mv test_paper_import.py backend/tests/paper/
mv test_websocket.py backend/tests/websocket/
```

**Risk:** 🟡 Medium - Test discovery patterns may need updating

**Verification:**

```bash
cd backend
poetry run pytest --collect-only  # Verify tests are discovered
```

### 2B. Backend Root Test Files (25 files - 🔄 ORGANIZE)

These test files are at `backend/*.py` but should be organized by feature.

```bash
# WebSocket tests (6 files) → backend/tests/websocket/
quick_websocket_test.py
test_frontend_news_websocket.py
test_news_streaming.py
test_news_streaming_debug.py
test_start_news_streaming.py
test_websocket_robustness.py

# Integration tests (3 files) → backend/tests/integration/
acceptance_test.py
test_integration.py
test_integration_api.py

# News/Alerts tests (4 files) → backend/tests/news/
test_alert_monitoring.py
test_enhanced_news.py
test_full_alert_flow.py
test_rss_quick.py

# Cognitive/Brain tests (3 files) → backend/tests/cognitive/
test_brain_data_flow.py
test_brain_flow_simple.py
test_realtime_brain.py

# Learning/ML tests (2 files) → backend/tests/learning/
test_learning_system.py
test_event_store_metrics.py

# Data hub tests (2 files) → backend/tests/data/
test_simple_hub.py
test_universal_data_hub.py

# Portfolio tests (1 file) → backend/tests/portfolio/
test_portfolio_market.py

# Utility/Debug (4 files) → backend/tests/utils/ or scripts/
debug_memory.py
restart_portfolio.py
test_startup_fix.py
```

**Actions:**

```bash
cd /home/runner/work/ZiggyAI/ZiggyAI/backend

# Create organized test directories
mkdir -p tests/websocket
mkdir -p tests/integration
mkdir -p tests/news
mkdir -p tests/cognitive
mkdir -p tests/learning
mkdir -p tests/data
mkdir -p tests/portfolio
mkdir -p tests/utils

# Move WebSocket tests
mv quick_websocket_test.py tests/websocket/
mv test_frontend_news_websocket.py tests/websocket/
mv test_news_streaming.py tests/websocket/
mv test_news_streaming_debug.py tests/websocket/
mv test_start_news_streaming.py tests/websocket/
mv test_websocket_robustness.py tests/websocket/

# Move Integration tests
mv acceptance_test.py tests/integration/
mv test_integration.py tests/integration/
mv test_integration_api.py tests/integration/

# Move News tests
mv test_alert_monitoring.py tests/news/
mv test_enhanced_news.py tests/news/
mv test_full_alert_flow.py tests/news/
mv test_rss_quick.py tests/news/

# Move Cognitive tests
mv test_brain_data_flow.py tests/cognitive/
mv test_brain_flow_simple.py tests/cognitive/
mv test_realtime_brain.py tests/cognitive/

# Move Learning tests
mv test_learning_system.py tests/learning/
mv test_event_store_metrics.py tests/learning/

# Move Data hub tests
mv test_simple_hub.py tests/data/
mv test_universal_data_hub.py tests/data/

# Move Portfolio tests
mv test_portfolio_market.py tests/portfolio/

# Move Utility scripts
mv debug_memory.py tests/utils/
mv restart_portfolio.py scripts/
mv test_startup_fix.py tests/utils/
```

**Risk:** 🟡 Medium - Test imports may need updating

**Verification:**

```bash
cd backend
poetry run pytest --collect-only  # Verify all tests discovered
poetry run pytest -v              # Run all tests
```

### 2C. Debug HTML Files (2 files - 🔄 MOVE)

Move debug tools to a dedicated directory.

```bash
# Files to move:
debug_websocket.html      → tools/debug/debug_websocket.html
websocket_debug.html      → tools/debug/websocket_debug.html
```

**Actions:**

```bash
cd /home/runner/work/ZiggyAI/ZiggyAI

mkdir -p tools/debug
mv debug_websocket.html tools/debug/
mv websocket_debug.html tools/debug/
```

**Risk:** 🟢 Low - These are standalone tools

---

## 📝 Phase 3: Documentation Consolidation (Low Risk)

### 3A. Archive Completed Implementation Docs

Move completed implementation notes to an archive.

```bash
# Create archive directory
mkdir -p docs/archive/implementations

# Move completed implementation docs:
implements/API_FIXES_COMPLETE.md
implements/COGNITIVE_CORE_COMPLETE.md
implements/EMOTIVE_INTERFACE_COMPLETE.md
implements/FRONTEND_DATA_AUDIT_COMPLETE.md
implements/LIVE_DATA_COMPLETE.md
implements/LIVE_DATA_SUCCESS_REPORT.md
implements/MEMORY_IMPLEMENTATION_COMPLETE.md
implements/PERCEPTION_LAYER_COMPLETE.md
implements/PRODUCTION_DEPLOYMENT_COMPLETE.md
```

**Actions:**

```bash
cd /home/runner/work/ZiggyAI/ZiggyAI

mkdir -p docs/archive/implementations

# Move completed docs
mv implements/API_FIXES_COMPLETE.md docs/archive/implementations/
mv implements/COGNITIVE_CORE_COMPLETE.md docs/archive/implementations/
mv implements/EMOTIVE_INTERFACE_COMPLETE.md docs/archive/implementations/
mv implements/FRONTEND_DATA_AUDIT_COMPLETE.md docs/archive/implementations/
mv implements/LIVE_DATA_COMPLETE.md docs/archive/implementations/
mv implements/LIVE_DATA_SUCCESS_REPORT.md docs/archive/implementations/
mv implements/MEMORY_IMPLEMENTATION_COMPLETE.md docs/archive/implementations/
mv implements/PERCEPTION_LAYER_COMPLETE.md docs/archive/implementations/
mv implements/PRODUCTION_DEPLOYMENT_COMPLETE.md docs/archive/implementations/
```

**Risk:** 🟢 Low - Archiving for reference

### 3B. Archive Large Planning Files

These are historical and very large.

```bash
# Files to archive/compress:
implements/ZiggyFileMap_20251013_124421.txt    # 632KB - File listing
implements/futurenotes.txt                     # 135KB - Planning
implements/futurenotes2.txt                    # 59KB - Planning
ALL_NOTES.md                                   # 6.2MB - Consolidated notes
```

**Actions:**

```bash
cd /home/runner/work/ZiggyAI/ZiggyAI

mkdir -p docs/archive/planning

# Move and optionally compress
mv implements/ZiggyFileMap_20251013_124421.txt docs/archive/planning/
mv implements/futurenotes.txt docs/archive/planning/
mv implements/futurenotes2.txt docs/archive/planning/
mv ALL_NOTES.md docs/archive/planning/

# Optional: Compress large files
cd docs/archive/planning
gzip ALL_NOTES.md  # Creates ALL_NOTES.md.gz
```

**Risk:** 🟢 Low - Historical documents

### 3C. Archive Session Logs

Move session logs and lessons learned to archive.

```bash
# Files to archive:
implements/Frontend_Backend_Integration_Session_Lessons_Learned.txt
implements/Routes_Signals_Type_Errors_Fixed.txt
implements/ZiggyAI_Backend_Functionality_Explained.txt
implements/ZiggyAI_Platform_Analysis.txt
implements/ZiggyAI_Project_Assessment_Next_Steps.txt
implements/BKimplements.txt
implements/UIimplements.txt
```

**Actions:**

```bash
cd /home/runner/work/ZiggyAI/ZiggyAI

mkdir -p docs/archive/sessions

mv implements/Frontend_Backend_Integration_Session_Lessons_Learned.txt docs/archive/sessions/
mv implements/Routes_Signals_Type_Errors_Fixed.txt docs/archive/sessions/
mv implements/ZiggyAI_Backend_Functionality_Explained.txt docs/archive/sessions/
mv implements/ZiggyAI_Platform_Analysis.txt docs/archive/sessions/
mv implements/ZiggyAI_Project_Assessment_Next_Steps.txt docs/archive/sessions/
mv implements/BKimplements.txt docs/archive/sessions/
mv implements/UIimplements.txt docs/archive/sessions/
```

**Risk:** 🟢 Low - Historical reference

### 3D. Keep Active Documentation

These docs should stay in `implements/` or move to `docs/`:

```bash
# Keep in implements/ (or move to docs/):
implements/ZiggyAI_FULL_WRITEUP.md           # Primary reference - KEEP
implements/PROTECT.md                         # Critical elements - KEEP
implements/STARTUP_README.md                  # Quick start - KEEP
implements/AUDIT_README.md                    # Quality system - KEEP
implements/ENDPOINTS_README.md                # API docs - KEEP
implements/README-dev.md                      # Developer guide - KEEP
implements/CLEANUP_REPORT.md                  # Previous cleanup - KEEP
implements/LIVE_DATA_ARCHITECTURE.md          # Architecture - KEEP
implements/DEPS_UNIFICATION_PLAN.md          # Planning - KEEP
implements/rate-limiting-setup.md            # Setup guide - KEEP
implements/ssl-setup.md                      # Setup guide - KEEP
```

---

## 📚 Phase 4: Create New Documentation (Low Risk)

### 4A. Create Master Documentation Files

```bash
# Already created:
✅ README.md                    # Main repository README
✅ REPOSITORY_ANALYSIS.md       # Complete analysis
✅ CLEANUP_CHECKLIST.md         # This file

# To create:
□ docs/ARCHITECTURE.md          # System architecture
□ docs/DEVELOPMENT.md           # Development workflow
□ docs/TESTING.md               # Testing guide
□ docs/DEPLOYMENT.md            # Deployment guide
□ scripts/README.md             # Scripts documentation
□ CHANGELOG.md                  # Change history
```

### 4B. Create Scripts README

Document all PowerShell scripts:

```markdown
# scripts/README.md

## Startup Scripts

- `dev-all.ps1` - Start all services
- `preflight.ps1` - Pre-deployment checks

## Audit Scripts

- `run_code_health.ps1` - Health checks
- `setup_ui_audit.ps1` - UI audit setup
- `run_lighthouse.ps1` - Performance audit

## Development Utilities

- `dev_clean_env.ps1` - Clean environment
- `dev_db_check.ps1` - Database checks
- `seed-dev.ps1` - Seed dev data

## Documentation Scripts

- `scan_repo.ps1` - Repository scanner
- `export_frontend_routes.ps1` - Export frontend routes
- `export_backend_routes.ps1` - Export backend routes

## Build Scripts

- `build_indexes.ps1` - Build indexes
- `run_blueprint_full.ps1` - Full blueprint
```

---

## ⚠️ Phase 5: Items Requiring Manual Review

### 5A. PowerShell Note Management Scripts

Review and decide fate of these scripts:

```bash
Consolidate-Notes.ps1         # 13KB - Consolidates notes to ALL_NOTES.md
Purge-To-AllNotes.ps1        # 12KB - Archives notes
audit.ps1                     # 11KB - Manual audit runner
```

**Options:**

1. 🔄 Move to `scripts/notes/` if still useful
2. 🗑️ Delete if superseded by new documentation system
3. 📝 Document and keep if actively used

**Decision:** ⚠️ NEEDS REVIEW

### 5B. Old Markdown Documentation

Review these for relevance:

```bash
ISSUE_REPORT.md               # Issue tracking - Check if current
ISSUES.md                     # Issues list - Check if current
TASK.md                       # Task guide - Check if current
ZiggyAI_valuation_note.txt   # Valuation note - Archive or keep?
```

**Decision:** ⚠️ NEEDS REVIEW

### 5C. Knip Unused Detection

```bash
knip-unused.json              # Unused code detection results
```

**Decision:** Review results, act on findings, then delete or update

---

## 🎯 Execution Plan

### Recommended Order

1. **Phase 1** (5 min) - Delete backup files
2. **Phase 3A-D** (15 min) - Archive documentation
3. **Phase 2C** (2 min) - Move debug HTML files
4. **Phase 2A** (10 min) - Move root test files
5. **Phase 2B** (20 min) - Organize backend tests
6. **Phase 4** (30 min) - Create new documentation
7. **Phase 5** (Manual) - Review and decide

**Total Estimated Time:** ~90 minutes + manual review time

### Safety Checks

After each phase:

```bash
# 1. Check build
cd frontend && npm run build
cd backend && poetry run pytest --collect-only

# 2. Check tests
cd frontend && npm run test
cd backend && poetry run pytest

# 3. Check git status
git status
git diff

# 4. Commit if successful
git add .
git commit -m "chore: [phase name] cleanup"
```

---

## ✅ Verification Checklist

After all cleanup:

- [ ] All tests still discoverable and passing
- [ ] Frontend builds successfully
- [ ] Backend starts without errors
- [ ] No broken imports
- [ ] Documentation updated
- [ ] `.gitignore` covers build artifacts
- [ ] README.md complete
- [ ] No broken links in docs
- [ ] Git history clean

---

## 🔄 Rollback Plan

If issues arise:

```bash
# Undo last commit
git reset --soft HEAD~1

# Restore specific file
git checkout HEAD -- <file>

# Restore entire commit
git revert <commit-hash>

# Nuclear option - reset to before cleanup
git reset --hard <commit-before-cleanup>
```

---

## 📊 Expected Results

After cleanup:

### Files Deleted: ~3

- 3 backup files removed

### Files Moved: ~35

- 8 root test files → backend/tests/
- 25 backend root tests → organized subdirectories
- 2 HTML debug files → tools/debug/

### Documentation Reorganized: ~20

- Completed docs → docs/archive/implementations/
- Planning docs → docs/archive/planning/
- Session logs → docs/archive/sessions/

### New Documentation: ~7

- README.md
- REPOSITORY_ANALYSIS.md
- CLEANUP_CHECKLIST.md
- scripts/README.md
- docs/ARCHITECTURE.md
- docs/DEVELOPMENT.md
- docs/TESTING.md

### Benefits

- ✅ Clearer project structure
- ✅ Easier to find tests
- ✅ Better documentation
- ✅ Reduced confusion
- ✅ Preserved all history

---

**Status:** Ready for execution  
**Review by:** Repository owner  
**Approval:** Pending  
**Execution:** Pending approval
