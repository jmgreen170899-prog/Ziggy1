# ZiggyAI - Intelligent Trading Platform

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19.1-blue.svg)](https://react.dev)
[![Next.js](https://img.shields.io/badge/Next.js-15.5-black.svg)](https://nextjs.org)

> **ZiggyAI** is a sophisticated full-stack paper trading platform featuring autonomous trading strategies, real-time market data integration, machine learning-powered signal generation, and comprehensive learning capabilities.

---

## 📋 Table of Contents

- [Project Summary](#-project-summary)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Architecture Overview](#-architecture-overview)
- [Folder Structure](#-folder-structure)
- [Installation](#-installation)
- [Running Locally](#-running-locally)
- [Environment Variables](#-environment-variables)
- [API Routes Summary](#-api-routes-summary)
- [Deployment](#-deployment)
- [Screenshots & Diagrams](#-screenshots--diagrams)
- [What This Project Demonstrates](#-what-this-project-demonstrates)
- [Documentation](#-documentation)
- [Contributing](#-contributing)

---

## 🎯 Project Summary

ZiggyAI is an intelligent trading platform designed for paper trading experimentation and strategy development. The system combines:

- **Autonomous Trading Engine**: Execute thousands of micro-trades with configurable strategies
- **Real-Time Market Data**: Integration with Polygon.io, Alpaca, and Yahoo Finance
- **Machine Learning**: Online learning models that adapt from trading outcomes
- **RAG-Powered AI Assistant**: Chat interface with retrieval-augmented generation
- **Comprehensive Dashboard**: React-based UI with live metrics and visualizations
- **Risk Management**: Built-in guardrails, position sizing, and exposure limits

---

## ✨ Features

### Trading & Analysis
- ✅ **Paper Trading Engine** - Autonomous strategies with thousands of concurrent micro-trades
- ✅ **Real-Time Market Data** - Multi-provider support (Polygon, Alpaca, yfinance)
- ✅ **Technical Analysis** - SMA, RSI, ATR, Z-score, and custom indicators
- ✅ **Market Screener** - Automated signal detection with confidence scoring
- ✅ **Backtesting** - Quick strategy validation with performance metrics
- ✅ **News Sentiment** - NLP-powered news analysis and aggregation

### Machine Learning
- ✅ **Online Learning** - Models that learn from trade outcomes in real-time
- ✅ **Market Brain** - Advanced signal generation with regime detection
- ✅ **RAG System** - Document ingestion and semantic search with Qdrant
- ✅ **Theory Performance** - Track and optimize multiple trading strategies

### Platform
- ✅ **WebSocket Streaming** - Live updates for market data and trades
- ✅ **React Dashboard** - Modern UI with dark/light mode and responsive design
- ✅ **Telegram Alerts** - Push notifications for trading signals
- ✅ **Docker Support** - Full containerization with Docker Compose
- ✅ **CI/CD Pipeline** - Automated testing and deployment with GitHub Actions

---

## 🛠️ Tech Stack

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Core runtime |
| FastAPI | 0.111+ | Web framework & API |
| SQLAlchemy | 2.0+ | ORM & database |
| PostgreSQL | 16 | Production database |
| Qdrant | 1.11+ | Vector database for RAG |
| Redis | 7 | Caching & sessions |

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| Next.js | 15.5 | React framework |
| React | 19.1 | UI library |
| TypeScript | 5.0+ | Type safety |
| Tailwind CSS | 4.0 | Styling |
| Zustand | 5.0 | State management |

### DevOps & Infrastructure
| Technology | Purpose |
|------------|---------|
| Docker | Containerization |
| Docker Compose | Multi-service orchestration |
| GitHub Actions | CI/CD pipeline |
| Pre-commit | Git hooks for code quality |

📖 **See:** [TechStack.md](docs/TechStack.md) for the complete technology documentation.

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         ZiggyAI Platform                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Frontend (Next.js)                     │   │
│  │  • React 19 Dashboard    • WebSocket Client              │   │
│  │  • Real-time Charts      • State Management (Zustand)    │   │
│  └────────────────────────────┬────────────────────────────┘   │
│                               │ HTTP/WebSocket                  │
│  ┌────────────────────────────▼────────────────────────────┐   │
│  │                    Backend (FastAPI)                      │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │   │
│  │  │ Trading  │  │  Market  │  │   Chat   │  │   News   │ │   │
│  │  │  Engine  │  │   Data   │  │   (LLM)  │  │   RSS    │ │   │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘ │   │
│  │       │             │             │             │        │   │
│  │  ┌────▼─────────────▼─────────────▼─────────────▼────┐  │   │
│  │  │              Core Services Layer                   │  │   │
│  │  │  • Paper Broker  • ML Learner  • RAG Pipeline     │  │   │
│  │  └───────────────────────┬───────────────────────────┘  │   │
│  └──────────────────────────┼──────────────────────────────┘   │
│                             │                                   │
│  ┌──────────────────────────▼──────────────────────────────┐   │
│  │                    Data Layer                            │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │   │
│  │  │PostgreSQL│  │  Qdrant  │  │  Redis   │  │ External │ │   │
│  │  │  (Data)  │  │ (Vectors)│  │ (Cache)  │  │  APIs    │ │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

📖 **See:** [architecture.md](docs/architecture.md) for detailed Mermaid diagrams.

---

## 📁 Folder Structure

```
ZiggyAI/
├── backend/                    # FastAPI backend application
│   ├── app/
│   │   ├── api/               # API route handlers (20+ modules)
│   │   ├── core/              # Config, security, logging
│   │   ├── models/            # SQLAlchemy database models
│   │   ├── paper/             # Paper trading engine
│   │   ├── services/          # External integrations
│   │   ├── tasks/             # Background workers & scheduler
│   │   ├── rag/               # RAG pipeline & vector store
│   │   └── trading/           # Trading signals & execution
│   ├── tests/                 # Test suite
│   └── requirements.lock      # Python dependencies
│
├── frontend/                   # Next.js React application
│   ├── src/
│   │   ├── app/               # Next.js App Router pages
│   │   ├── components/        # Reusable UI components
│   │   ├── features/          # Feature-specific components
│   │   ├── services/          # API clients & providers
│   │   ├── hooks/             # Custom React hooks
│   │   └── store/             # Zustand state stores
│   └── package.json           # Node.js dependencies
│
├── docs/                       # Documentation
│   ├── architecture/          # Architecture documentation
│   ├── development/           # Development guides
│   └── *.md                   # Various guides
│
├── scripts/                    # Automation scripts
├── tools/                      # Audit and analysis tools
├── docker-compose.yml          # Docker orchestration
├── Makefile                    # Task automation
└── README.md                   # This file
```

---

## 🚀 Installation

### Prerequisites

- **Python 3.11+** - [Download](https://python.org/downloads/)
- **Node.js 18+** - [Download](https://nodejs.org/)
- **Docker** (optional) - [Download](https://docker.com/get-started)
- **Git** - [Download](https://git-scm.com/)

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/jmgreen170899-prog/ZiggyAI.git
cd ZiggyAI

# 2. Install dependencies
npm install                                    # Root dependencies
cd frontend && npm install && cd ..            # Frontend
cd backend && pip install -r requirements.lock && cd ..  # Backend

# 3. Start services (choose one)
npm run dev:all                                # All services
# OR with Docker:
docker-compose up
```

📖 **See:** [SetupGuide.md](docs/SetupGuide.md) for complete installation instructions.

---

## 🏃 Running Locally

### Option 1: Without Docker (Development)

```bash
# Terminal 1: Start Backend
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start Frontend
cd frontend
npm run dev
```

### Option 2: With Docker Compose (Recommended)

```bash
# Start all services
docker-compose up

# Or in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Service URLs

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:5173 | React dashboard |
| Backend API | http://localhost:8000 | FastAPI REST API |
| API Docs | http://localhost:8000/docs | Swagger UI |
| ReDoc | http://localhost:8000/redoc | Alternative API docs |

---

## 🔐 Environment Variables

Create `.env` files in the root, backend, and frontend directories.

### Backend (`backend/.env`)

```bash
# Core Settings
ENV=development
DEBUG=true
SECRET_KEY=your-secret-key-change-in-production

# Database
DATABASE_URL=postgresql://ziggy:ziggy@localhost:5432/ziggy
# Or for SQLite (development):
# DATABASE_URL=sqlite:///./ziggy.db

# External Services (Optional)
OPENAI_API_KEY=your-openai-api-key
POLYGON_API_KEY=your-polygon-api-key
ALPACA_API_KEY=your-alpaca-api-key
ALPACA_SECRET_KEY=your-alpaca-secret
NEWS_API_KEY=your-newsapi-key

# Vector Database
QDRANT_URL=http://localhost:6333

# Cache (Optional)
REDIS_URL=redis://localhost:6379/0

# Telegram Alerts (Optional)
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
```

### Frontend (`frontend/.env`)

```bash
VITE_API_BASE=http://localhost:8000
```

📖 **See:** [SetupGuide.md](docs/SetupGuide.md) for complete environment variable documentation.

---

## 🔌 API Routes Summary

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Basic health check |
| `GET` | `/health/detailed` | Detailed health with route info |
| `GET` | `/api/core/health` | Core service dependencies status |

### Trading & Market

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/trade/health` | Trading service health |
| `GET` | `/trade/screener` | Run market screener |
| `POST` | `/trade/explain` | Explain trading signal |
| `GET` | `/trade/ohlc` | OHLC data for charts |
| `POST` | `/backtest` | Run quick backtest |
| `GET` | `/market/overview` | Market overview with prices |
| `GET` | `/market/breadth` | Market breadth indicators |
| `GET` | `/market/risk-lite` | Put/Call ratio analysis |

### Paper Trading

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/paper/runs` | Create paper trading run |
| `GET` | `/api/paper/runs` | List paper trading runs |
| `GET` | `/api/paper/runs/{id}/trades` | Get trade history |
| `GET` | `/api/paper/runs/{id}/stats` | Get run statistics |
| `GET` | `/api/paper/health` | Paper trading health |
| `POST` | `/api/paper/emergency/stop_all` | Emergency stop |

### News & Sentiment

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/news/headlines` | RSS news headlines |
| `GET` | `/news/sources` | Available news sources |
| `GET` | `/news/sentiment` | NLP sentiment analysis |
| `GET` | `/news/filings` | SEC filings |

### Chat & AI

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/chat/complete` | LLM chat completion |
| `GET` | `/chat/health` | LLM provider health |
| `POST` | `/api/query` | RAG query |
| `POST` | `/api/agent` | AI agent with tools |

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/login` | User login |
| `GET` | `/auth/status` | Auth status |
| `GET` | `/auth/me` | Current user info |
| `POST` | `/auth/refresh` | Refresh token |

📖 **See:** [API.md](docs/API.md) for complete API documentation with request/response examples.

---

## 🚀 Deployment

### Docker Deployment

```bash
# Build and deploy
docker-compose -f docker-compose.yml up -d --build

# Check service health
docker-compose ps
docker-compose logs backend
```

### Manual Deployment

1. **Backend**: Deploy FastAPI with Gunicorn/Uvicorn
2. **Frontend**: Build and deploy to Vercel/Netlify
3. **Database**: PostgreSQL on managed service (e.g., RDS, Supabase)

📖 **See:** [Deployment.md](docs/Deployment.md) for detailed deployment guides.

---

## 📸 Screenshots & Diagrams

### Dashboard
*[Screenshot placeholder: Main trading dashboard with market overview]*

### Trading Interface
*[Screenshot placeholder: Paper trading interface with signals]*

### Architecture Diagram
*[Diagram placeholder: System architecture visualization]*

📖 **See:** [architecture.md](docs/architecture.md) for detailed Mermaid diagrams.

---

## 💡 What This Project Demonstrates

This project showcases advanced skills in:

### Backend Development
- **FastAPI** - Modern Python web framework with async support
- **SQLAlchemy 2.0** - Advanced ORM patterns and database design
- **API Design** - RESTful APIs with OpenAPI documentation
- **WebSockets** - Real-time bidirectional communication
- **Background Tasks** - APScheduler for periodic jobs
- **Circuit Breakers** - Resilient external service integration

### Frontend Development
- **Next.js 15** - App Router, SSR/CSR hybrid rendering
- **React 19** - Latest React features and patterns
- **TypeScript** - End-to-end type safety
- **State Management** - Zustand for global state
- **Data Fetching** - React Query for server state

### Machine Learning & AI
- **Online Learning** - Models that adapt from real-time data
- **RAG Pipeline** - Document ingestion, embedding, retrieval
- **LLM Integration** - OpenAI and local model support
- **NLP** - Sentiment analysis and text processing

### DevOps & Infrastructure
- **Docker** - Multi-service containerization
- **CI/CD** - GitHub Actions pipelines
- **Database Management** - PostgreSQL, SQLite, migrations
- **Monitoring** - Health checks, logging, observability

### Trading Domain
- **Paper Trading Engine** - Realistic trade simulation
- **Market Data Integration** - Multi-provider data aggregation
- **Technical Analysis** - Indicators and signal generation
- **Risk Management** - Position sizing, exposure limits

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [API.md](docs/API.md) | Complete API reference |
| [architecture.md](docs/architecture.md) | System architecture diagrams |
| [SetupGuide.md](docs/SetupGuide.md) | Installation instructions |
| [Deployment.md](docs/Deployment.md) | Deployment guides |
| [TechStack.md](docs/TechStack.md) | Technology documentation |
| [Troubleshooting.md](docs/Troubleshooting.md) | Common issues and fixes |
| [Changelog.md](docs/Changelog.md) | Version history |

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
# 1. Fork and clone
git clone https://github.com/your-username/ZiggyAI.git

# 2. Create feature branch
git checkout -b feature/amazing-feature

# 3. Make changes and commit
git add .
git commit -m "feat: add amazing feature"

# 4. Push and create PR
git push origin feature/amazing-feature
```

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- FastAPI team for the excellent framework
- React and Next.js teams for the frontend ecosystem
- The open-source community for invaluable tools and libraries

---

**Built with ❤️ by the ZiggyAI team**

---

**Quick Links:** [API Docs](docs/API.md) | [Setup Guide](docs/SetupGuide.md) | [Architecture](docs/architecture.md) | [Contributing](CONTRIBUTING.md)
