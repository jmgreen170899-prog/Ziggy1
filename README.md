# ZiggyAI - Intelligent Trading Platform

ZiggyAI is a full-stack paper trading system with autonomous trading strategies, real-time market data integration, and comprehensive learning capabilities.

## 🚀 Quick Start

### Syncing Changes from GitHub

**Need to update your local files with GitHub changes?**

```bash
# Option 1: Use our automated script (recommended)
./scripts/sync-from-github.sh         # Linux/Mac
.\scripts\sync-from-github.ps1        # Windows

# Option 2: Manual sync
git pull origin main
npm install
pip install -r backend/requirements.lock
```

📖 **See:** [SYNC_GUIDE.md](docs/SYNC_GUIDE.md) for detailed instructions.

### Setting Up Development Environment

```bash
# 1. Clone repository (if not already done)
git clone https://github.com/jmgreen170899-prog/ZiggyAI.git
cd ZiggyAI

# 2. Install dependencies
npm install                                    # Root dependencies
cd frontend && npm install                     # Frontend
cd ../backend && pip install -r requirements.lock  # Backend

# 3. Start services
npm run dev:all                                # All services
# OR individually:
cd backend && uvicorn app.main:app --reload   # Backend only
cd frontend && npm run dev                     # Frontend only
```

📖 **See:** [Development Setup Guide](implements/README-dev.md)

---

## 📚 Documentation

### Essential Guides

| Guide                                             | Purpose                                    | Time   |
| ------------------------------------------------- | ------------------------------------------ | ------ |
| **[SYNC_GUIDE.md](docs/SYNC_GUIDE.md)**           | Quick reference for syncing GitHub changes | 5 min  |
| **[GITHUB_WORKFLOW.md](docs/GITHUB_WORKFLOW.md)** | Visual guide to GitHub workflows           | 10 min |
| **[CONTRIBUTING.md](CONTRIBUTING.md)**            | Complete contributing guide                | 20 min |
| **[README-dev.md](implements/README-dev.md)**     | Development environment setup              | 15 min |
| **[AUDIT_README.md](implements/AUDIT_README.md)** | Code health audit system                   | 10 min |

📂 **Full Documentation:** [docs/README.md](docs/README.md)

---

## 🏗️ Architecture

### Project Structure

```
ZiggyAI/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API routes
│   │   ├── paper/       # Paper trading engine
│   │   └── ...
│   └── requirements.lock
├── frontend/             # React/Vite frontend
│   ├── src/
│   │   ├── components/  # UI components
│   │   ├── services/    # API clients
│   │   └── ...
│   └── package.json
├── scripts/              # Automation scripts
├── tools/                # Audit and analysis tools
├── docs/                 # Documentation
└── .github/workflows/    # CI/CD
```

### Key Technologies

**Backend:**

- Python 3.11
- FastAPI
- SQLAlchemy
- Paper Trading Engine

**Frontend:**

- React 18
- TypeScript
- Vite
- Tailwind CSS

**Infrastructure:**

- Docker & Docker Compose
- PostgreSQL
- CI/CD via GitHub Actions

---

## 🛠️ Common Tasks

### Daily Workflow

```bash
# Start of day: sync with GitHub
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/my-feature

# Make changes, commit
git add .
git commit -m "feat: add new feature"

# Push to GitHub
git push origin feature/my-feature
# Then create PR on GitHub
```

### Running Tests

```bash
# Backend tests
cd backend
pytest -q -m "not slow"

# Frontend tests (if configured)
cd frontend
npm run test
```

### Code Health Audits

```bash
# Quick check (fast)
make audit-quick

# Full audit
make audit-all

# Individual audits
make audit-frontend-full
make audit-backend-full
```

📖 **See:** [Makefile](Makefile) for all available commands

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Sync your local repository:**

   ```bash
   git pull origin main
   ```

2. **Create a feature branch:**

   ```bash
   git checkout -b feature/your-feature
   ```

3. **Make your changes and commit:**

   ```bash
   git add .
   git commit -m "feat: description"
   ```

4. **Push and create a pull request:**
   ```bash
   git push origin feature/your-feature
   ```

📖 **Full Guide:** [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 🔄 Keeping Your Local Repository Updated

### The Core Question

**"How do I ensure GitHub changes are reflected in my local files?"**

### The Simple Answer

Git automatically updates your files when you pull:

```bash
git pull origin main
```

Your core files (`backend/`, `frontend/`, etc.) are now synced! ✅

### The Complete Answer

1. **Pull code changes:** `git pull origin main`
2. **Install dependencies** (if they changed):
   ```bash
   npm install
   cd backend && pip install -r requirements.lock
   ```
3. **Verify sync:** `git log --oneline -5`

📖 **Detailed Guide:** [SYNC_GUIDE.md](docs/SYNC_GUIDE.md)

---

## 📊 Project Status

### Features

- ✅ Paper trading engine with autonomous strategies
- ✅ Real-time market data integration
- ✅ WebSocket streaming for live updates
- ✅ Comprehensive learning system
- ✅ React dashboard with live metrics
- ✅ CI/CD pipeline with automated tests
- ✅ Code health audit system

### Recent Updates

Check [ISSUES.md](ISSUES.md) for current status and known issues.

---

## 🚨 Troubleshooting

### Common Issues

**Problem:** My local files don't have the latest GitHub changes

**Solution:**

```bash
git fetch origin
git pull origin main
```

---

**Problem:** Dependencies are out of sync

**Solution:**

```bash
# Frontend
rm -rf node_modules package-lock.json
npm install

# Backend
pip install --upgrade -r backend/requirements.lock
```

---

**Problem:** Merge conflicts

**Solution:**

```bash
git pull origin main
# Edit conflicted files (look for <<<<<<< markers)
git add <resolved-files>
git commit -m "merge: resolve conflicts"
```

---

📖 **More Solutions:** [CONTRIBUTING.md - Troubleshooting](CONTRIBUTING.md#troubleshooting)

---

## 📖 Additional Resources

### Documentation

- [Task Overview](TASK.md)
- [Issue Tracking](ISSUES.md)
- [Architecture Details](implements/ZiggyAI_FULL_WRITEUP.md)
- [Learning System](docs/LearningSystem.md)
- [Integration System](docs/IntegrationSystem.md)

### External Links

- [Git Documentation](https://git-scm.com/doc)
- [GitHub Flow](https://guides.github.com/introduction/flow/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [React Docs](https://react.dev/)

---

## 🎯 Next Steps

**New to the project?**

1. Read [SYNC_GUIDE.md](docs/SYNC_GUIDE.md) (5 min)
2. Set up your environment: [README-dev.md](implements/README-dev.md) (15 min)
3. Run the sync script: `./scripts/sync-from-github.sh`

**Ready to contribute?**

1. Read [CONTRIBUTING.md](CONTRIBUTING.md) (20 min)
2. Create a feature branch
3. Make your changes
4. Submit a pull request

**Debugging an issue?**

1. Check [docs/SYNC_GUIDE.md - Troubleshooting](docs/SYNC_GUIDE.md#troubleshooting)
2. Check [CONTRIBUTING.md - Troubleshooting](CONTRIBUTING.md#troubleshooting)
3. Search existing issues on GitHub

---

## 📞 Getting Help

1. **Documentation:** Check [docs/README.md](docs/README.md)
2. **Issues:** Search existing issues on GitHub
3. **Team Chat:** Ask in discussions or team chat
4. **New Issue:** Create an issue for bugs or questions

---

## 📝 License

[Add license information here]

---

## 🙏 Acknowledgments

Built with ❤️ by the ZiggyAI team.

---

**Quick Links:**

- 📖 [Complete Documentation Index](docs/README.md)
- 🔄 [Sync Guide](docs/SYNC_GUIDE.md)
- 🔀 [GitHub Workflow](docs/GITHUB_WORKFLOW.md)
- 🤝 [Contributing Guide](CONTRIBUTING.md)
- 🛠️ [Development Setup](implements/README-dev.md)
- 🏥 [Audit System](implements/AUDIT_README.md)

---

**Remember:** Syncing your local files with GitHub is as simple as:

```bash
git pull origin main
```

Your files are automatically updated! 🎉
