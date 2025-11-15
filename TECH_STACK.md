# ZiggyAI Technology Stack

**Last Updated:** 2025-11-09  
**Purpose:** Comprehensive documentation of all technologies, libraries, and tools used in ZiggyAI

---

## 🎯 Stack Overview

ZiggyAI is built on a modern, production-ready technology stack:

- **Frontend:** Next.js 15 + React 19 + TypeScript
- **Backend:** FastAPI + Python 3.11+ + SQLAlchemy
- **Database:** PostgreSQL (prod) / SQLite (dev) + Qdrant (vector)
- **AI/ML:** OpenAI API + Sentence Transformers + Custom ML
- **Data:** Polygon.io + Alpaca + yfinance + NewsAPI
- **DevOps:** Docker + GitHub Actions + Pre-commit

---

## 🎨 Frontend Stack

### Core Framework

```json
{
  "next": "15.5.6", // React framework with App Router
  "react": "19.1.0", // UI library (latest)
  "react-dom": "19.1.0" // React DOM renderer
}
```

**Why Next.js 15:**

- App Router for modern routing
- Server/Client Components
- Turbopack for faster builds
- Built-in optimization
- Excellent TypeScript support

**Why React 19:**

- Latest features and performance
- Improved concurrent rendering
- Better error handling
- Enhanced hooks

---

### Language & Type Safety

```json
{
  "typescript": "^5.0.0" // Static typing
}
```

**Configuration:**

- Strict mode enabled (`tsconfig.strict.json`)
- `noImplicitAny`, `strictNullChecks`, etc.
- Comprehensive type coverage

---

### Styling & UI

```json
{
  "tailwindcss": "^4.0.0", // Utility-first CSS
  "clsx": "^2.1.1", // Conditional classes
  "tailwind-merge": "^3.3.1", // Merge Tailwind classes
  "lucide-react": "^0.546.0", // Icon library
  "framer-motion": "^12.23.24" // Animations
}
```

**Design System:**

- Tailwind CSS with custom config
- Design tokens for consistency
- Dark/light mode support
- Responsive by default
- Accessibility-first

---

### State Management

```json
{
  "zustand": "^5.0.8" // Simple state management
}
```

**Why Zustand:**

- Lightweight (~1KB)
- Simple API
- No boilerplate
- React Hooks compatible
- DevTools support

---

### Data Fetching & API

```json
{
  "axios": "^1.12.2" // HTTP client
}
```

**API Client Features:**

- Mock/Real provider switching
- Auto-discovery of backend
- Request/response interceptors
- Error handling
- TypeScript types from OpenAPI

---

### Validation

```json
{
  "zod": "^3.23.8" // Schema validation
}
```

**Usage:**

- API response validation
- Form validation
- Type-safe schemas
- Runtime type checking

---

### Testing

```json
{
  "@playwright/test": "^1.48.2", // E2E testing
  "jest": "^30.2.0", // Unit testing
  "jest-environment-jsdom": "^30.2.0", // DOM environment
  "@testing-library/react": "^16.3.0", // Component testing
  "@testing-library/jest-dom": "^6.9.1" // Jest matchers
}
```

**Testing Strategy:**

- **Unit Tests:** Jest + Testing Library
- **E2E Tests:** Playwright (27 tests)
- **Component Tests:** React Testing Library
- **Visual Tests:** Screenshots in E2E

---

### Code Quality Tools

```json
{
  "eslint": "^9", // Linting
  "eslint-config-next": "^15.5.6", // Next.js rules
  "jscpd": "^4.0.5", // Duplication detection
  "knip": "^5.37.0", // Unused code detection
  "ts-prune": "^0.10.3", // Unused exports
  "depcheck": "^1.4.7" // Unused dependencies
}
```

---

### Accessibility & Performance

```json
{
  "@axe-core/playwright": "^4.11.0", // A11y testing
  "axe-core": "^4.11.0", // A11y engine
  "lighthouse": "^12.2.1" // Performance audits
}
```

---

## ⚙️ Backend Stack

### Core Framework

```toml
fastapi = "^0.111.0"        # Modern Python web framework
uvicorn = "^0.30.0"         # ASGI server with [standard] extras
```

**Why FastAPI:**

- Automatic API documentation
- Type hints for validation
- Async/await support
- Excellent performance
- OpenAPI/Swagger built-in

---

### Language & Runtime

```
Python 3.11+                # Modern Python features
```

**Python Features Used:**

- Type hints everywhere
- Async/await patterns
- Dataclasses
- Pattern matching
- Modern error handling

---

### Data Validation

```toml
pydantic = "^2.8.0"                # Data validation
pydantic-settings = "^2.3.0"       # Settings management
```

**Usage:**

- Request/response validation
- Configuration management
- Type-safe models
- Automatic serialization

---

### Database & ORM

```toml
sqlalchemy = "^2.0.36"      # SQL ORM
alembic = "^1.13.2"         # Database migrations
psycopg2-binary = "^2.9.9"  # PostgreSQL adapter
```

**Database Support:**

- **Primary:** PostgreSQL (production)
- **Development:** SQLite
- **Migrations:** Alembic
- **Models:** SQLAlchemy 2.0 (modern API)

---

### Vector Database (RAG)

```toml
qdrant-client = "^1.9.2"           # Vector database client
sentence-transformers = "^3.0.1"   # Text embeddings
numpy = "^1.26.4"                  # Numerical operations
```

**RAG System:**

- Document storage in Qdrant
- Semantic search
- Context retrieval
- Citation tracking

---

### Market Data Providers

```toml
yfinance = "^0.2.50"        # Yahoo Finance (historical)
pandas = "^2.2.2"           # Data analysis
pyarrow = "^17.0.0"         # Efficient data storage
```

**API Integrations:**

- Polygon.io (via HTTP)
- Alpaca API (via HTTP)
- yfinance (library)
- Custom data normalization

---

### News & Web Scraping

```toml
feedparser = "^6.0.11"      # RSS/Atom parser
trafilatura = "^1.8.0"      # Web content extraction
beautifulsoup4 = "^4.12.3"  # HTML parsing
duckduckgo-search = "^6.1.6" # Web search
```

---

### File Processing

```toml
pypdf = "^4.2.0"            # PDF processing
python-multipart = "^0.0.9" # Multipart form data
```

---

### Async & HTTP

```toml
httpx = "^0.28.1"           # Async HTTP client
aiohttp = "^3.10.5"         # Alternative async HTTP
```

---

### Scheduling & Background Tasks

```toml
apscheduler = "^3.11.0"     # Task scheduling
```

---

### Caching (Optional)

```toml
redis = "^5.0.7"            # Redis client
```

---

### Utilities

```toml
tenacity = "^8.3.0"         # Retry logic
python-dotenv = "^1.0.1"    # Environment variables
passlib = "^1.7.4"          # Password hashing with [bcrypt]
```

---

## 🧪 Testing & Quality (Backend)

### Testing Framework

```toml
pytest = "^8.2.1"           # Test framework
```

**Test Organization:**

- Unit tests in `tests/`
- Integration tests
- API smoke tests
- WebSocket tests

---

### Type Checking & Linting

```toml
mypy = "^1.10.0"            # Static type checking
ruff = "^0.5.1"             # Fast Python linter
black = "^24.0.0"           # Code formatting
```

**Configuration:**

- Strict MyPy settings
- Comprehensive Ruff rules
- Black formatting enforced
- Pre-commit hooks

---

### Security & Quality

```toml
bandit = "^1.7.5"           # Security linter
vulture = "^2.11"           # Dead code detection
schemathesis = "^3.21.0"    # API fuzzing
pre-commit = "^3.7.0"       # Git hooks
```

---

## 🤖 AI/ML Stack

### LLM Integration

```
OpenAI API                  # GPT models for chat
```

**Usage:**

- Chat interface
- Signal explanation
- Market analysis
- Research assistance

---

### Embeddings & Vector Search

```toml
sentence-transformers = "^3.0.1"  # Text embeddings
qdrant-client = "^1.9.2"          # Vector database
```

**RAG Pipeline:**

1. Document ingestion
2. Chunk splitting
3. Embedding generation
4. Vector storage
5. Semantic search
6. Context retrieval

---

### Custom ML Systems

**Learning System:**

- Brier score calculation
- Signal performance tracking
- Model evaluation
- Feedback loops

**Cognitive Engine:**

- Decision tracking
- Event correlation
- Pattern recognition
- Confidence scoring

---

## 🗄️ Data Storage

### Primary Database

```
PostgreSQL (Production)     # Relational data
SQLite (Development)        # Local development
```

**Schema:**

- Users & authentication
- Trading signals & history
- Portfolio & positions
- Market data cache
- System logs

---

### Vector Database

```
Qdrant                      # Semantic search
```

**Storage:**

- Document embeddings
- News articles
- Research papers
- Chat context

---

### Caching Layer (Optional)

```
Redis                       # Fast key-value store
```

**Usage:**

- Session management
- API rate limiting
- Query caching
- Real-time data

---

### File Storage

```
Local filesystem            # Development
S3-compatible (Optional)    # Production
```

**Stored:**

- ML model checkpoints
- Market data history
- Decision logs
- Audit reports

---

## 🐳 DevOps & Infrastructure

### Containerization

```yaml
docker: latest
docker-compose: latest
```

**Services:**

- Frontend (Next.js)
- Backend (FastAPI)
- PostgreSQL
- Qdrant
- Redis (optional)

---

### CI/CD

```yaml
GitHub Actions # Automated workflows
```

**Workflows:**

- Lint & type check
- Run tests
- Build Docker images
- Deploy to staging/prod
- Security scanning

---

### Code Quality Automation

```yaml
pre-commit: "^3.7.0" # Git hooks
```

**Hooks:**

- Trailing whitespace
- YAML validation
- Large file prevention
- Python formatting (Black)
- Linting (Ruff)

---

### Build Tools

```
Make                        # Task automation
Poetry                      # Python deps
npm                         # Node deps
```

**Makefile Targets:**

- `make install-deps` - Install everything
- `make dev-setup` - Setup environment
- `make audit-all` - Run all checks
- `make test` - Run all tests

---

## 📊 Monitoring & Observability (Future)

### Planned Additions

```
Sentry                      # Error tracking
Prometheus                  # Metrics
Grafana                     # Dashboards
OpenTelemetry              # Tracing
```

---

## 🔐 Security Stack

### Authentication

```toml
passlib[bcrypt]            # Password hashing
```

**Features:**

- Secure password storage
- Session management
- API key authentication
- Rate limiting

---

### Security Scanning

```toml
bandit                     # Python security
```

**GitHub Security:**

- Dependabot alerts
- CodeQL scanning
- Secret scanning

---

## 📈 Market Data Stack

### Primary Providers

**Polygon.io:**

- Real-time quotes
- Historical data
- Company fundamentals
- News feed

**Alpaca:**

- Trading API
- Market data
- Paper trading
- WebSocket streams

**yfinance:**

- Historical prices
- Dividend data
- Stock info
- Fallback provider

**NewsAPI:**

- News aggregation
- Multiple sources
- Search & filtering

---

### Data Processing

```toml
pandas                     # Data manipulation
numpy                      # Numerical computing
pyarrow                    # Columnar storage
```

---

## 🎓 Development Tools

### IDE Extensions (Recommended)

- **VS Code:** ESLint, Prettier, Python, TypeScript
- **PyCharm:** Python, FastAPI support
- **IntelliJ:** TypeScript, Node.js

---

### CLI Tools

```bash
node >= 18.0.0             # JavaScript runtime
python >= 3.11.0           # Python runtime
poetry >= 1.8.0            # Python dependency management
git >= 2.0.0               # Version control
docker >= 20.0.0           # Containerization
make                       # Build automation
```

---

## 📦 Package Management

### Frontend

```
npm                        # Package manager
package-lock.json         # Lock file for reproducibility
```

---

### Backend

```
poetry                     # Dependency management
pyproject.toml            # Project config
poetry.lock               # Lock file (not tracked in git)
```

---

## 🔄 Version Strategy

### Frontend Dependencies

- **Lock minor versions** for stability
- **Update quarterly** for security
- **Test thoroughly** before major updates

### Backend Dependencies

- **Use caret versions** (^) for flexibility
- **Lock to major versions** for compatibility
- **Weekly Dependabot** checks

---

## 🚀 Performance Optimization

### Frontend

- Next.js automatic optimizations
- Image optimization built-in
- Code splitting by route
- Tree shaking unused code
- Compression enabled

### Backend

- Async/await for concurrency
- Database query optimization
- Response caching
- Connection pooling
- Lazy loading

---

## 🎯 Technology Decisions

### Why This Stack?

**Modern & Maintainable:**

- Latest stable versions
- Strong typing everywhere
- Active communities
- Good documentation

**Developer Experience:**

- Fast iteration cycles
- Hot reload everywhere
- Great debugging tools
- Comprehensive testing

**Production Ready:**

- Battle-tested frameworks
- Excellent performance
- Security best practices
- Scalable architecture

**AI-First:**

- RAG capabilities
- LLM integration
- Vector search
- Custom ML systems

---

## 📚 Learning Resources

### Frontend

- [Next.js Docs](https://nextjs.org/docs)
- [React Docs](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Tailwind CSS](https://tailwindcss.com/docs)

### Backend

- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [Pydantic Docs](https://docs.pydantic.dev/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)

### AI/ML

- [OpenAI API](https://platform.openai.com/docs)
- [Sentence Transformers](https://www.sbert.net/)
- [Qdrant Docs](https://qdrant.tech/documentation/)

---

## 🔮 Future Considerations

### Potential Additions

- **Nx/Turborepo** for monorepo management
- **Prisma** as alternative ORM
- **tRPC** for type-safe APIs
- **Vitest** for faster testing
- **Biome** as ESLint/Prettier alternative
- **Bun** as Node.js alternative

### Evaluation Criteria

- Developer experience improvement
- Performance benefits
- Maintenance overhead
- Community adoption
- Migration effort

---

**Maintained by:** ZiggyAI Development Team  
**Review Frequency:** Quarterly or when major updates available  
**Next Review:** 2025-02-09
