# ZiggyAI Troubleshooting Guide

Solutions to common issues when running ZiggyAI.

---

## Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Installation Issues](#installation-issues)
- [Backend Issues](#backend-issues)
- [Frontend Issues](#frontend-issues)
- [Database Issues](#database-issues)
- [API & Network Issues](#api--network-issues)
- [Docker Issues](#docker-issues)
- [Performance Issues](#performance-issues)
- [Getting Help](#getting-help)

---

## Quick Diagnostics

### Health Check Commands

```bash
# Backend health
curl http://localhost:8000/health

# Detailed health
curl http://localhost:8000/health/detailed

# Core dependencies
curl http://localhost:8000/api/core/health

# Trading service
curl http://localhost:8000/trade/health

# Paper trading
curl http://localhost:8000/api/paper/health
```

### Check Service Status

```bash
# Check if ports are in use
lsof -i :8000  # Backend
lsof -i :5173  # Frontend
lsof -i :5432  # PostgreSQL
lsof -i :6333  # Qdrant
lsof -i :6379  # Redis

# Docker services
docker-compose ps
docker-compose logs --tail=50
```

---

## Installation Issues

### Python Version Mismatch

**Error:**
```
Python 3.11 or higher is required
```

**Solution:**
```bash
# Check current version
python --version

# Install Python 3.11 with pyenv
curl https://pyenv.run | bash
pyenv install 3.11.0
pyenv local 3.11.0

# Or use apt (Ubuntu)
sudo apt install python3.11 python3.11-venv
```

### Node.js Version Mismatch

**Error:**
```
error engine: required { "node": ">=18" }
```

**Solution:**
```bash
# Install with nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
nvm use 18
```

### pip Install Failures

**Error:**
```
ERROR: Could not build wheels for ...
```

**Solution:**
```bash
# Install build dependencies
sudo apt install python3-dev build-essential

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Retry installation
pip install -r requirements.lock
```

### npm Install Failures

**Error:**
```
npm ERR! code ERESOLVE
npm ERR! ERESOLVE could not resolve
```

**Solution:**
```bash
# Clean install
rm -rf node_modules package-lock.json
npm cache clean --force
npm install

# Or use legacy peer deps
npm install --legacy-peer-deps
```

---

## Backend Issues

### Server Won't Start

**Error:**
```
Address already in use: port 8000
```

**Solution:**
```bash
# Find and kill process
lsof -i :8000
kill -9 <PID>

# Or use different port
uvicorn app.main:app --port 8001
```

### Import Errors

**Error:**
```
ModuleNotFoundError: No module named 'app'
```

**Solution:**
```bash
# Make sure you're in backend directory
cd backend

# Activate virtual environment
source .venv/bin/activate

# Reinstall in editable mode
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Configuration Errors

**Error:**
```
pydantic.ValidationError: SECRET_KEY required
```

**Solution:**
```bash
# Create .env file
cp .env.demo.example .env

# Or set environment variable
export SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
```

### Database Not Connected

**Error:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solution:**
```bash
# For SQLite (default)
# Ensure DATABASE_URL is set correctly
DATABASE_URL=sqlite:///./ziggy.db

# For PostgreSQL
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -h localhost -U ziggy -d ziggy
```

---

## Frontend Issues

### Development Server Won't Start

**Error:**
```
Error: listen EADDRINUSE: address already in use :::5173
```

**Solution:**
```bash
# Kill process on port
lsof -i :5173
kill -9 <PID>

# Or use different port
npm run dev -- --port 5174
```

### Build Failures

**Error:**
```
Module not found: Can't resolve '...'
```

**Solution:**
```bash
# Clean install
rm -rf node_modules .next
npm install
npm run build
```

### Environment Variables Not Loading

**Error:**
```
VITE_API_BASE is undefined
```

**Solution:**
```bash
# Create .env file
echo "VITE_API_BASE=http://localhost:8000" > .env

# Or .env.local for Next.js
echo "NEXT_PUBLIC_API_BASE=http://localhost:8000" > .env.local

# Restart dev server after changes
```

### TypeScript Errors

**Error:**
```
Type error: Property 'x' does not exist on type 'y'
```

**Solution:**
```bash
# Clear TypeScript cache
rm -rf .next tsconfig.tsbuildinfo

# Regenerate types
npm run typecheck

# Or skip type checking temporarily
npm run build -- --no-type-check
```

---

## Database Issues

### SQLite Locked

**Error:**
```
sqlite3.OperationalError: database is locked
```

**Solution:**
```bash
# Ensure only one connection
# Close other database clients

# Or switch to PostgreSQL for concurrency
DATABASE_URL=postgresql://user:pass@localhost/ziggy
```

### PostgreSQL Connection Refused

**Error:**
```
connection refused to localhost:5432
```

**Solution:**
```bash
# Start PostgreSQL
sudo systemctl start postgresql

# Check it's running
sudo systemctl status postgresql

# Check connection settings
sudo -u postgres psql -c "SHOW port;"
```

### Migration Errors

**Error:**
```
Table already exists / doesn't exist
```

**Solution:**
```bash
# Reset database (development only!)
cd backend
python -c "
from app.models.base import engine, Base
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
"
```

### Connection Pool Exhausted

**Error:**
```
QueuePool limit of 5 overflow 10 reached
```

**Solution:**
```python
# In config.py, increase pool size
SQLALCHEMY_POOL_SIZE = 10
SQLALCHEMY_MAX_OVERFLOW = 20
```

---

## API & Network Issues

### CORS Errors

**Error:**
```
Access to fetch has been blocked by CORS policy
```

**Solution:**
```python
# In backend main.py, add origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### API Timeout

**Error:**
```
TimeoutError: Request timed out
```

**Solution:**
```bash
# Increase timeout in frontend
const response = await fetch(url, { timeout: 30000 });

# Or in backend
CHAT_REQUEST_TIMEOUT_SEC=90
```

### Rate Limiting

**Error:**
```
429 Too Many Requests
```

**Solution:**
```bash
# Wait and retry
# Or adjust rate limits in backend

# Check your request frequency
# Implement exponential backoff
```

### WebSocket Connection Failed

**Error:**
```
WebSocket connection failed
```

**Solution:**
```bash
# Check WebSocket endpoint
wscat -c ws://localhost:8000/ws/market

# Ensure backend supports WebSocket
# Check nginx/proxy configuration
```

---

## Docker Issues

### Container Won't Start

**Error:**
```
Error starting container: port is already allocated
```

**Solution:**
```bash
# Stop all containers
docker-compose down

# Remove orphan containers
docker-compose down --remove-orphans

# Start fresh
docker-compose up
```

### Volume Permission Issues

**Error:**
```
Permission denied: '/data/...'
```

**Solution:**
```bash
# Fix permissions
sudo chown -R 1000:1000 ./data

# Or run as root (development only)
docker-compose run --user root backend bash
```

### Out of Disk Space

**Error:**
```
no space left on device
```

**Solution:**
```bash
# Clean Docker resources
docker system prune -a --volumes

# Remove specific volumes
docker volume ls
docker volume rm ziggy_postgres_data
```

### Build Cache Issues

**Error:**
```
Using cache for layer that should be rebuilt
```

**Solution:**
```bash
# Force rebuild
docker-compose build --no-cache

# Or specific service
docker-compose build --no-cache backend
```

---

## Performance Issues

### Slow API Responses

**Diagnosis:**
```bash
# Check response time
time curl http://localhost:8000/health

# Check backend logs for slow queries
docker-compose logs backend | grep -i slow
```

**Solutions:**
1. Enable database query logging to find slow queries
2. Add indexes to frequently queried columns
3. Implement caching with Redis
4. Reduce N+1 queries

### High Memory Usage

**Diagnosis:**
```bash
# Check container memory
docker stats

# Check system memory
free -h
```

**Solutions:**
1. Reduce worker processes
2. Add memory limits in docker-compose
3. Optimize pandas operations
4. Clear caches periodically

### Slow Frontend

**Diagnosis:**
- Open browser DevTools → Performance tab
- Check Network waterfall

**Solutions:**
1. Enable production build
2. Implement lazy loading
3. Optimize bundle size
4. Use CDN for static assets

---

## External Service Issues

### Market Data Provider Errors

**Error:**
```
Polygon API error: 401 Unauthorized
```

**Solution:**
```bash
# Verify API key
echo $POLYGON_API_KEY

# Test directly
curl "https://api.polygon.io/v2/aggs/ticker/AAPL/prev?apiKey=$POLYGON_API_KEY"

# Fallback to yfinance (no key required)
PROVIDERS_PRICES=yfinance
```

### OpenAI API Errors

**Error:**
```
openai.error.AuthenticationError
```

**Solution:**
```bash
# Verify API key
echo $OPENAI_API_KEY

# Test with curl
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Use local LLM fallback
USE_OPENAI=false
LOCAL_LLM_BASE_URL=http://localhost:11434/v1
```

### Telegram Not Sending

**Error:**
```
Telegram send failed
```

**Solution:**
```bash
# Verify bot token
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe"

# Check chat ID
# Send message to bot, then:
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getUpdates"
```

---

## Getting Help

### Before Creating an Issue

1. **Search existing issues** on GitHub
2. **Check this guide** for your error
3. **Gather information:**
   - Error message (full stack trace)
   - Steps to reproduce
   - Environment (OS, Python/Node versions)
   - Configuration (sanitized)

### Creating a Good Issue

```markdown
## Description
Brief description of the issue

## Environment
- OS: Ubuntu 22.04
- Python: 3.11.0
- Node.js: 18.17.0
- Docker: 24.0.5 (if applicable)

## Steps to Reproduce
1. Clone repository
2. Run `npm run dev:all`
3. Navigate to /trading
4. Error appears

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Error Log
```
Paste full error message here
```

## Configuration
```bash
# Relevant env vars (redact secrets!)
DATABASE_URL=postgresql://...
```
```

### Quick Contact

- **GitHub Issues**: For bugs and features
- **Discussions**: For questions and help
- **Documentation**: Check `/docs` folder

---

## Common Error Reference

| Error | Cause | Quick Fix |
|-------|-------|-----------|
| `EADDRINUSE` | Port in use | `lsof -i :PORT && kill -9 PID` |
| `ModuleNotFoundError` | Missing dependency | `pip install -r requirements.lock` |
| `CORS error` | Cross-origin blocked | Add origin to CORS middleware |
| `401 Unauthorized` | Invalid API key | Check/regenerate API key |
| `500 Internal Error` | Server error | Check backend logs |
| `Connection refused` | Service not running | Start the service |
| `database locked` | SQLite concurrency | Use PostgreSQL |
| `disk full` | No space | `docker system prune` |

---

**Still stuck?** Create an issue with details from this guide.
