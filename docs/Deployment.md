# ZiggyAI Deployment Guide

Complete guide for deploying ZiggyAI to production environments.

---

## Table of Contents

- [Deployment Options](#deployment-options)
- [Docker Deployment](#docker-deployment)
- [Render Deployment](#render-deployment)
- [Vercel Deployment](#vercel-deployment)
- [Manual VPS Deployment](#manual-vps-deployment)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [SSL/HTTPS Setup](#sslhttps-setup)
- [Monitoring & Logging](#monitoring--logging)
- [Scaling Considerations](#scaling-considerations)
- [Security Checklist](#security-checklist)

---

## Deployment Options

| Platform | Best For | Complexity | Cost |
|----------|----------|------------|------|
| Docker Compose | Self-hosted, VPS | Medium | Variable |
| Render | Full-stack apps | Low | $7+/month |
| Vercel + Render | Frontend + Backend | Low | $0-20/month |
| Railway | Full-stack apps | Low | $5+/month |
| AWS/GCP/Azure | Enterprise scale | High | Variable |

---

## Docker Deployment

### Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        VITE_API_BASE: https://api.your-domain.com
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
    depends_on:
      - backend
    restart: unless-stopped

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - ENV=production
      - DEBUG=false
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379/0
      - QDRANT_URL=http://qdrant:6333
    depends_on:
      - postgres
      - redis
      - qdrant
    restart: unless-stopped

  postgres:
    image: postgres:16-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

  qdrant:
    image: qdrant/qdrant:latest
    volumes:
      - qdrant_data:/qdrant/storage
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - frontend
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  qdrant_data:
```

### Backend Dockerfile

Create `backend/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.lock .
RUN pip install --no-cache-dir -r requirements.lock

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Run with gunicorn
CMD ["gunicorn", "app.main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120"]
```

### Frontend Dockerfile

Create `frontend/Dockerfile`:

```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Build application
COPY . .
ARG VITE_API_BASE
ENV VITE_API_BASE=$VITE_API_BASE
RUN npm run build

# Production image
FROM node:18-alpine

WORKDIR /app

COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/node_modules ./node_modules

EXPOSE 3000

CMD ["npm", "start"]
```

### Deploy with Docker

```bash
# Create environment file
cp .env.example .env.prod
# Edit .env.prod with production values

# Build and deploy
docker-compose -f docker-compose.prod.yml up -d --build

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Scale backend
docker-compose -f docker-compose.prod.yml up -d --scale backend=3
```

---

## Render Deployment

### Backend on Render

1. **Create New Web Service**
   - Connect GitHub repository
   - Select `backend` directory as root

2. **Configure Build Settings**
   ```
   Build Command: pip install -r requirements.lock
   Start Command: gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
   ```

3. **Set Environment Variables**
   ```
   ENV=production
   DEBUG=false
   SECRET_KEY=your-secret-key
   DATABASE_URL=postgresql://... (from Render PostgreSQL)
   ```

4. **Add PostgreSQL Database**
   - Create PostgreSQL service on Render
   - Copy connection string to `DATABASE_URL`

### Frontend on Render

1. **Create Static Site**
   - Connect GitHub repository
   - Select `frontend` directory as root

2. **Configure Build Settings**
   ```
   Build Command: npm install && npm run build
   Publish Directory: .next
   ```

3. **Set Environment Variables**
   ```
   VITE_API_BASE=https://your-backend.onrender.com
   ```

### render.yaml (Infrastructure as Code)

```yaml
services:
  - type: web
    name: ziggy-backend
    env: python
    buildCommand: pip install -r requirements.lock
    startCommand: gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
    envVars:
      - key: ENV
        value: production
      - key: DATABASE_URL
        fromDatabase:
          name: ziggy-db
          property: connectionString

  - type: web
    name: ziggy-frontend
    env: node
    buildCommand: npm install && npm run build
    startCommand: npm start
    envVars:
      - key: VITE_API_BASE
        value: https://ziggy-backend.onrender.com

databases:
  - name: ziggy-db
    databaseName: ziggy
    user: ziggy
```

---

## Vercel Deployment

### Frontend on Vercel

1. **Import Project**
   - Connect GitHub repository
   - Select `frontend` as root directory

2. **Configure Project**
   ```json
   // frontend/vercel.json
   {
     "buildCommand": "npm run build",
     "outputDirectory": ".next",
     "framework": "nextjs"
   }
   ```

3. **Environment Variables**
   ```
   VITE_API_BASE=https://your-backend-url.com
   ```

4. **Deploy**
   - Push to main branch
   - Vercel auto-deploys

### Backend (Vercel Serverless Functions)

> Note: FastAPI on Vercel requires adaptation. Consider using Render for the backend.

```python
# api/index.py (alternative serverless approach)
from app.main import app

handler = app
```

---

## Manual VPS Deployment

### Prerequisites

- Ubuntu 22.04 LTS server
- Domain name pointing to server IP
- SSH access

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.11 python3.11-venv python3-pip \
    nodejs npm nginx certbot python3-certbot-nginx \
    postgresql postgresql-contrib redis-server

# Create application user
sudo useradd -m -s /bin/bash ziggy
sudo su - ziggy
```

### 2. Clone and Setup

```bash
# Clone repository
git clone https://github.com/your-org/ZiggyAI.git
cd ZiggyAI

# Backend setup
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.lock

# Frontend setup
cd ../frontend
npm install
npm run build
```

### 3. Systemd Services

**Backend Service** (`/etc/systemd/system/ziggy-backend.service`):

```ini
[Unit]
Description=ZiggyAI Backend
After=network.target postgresql.service

[Service]
User=ziggy
Group=ziggy
WorkingDirectory=/home/ziggy/ZiggyAI/backend
Environment="PATH=/home/ziggy/ZiggyAI/backend/.venv/bin"
EnvironmentFile=/home/ziggy/ZiggyAI/backend/.env
ExecStart=/home/ziggy/ZiggyAI/backend/.venv/bin/gunicorn \
    app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

**Frontend Service** (`/etc/systemd/system/ziggy-frontend.service`):

```ini
[Unit]
Description=ZiggyAI Frontend
After=network.target

[Service]
User=ziggy
Group=ziggy
WorkingDirectory=/home/ziggy/ZiggyAI/frontend
ExecStart=/usr/bin/npm start
Restart=always
Environment="NODE_ENV=production"
Environment="PORT=3000"

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable ziggy-backend ziggy-frontend
sudo systemctl start ziggy-backend ziggy-frontend
```

### 4. Nginx Configuration

```nginx
# /etc/nginx/sites-available/ziggy
server {
    listen 80;
    server_name your-domain.com api.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}

server {
    listen 443 ssl http2;
    server_name api.your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable site and get SSL
sudo ln -s /etc/nginx/sites-available/ziggy /etc/nginx/sites-enabled/
sudo certbot --nginx -d your-domain.com -d api.your-domain.com
sudo systemctl restart nginx
```

---

## Environment Configuration

### Production Environment Variables

```bash
# Core
ENV=production
DEBUG=false
SECRET_KEY=generate-strong-256-bit-key

# Database
DATABASE_URL=postgresql://user:password@host:5432/ziggy

# Security
ALLOWED_ORIGINS=https://your-domain.com
ENABLE_AUTH=true
ACCESS_TOKEN_EXPIRE_MINUTES=30

# External Services
POLYGON_API_KEY=your-key
OPENAI_API_KEY=your-key
```

### Generating Secret Key

```bash
# Python
python -c "import secrets; print(secrets.token_hex(32))"

# OpenSSL
openssl rand -hex 32
```

---

## Database Setup

### PostgreSQL Production Setup

```sql
-- Create production database
CREATE DATABASE ziggy_prod;
CREATE USER ziggy_app WITH ENCRYPTED PASSWORD 'strong-password';
GRANT ALL PRIVILEGES ON DATABASE ziggy_prod TO ziggy_app;

-- Enable extensions
\c ziggy_prod
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

### Database Migrations

```bash
# Initialize tables
cd backend
source .venv/bin/activate
python -c "from app.models.base import create_tables; create_tables()"
```

### Backup Strategy

```bash
# Daily backup cron job
0 2 * * * pg_dump $DATABASE_URL | gzip > /backups/ziggy_$(date +\%Y\%m\%d).sql.gz

# Restore from backup
gunzip < backup.sql.gz | psql $DATABASE_URL
```

---

## SSL/HTTPS Setup

### Let's Encrypt (Certbot)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal (added automatically)
sudo certbot renew --dry-run
```

---

## Monitoring & Logging

### Application Logs

```bash
# View backend logs
journalctl -u ziggy-backend -f

# View frontend logs
journalctl -u ziggy-frontend -f
```

### Health Checks

```bash
# Backend health
curl https://api.your-domain.com/health

# Detailed health
curl https://api.your-domain.com/health/detailed
```

### Monitoring Tools

- **Uptime**: UptimeRobot, Pingdom
- **Metrics**: Prometheus + Grafana
- **Error Tracking**: Sentry
- **Logs**: Datadog, Papertrail

---

## Scaling Considerations

### Horizontal Scaling

```bash
# Scale backend instances
docker-compose up -d --scale backend=4

# With load balancer (nginx)
upstream backend {
    least_conn;
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}
```

### Database Scaling

- Read replicas for heavy read workloads
- Connection pooling with PgBouncer
- Consider managed databases (RDS, Cloud SQL)

### Caching Strategy

- Redis for session/cache
- CDN for static assets
- Response caching for expensive queries

---

## Security Checklist

### Before Going Live

- [ ] Change default SECRET_KEY
- [ ] Enable HTTPS only
- [ ] Configure CORS properly
- [ ] Enable rate limiting
- [ ] Disable debug mode
- [ ] Set up database backups
- [ ] Configure firewall rules
- [ ] Review authentication settings
- [ ] Audit environment variables
- [ ] Test health endpoints

### Ongoing Security

- [ ] Keep dependencies updated
- [ ] Monitor for vulnerabilities
- [ ] Review access logs
- [ ] Regular security audits
- [ ] Rotate API keys periodically

---

## Troubleshooting Deployment

### Common Issues

**502 Bad Gateway**
- Check backend service is running
- Verify nginx proxy_pass URL
- Check application logs

**Database Connection Failed**
- Verify DATABASE_URL format
- Check PostgreSQL is running
- Verify network/firewall rules

**SSL Certificate Issues**
- Renew certificate: `sudo certbot renew`
- Check certificate paths in nginx config

---

## Additional Resources

- [SetupGuide.md](SetupGuide.md) - Local development setup
- [Troubleshooting.md](Troubleshooting.md) - Common issues
- [Architecture.md](architecture.md) - System design

---

**Need help?** Create an issue on GitHub with deployment logs and configuration details.
