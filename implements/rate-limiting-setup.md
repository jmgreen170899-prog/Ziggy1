# Rate Limiting Configuration for ZiggyAI

## Overview
Rate limiting implementation to protect the ZiggyAI API from abuse and ensure fair usage.

## Backend Rate Limiting Implementation

### Install Required Package
```bash
pip install slowapi
```

### Add to requirements.txt
```
slowapi==0.1.9
redis==4.5.5
```

### Rate Limiting Middleware (backend/app/middleware/rate_limit.py)
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, FastAPI
import redis

# Redis connection for rate limiting
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Initialize limiter
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379",
    default_limits=["100/minute"]
)

def setup_rate_limiting(app: FastAPI):
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    # Custom rate limit exceeded handler
    @app.exception_handler(RateLimitExceeded)
    async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return {
            "error": "Rate limit exceeded",
            "detail": f"Rate limit exceeded: {exc.detail}",
            "retry_after": exc.retry_after
        }
```

### Apply Rate Limits to Routes (backend/app/api/routes_signals.py)
```python
from fastapi import Depends
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.get("/signals/status")
@limiter.limit("30/minute")  # 30 requests per minute
async def get_signals_status(request: Request):
    # Existing implementation
    pass

@router.post("/signals/generate")
@limiter.limit("10/minute")  # 10 signal generations per minute
async def generate_signal(request: Request, symbol: str):
    # Existing implementation
    pass

@router.get("/market/data")
@limiter.limit("100/minute")  # 100 market data requests per minute
async def get_market_data(request: Request):
    # Existing implementation
    pass
```

### API Key Based Rate Limiting
```python
from fastapi import Header, HTTPException
import hashlib

def get_api_key_rate_limit(api_key: str = Header(None)):
    if not api_key:
        return get_remote_address
    
    # Use API key for rate limiting
    return lambda request: hashlib.md5(api_key.encode()).hexdigest()

@router.get("/premium/signals")
@limiter.limit("500/minute", key_func=get_api_key_rate_limit)
async def get_premium_signals(request: Request, api_key: str = Header(None)):
    # Premium endpoint with higher limits
    pass
```

## Redis Configuration

### Docker Compose Redis Service
```yaml
version: '3.8'
services:
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

volumes:
  redis_data:
```

### Redis Configuration for Production
```redis
# redis.conf
maxmemory 256mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

## Frontend Rate Limiting Awareness

### API Client with Rate Limiting (frontend/src/services/api.ts)
```typescript
export class APIClient {
  private retryAfter: number = 0;
  
  async makeRequest(url: string, options: RequestInit = {}) {
    // Check if we're in a rate limit cooldown
    if (this.retryAfter > Date.now()) {
      throw new Error(`Rate limited. Retry after ${Math.ceil((this.retryAfter - Date.now()) / 1000)} seconds`);
    }
    
    try {
      const response = await fetch(url, options);
      
      if (response.status === 429) {
        // Rate limited
        const retryAfter = response.headers.get('Retry-After');
        if (retryAfter) {
          this.retryAfter = Date.now() + (parseInt(retryAfter) * 1000);
        }
        throw new Error('Rate limit exceeded');
      }
      
      return response;
    } catch (error) {
      throw error;
    }
  }
}
```

## Rate Limiting Tiers

### Free Tier
- 100 requests/minute
- 1000 requests/day
- Basic endpoints only

### Premium Tier
- 500 requests/minute
- 10000 requests/day
- All endpoints including premium signals

### Enterprise Tier
- 1000 requests/minute
- Unlimited daily requests
- Custom rate limits available

## Monitoring Rate Limits

### Rate Limit Metrics
```python
import time
from collections import defaultdict

class RateLimitMonitor:
    def __init__(self):
        self.request_counts = defaultdict(int)
        self.blocked_requests = defaultdict(int)
    
    def log_request(self, client_id: str, endpoint: str):
        key = f"{client_id}:{endpoint}"
        self.request_counts[key] += 1
    
    def log_blocked(self, client_id: str, endpoint: str):
        key = f"{client_id}:{endpoint}"
        self.blocked_requests[key] += 1
    
    def get_stats(self):
        return {
            "total_requests": sum(self.request_counts.values()),
            "blocked_requests": sum(self.blocked_requests.values()),
            "top_clients": sorted(self.request_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        }
```

## Implementation Checklist
- [ ] Install slowapi and redis packages
- [ ] Set up Redis server
- [ ] Implement rate limiting middleware
- [ ] Apply limits to API endpoints
- [ ] Configure different tiers
- [ ] Add monitoring and logging
- [ ] Test rate limiting functionality
- [ ] Document API limits for users

## Testing Rate Limits
```bash
# Test basic rate limit
for i in {1..35}; do curl http://localhost:8000/signals/status; done

# Test with different IPs
curl --header "X-Forwarded-For: 192.168.1.100" http://localhost:8000/signals/status

# Monitor Redis keys
redis-cli keys "*rate_limit*"
```