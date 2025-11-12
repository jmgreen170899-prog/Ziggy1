# Contributing to ZiggyAI

Thank you for your interest in contributing to ZiggyAI! This guide explains how to ensure that all changes made through GitHub (pull requests, commits, etc.) are properly reflected in the core repository files.

## Table of Contents

1. [Understanding the Repository Structure](#understanding-the-repository-structure)
2. [GitHub Workflow Overview](#github-workflow-overview)
3. [Syncing Changes from GitHub to Local](#syncing-changes-from-github-to-local)
4. [Creating and Managing Pull Requests](#creating-and-managing-pull-requests)
5. [CI/CD Pipeline](#cicd-pipeline)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Understanding the Repository Structure

ZiggyAI is a full-stack trading application with the following core components:

### Core Directories

- **`backend/`** - FastAPI backend with trading logic, paper trading engine, and APIs
- **`frontend/`** - React/Vite frontend with trading dashboard and UI components
- **`scripts/`** - Automation scripts for development and deployment
- **`tools/`** - Audit and analysis tools
- **`.github/workflows/`** - CI/CD automation

### Important Files

- **`package.json`** - Root-level npm scripts and dependencies
- **`Makefile`** - Build and audit commands
- **`docker-compose.yml`** - Container orchestration
- **`.gitignore`** - Files excluded from version control

---

## GitHub Workflow Overview

### The Flow: GitHub → Local → Core Files

```
GitHub Repository (Remote)
    ↓
Pull/Fetch Changes
    ↓
Local Repository (Your Machine)
    ↓
Build/Test/Verify
    ↓
Core Files Updated
```

### Key Concepts

1. **Remote Repository**: The source of truth on GitHub (`origin`)
2. **Local Repository**: Your working copy with `.git` directory
3. **Working Directory**: The actual files you edit
4. **Pull Requests**: Proposed changes awaiting review and merge
5. **CI/CD**: Automated tests that run on every change

---

## Syncing Changes from GitHub to Local

### Initial Setup (First Time Only)

```bash
# Clone the repository
git clone https://github.com/jmgreen170899-prog/ZiggyAI.git
cd ZiggyAI

# Verify remote is set up
git remote -v
# Should show:
# origin  https://github.com/jmgreen170899-prog/ZiggyAI (fetch)
# origin  https://github.com/jmgreen170899-prog/ZiggyAI (push)
```

### Regular Workflow: Keeping Your Local Copy Updated

#### Step 1: Check Current Status

```bash
# See what branch you're on and if you have uncommitted changes
git status

# View recent commits
git log --oneline -10
```

#### Step 2: Fetch All Changes from GitHub

```bash
# Download all changes from GitHub without modifying your files
git fetch origin

# See what branches exist remotely
git branch -a
```

#### Step 3: Pull Changes into Your Current Branch

```bash
# Update your current branch with changes from GitHub
git pull origin main

# Or for a specific branch:
git pull origin <branch-name>
```

#### Alternative: Update All Branches

```bash
# Fetch all changes
git fetch --all --prune

# Switch to main and update
git checkout main
git pull origin main

# Update other branches
git checkout <other-branch>
git pull origin <other-branch>
```

### Ensuring Core Files Are Updated

After pulling changes, **verify** that your core files reflect the updates:

```bash
# 1. Check file timestamps
ls -lt backend/app/ | head -10
ls -lt frontend/src/ | head -10

# 2. View recent changes
git log --name-status -5

# 3. See what files changed
git diff HEAD~1 HEAD --name-only
```

### Installing Dependencies After Updates

When changes include dependency updates, you must reinstall:

```bash
# Frontend dependencies (if package.json changed)
cd frontend
npm install

# Backend dependencies (if requirements changed)
cd ../backend
pip install -r requirements.lock

# Root dependencies (if package.json at root changed)
cd ..
npm install
```

---

## Creating and Managing Pull Requests

### Creating a Pull Request

#### Step 1: Create a Feature Branch

```bash
# Create and switch to a new branch
git checkout -b feature/your-feature-name

# Or for bug fixes:
git checkout -b fix/issue-description
```

#### Step 2: Make Your Changes

Edit the necessary files, then:

```bash
# See what you changed
git status
git diff

# Stage your changes
git add <file1> <file2>
# Or stage all changes:
git add .

# Commit with a descriptive message
git commit -m "feat: add new trading signal algorithm"
```

#### Step 3: Push to GitHub

```bash
# Push your branch to GitHub
git push origin feature/your-feature-name
```

#### Step 4: Create PR on GitHub

1. Go to https://github.com/jmgreen170899-prog/ZiggyAI
2. Click "Pull requests" → "New pull request"
3. Select your branch as the source
4. Fill in the PR description explaining your changes
5. Click "Create pull request"

### Reviewing and Updating Pull Requests

When reviewers request changes:

```bash
# Make the requested changes in your files
# Then commit and push:
git add .
git commit -m "fix: address review comments"
git push origin feature/your-feature-name

# The PR automatically updates!
```

### Merging Pull Requests

Once approved:

1. **GitHub Web UI**: Click "Merge pull request" button
2. **Command Line**:
   ```bash
   # Switch to main branch
   git checkout main
   
   # Pull latest changes
   git pull origin main
   
   # Merge your feature branch
   git merge feature/your-feature-name
   
   # Push to GitHub
   git push origin main
   ```

### After Merge: Sync Your Local Repository

```bash
# Switch to main
git checkout main

# Pull the merged changes
git pull origin main

# Your local files now have the merged changes!

# Optional: Delete the feature branch
git branch -d feature/your-feature-name
git push origin --delete feature/your-feature-name
```

---

## CI/CD Pipeline

### Understanding Automated Checks

ZiggyAI has automated tests that run on every pull request. See `.github/workflows/ci.yml`:

```yaml
# Triggers:
- On pull requests affecting backend/
- On pushes to main branch

# Tests:
- Python 3.11 environment
- Install backend dependencies
- Run pytest tests (non-slow tests only)
```

### How CI Ensures Core Files Stay Healthy

1. **Automated Testing**: Every PR runs tests before merge
2. **Code Quality**: Lint checks prevent broken code
3. **Isolation**: Tests use isolated environments
4. **Fast Feedback**: You know immediately if changes break anything

### Viewing CI Results

After pushing to a PR:

1. Go to your PR on GitHub
2. Scroll to "Checks" section
3. See ✅ (passed) or ❌ (failed)
4. Click "Details" to see logs

### Running CI Tests Locally (Before Pushing)

```bash
# Backend tests
cd backend
pytest -q -m "not slow"

# Frontend type checking
cd ../frontend
npm run type-check

# Full audit (if time permits)
cd ..
make audit-quick
```

---

## Best Practices

### 1. Always Pull Before Starting Work

```bash
# Every day before coding:
git checkout main
git pull origin main
git checkout -b feature/new-work
```

### 2. Commit Frequently with Clear Messages

```bash
# Good commit messages:
git commit -m "feat: add WebSocket reconnection logic"
git commit -m "fix: resolve NaN display in portfolio widget"
git commit -m "docs: update API endpoint documentation"
git commit -m "test: add unit tests for paper trading engine"

# Bad commit messages:
git commit -m "updates"
git commit -m "fix stuff"
git commit -m "wip"
```

### 3. Keep Branches Short-Lived

- Create a branch
- Make focused changes
- Create PR
- Merge quickly
- Delete branch

### 4. Review Your Own Changes First

```bash
# Before pushing:
git diff origin/main...HEAD

# Review what you're about to push:
git log origin/main..HEAD --oneline
```

### 5. Use .gitignore Properly

Never commit:
- `node_modules/`
- `.next/`
- `__pycache__/`
- `.venv/`
- `*.pyc`
- `.env` files with secrets
- Build artifacts

### 6. Handle Merge Conflicts Carefully

When conflicts occur:

```bash
# Pull latest changes
git pull origin main

# Git will tell you which files have conflicts
# Edit those files, look for:
<<<<<<< HEAD
your changes
=======
their changes
>>>>>>> branch-name

# Choose the correct version or merge both
# Then:
git add <conflicted-files>
git commit -m "merge: resolve conflicts with main"
git push origin your-branch
```

---

## Troubleshooting

### Problem: "Your local files don't have GitHub changes"

**Solution:**

```bash
# 1. Check which branch you're on
git branch

# 2. Make sure you're on the right branch
git checkout main

# 3. Fetch all changes
git fetch origin

# 4. Pull changes
git pull origin main

# 5. Verify update
git log --oneline -5
```

### Problem: "I made changes but they're not on GitHub"

**Solution:**

```bash
# 1. Check if you committed
git status
git log -1

# 2. Check if you pushed
git log origin/main..HEAD

# 3. If not pushed:
git push origin your-branch
```

### Problem: "Merge conflicts are blocking me"

**Solution:**

```bash
# Option 1: Rebase (cleaner history)
git fetch origin
git rebase origin/main
# Resolve conflicts in each file
git add <resolved-files>
git rebase --continue

# Option 2: Merge (safer)
git merge origin/main
# Resolve conflicts
git add <resolved-files>
git commit -m "merge: resolve conflicts"

# Push
git push origin your-branch
```

### Problem: "CI tests fail but work locally"

**Reasons:**
- Different environment (Python version, Node version)
- Missing environment variables
- Database state differences

**Solution:**

```bash
# Check CI logs on GitHub
# Look for error messages
# Reproduce locally:

# Backend:
cd backend
ZIGGY_TEST_MODE=1 VECDB_BACKEND=memory pytest -q

# Frontend:
cd frontend
npm run test
```

### Problem: "I accidentally committed secrets"

**Solution:**

```bash
# If NOT yet pushed:
git reset HEAD~1  # Undo last commit
# Edit .gitignore to exclude the file
# Recommit without the secrets

# If already pushed:
# 1. Rotate the secrets immediately!
# 2. Use git-filter-branch or BFG Repo-Cleaner
# 3. Force push (contact maintainer)
```

### Problem: "Dependencies are out of sync"

**Solution:**

```bash
# After pulling changes that modify dependencies:

# Frontend
cd frontend
rm -rf node_modules package-lock.json
npm install

# Backend
cd ../backend
pip install --upgrade -r requirements.lock

# Root
cd ..
rm -rf node_modules package-lock.json
npm install
```

---

## Quick Reference Commands

### Daily Workflow

```bash
# Start of day
git checkout main
git pull origin main

# Start new work
git checkout -b feature/my-feature

# During work
git add .
git commit -m "feat: description"

# Push to GitHub
git push origin feature/my-feature

# End of day / create PR
# Go to GitHub and create pull request

# After PR merged
git checkout main
git pull origin main
git branch -d feature/my-feature
```

### Common Git Commands

```bash
# Status and history
git status                    # What changed?
git log --oneline -10        # Recent commits
git diff                     # What did I edit?
git branch -a               # All branches

# Moving between branches
git checkout main           # Switch to main
git checkout -b new-branch  # Create and switch

# Syncing
git fetch origin           # Download changes
git pull origin main       # Download and merge
git push origin branch     # Upload your changes

# Undoing things (careful!)
git reset HEAD~1           # Undo last commit (keep changes)
git checkout -- file.txt   # Discard changes to file
git clean -fd              # Remove untracked files

# Merging
git merge other-branch     # Merge other-branch into current
git rebase main           # Rebase current onto main
```

---

## Additional Resources

- **Git Documentation**: https://git-scm.com/doc
- **GitHub Flow**: https://guides.github.com/introduction/flow/
- **ZiggyAI Architecture**: See `implements/ZiggyAI_FULL_WRITEUP.md`
- **Development Setup**: See `implements/README-dev.md`
- **Audit System**: See `implements/AUDIT_README.md`

---

## Getting Help

If you're stuck:

1. Check this guide's troubleshooting section
2. Review existing pull requests for examples
3. Check GitHub Issues for similar problems
4. Ask in team chat or discussions

Remember: **The key to keeping core files synced is regular `git pull` and understanding when to run build/install commands after pulling changes!**
