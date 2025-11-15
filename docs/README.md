# ZiggyAI Documentation

Welcome to the ZiggyAI documentation! This directory contains comprehensive guides for working with the ZiggyAI repository.

## 📚 Available Documentation

### Getting Started

- **[SYNC_GUIDE.md](./SYNC_GUIDE.md)** - Quick reference for syncing GitHub changes to your local repository
  - Perfect for: Daily workflow, quick lookups
  - Time to read: 5 minutes

### Workflow & Process

- **[GITHUB_WORKFLOW.md](./GITHUB_WORKFLOW.md)** - Visual guide to GitHub workflows
  - Perfect for: Understanding the complete flow, visual learners
  - Time to read: 10 minutes
  - Includes: Diagrams, timelines, common patterns

- **[../CONTRIBUTING.md](../CONTRIBUTING.md)** - Complete contributing guide
  - Perfect for: In-depth understanding, troubleshooting
  - Time to read: 20 minutes
  - Includes: Detailed workflows, best practices, comprehensive troubleshooting

### Architecture & Technical

- **[IntegrationSystem.md](./IntegrationSystem.md)** - Integration architecture
- **[LearningSystem.md](./LearningSystem.md)** - Machine learning system details
- **[UI_AUDIT_SYSTEM.md](./UI_AUDIT_SYSTEM.md)** - UI auditing system
- **[ZiggyContext.md](./ZiggyContext.md)** - Overall system context

### Development

- **[../implements/README-dev.md](../implements/README-dev.md)** - Development environment setup
- **[../implements/AUDIT_README.md](../implements/AUDIT_README.md)** - Code health audit system

---

## 🚀 Quick Start: Syncing Changes from GitHub

### The Problem

You need to ensure all changes from GitHub (pull requests, commits) are reflected in your local files.

### The Solution

**Three simple steps:**

```bash
# 1. Fetch changes
git fetch origin

# 2. Pull into your branch
git pull origin main

# 3. Install dependencies (if needed)
npm install
pip install -r backend/requirements.lock
```

**Or use our automated script:**

```bash
# Linux/Mac
./scripts/sync-from-github.sh

# Windows
.\scripts\sync-from-github.ps1
```

---

## 📖 Documentation Quick Reference

### I want to...

| Goal                                 | Documentation                                                             | Estimated Time |
| ------------------------------------ | ------------------------------------------------------------------------- | -------------- |
| **Sync my local files with GitHub**  | [SYNC_GUIDE.md](./SYNC_GUIDE.md)                                          | 5 min          |
| **Understand the complete workflow** | [GITHUB_WORKFLOW.md](./GITHUB_WORKFLOW.md)                                | 10 min         |
| **Create my first pull request**     | [CONTRIBUTING.md](../CONTRIBUTING.md#creating-and-managing-pull-requests) | 5 min          |
| **Resolve merge conflicts**          | [CONTRIBUTING.md](../CONTRIBUTING.md#troubleshooting)                     | 10 min         |
| **Set up my dev environment**        | [README-dev.md](../implements/README-dev.md)                              | 15 min         |
| **Run code health audits**           | [AUDIT_README.md](../implements/AUDIT_README.md)                          | 10 min         |
| **Understand CI/CD pipeline**        | [CONTRIBUTING.md](../CONTRIBUTING.md#cicd-pipeline)                       | 5 min          |
| **Fix "my files aren't syncing"**    | [SYNC_GUIDE.md](./SYNC_GUIDE.md#troubleshooting)                          | 5 min          |

---

## 🎯 Common Scenarios

### Scenario 1: Daily Development

**Morning routine:**

```bash
git checkout main
git pull origin main
git checkout -b feature/my-work
# Start coding...
```

**See:** [SYNC_GUIDE.md - When to Sync](./SYNC_GUIDE.md#when-to-sync)

### Scenario 2: Someone Merged a PR

**Get their changes:**

```bash
git checkout main
git pull origin main
# Your files now have their changes!
```

**See:** [GITHUB_WORKFLOW.md - After PR is Merged](./GITHUB_WORKFLOW.md#after-pr-is-merged)

### Scenario 3: Creating a Pull Request

**Complete workflow:**

```bash
# Create branch
git checkout -b feature/new-feature

# Make changes, commit
git add .
git commit -m "feat: add new feature"

# Push to GitHub
git push origin feature/new-feature

# Create PR on GitHub web UI
```

**See:** [CONTRIBUTING.md - Creating Pull Requests](../CONTRIBUTING.md#creating-and-managing-pull-requests)

### Scenario 4: Merge Conflicts

**Resolution:**

```bash
git pull origin main
# CONFLICT detected!

# Edit conflicted files
# Look for <<<<<<< HEAD markers

git add <resolved-files>
git commit -m "merge: resolve conflicts"
```

**See:** [CONTRIBUTING.md - Handling Merge Conflicts](../CONTRIBUTING.md#6-handle-merge-conflicts-carefully)

---

## 🛠️ Tools & Scripts

### Sync Script

Automated synchronization with GitHub:

```bash
# Linux/Mac
./scripts/sync-from-github.sh

# Windows
.\scripts\sync-from-github.ps1

# With auto-install dependencies (Windows)
.\scripts\sync-from-github.ps1 -AutoInstall
```

**Features:**

- ✅ Automatic fetch and pull
- ✅ Stash uncommitted changes
- ✅ Detect dependency updates
- ✅ Auto-install dependencies
- ✅ Restore stashed changes
- ✅ Summary and verification

### Audit Commands

Code health and quality checks:

```bash
# Quick checks (fast)
make audit-quick

# Full audit
make audit-all

# Frontend only
make audit-frontend-full

# Backend only
make audit-backend-full
```

**See:** [AUDIT_README.md](../implements/AUDIT_README.md)

### Development Commands

```bash
# Start all services
npm run dev:all

# Backend only
cd backend && uvicorn app.main:app --reload

# Frontend only
cd frontend && npm run dev

# Run tests
cd backend && pytest -q
```

**See:** [README-dev.md](../implements/README-dev.md)

---

## 🔍 Understanding the Flow

### High-Level Overview

```
GitHub (Remote)
    ↓ git fetch
.git Directory (Local Git DB)
    ↓ git checkout/pull
Working Directory (Your Files)
    ↓ npm install / pip install
Dependencies Installed
    ↓
Ready to Code!
```

**Key Points:**

1. **`git pull`** automatically updates your files
2. **Dependencies** must be installed separately
3. **Your files** = the actual code in directories
4. **`.git`** = Git's internal database

**See:** [GITHUB_WORKFLOW.md - Complete Flow Diagram](./GITHUB_WORKFLOW.md#the-complete-flow-diagram)

---

## ❓ FAQ

### Q: How do I know if my files are synced?

**A:** Run these commands:

```bash
git fetch origin
git diff main origin/main  # Should be empty if synced
git status                 # Should be clean
```

**See:** [SYNC_GUIDE.md - Verification](./SYNC_GUIDE.md#verification-did-it-work)

### Q: What are "core files"?

**A:** Core files are the actual source code files in your working directory:

- `backend/` - Python API code
- `frontend/` - React UI code
- `scripts/` - Automation scripts
- Configuration files

**See:** [SYNC_GUIDE.md - Understanding Core Files](./SYNC_GUIDE.md#understanding-the-core-files)

### Q: Do I need to manually copy files from GitHub?

**A:** No! Git automatically updates your files when you `git pull`. Never manually copy files.

### Q: What if I have uncommitted changes?

**A:** Either:

1. Commit them first: `git add . && git commit -m "message"`
2. Stash them: `git stash`
3. Use our sync script which handles this automatically

**See:** [CONTRIBUTING.md - Best Practices](../CONTRIBUTING.md#best-practices)

### Q: What if dependencies changed?

**A:** After pulling, run:

```bash
npm install                         # Root dependencies
cd frontend && npm install          # Frontend
cd ../backend && pip install -r requirements.lock  # Backend
```

**See:** [SYNC_GUIDE.md - Dependencies](./SYNC_GUIDE.md#dependencies-the-extra-step)

### Q: How do I sync a specific branch?

**A:**

```bash
git fetch origin
git checkout branch-name
git pull origin branch-name
```

**See:** [CONTRIBUTING.md - Syncing Changes](../CONTRIBUTING.md#syncing-changes-from-github-to-local)

---

## 🚨 Troubleshooting

### Problem: My files didn't update after `git pull`

**Checklist:**

- [ ] Are you on the right branch? (`git branch`)
- [ ] Did the pull succeed? (check for errors)
- [ ] Do you have uncommitted changes? (`git status`)
- [ ] Did you clear build caches? (delete `.next/`, `__pycache__/`)

**See:** [SYNC_GUIDE.md - Troubleshooting](./SYNC_GUIDE.md#troubleshooting)

### Problem: Merge conflicts

**Solution:**

1. Open conflicted files
2. Look for `<<<<<<<` markers
3. Choose correct version
4. Remove markers
5. `git add` and `git commit`

**See:** [CONTRIBUTING.md - Merge Conflicts](../CONTRIBUTING.md#problem-merge-conflicts-are-blocking-me)

### Problem: Dependencies are broken

**Solution:**

```bash
# Clean install
rm -rf node_modules package-lock.json
npm install

# Backend
cd backend
pip install --upgrade -r requirements.lock
```

**See:** [CONTRIBUTING.md - Dependencies Out of Sync](../CONTRIBUTING.md#problem-dependencies-are-out-of-sync)

---

## 📚 Further Reading

### Git Resources

- [Git Documentation](https://git-scm.com/doc)
- [GitHub Flow Guide](https://guides.github.com/introduction/flow/)
- [Pro Git Book](https://git-scm.com/book/en/v2)

### ZiggyAI Specific

- [Architecture Overview](../implements/ZiggyAI_FULL_WRITEUP.md)
- [Backend Functionality](../implements/ZiggyAI_Backend_Functionality_Explained.txt)
- [Task Documentation](../TASK.md)
- [Issue Reports](../ISSUES.md)

---

## 🤝 Getting Help

1. **Check documentation** in this directory
2. **Search existing issues** on GitHub
3. **Ask in team chat** or discussions
4. **Create an issue** for bugs or feature requests

---

## 📝 Documentation Maintenance

This documentation is maintained by the ZiggyAI team. To update:

1. Edit the relevant `.md` file
2. Create a pull request
3. Request review from a maintainer

**Documentation Structure:**

```
docs/
├── README.md              ← You are here (index)
├── SYNC_GUIDE.md          ← Quick sync reference
├── GITHUB_WORKFLOW.md     ← Visual workflow guide
└── ...other docs

CONTRIBUTING.md            ← Complete contributing guide (root)
```

---

## ✅ Next Steps

**If you're new to the project:**

1. Read [SYNC_GUIDE.md](./SYNC_GUIDE.md) (5 min)
2. Set up your environment: [README-dev.md](../implements/README-dev.md) (15 min)
3. Try the sync script: `./scripts/sync-from-github.sh`

**If you're making your first contribution:**

1. Read [CONTRIBUTING.md](../CONTRIBUTING.md) (20 min)
2. Create a feature branch
3. Make your changes
4. Create a pull request

**If you're debugging an issue:**

1. Check [SYNC_GUIDE.md - Troubleshooting](./SYNC_GUIDE.md#troubleshooting)
2. Check [CONTRIBUTING.md - Troubleshooting](../CONTRIBUTING.md#troubleshooting)
3. Search existing issues on GitHub

---

## 📊 Documentation Stats

- **Total Guides:** 15+
- **Quick Start Time:** 5 minutes
- **Complete Onboarding:** 45 minutes
- **Last Updated:** 2025-11-10

---

**Remember:** Syncing is as simple as `git pull` + dependency installation!

For quick reference, bookmark [SYNC_GUIDE.md](./SYNC_GUIDE.md). 🔖
