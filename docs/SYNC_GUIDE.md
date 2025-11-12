# Quick Guide: Syncing GitHub Changes to Your Local Files

This is a **simplified guide** for ensuring all GitHub changes (from pull requests and commits) are reflected in your local core files.

---

## The 3-Step Process

### Step 1: Fetch Changes from GitHub

```bash
# Download all updates from GitHub
git fetch origin
```

This downloads changes but **doesn't modify your files yet**.

### Step 2: Pull Changes into Your Branch

```bash
# Update your current branch
git pull origin main

# Or for a different branch:
git pull origin <branch-name>
```

This **updates your files** with the changes from GitHub.

### Step 3: Install Updated Dependencies

```bash
# If backend dependencies changed:
cd backend
pip install -r requirements.lock

# If frontend dependencies changed:
cd frontend
npm install

# If root package.json changed:
cd ..
npm install
```

This ensures all libraries are up-to-date.

---

## When to Sync

### Daily (Recommended)
```bash
# Before starting work each day:
git checkout main
git pull origin main
```

### Before Creating a Pull Request
```bash
# Make sure you have latest changes:
git checkout main
git pull origin main
git checkout your-feature-branch
git merge main
```

### After a Pull Request is Merged
```bash
# Get the newly merged code:
git checkout main
git pull origin main
```

### After Reviewing Someone's PR
```bash
# To test their changes locally:
git fetch origin
git checkout origin/their-branch-name
```

---

## Verification: Did It Work?

### Check 1: View Recent Commits
```bash
git log --oneline -10
```
You should see the latest commits from GitHub.

### Check 2: Check File Modification Times
```bash
# Linux/Mac:
ls -lt backend/app/ | head -5
ls -lt frontend/src/ | head -5

# Windows (PowerShell):
Get-ChildItem backend\app\ | Sort-Object LastWriteTime -Descending | Select-Object -First 5
```
Recently updated files should show recent timestamps.

### Check 3: Compare with GitHub
```bash
# See if your local matches remote:
git fetch origin
git diff main origin/main
```
If output is empty, you're fully synced! ✅

---

## Common Scenarios

### Scenario 1: Someone Merged a PR, I Need That Code

```bash
git checkout main
git pull origin main
```

✅ **Done!** Your files now have that merged code.

### Scenario 2: A PR is Under Review, I Want to Test It

```bash
# Option A: Checkout the PR branch
git fetch origin
git checkout pr-branch-name

# Option B: Pull the PR locally
git fetch origin pull/123/head:pr-123
git checkout pr-123
```

### Scenario 3: Multiple PRs Merged, Update Everything

```bash
# Get all branches updated:
git fetch --all --prune

# Update main:
git checkout main
git pull origin main

# Update your feature branch:
git checkout your-feature
git merge main
```

### Scenario 4: I Changed Files But Need GitHub Updates Too

```bash
# Option A: Stash your changes temporarily
git stash
git pull origin main
git stash pop

# Option B: Commit first, then pull
git add .
git commit -m "wip: temporary commit"
git pull origin main
```

---

## Understanding the Core Files

The **"core files"** are the actual source code files in your working directory:

| Directory | Core Files |
|-----------|------------|
| `backend/` | Python API code, trading logic, database models |
| `frontend/` | React components, TypeScript code, UI logic |
| `scripts/` | Automation and utility scripts |
| `.github/workflows/` | CI/CD configuration |

**Key Point**: These files are **automatically updated** when you run `git pull`. You don't need to manually copy anything!

---

## What Happens Behind the Scenes

```
┌─────────────────────────────────────┐
│  GitHub Repository (Remote)         │
│  - Has all PRs and commits          │
└──────────────┬──────────────────────┘
               │ git fetch/pull
               ▼
┌─────────────────────────────────────┐
│  .git Directory (Local)             │
│  - Git database of all history      │
└──────────────┬──────────────────────┘
               │ Git automatically updates
               ▼
┌─────────────────────────────────────┐
│  Working Directory (Your Files)     │
│  - backend/, frontend/, etc.        │
│  - The actual code you edit         │
└─────────────────────────────────────┘
```

When you `git pull`:
1. Git downloads changes to `.git/` directory
2. Git automatically updates your working files
3. Core files now match GitHub! ✅

---

## Dependencies: The Extra Step

**Important**: `git pull` updates code files, but **not installed dependencies**.

### Files That Require Re-Installation

| File | Action Required |
|------|----------------|
| `backend/requirements.lock` | Run `pip install -r requirements.lock` |
| `frontend/package.json` | Run `npm install` |
| `package.json` (root) | Run `npm install` |
| `docker-compose.yml` | Run `docker-compose pull` |

### How to Know If You Need to Reinstall

```bash
# See what files changed:
git diff HEAD~1 HEAD --name-only

# If you see requirements.lock or package.json:
# → Re-run the install commands!
```

---

## Troubleshooting

### "My files didn't update after git pull"

**Check:**
1. Are you on the right branch? → `git branch`
2. Do you have uncommitted changes blocking the pull? → `git status`
3. Did the pull actually succeed? → Look for error messages

**Fix:**
```bash
# If you have uncommitted changes:
git stash
git pull origin main
git stash pop

# If on wrong branch:
git checkout main
git pull origin main
```

### "I see old code even after pulling"

**Possible causes:**
1. **Cached build artifacts**: 
   ```bash
   # Backend
   find . -name "*.pyc" -delete
   find . -type d -name "__pycache__" -exec rm -rf {} +
   
   # Frontend
   rm -rf frontend/.next
   rm -rf frontend/node_modules/.cache
   ```

2. **Wrong branch**:
   ```bash
   git branch  # Verify you're on the right branch
   ```

3. **Dependencies not updated**:
   ```bash
   cd backend && pip install -r requirements.lock
   cd ../frontend && npm install
   ```

### "Git says 'already up to date' but I know there are changes"

```bash
# Your local tracking might be stale:
git fetch origin --prune

# Then try again:
git pull origin main
```

---

## Best Practices

### ✅ DO

- Pull changes before starting work each day
- Commit your work before pulling
- Check `git status` before pulling
- Reinstall dependencies after pulling
- Verify changes with `git log`

### ❌ DON'T

- Work directly on main branch (use feature branches)
- Forget to commit before pulling
- Ignore merge conflicts
- Skip dependency installation
- Force push to shared branches

---

## Quick Reference Card

```bash
# Daily sync routine:
git checkout main           # Switch to main branch
git pull origin main        # Get latest changes
git log --oneline -5       # Verify what changed

# If dependencies changed:
cd backend && pip install -r requirements.lock
cd ../frontend && npm install
cd .. && npm install

# Start new work:
git checkout -b feature/my-work   # Create feature branch

# When done:
git add .
git commit -m "feat: my changes"
git push origin feature/my-work
# Then create PR on GitHub
```

---

## Summary

**The core principle**: 

> `git pull` automatically updates your core files to match GitHub. Just remember to reinstall dependencies when needed!

Three simple steps:
1. **Fetch**: `git fetch origin` (optional but safe)
2. **Pull**: `git pull origin main` (updates files)
3. **Install**: Run `npm install` or `pip install` if dependencies changed

That's it! Your local core files now match GitHub. 🎉

---

## Need More Details?

See the full [CONTRIBUTING.md](../CONTRIBUTING.md) guide for:
- Creating pull requests
- Handling merge conflicts  
- CI/CD pipeline details
- Advanced Git workflows
- Complete troubleshooting guide
