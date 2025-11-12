# GitHub Sync Quick Reference Card

**Keep this handy!** 📋 One-page reference for syncing GitHub changes to your local repository.

---

## 🚀 Daily Sync (Most Common)

```bash
git checkout main
git pull origin main
```

**That's it!** Your files are now synced with GitHub. ✅

---

## 📦 If Dependencies Changed

After pulling, if you see changes to `package.json` or `requirements.lock`:

```bash
npm install                              # Root + Frontend
cd backend && pip install -r requirements.lock  # Backend
```

---

## 🤖 Automated Sync (Recommended)

**Linux/Mac:**
```bash
./scripts/sync-from-github.sh
```

**Windows:**
```powershell
.\scripts\sync-from-github.ps1
```

---

## ✅ Verify Sync

```bash
git status                # Should be clean
git log --oneline -5     # See recent commits
git diff origin/main     # Should be empty if synced
```

---

## 🔀 Common Workflows

### Start New Work
```bash
git checkout main
git pull origin main
git checkout -b feature/my-feature
# Make changes...
```

### Commit and Push
```bash
git add .
git commit -m "feat: description"
git push origin feature/my-feature
```

### After PR Merged
```bash
git checkout main
git pull origin main
git branch -d feature/my-feature
```

---

## 🚨 Quick Fixes

### "I have uncommitted changes"
```bash
git stash                # Save changes
git pull origin main     # Pull updates
git stash pop           # Restore changes
```

### "Merge conflict!"
```bash
# 1. Open conflicted files
# 2. Look for <<<<<<< markers
# 3. Choose correct version
# 4. Remove markers
git add <files>
git commit -m "merge: resolve conflicts"
```

### "My files didn't update"
```bash
git fetch origin --prune
git pull origin main
# Check if on right branch: git branch
```

---

## 📚 Full Documentation

| Quick Link | Purpose |
|------------|---------|
| [SYNC_GUIDE.md](./SYNC_GUIDE.md) | Detailed sync guide |
| [GITHUB_WORKFLOW.md](./GITHUB_WORKFLOW.md) | Visual workflows |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | Complete guide |

---

## 💡 Key Concepts

**Core Files** = Your working directory files (`backend/`, `frontend/`, etc.)

**The Flow:**
```
GitHub → git pull → Core Files Updated ✅
```

**Dependencies** = Separate step after pulling:
```
npm install / pip install
```

---

## 🎯 Remember

1. `git pull` **automatically** updates your files
2. Never manually copy files from GitHub
3. Install dependencies separately if needed
4. Use the automation script for easy sync

---

**Quick Help:** See [docs/README.md](./README.md) for full documentation index
