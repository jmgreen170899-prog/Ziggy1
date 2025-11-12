# app/core/rate_limiting.py
from __future__ import annotations

import logging
import os

from fastapi import Request, Response
from starlette.responses import JSONResponse

# Import HAVE_SLOWAPI flag from main
from app.main import HAVE_SLOWAPI

if HAVE_SLOWAPI:
    from slowapi import Limiter
    from slowapi.errors import RateLimitExceeded
    from slowapi.util import get_remote_address
else:
    # Provide fallback implementations
    class Limiter:
        def __init__(self, **kwargs):
            pass
        
        def limit(self, rate_limit: str):
            """No-op decorator when rate limiting is not available"""
            def decorator(func):
                return func
            return decorator
    
    class RateLimitExceeded(Exception):
        def __init__(self, detail="Rate limit exceeded"):
            self.detail = detail
            self.retry_after = 60
            super().__init__(detail)
    
    def get_remote_address(request):
        return "127.0.0.1"


logger = logging.getLogger("ziggy.rate_limiting")


def get_client_id(request: Request) -> str:
    """
    Get client identifier for rate limiting.
    Uses IP address by default, but can be extended to use API keys, user IDs, etc.
    """
    # Try to get API key from header first
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"api_key:{api_key}"

    # Try to get user ID from auth context (if available)
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"

    # Fall back to IP address
    return get_remote_address(request)


def create_limiter() -> Limiter:
    """Create rate limiter with Redis backend if available"""
    redis_url = os.getenv("REDIS_URL")

    if redis_url:
        try:
            # Test Redis connection
            import redis

            redis.from_url(redis_url).ping()
            storage_uri = redis_url
            logger.info(f"Rate limiter using Redis backend: {redis_url}")
        except Exception as e:
            logger.warning(f"Redis not available for rate limiting ({e}), using in-memory storage")
            storage_uri = "memory://"
    else:
        logger.info("Rate limiter using in-memory storage")
        storage_uri = "memory://"

    return Limiter(
        key_func=get_client_id,
        storage_uri=storage_uri,
        default_limits=["1000/hour", "100/minute"],  # Global default limits
    )


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """Custom rate limit exceeded handler"""
    logger.warning(f"Rate limit exceeded for {get_client_id(request)}: {exc.detail}")

    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "error": {
                "type": "RateLimitExceeded",
                "message": "Rate limit exceeded",
                "details": {"retry_after": exc.retry_after, "limit": exc.detail},
            },
        },
        headers={"Retry-After": str(exc.retry_after)},
    )


# Global limiter instance
limiter = create_limiter()

# Rate limit configurations for different endpoint types
RATE_LIMITS = {
    # Core API endpoints
    "query": "10/minute",
    "agent": "5/minute",
    "ingest": "20/hour",
    # Market data endpoints
    "market_overview": "30/minute",
    "market_quotes": "60/minute",
    "market_history": "20/minute",
    # Trading endpoints
    "screener": "10/minute",
    "signals": "20/minute",
    "backtest": "5/minute",
    # News endpoints
    "news": "30/minute",
    "browse": "20/minute",
    # Health/debug endpoints (more lenient)
    "health": "60/minute",
    "debug": "100/minute",
}


def get_rate_limit(endpoint_type: str) -> str:
    """Get rate limit for specific endpoint type"""
    return RATE_LIMITS.get(endpoint_type, "30/minute")  # Default limit
