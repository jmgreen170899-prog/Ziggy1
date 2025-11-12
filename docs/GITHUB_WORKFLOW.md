# GitHub Workflow: Complete Visual Guide

This document provides a **visual representation** of how changes flow from GitHub to your local repository.

---

## The Complete Flow Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                     GitHub (Remote Origin)                      │
│  https://github.com/jmgreen170899-prog/ZiggyAI                 │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   Main       │  │  Feature     │  │   Other      │        │
│  │   Branch     │  │  Branches    │  │   PRs        │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
└────────────────────────────────────────────────────────────────┘
                              │
                              │ git fetch / git pull
                              ▼
┌────────────────────────────────────────────────────────────────┐
│                   Your Local Git Repository                     │
│  Location: /home/runner/work/ZiggyAI/ZiggyAI/.git             │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Git Object Database                                     │ │
│  │  - Commits, trees, blobs                                 │ │
│  │  - Branch pointers                                       │ │
│  │  - Remote tracking branches                              │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
                              │
                              │ git checkout / automatic
                              ▼
┌────────────────────────────────────────────────────────────────┐
│              Working Directory (Core Files)                     │
│  Location: /home/runner/work/ZiggyAI/ZiggyAI/                 │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │  backend/   │  │  frontend/  │  │  scripts/   │          │
│  │  - Python   │  │  - React    │  │  - Tools    │          │
│  │  - FastAPI  │  │  - TypeScript│  │  - Configs  │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└────────────────────────────────────────────────────────────────┘
                              │
                              │ npm install / pip install
                              ▼
┌────────────────────────────────────────────────────────────────┐
│                  Installed Dependencies                         │
│                                                                 │
│  ┌─────────────────┐         ┌──────────────────┐            │
│  │ node_modules/   │         │  .venv/          │            │
│  │ (frontend deps) │         │  (Python env)    │            │
│  └─────────────────┘         └──────────────────┘            │
└────────────────────────────────────────────────────────────────┘
```

---

## Workflow 1: Daily Sync (Getting Latest Changes)

### Before You Start

```
You                     Local Repo              GitHub
 │                          │                       │
 │                          │  May be outdated      │  Has new commits
 │                          │                       │
```

### Step 1: Fetch

```bash
git fetch origin
```

```
You                     Local Repo              GitHub
 │                          │                       │
 │ ─────── fetch ──────────────────────────────────▶│
 │                          │                       │
 │                          │◀──── downloads ───────│
 │                          │  (metadata only)      │
 │                          │                       │
 │                    [.git updated]                │
 │                  [files unchanged]               │
```

**What happened**: Git database updated, but your files didn't change yet.

### Step 2: Pull

```bash
git pull origin main
```

```
You                     Local Repo              GitHub
 │                          │                       │
 │ ─────── pull ───────────▶│                       │
 │                          │                       │
 │                          │ Merges changes        │
 │                          │ into working dir      │
 │                          ▼                       │
 │                    [Files updated!]              │
 │                     backend/...                  │
 │                     frontend/...                 │
```

**What happened**: Your core files now match GitHub! ✅

### Step 3: Install Dependencies (If Needed)

```bash
npm install
pip install -r requirements.lock
```

```
You                  Dependencies            Core Files
 │                          │                    │
 │ ── npm install ─────────▶│                    │
 │                          │                    │
 │                    [Reads package.json] ──────│
 │                          │                    │
 │                    [Installs to               │
 │                     node_modules/]            │
 │                          │                    │
 │◀─── Ready to run ────────│                    │
```

**What happened**: Dependencies now match what the code needs! ✅

---

## Workflow 2: Creating and Merging a Pull Request

### Creating a PR

```
Step 1: Create Branch
┌─────────────┐
│    main     │
└──────┬──────┘
       │
       │ git checkout -b feature/new-feature
       │
       ├─────────────┐
       │             │
   ┌───▼────┐  ┌────▼────────┐
   │  main  │  │  feature/   │
   │        │  │  new-feature│
   └────────┘  └─────────────┘


Step 2: Make Changes
┌─────────────────┐
│  feature/       │
│  new-feature    │
│                 │
│  [commit A]     │
│  [commit B]     │
│  [commit C]     │
└─────────────────┘
       │
       │ git push origin feature/new-feature
       ▼
┌─────────────────┐
│  GitHub:        │
│  feature/       │
│  new-feature    │
└─────────────────┘


Step 3: Create PR on GitHub
┌────────────────────────────────┐
│  Pull Request #123             │
│                                │
│  feature/new-feature → main    │
│                                │
│  [CI Tests Running...]         │
│  ✅ All checks passed          │
│                                │
│  [Review Comments]             │
│  [Approve] [Request Changes]   │
└────────────────────────────────┘


Step 4: Merge PR
         Before                    After
    ┌────────────┐           ┌────────────┐
    │    main    │           │    main    │
    │            │           │            │
    │ [older]    │           │ [commit A] │
    └────────────┘           │ [commit B] │
                             │ [commit C] │
         +                   └────────────┘
    ┌────────────┐
    │  feature/  │           Feature branch
    │            │           can be deleted
    │ [commit A] │
    │ [commit B] │
    │ [commit C] │
    └────────────┘
```

### After PR is Merged

Everyone on the team needs to sync:

```
Team Member A                Team Member B
      │                            │
      │ git pull origin main       │ git pull origin main
      ▼                            ▼
[Gets commits A, B, C]       [Gets commits A, B, C]
      │                            │
      ▼                            ▼
[Local files updated]        [Local files updated]
```

---

## Workflow 3: Handling Merge Conflicts

### The Scenario

```
GitHub (main)          Your Branch (feature)
      │                        │
      │                        │
[commit X]                [commit X]
      │                        │
[commit Y] ◀────┐              │
  └─ edit file.py│              │
                 │         [commit A]
                 │           └─ also edit file.py
                 │              │
                 └──────┬───────┘
                        │
                  CONFLICT!
```

### Resolution Process

```bash
# Step 1: Try to merge
git merge origin/main
# Output: CONFLICT in backend/app/file.py

# Step 2: Git marks conflicts in the file
┌──────────────────────────────────────┐
│ backend/app/file.py                  │
│                                      │
│ def some_function():                 │
│ <<<<<<< HEAD (your changes)         │
│     return "your version"            │
│ =======                              │
│     return "their version"           │
│ >>>>>>> origin/main                  │
│                                      │
└──────────────────────────────────────┘

# Step 3: You edit and choose
┌──────────────────────────────────────┐
│ backend/app/file.py                  │
│                                      │
│ def some_function():                 │
│     return "merged version"          │
│                                      │
└──────────────────────────────────────┘

# Step 4: Mark as resolved
git add backend/app/file.py
git commit -m "merge: resolve conflicts"
```

---

## Workflow 4: CI/CD Integration

### Pull Request with CI

```
1. Developer                  2. GitHub               3. CI System
   │                             │                        │
   │ git push                    │                        │
   │────────────────────────────▶│                        │
   │                             │                        │
   │                             │ Trigger CI             │
   │                             │───────────────────────▶│
   │                             │                        │
   │                             │                        │ Run Tests
   │                             │                        │ ├─ pytest
   │                             │                        │ ├─ type check
   │                             │                        │ └─ lint
   │                             │                        │
   │                             │ ◀─── Report Results ───│
   │                             │    ✅ All passed       │
   │ ◀─── View Status ───────────│                        │
   │    ✅ Checks passed         │                        │
   │                             │                        │
   │ Click "Merge"               │                        │
   │────────────────────────────▶│                        │
   │                             │                        │
   │                             │ Merge to main          │
   │                             │ └─ Update core files   │
```

### What CI Checks

```
┌─────────────────────────────────────────┐
│  CI Pipeline (.github/workflows/ci.yml) │
│                                         │
│  ┌────────────────────────────────┐   │
│  │ 1. Setup Python 3.11           │   │
│  └────────────────────────────────┘   │
│             │                          │
│  ┌──────────▼──────────────────────┐  │
│  │ 2. Install Dependencies         │  │
│  │    pip install -r requirements  │  │
│  └──────────┬──────────────────────┘  │
│             │                          │
│  ┌──────────▼──────────────────────┐  │
│  │ 3. Run Tests                    │  │
│  │    cd backend                   │  │
│  │    pytest -q -m "not slow"      │  │
│  └──────────┬──────────────────────┘  │
│             │                          │
│  ┌──────────▼──────────────────────┐  │
│  │ 4. Report Results               │  │
│  │    ✅ Pass → Allow merge        │  │
│  │    ❌ Fail → Block merge        │  │
│  └─────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

---

## Timeline View: A Day in the Life

```
09:00 - Start of Day
│
│ git checkout main
│ git pull origin main
│ [Files synced with GitHub]
│
├─ 09:15 - Start New Feature
│  │
│  │ git checkout -b feature/add-widget
│  │ [Edit files...]
│  │
│  ├─ 10:30 - First Commit
│  │  git commit -m "feat: add widget skeleton"
│  │
│  ├─ 11:45 - Another Commit
│  │  git commit -m "feat: add widget logic"
│  │
│  └─ 12:00 - Push to GitHub
│     git push origin feature/add-widget
│     [Create PR on GitHub]
│
├─ 13:00 - Teammate Merges Their PR
│  │ [main branch on GitHub updated]
│  │
│  └─ Need to sync your feature branch:
│     git checkout main
│     git pull origin main
│     git checkout feature/add-widget
│     git merge main
│
├─ 14:00 - Address Review Comments
│  │ [Edit files based on feedback]
│  │ git commit -m "fix: address review comments"
│  │ git push origin feature/add-widget
│  │ [PR automatically updates]
│
├─ 15:00 - PR Approved and Merged
│  │ [Click merge on GitHub]
│  │ [Your changes now in main]
│  │
│  └─ Clean up:
│     git checkout main
│     git pull origin main
│     git branch -d feature/add-widget
│
└─ 16:00 - Everyone Else Syncs
   │ Team member A: git pull origin main
   │ Team member B: git pull origin main
   │ [Everyone has your changes now]
```

---

## Common Patterns

### Pattern 1: Feature Development

```
main ──●────●────●────●────●────●────●──▶
       │              │              │
       │              │         ┌────●────● feature/b
       │              │         │    
       │         ┌────●────●────●  feature/a (merged)
       │         │    
       └─────────┘
```

### Pattern 2: Hotfix

```
main ──●────●────●────●────●──▶
                 │    │
                 │    └─●  hotfix (fast)
                 │      │
                 └──────┘
```

### Pattern 3: Long-Running Feature

```
main ──●────●────●────●────●────●──▶
       │         ↓         ↓
       └────●────●────●────●  feature (sync with main periodically)
```

---

## Checklist: "Are My Files Synced?"

Use this checklist to verify your local files match GitHub:

```
□ 1. Checked current branch:
     git branch
     
□ 2. Fetched latest from GitHub:
     git fetch origin
     
□ 3. Pulled changes into my branch:
     git pull origin main
     
□ 4. Verified no uncommitted changes blocking:
     git status
     
□ 5. Checked recent commits match:
     git log --oneline -5
     
□ 6. Compared with remote:
     git diff main origin/main
     (should be empty if synced)
     
□ 7. Reinstalled dependencies if needed:
     - Check if package.json changed → npm install
     - Check if requirements.lock changed → pip install
     
□ 8. Cleared build artifacts:
     - Deleted __pycache__/ folders
     - Deleted .next/ folder
     
✅ All checks passed = Files are synced!
```

---

## Summary

The key takeaway:

> **Git automatically updates your core files when you pull. The flow is:**
> 
> 1. **GitHub** (source of truth)
> 2. **git pull** (sync mechanism)
> 3. **Working Directory** (your core files)
> 4. **npm/pip install** (dependencies)

Follow this flow, and your local files will always reflect GitHub changes! 🎉

---

## Related Documentation

- [CONTRIBUTING.md](../CONTRIBUTING.md) - Full contributing guide
- [SYNC_GUIDE.md](./SYNC_GUIDE.md) - Quick sync reference
- [README-dev.md](../implements/README-dev.md) - Development setup
