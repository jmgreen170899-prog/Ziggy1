# ZiggyAI Setup Guide

Complete guide for setting up ZiggyAI locally or in production.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Manual Installation](#manual-installation)
- [Docker Installation](#docker-installation)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [Verification](#verification)
- [Development Tools](#development-tools)
- [Troubleshooting Installation](#troubleshooting-installation)

---

## Prerequisites

### Required Software

| Software | Minimum Version | Purpose |
|----------|----------------|---------|
| Python | 3.11+ | Backend runtime |
| Node.js | 18+ | Frontend build/runtime |
| npm | 8+ | Package management |
| Git | 2.0+ | Version control |

### Optional Software

| Software | Purpose | When Needed |
|----------|---------|-------------|
| Docker | Containerization | Production, easy setup |
| Docker Compose | Multi-service orchestration | Production |
| PostgreSQL | Production database | Non-SQLite setups |
| Redis | Caching | Production |

### System Requirements

- **RAM**: 4GB minimum, 8GB recommended
- **Disk**: 2GB free space
- **OS**: macOS, Linux, or Windows (WSL2 recommended)

---

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/jmgreen170899-prog/ZiggyAI.git
cd ZiggyAI
```

### 2. One-Command Setup (Docker)

```bash
docker-compose up
```

This starts all services:
- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- PostgreSQL: localhost:5432
- Qdrant: localhost:6333

### 3. Alternative: Manual Setup

```bash
# Install all dependencies
npm install
cd frontend && npm install && cd ..
cd backend && pip install -r requirements.lock && cd ..

# Start services
npm run dev:all
```

---

## Manual Installation

### Backend Setup

#### 1. Create Python Virtual Environment

```bash
cd backend

# Using venv
python -m venv .venv

# Activate (Linux/macOS)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate
```

#### 2. Install Dependencies

```bash
pip install -r requirements.lock
```

#### 3. Configure Environment

```bash
# Copy example configuration
cp .env.demo.example .env

# Edit with your settings
nano .env  # or use your preferred editor
```

#### 4. Initialize Database

```bash
# For SQLite (development)
python -c "from app.models.base import create_tables; create_tables()"

# For PostgreSQL
# Ensure DATABASE_URL is set, then:
python -c "from app.models.base import create_tables; create_tables()"
```

### Frontend Setup

#### 1. Install Dependencies

```bash
cd frontend
npm install
```

#### 2. Configure Environment

```bash
# Create environment file
echo "VITE_API_BASE=http://localhost:8000" > .env
```

### Root Dependencies (Optional)

```bash
# From project root
npm install
```

This installs shared development tools.

---

## Docker Installation

### Using Docker Compose

#### 1. Build and Start

```bash
# Build images and start containers
docker-compose up --build

# Or in detached mode
docker-compose up -d --build
```

#### 2. View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

#### 3. Stop Services

```bash
docker-compose down

# Remove volumes (clean slate)
docker-compose down -v
```

### Docker Compose Services

| Service | Port | Description |
|---------|------|-------------|
| `frontend` | 5173 | Next.js React app |
| `backend` | 8000 | FastAPI application |
| `postgres` | 5432 | PostgreSQL database |
| `qdrant` | 6333 | Vector database |
| `redis` | 6379 | Cache (optional) |

### Custom Docker Configuration

```yaml
# docker-compose.override.yml
version: '3.8'
services:
  backend:
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
```

---

## Environment Configuration

### Backend Environment Variables

Create `backend/.env`:

```bash
# ============================================
# Core Settings
# ============================================
ENV=development
DEBUG=true
SECRET_KEY=your-secure-secret-key-change-in-production

# ============================================
# Database
# ============================================
# SQLite (development)
DATABASE_URL=sqlite:///./ziggy.db

# PostgreSQL (production)
# DATABASE_URL=postgresql://user:password@localhost:5432/ziggy

# ============================================
# Market Data Providers (Optional)
# ============================================
# Polygon.io - Real-time market data
POLYGON_API_KEY=your-polygon-api-key

# Alpaca - Trading API
ALPACA_API_KEY=your-alpaca-api-key
ALPACA_SECRET_KEY=your-alpaca-secret-key
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Provider priority chain
PROVIDERS_PRICES=polygon,yfinance
PROVIDERS_QUOTES=polygon,alpaca,yfinance
PROVIDERS_CRYPTO=polygon,yfinance

# ============================================
# AI / LLM Settings (Optional)
# ============================================
# OpenAI
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o-mini
USE_OPENAI=false

# Local LLM (Ollama)
LOCAL_LLM_BASE_URL=http://localhost:11434/v1
LOCAL_LLM_MODEL=llama3.2:3b

# ============================================
# Vector Database (Optional)
# ============================================
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=

# ============================================
# Cache (Optional)
# ============================================
REDIS_URL=redis://localhost:6379/0
CACHE_TTL_SECONDS=60

# ============================================
# Notifications (Optional)
# ============================================
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id

# ============================================
# News
# ============================================
NEWS_API_KEY=your-newsapi-key
NEWS_RSS_EXTRA=  # Additional RSS feeds (comma-separated)

# ============================================
# Authentication
# ============================================
ENABLE_AUTH=false
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ============================================
# Paper Trading
# ============================================
PAPER_SLIPPAGE_BPS=5
PAPER_MIN_FILL_LATENCY_MS=10
PAPER_COMMISSION_PER_TRADE=1.0
PAPER_MAX_POSITION_SIZE=0.05
PAPER_MAX_DAILY_LOSS=0.10

# ============================================
# API Documentation
# ============================================
DOCS_ENABLED=true
```

### Frontend Environment Variables

Create `frontend/.env`:

```bash
# API Configuration
VITE_API_BASE=http://localhost:8000

# WebSocket (if different)
VITE_WS_BASE=ws://localhost:8000

# Feature Flags
VITE_ENABLE_PAPER_TRADING=true
VITE_ENABLE_MOCK_DATA=false
```

### Environment Variable Reference

#### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Application secret | `your-256-bit-secret` |
| `DATABASE_URL` | Database connection | `sqlite:///./ziggy.db` |

#### Market Data (Choose One)

| Variable | Description |
|----------|-------------|
| `POLYGON_API_KEY` | Polygon.io API key |
| `ALPACA_API_KEY` | Alpaca API key |
| (none) | Falls back to yfinance |

#### AI Features

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `LOCAL_LLM_BASE_URL` | Local LLM endpoint |

---

## Database Setup

### SQLite (Development)

SQLite is the default for development - no additional setup required.

```bash
# Database file is created automatically at:
backend/ziggy.db
```

### PostgreSQL (Production)

#### 1. Install PostgreSQL

```bash
# macOS
brew install postgresql
brew services start postgresql

# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql

# Docker
docker run -d \
  --name ziggy-postgres \
  -e POSTGRES_USER=ziggy \
  -e POSTGRES_PASSWORD=ziggy \
  -e POSTGRES_DB=ziggy \
  -p 5432:5432 \
  postgres:16
```

#### 2. Create Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create user and database
CREATE USER ziggy WITH PASSWORD 'your-password';
CREATE DATABASE ziggy OWNER ziggy;
GRANT ALL PRIVILEGES ON DATABASE ziggy TO ziggy;
\q
```

#### 3. Configure Connection

```bash
# In backend/.env
DATABASE_URL=postgresql://ziggy:your-password@localhost:5432/ziggy
```

### Qdrant (Vector Database)

```bash
# Docker
docker run -d \
  --name ziggy-qdrant \
  -p 6333:6333 \
  -v qdrant_storage:/qdrant/storage \
  qdrant/qdrant

# Configuration
QDRANT_URL=http://localhost:6333
```

### Redis (Cache)

```bash
# Docker
docker run -d \
  --name ziggy-redis \
  -p 6379:6379 \
  redis:7-alpine

# Configuration
REDIS_URL=redis://localhost:6379/0
```

---

## Running the Application

### Development Mode

#### Option 1: Both Services

```bash
npm run dev:all
```

#### Option 2: Individual Services

**Terminal 1 - Backend:**

```bash
cd backend
source .venv/bin/activate  # if using venv
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**

```bash
cd frontend
npm run dev
```

### Production Mode

#### Backend

```bash
cd backend
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

#### Frontend

```bash
cd frontend
npm run build
npm run start
```

### Using Make

```bash
# Start all services
make dev

# Run tests
make test

# Run audits
make audit-all
```

---

## Verification

### Check Backend

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
# {"status":"ok","ok":true,"service":"ZiggyAI Backend","version":"0.1.0"}
```

### Check Frontend

1. Open http://localhost:5173 in browser
2. You should see the ZiggyAI dashboard

### Check API Documentation

1. Swagger UI: http://localhost:8000/docs
2. ReDoc: http://localhost:8000/redoc

### Run Tests

```bash
# Backend tests
cd backend
pytest -q

# Frontend tests
cd frontend
npm run test
```

---

## Development Tools

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Set up hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### Code Formatting

```bash
# Backend (Python)
cd backend
ruff format .
ruff check --fix .

# Frontend (TypeScript)
cd frontend
npm run lint
npm run lint:fix
```

### Type Checking

```bash
# Backend
cd backend
mypy app/

# Frontend
cd frontend
npm run typecheck
```

### Audit Tools

```bash
# Quick audit
make audit-quick

# Full audit
make audit-all

# Individual audits
make audit-backend-full
make audit-frontend-full
```

---

## Troubleshooting Installation

### Common Issues

#### Python Version Mismatch

```bash
# Check Python version
python --version

# Should be 3.11+
# If not, install via pyenv:
pyenv install 3.11.0
pyenv local 3.11.0
```

#### Node.js Version Mismatch

```bash
# Check Node version
node --version

# Should be 18+
# If not, install via nvm:
nvm install 18
nvm use 18
```

#### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000  # Linux/macOS
netstat -ano | findstr :8000  # Windows

# Kill the process
kill -9 <PID>
```

#### Database Connection Failed

```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Check connection string
psql "postgresql://ziggy:password@localhost:5432/ziggy"
```

#### Missing Dependencies

```bash
# Backend - reinstall all
cd backend
pip install -r requirements.lock --force-reinstall

# Frontend - clean install
cd frontend
rm -rf node_modules package-lock.json
npm install
```

#### Docker Issues

```bash
# Reset Docker containers
docker-compose down -v
docker system prune -f
docker-compose up --build
```

### Getting Help

1. Check [Troubleshooting.md](Troubleshooting.md) for more solutions
2. Search existing GitHub issues
3. Create a new issue with:
   - Error message
   - Steps to reproduce
   - Environment details (OS, Python/Node versions)

---

## Next Steps

After successful setup:

1. 📖 Read the [API Documentation](API.md)
2. 🏗️ Explore the [Architecture](architecture.md)
3. 🚀 Try [Deployment](Deployment.md) for production
4. 🤝 Check [Contributing Guide](../CONTRIBUTING.md) to contribute

---

**Need help?** Create an issue on GitHub or check [Troubleshooting.md](Troubleshooting.md)
