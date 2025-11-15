"""
Centralized timeout, retry, and queue configuration for ZiggyAI.

This module provides a single authoritative source for all timing-related
tuning parameters used throughout the application. Values can be overridden
via environment variables for production tuning without code changes.

Environment Variable Format:
- TIMEOUT_<KEY> for timeout overrides (e.g., TIMEOUT_HTTP_CLIENT_DEFAULT)
- BACKOFF_<KEY> for backoff overrides (e.g., BACKOFF_MIN_DELAY)
- QUEUE_<KEY> for queue limit overrides (e.g., QUEUE_WEBSOCKET)
"""

from __future__ import annotations

import os
from typing import Any


def _get_float_env(key: str, default: float) -> float:
    """Get float value from environment with fallback to default."""
    try:
        val = os.getenv(key)
        return float(val) if val is not None else default
    except (ValueError, TypeError):
        return default


def _get_int_env(key: str, default: int) -> int:
    """Get integer value from environment with fallback to default."""
    try:
        val = os.getenv(key)
        return int(val) if val is not None else default
    except (ValueError, TypeError):
        return default


# =============================================================================
# TIMEOUTS
# =============================================================================
# All timeout values in seconds unless otherwise specified

TIMEOUTS = {
    # HTTP Client Timeouts
    "http_client_default": _get_float_env("TIMEOUT_HTTP_CLIENT_DEFAULT", 15.0),
    "http_client_short": _get_float_env("TIMEOUT_HTTP_CLIENT_SHORT", 5.0),
    "http_client_medium": _get_float_env("TIMEOUT_HTTP_CLIENT_MEDIUM", 10.0),
    "http_client_long": _get_float_env("TIMEOUT_HTTP_CLIENT_LONG", 20.0),
    # WebSocket Timeouts
    "websocket_send": _get_float_env("TIMEOUT_WEBSOCKET_SEND", 2.5),
    "websocket_queue_get": _get_float_env("TIMEOUT_WEBSOCKET_QUEUE_GET", 1.5),
    # Async Operation Timeouts
    "async_fast": _get_float_env("TIMEOUT_ASYNC_FAST", 0.5),
    "async_standard": _get_float_env("TIMEOUT_ASYNC_STANDARD", 1.0),
    "async_medium": _get_float_env("TIMEOUT_ASYNC_MEDIUM", 2.5),
    "async_slow": _get_float_env("TIMEOUT_ASYNC_SLOW", 3.5),
    # RSS Feed Timeouts
    "rss_total": _get_float_env("TIMEOUT_RSS_TOTAL", 5.0),
    "rss_connect": _get_float_env("TIMEOUT_RSS_CONNECT", 1.5),
    "rss_sock_read": _get_float_env("TIMEOUT_RSS_SOCK_READ", 2.5),
    # Telemetry
    "telemetry_http": _get_int_env("TIMEOUT_TELEMETRY_HTTP", 5),
    "telemetry_queue_get": _get_float_env("TIMEOUT_TELEMETRY_QUEUE_GET", 1.0),
    # Provider-specific
    "provider_default": _get_float_env("TIMEOUT_PROVIDER_DEFAULT", 5.0),
    "provider_market_data": _get_float_env("TIMEOUT_PROVIDER_MARKET_DATA", 15.0),
    # Health Check
    "health_check": _get_float_env("TIMEOUT_HEALTH_CHECK", 5.0),
}


# =============================================================================
# BACKOFFS
# =============================================================================
# Retry backoff configuration for exponential backoff with jitter

BACKOFFS = {
    # Default backoff settings (used by JitterBackoff class)
    "min_delay": _get_float_env("BACKOFF_MIN_DELAY", 0.5),
    "max_delay": _get_float_env("BACKOFF_MAX_DELAY", 10.0),
    "factor": _get_float_env("BACKOFF_FACTOR", 2.0),
    "jitter": _get_float_env("BACKOFF_JITTER", 0.2),
    # News streaming specific backoff
    "news_min_delay": _get_float_env("BACKOFF_NEWS_MIN_DELAY", 1.0),
    "news_max_delay": _get_float_env("BACKOFF_NEWS_MAX_DELAY", 15.0),
    "news_factor": _get_float_env("BACKOFF_NEWS_FACTOR", 2.0),
    "news_jitter": _get_float_env("BACKOFF_NEWS_JITTER", 0.25),
    # Portfolio streaming backoff
    "portfolio_max_delay": _get_float_env("BACKOFF_PORTFOLIO_MAX_DELAY", 30.0),
    "portfolio_base": _get_float_env("BACKOFF_PORTFOLIO_BASE", 2.0),
    "portfolio_max_streak": _get_int_env("BACKOFF_PORTFOLIO_MAX_STREAK", 5),
    # Provider retry backoff
    "provider_base": _get_float_env("BACKOFF_PROVIDER_BASE", 0.5),
    "provider_retries": _get_int_env("BACKOFF_PROVIDER_RETRIES", 2),
    "provider_fail_penalty": _get_int_env("BACKOFF_PROVIDER_FAIL_PENALTY", 10),
}


# =============================================================================
# QUEUE_LIMITS
# =============================================================================
# Maximum queue sizes for various async queues

QUEUE_LIMITS = {
    # WebSocket queues
    "websocket_default": _get_int_env("QUEUE_WEBSOCKET_DEFAULT", 100),
    "websocket_enqueue_timeout_ms": _get_int_env(
        "QUEUE_WEBSOCKET_ENQUEUE_TIMEOUT_MS", 50
    ),
    # Telemetry queue
    "telemetry_events": _get_int_env("QUEUE_TELEMETRY_EVENTS", 1000),
    "telemetry_batch_size": _get_int_env("QUEUE_TELEMETRY_BATCH_SIZE", 50),
    "telemetry_flush_interval": _get_int_env("QUEUE_TELEMETRY_FLUSH_INTERVAL", 30),
    # Portfolio streaming queue
    "portfolio_snapshots": _get_int_env("QUEUE_PORTFOLIO_SNAPSHOTS", 100),
}


# =============================================================================
# Helper Functions
# =============================================================================


def get_timeout(key: str, default: float | None = None) -> float:
    """
    Get timeout value by key with optional default fallback.

    Args:
        key: Timeout key from TIMEOUTS dictionary
        default: Optional default value if key not found

    Returns:
        Timeout value in seconds

    Raises:
        KeyError: If key not found and no default provided
    """
    if default is not None:
        return TIMEOUTS.get(key, default)
    return TIMEOUTS[key]


def get_backoff(key: str, default: Any = None) -> Any:
    """
    Get backoff parameter by key with optional default fallback.

    Args:
        key: Backoff key from BACKOFFS dictionary
        default: Optional default value if key not found

    Returns:
        Backoff parameter value

    Raises:
        KeyError: If key not found and no default provided
    """
    if default is not None:
        return BACKOFFS.get(key, default)
    return BACKOFFS[key]


def get_queue_limit(key: str, default: int | None = None) -> int:
    """
    Get queue limit by key with optional default fallback.

    Args:
        key: Queue limit key from QUEUE_LIMITS dictionary
        default: Optional default value if key not found

    Returns:
        Queue size limit (integer)

    Raises:
        KeyError: If key not found and no default provided
    """
    if default is not None:
        return QUEUE_LIMITS.get(key, default)
    return QUEUE_LIMITS[key]


# =============================================================================
# Exports for backward compatibility
# =============================================================================
# These constants are exported for easier migration from Settings class

# From Settings (lines 149-156 in config.py)
BACKOFF_MIN_MS = int(BACKOFFS["min_delay"] * 1000)
BACKOFF_MAX_MS = int(BACKOFFS["max_delay"] * 1000)
BACKOFF_FACTOR = BACKOFFS["factor"]
BACKOFF_JITTER = BACKOFFS["jitter"]

# WebSocket settings (from Settings lines 145-147)
WS_QUEUE_MAXSIZE = QUEUE_LIMITS["websocket_default"]
WS_ENQUEUE_TIMEOUT_MS = QUEUE_LIMITS["websocket_enqueue_timeout_ms"]

# Provider timeout (from Settings line 156)
MARKET_FETCH_TIMEOUT_S = TIMEOUTS["provider_default"]
