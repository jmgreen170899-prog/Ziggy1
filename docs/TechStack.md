# ZiggyAI Technology Stack

Comprehensive documentation of all technologies used in the ZiggyAI trading platform.

---

## Table of Contents

- [Overview](#overview)
- [Backend Technologies](#backend-technologies)
- [Frontend Technologies](#frontend-technologies)
- [Database & Storage](#database--storage)
- [External Services](#external-services)
- [DevOps & Infrastructure](#devops--infrastructure)
- [Development Tools](#development-tools)
- [Version Information](#version-information)

---

## Overview

ZiggyAI is built with a modern, scalable technology stack designed for real-time trading applications:

```
┌─────────────────────────────────────────────────────────────┐
│                      ZiggyAI Stack                          │
├─────────────────────────────────────────────────────────────┤
│  Frontend         │  Next.js 15 + React 19 + TypeScript     │
│  Backend          │  FastAPI + Python 3.11 + SQLAlchemy     │
│  Database         │  PostgreSQL + Qdrant + Redis            │
│  Infrastructure   │  Docker + GitHub Actions                │
└─────────────────────────────────────────────────────────────┘
```

---

## Backend Technologies

### Core Framework

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.11+ | Core programming language |
| **FastAPI** | 0.111+ | High-performance async web framework |
| **Uvicorn** | 0.30+ | ASGI server |
| **Gunicorn** | 22+ | Production WSGI/ASGI server |

### Key Python Libraries

#### Web & API

| Library | Version | Purpose |
|---------|---------|---------|
| `fastapi` | 0.111+ | REST API framework |
| `pydantic` | 2.0+ | Data validation and settings |
| `slowapi` | 0.1+ | Rate limiting |
| `python-jose` | 3.3+ | JWT authentication |
| `passlib` | 1.7+ | Password hashing |
| `httpx` | 0.27+ | Async HTTP client |

#### Database & ORM

| Library | Version | Purpose |
|---------|---------|---------|
| `sqlalchemy` | 2.0+ | ORM and database toolkit |
| `psycopg2-binary` | 2.9+ | PostgreSQL adapter |
| `redis` | 5.0+ | Redis client |
| `qdrant-client` | 1.11+ | Vector database client |

#### Data Processing

| Library | Version | Purpose |
|---------|---------|---------|
| `pandas` | 2.0+ | Data manipulation |
| `numpy` | 1.26+ | Numerical computing |
| `scipy` | 1.11+ | Scientific computing |

#### Machine Learning

| Library | Version | Purpose |
|---------|---------|---------|
| `scikit-learn` | 1.3+ | ML algorithms |
| `sentence-transformers` | 2.2+ | Text embeddings |
| `river` | 0.21+ | Online/streaming ML |

#### Market Data & Trading

| Library | Version | Purpose |
|---------|---------|---------|
| `yfinance` | 0.2+ | Yahoo Finance data |
| `alpaca-trade-api` | 3.0+ | Alpaca trading API |
| `polygon-api-client` | 1.12+ | Polygon.io data |
| `ta` | 0.10+ | Technical analysis |

#### Background Tasks

| Library | Version | Purpose |
|---------|---------|---------|
| `apscheduler` | 3.10+ | Task scheduling |
| `celery` | 5.3+ | Distributed task queue (optional) |

#### Utilities

| Library | Version | Purpose |
|---------|---------|---------|
| `python-dotenv` | 1.0+ | Environment management |
| `loguru` | 0.7+ | Logging |
| `tenacity` | 8.2+ | Retry logic |
| `cachetools` | 5.3+ | Caching utilities |

---

## Frontend Technologies

### Core Framework

| Technology | Version | Purpose |
|------------|---------|---------|
| **Next.js** | 15.5 | React framework with App Router |
| **React** | 19.1 | UI component library |
| **TypeScript** | 5.0+ | Type-safe JavaScript |

### UI & Styling

| Library | Version | Purpose |
|---------|---------|---------|
| `tailwindcss` | 4.0 | Utility-first CSS |
| `@radix-ui/*` | Latest | Accessible UI primitives |
| `lucide-react` | 0.468+ | Icon library |
| `clsx` | 2.0+ | Class name utilities |
| `tailwind-merge` | 2.0+ | Tailwind class merging |

### State Management

| Library | Version | Purpose |
|---------|---------|---------|
| `zustand` | 5.0 | Lightweight state management |
| `@tanstack/react-query` | 5.0+ | Server state management |
| `immer` | 10.0+ | Immutable state updates |

### Data Visualization

| Library | Version | Purpose |
|---------|---------|---------|
| `recharts` | 2.12+ | React charting library |
| `lightweight-charts` | 4.1+ | Trading charts |

### Forms & Validation

| Library | Version | Purpose |
|---------|---------|---------|
| `react-hook-form` | 7.53+ | Form management |
| `zod` | 3.23+ | Schema validation |

### Networking

| Library | Version | Purpose |
|---------|---------|---------|
| `axios` | 1.6+ | HTTP client |
| `socket.io-client` | 4.7+ | WebSocket client |

### Utilities

| Library | Version | Purpose |
|---------|---------|---------|
| `date-fns` | 3.6+ | Date manipulation |
| `lodash` | 4.17+ | Utility functions |

---

## Database & Storage

### Primary Database

| Technology | Version | Purpose |
|------------|---------|---------|
| **PostgreSQL** | 16 | Production database |
| **SQLite** | 3.x | Development database |

**PostgreSQL Features Used:**
- JSON/JSONB columns for flexible data
- Indexes for query optimization
- Connection pooling
- Full-text search (optional)

### Vector Database

| Technology | Version | Purpose |
|------------|---------|---------|
| **Qdrant** | 1.11+ | Vector similarity search |

**Qdrant Use Cases:**
- Document embeddings for RAG
- Semantic search
- Similar item retrieval

### Cache & Sessions

| Technology | Version | Purpose |
|------------|---------|---------|
| **Redis** | 7 | Caching and sessions |

**Redis Use Cases:**
- API response caching
- Session storage
- Rate limiting counters
- Pub/sub messaging

---

## External Services

### Market Data Providers

| Provider | API | Purpose |
|----------|-----|---------|
| **Polygon.io** | REST/WebSocket | Real-time market data |
| **Alpaca** | REST/WebSocket | Trading API and data |
| **Yahoo Finance** | yfinance library | Free historical data |

### AI & Language Models

| Provider | Models | Purpose |
|----------|--------|---------|
| **OpenAI** | GPT-4o, GPT-4o-mini | Chat completions |
| **Ollama** | Llama, Mistral | Local LLM inference |
| **Sentence Transformers** | all-MiniLM-L6-v2 | Text embeddings |

### News & Data

| Provider | Purpose |
|----------|---------|
| **NewsAPI** | News headlines |
| **SEC EDGAR** | SEC filings |
| **RSS Feeds** | Free news sources |

### Notifications

| Service | Purpose |
|---------|---------|
| **Telegram Bot API** | Trading alerts |

---

## DevOps & Infrastructure

### Containerization

| Technology | Version | Purpose |
|------------|---------|---------|
| **Docker** | 24+ | Container runtime |
| **Docker Compose** | 2.20+ | Multi-container orchestration |

### CI/CD

| Technology | Purpose |
|------------|---------|
| **GitHub Actions** | Automated testing and deployment |

**Workflow Features:**
- Automated testing on PR
- Code quality checks
- Docker image building
- Deployment automation

### Web Server

| Technology | Purpose |
|------------|---------|
| **Nginx** | Reverse proxy, SSL termination |
| **Gunicorn** | Python WSGI/ASGI server |

### SSL/TLS

| Technology | Purpose |
|------------|---------|
| **Let's Encrypt** | Free SSL certificates |
| **Certbot** | Certificate automation |

---

## Development Tools

### Code Quality

| Tool | Purpose |
|------|---------|
| **Ruff** | Python linting and formatting |
| **ESLint** | JavaScript/TypeScript linting |
| **Prettier** | Code formatting |
| **mypy** | Python static type checking |
| **TypeScript** | Frontend type checking |

### Testing

| Tool | Purpose |
|------|---------|
| **pytest** | Python testing framework |
| **pytest-asyncio** | Async test support |
| **Jest** | JavaScript testing |
| **React Testing Library** | React component testing |

### Git Hooks

| Tool | Purpose |
|------|---------|
| **pre-commit** | Git hook management |
| **commitizen** | Commit message standardization |

### Documentation

| Tool | Purpose |
|------|---------|
| **Swagger/OpenAPI** | API documentation |
| **ReDoc** | Alternative API docs |
| **Markdown** | Project documentation |

---

## Version Information

### Current Versions

```json
{
  "python": "3.11.0",
  "node": "18.17.0",
  "fastapi": "0.111.0",
  "next": "15.5.0",
  "react": "19.1.0",
  "postgresql": "16",
  "redis": "7",
  "qdrant": "1.11.0",
  "docker": "24.0.5",
  "docker-compose": "2.20.0"
}
```

### Dependency Management

**Backend:**
- `requirements.lock` - Locked dependencies
- `pyproject.toml` - Project configuration

**Frontend:**
- `package.json` - Dependencies and scripts
- `package-lock.json` - Locked versions

### Updating Dependencies

```bash
# Backend
cd backend
pip install pip-tools
pip-compile requirements.in -o requirements.lock
pip install -r requirements.lock

# Frontend
cd frontend
npm update
npm audit fix
```

---

## Architecture Decisions

### Why FastAPI?

- **Performance**: One of the fastest Python frameworks
- **Async Support**: Native async/await
- **Type Safety**: Pydantic integration
- **Auto Documentation**: OpenAPI/Swagger built-in
- **Modern Python**: Leverages Python 3.10+ features

### Why Next.js 15?

- **App Router**: Modern React patterns
- **SSR/SSG**: Flexible rendering strategies
- **Performance**: Automatic optimizations
- **Developer Experience**: Hot reload, TypeScript support
- **Production Ready**: Built-in optimizations

### Why PostgreSQL?

- **Reliability**: ACID compliance
- **Performance**: Excellent for complex queries
- **JSON Support**: Flexible schema when needed
- **Scalability**: Read replicas, connection pooling
- **Ecosystem**: Rich tool support

### Why Qdrant?

- **Performance**: Optimized for vector operations
- **Filtering**: Metadata filtering with vector search
- **Self-Hosted**: Can run locally or in cloud
- **REST API**: Easy integration

### Why Zustand?

- **Simplicity**: Minimal boilerplate
- **Performance**: No providers needed
- **TypeScript**: Excellent type inference
- **Size**: Very small bundle impact

---

## Security Considerations

### Dependencies

- Regular security audits with `npm audit` and `pip-audit`
- Dependabot for automated updates
- Snyk integration (optional)

### Authentication

- JWT tokens with secure signing
- Password hashing with bcrypt
- API key support for services

### Data Protection

- Environment variables for secrets
- No secrets in code or logs
- HTTPS in production

---

## Performance Optimizations

### Backend

- Connection pooling for databases
- Response caching with Redis
- Async operations where possible
- Efficient database queries

### Frontend

- Code splitting
- Image optimization
- Static generation where appropriate
- Bundle size monitoring

---

## Additional Resources

- [Architecture Documentation](architecture.md)
- [API Documentation](API.md)
- [Setup Guide](SetupGuide.md)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
