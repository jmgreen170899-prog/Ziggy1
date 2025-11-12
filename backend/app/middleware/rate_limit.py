"""
Rate limiting middleware for ZiggyAI API
"""

import logging
import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Import HAVE_SLOWAPI flag from main
from app.main import HAVE_SLOWAPI

if HAVE_SLOWAPI:
    from slowapi import Limiter as SlowAPILimiter
    from slowapi.errors import RateLimitExceeded as SlowAPIRateLimitExceeded
    from slowapi.util import get_remote_address as slowapi_get_remote_address
    
    # Use the real implementations
    Limiter = SlowAPILimiter
    RateLimitExceeded = SlowAPIRateLimitExceeded
    get_remote_address = slowapi_get_remote_address
else:
    # Provide fallback implementations
    class Limiter:
        def __init__(self, **kwargs):
            pass
    
    class RateLimitExceeded(Exception):
        def __init__(self, detail="Rate limit exceeded"):
            self.detail = detail
            super().__init__(detail)
    
    def get_remote_address(request):
        return "127.0.0.1"  # fallback IP


logger = logging.getLogger(__name__)


# Determine storage URI based on environment
def get_storage_uri():
    """Get storage URI for rate limiting backend"""
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        return redis_url
    else:
        # Fallback to memory storage for development
        logger.warning("No REDIS_URL found, using memory storage for rate limiting")
        return "memory://"


# Initialize limiter with fallback to memory storage
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=get_storage_uri(),
    default_limits=["100/minute", "1000/day"],
)


def setup_rate_limiting(app: FastAPI):
    """Setup rate limiting for the FastAPI application"""
    app.state.limiter = limiter

    # Custom rate limit exceeded handler
    @app.exception_handler(RateLimitExceeded)
    async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
        """Custom handler for rate limit exceeded errors"""
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "detail": f"Rate limit exceeded: {exc.detail}",
                "endpoint": str(request.url.path),
                "message": "Please wait before making more requests",
            },
            headers={"Retry-After": "60"},  # Default retry after 60 seconds
        )


def get_api_key_identifier(request: Request) -> str:
    """
    Get identifier for rate limiting based on API key or IP address
    """
    # Check for API key in headers
    api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization")

    if api_key:
        # Use a hash of the API key for privacy
        import hashlib

        return f"api_key_{hashlib.md5(api_key.encode()).hexdigest()[:16]}"

    # Fallback to IP address
    return get_remote_address(request)


# Rate limiting tiers
RATE_LIMITS = {
    "free": {"per_minute": 30, "per_hour": 500, "per_day": 1000},
    "premium": {"per_minute": 100, "per_hour": 2000, "per_day": 10000},
    "enterprise": {"per_minute": 500, "per_hour": 10000, "per_day": 50000},
}


def get_rate_limit_for_endpoint(endpoint_type: str = "standard") -> str:
    """
    Get rate limit string for specific endpoint types
    """
    limits = {
        "standard": "100/minute",
        "intensive": "20/minute",  # For data-intensive operations
        "signals": "30/minute",  # For signal generation
        "market_data": "200/minute",  # For market data endpoints
        "premium": "500/minute",  # For premium features
    }

    return limits.get(endpoint_type, "100/minute")
