# ZiggyAI Mobile API & Android App Deployment Guide

## Overview

This guide covers the complete deployment process for both the mobile API backend and the Android application, from development to production.

## Table of Contents

1. [Backend API Deployment](#backend-api-deployment)
2. [Android App Deployment](#android-app-deployment)
3. [Infrastructure Setup](#infrastructure-setup)
4. [Monitoring & Maintenance](#monitoring--maintenance)
5. [Security Hardening](#security-hardening)

---

## Backend API Deployment

### Prerequisites

- Python 3.11+
- PostgreSQL database
- Redis for caching
- SSL/TLS certificates
- Domain name configured

### Option 1: Docker Deployment (Recommended)

#### 1. Create Dockerfile for Mobile API

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY backend /app/backend
COPY mobile /app/mobile

# Set environment
ENV PYTHONPATH=/app
ENV ENV=production

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. Docker Compose Configuration

```yaml
# docker-compose.yml
version: "3.8"

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/ziggyai
      - REDIS_URL=redis://redis:6379/0
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - ENV=production
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  postgres:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=ziggyai
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - api
    restart: unless-stopped

volumes:
  postgres_data:
```

#### 3. Deploy with Docker

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f api

# Scale API instances
docker-compose up -d --scale api=3
```

### Option 2: Traditional Deployment

#### 1. Setup Virtual Environment

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 2. Configure Environment

```bash
# Create production .env file
cat > .env << EOF
ENV=production
DEBUG=False
DATABASE_URL=postgresql://user:pass@localhost/ziggyai
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=$(openssl rand -hex 32)
ALLOWED_ORIGINS=https://app.ziggyai.com,https://mobile.ziggyai.com
EOF
```

#### 3. Run with Gunicorn

```bash
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
```

#### 4. Setup Systemd Service

```ini
# /etc/systemd/system/ziggyai-api.service
[Unit]
Description=ZiggyAI Mobile API
After=network.target

[Service]
Type=notify
User=ziggyai
Group=ziggyai
WorkingDirectory=/opt/ziggyai/backend
Environment="PATH=/opt/ziggyai/venv/bin"
ExecStart=/opt/ziggyai/venv/bin/gunicorn \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 127.0.0.1:8000 \
  --timeout 120 \
  app.main:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable ziggyai-api
sudo systemctl start ziggyai-api
sudo systemctl status ziggyai-api
```

### Nginx Configuration

```nginx
# /etc/nginx/sites-available/ziggyai-mobile-api
upstream ziggyai_api {
    server 127.0.0.1:8000;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name api.ziggyai.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name api.ziggyai.com;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/api.ziggyai.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.ziggyai.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=mobile_api:10m rate=60r/m;
    limit_req zone=mobile_api burst=20 nodelay;

    # Mobile API
    location /mobile/ {
        proxy_pass http://ziggyai_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://ziggyai_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Health check
    location /health {
        proxy_pass http://ziggyai_api;
        access_log off;
    }
}
```

```bash
# Enable site and reload Nginx
sudo ln -s /etc/nginx/sites-available/ziggyai-mobile-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### SSL Certificate Setup

```bash
# Install Certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d api.ziggyai.com

# Auto-renewal
sudo certbot renew --dry-run
```

---

## Android App Deployment

### Prerequisites

- Android Studio
- JDK 11+
- Gradle
- Google Play Developer Account ($25 one-time fee)
- Signing keystore

### 1. Prepare Release Build

#### Generate Signing Key

```bash
keytool -genkey -v \
  -keystore ziggyai-release-key.jks \
  -keyalg RSA \
  -keysize 2048 \
  -validity 10000 \
  -alias ziggyai
```

#### Configure Signing in build.gradle.kts

```kotlin
android {
    signingConfigs {
        create("release") {
            storeFile = file("ziggyai-release-key.jks")
            storePassword = System.getenv("KEYSTORE_PASSWORD")
            keyAlias = "ziggyai"
            keyPassword = System.getenv("KEY_PASSWORD")
        }
    }

    buildTypes {
        release {
            signingConfig = signingConfigs.getByName("release")
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
}
```

#### Configure ProGuard

```proguard
# proguard-rules.pro

# Keep Retrofit interfaces
-keep interface com.ziggyai.mobile.data.api.** { *; }

# Keep data models
-keep class com.ziggyai.mobile.data.api.models.** { *; }
-keep class com.ziggyai.mobile.domain.model.** { *; }

# Gson
-keepattributes Signature
-keepattributes *Annotation*
-keep class com.google.gson.** { *; }

# OkHttp
-dontwarn okhttp3.**
-keep class okhttp3.** { *; }

# Retrofit
-dontwarn retrofit2.**
-keep class retrofit2.** { *; }

# Firebase
-keep class com.google.firebase.** { *; }
```

### 2. Build Release APK/AAB

```bash
# Build APK
./gradlew assembleRelease

# Build App Bundle (recommended for Play Store)
./gradlew bundleRelease

# Output locations:
# APK: app/build/outputs/apk/release/app-release.apk
# AAB: app/build/outputs/bundle/release/app-release.aab
```

### 3. Test Release Build

```bash
# Install release build on device
adb install app/build/outputs/apk/release/app-release.apk

# Check for crashes
adb logcat | grep -i ziggyai
```

### 4. Google Play Store Submission

#### Prepare Store Listing

1. **App Information**
   - Title: ZiggyAI - AI Trading Assistant
   - Short description: Smart trading signals and market insights
   - Full description: [Detailed description of features]
   - Category: Finance
   - Content rating: Everyone

2. **Graphics Assets**
   - App icon: 512x512 PNG
   - Feature graphic: 1024x500 PNG
   - Phone screenshots: At least 2 (1080x1920 or higher)
   - Tablet screenshots: At least 1 (7" and 10")
   - Promo video (optional but recommended)

3. **Privacy Policy**
   - Required for apps that collect user data
   - Host at: https://ziggyai.com/privacy-policy

#### Upload to Play Console

1. **Create App in Play Console**

   ```
   https://play.google.com/console
   → Create app
   ```

2. **Upload App Bundle**

   ```
   Production → Create new release
   → Upload app-release.aab
   → Add release notes
   ```

3. **Complete Questionnaires**
   - Content rating
   - Target audience
   - Privacy policy
   - Data safety

4. **Submit for Review**
   - Initial review takes 1-7 days
   - Updates typically reviewed in 1-3 days

### 5. Beta Testing (Optional but Recommended)

#### Internal Testing

```
Play Console → Testing → Internal testing
→ Create release
→ Add testers via email
```

#### Closed Beta

```
Play Console → Testing → Closed testing
→ Create release
→ Share opt-in link
```

#### Open Beta

```
Play Console → Testing → Open testing
→ Create release
→ Anyone can join
```

---

## Infrastructure Setup

### Cloud Providers

#### AWS Deployment

```bash
# Using AWS Elastic Beanstalk
eb init ziggyai-mobile-api
eb create production
eb deploy

# Using ECS
aws ecs create-cluster --cluster-name ziggyai
aws ecs register-task-definition --cli-input-json file://task-definition.json
aws ecs create-service --cluster ziggyai --service-name api --task-definition ziggyai-api
```

#### Google Cloud Platform

```bash
# Using Cloud Run
gcloud run deploy ziggyai-api \
  --image gcr.io/PROJECT-ID/ziggyai-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated

# Using GKE
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

#### Azure Deployment

```bash
# Using Azure App Service
az webapp create --resource-group ziggyai --plan ziggyai-plan --name ziggyai-api
az webapp deployment source config --name ziggyai-api --resource-group ziggyai --repo-url https://github.com/user/ziggyai
```

### Database Setup

#### PostgreSQL on RDS (AWS)

```bash
aws rds create-db-instance \
  --db-instance-identifier ziggyai-prod \
  --db-instance-class db.t3.small \
  --engine postgres \
  --master-username admin \
  --master-user-password <password> \
  --allocated-storage 20 \
  --backup-retention-period 7
```

#### Redis Setup

```bash
# AWS ElastiCache
aws elasticache create-cache-cluster \
  --cache-cluster-id ziggyai-cache \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1
```

---

## Monitoring & Maintenance

### Application Monitoring

#### Setup Sentry for Error Tracking

```python
# backend/app/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FastApiIntegration()],
    traces_sample_rate=1.0,
    environment=settings.ENV,
)
```

#### Setup Prometheus Metrics

```python
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()
Instrumentator().instrument(app).expose(app)
```

### Android App Monitoring

#### Firebase Crashlytics

```kotlin
// build.gradle.kts
plugins {
    id("com.google.firebase.crashlytics")
}

dependencies {
    implementation("com.google.firebase:firebase-crashlytics-ktx")
}

// In Application class
FirebaseCrashlytics.getInstance().setCrashlyticsCollectionEnabled(true)
```

#### Firebase Analytics

```kotlin
dependencies {
    implementation("com.google.firebase:firebase-analytics-ktx")
}

// Track events
analytics.logEvent("screen_view") {
    param("screen_name", "Dashboard")
}
```

### Logging

#### Centralized Logging

```bash
# Using ELK Stack
docker-compose.yml:
  elasticsearch:
    image: elasticsearch:8.11.0
  logstash:
    image: logstash:8.11.0
  kibana:
    image: kibana:8.11.0
```

### Health Checks

```python
@router.get("/health/detailed")
async def detailed_health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": await check_database(),
            "redis": await check_redis(),
            "api": "up"
        },
        "version": "1.0.0"
    }
```

---

## Security Hardening

### API Security

1. **Rate Limiting**

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@router.get("/mobile/sync")
@limiter.limit("60/minute")
async def sync_data():
    pass
```

2. **API Key Rotation**

```bash
# Rotate JWT secret regularly
NEW_SECRET=$(openssl rand -hex 32)
# Update in environment
# Redeploy services
```

3. **Input Validation**

```python
from pydantic import validator

class LoginRequest(BaseModel):
    username: str
    password: str

    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username too short')
        return v.lower()
```

### Android App Security

1. **Certificate Pinning**

```kotlin
val certificatePinner = CertificatePinner.Builder()
    .add("api.ziggyai.com", "sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")
    .build()

OkHttpClient.Builder()
    .certificatePinner(certificatePinner)
    .build()
```

2. **ProGuard/R8**

```kotlin
buildTypes {
    release {
        isMinifyEnabled = true
        isShrinkResources = true
    }
}
```

3. **Root Detection**

```kotlin
fun isDeviceRooted(): Boolean {
    val paths = arrayOf(
        "/system/app/Superuser.apk",
        "/sbin/su",
        "/system/bin/su"
    )
    return paths.any { File(it).exists() }
}
```

---

## Rollback Procedures

### API Rollback

```bash
# Docker
docker-compose down
docker-compose up -d --force-recreate --build

# Systemd
sudo systemctl stop ziggyai-api
# Restore previous version
sudo systemctl start ziggyai-api
```

### App Rollback

```
Play Console → Production → Previous releases
→ Promote to production
```

---

## Checklist

### Pre-Deployment

- [ ] All tests passing
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] SSL certificates obtained
- [ ] Monitoring configured
- [ ] Backup procedures in place

### Post-Deployment

- [ ] Health check passing
- [ ] API endpoints responding
- [ ] Database connections stable
- [ ] Logs accessible
- [ ] Metrics collecting
- [ ] Alerts configured

### Android Release

- [ ] Release build tested
- [ ] ProGuard configuration verified
- [ ] Graphics assets prepared
- [ ] Store listing complete
- [ ] Privacy policy published
- [ ] Beta testing completed

---

## Support

For deployment support:

- Documentation: https://docs.ziggyai.com
- Email: devops@ziggyai.com
- Emergency: Create high-priority GitHub issue

---

## Changelog

Track all deployments:

- Date deployed
- Version number
- Changes included
- Deployment duration
- Issues encountered
