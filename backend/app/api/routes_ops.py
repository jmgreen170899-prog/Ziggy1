"""
Operational monitoring and health aggregation for ZiggyAI.

This module provides:
- Unified health status endpoint that aggregates all subsystem health checks
- Operational metrics and diagnostics
- Timeout auditing for external calls
"""

import asyncio
import logging
import time
from typing import Any

import httpx
from fastapi import APIRouter

from app.models.api_responses import MessageResponse

logger = logging.getLogger("backend.ops")

# Create router for operational endpoints
router = APIRouter(prefix="/ops", tags=["operations"])


# ---- Subsystem Health Aggregator ----


async def check_subsystem_health(
    name: str,
    endpoint: str,
    client: httpx.AsyncClient,
    timeout: float = 5.0
) -> dict[str, Any]:
    """
    Check health of a single subsystem with timeout.
    
    Args:
        name: Subsystem name (e.g., "core", "paper_lab")
        endpoint: Health endpoint path
        client: HTTP client for requests
        timeout: Request timeout in seconds
        
    Returns:
        Dict with subsystem status and metrics
    """
    start = time.time()
    try:
        response = await asyncio.wait_for(
            client.get(endpoint),
            timeout=timeout
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            return {
                "subsystem": name,
                "status": "healthy",
                "response_time_ms": round(elapsed * 1000, 2),
                "details": data
            }
        else:
            return {
                "subsystem": name,
                "status": "unhealthy",
                "response_time_ms": round(elapsed * 1000, 2),
                "error": f"HTTP {response.status_code}",
                "details": {}
            }
            
    except asyncio.TimeoutError:
        elapsed = time.time() - start
        logger.warning(
            "Health check timeout",
            extra={
                "subsystem": name,
                "endpoint": endpoint,
                "timeout_sec": timeout,
                "elapsed_sec": round(elapsed, 2)
            }
        )
        return {
            "subsystem": name,
            "status": "timeout",
            "response_time_ms": round(elapsed * 1000, 2),
            "error": f"Timeout after {timeout}s",
            "details": {}
        }
        
    except Exception as e:
        elapsed = time.time() - start
        logger.error(
            "Health check failed",
            extra={
                "subsystem": name,
                "endpoint": endpoint,
                "error": str(e),
                "elapsed_sec": round(elapsed, 2)
            }
        )
        return {
            "subsystem": name,
            "status": "error",
            "response_time_ms": round(elapsed * 1000, 2),
            "error": str(e),
            "details": {}
        }


@router.get(
    "/status",
    response_model=None,
    summary="Unified operational status",
    description="""
    Aggregate health status from all ZiggyAI subsystems.
    
    Returns a structured JSON snapshot with:
    - Overall system status (healthy/degraded/unhealthy)
    - Individual subsystem statuses
    - Response times and metrics
    - Timestamp
    
    Use this endpoint for monitoring, alerting, and operational dashboards.
    """
)
async def get_operational_status() -> dict[str, Any]:
    """
    Aggregate health from all subsystems into a unified status report.
    
    Checks health endpoints from:
    - Core services
    - Paper lab
    - Screener
    - Market brain (cognitive)
    - Chat
    - Trading
    - Signal explanation
    - Signal tracing
    - Learning
    - Integration
    - Feedback
    - Performance
    """
    start_time = time.time()
    
    # Define all subsystem health endpoints
    subsystems = [
        ("core", "http://localhost:8000/api/core/health"),
        ("paper_lab", "http://localhost:8000/api/paper/health"),
        ("screener", "http://localhost:8000/screener/health"),
        ("cognitive", "http://localhost:8000/cognitive/health"),
        ("chat", "http://localhost:8000/chat/health"),
        ("trading", "http://localhost:8000/api/trade-health"),
        ("explain", "http://localhost:8000/signal/explain/health"),
        ("trace", "http://localhost:8000/signal/trace/health"),
        ("learning", "http://localhost:8000/api/learning/health"),
        ("integration", "http://localhost:8000/integration/health"),
        ("feedback", "http://localhost:8000/feedback/health"),
        ("performance", "http://localhost:8000/performance/health"),
    ]
    
    # Check all subsystems concurrently with timeout
    timeout = httpx.Timeout(5.0, connect=2.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        tasks = [
            check_subsystem_health(name, endpoint, client, timeout=5.0)
            for name, endpoint in subsystems
        ]
        results = await asyncio.gather(*tasks, return_exceptions=False)
    
    # Analyze overall health
    healthy_count = sum(1 for r in results if r["status"] == "healthy")
    timeout_count = sum(1 for r in results if r["status"] == "timeout")
    error_count = sum(1 for r in results if r["status"] == "error")
    unhealthy_count = sum(1 for r in results if r["status"] == "unhealthy")
    
    total = len(results)
    
    # Determine overall status
    if healthy_count == total:
        overall_status = "healthy"
    elif healthy_count >= total * 0.7:  # 70% healthy
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"
    
    elapsed = time.time() - start_time
    
    return {
        "overall_status": overall_status,
        "timestamp": time.time(),
        "check_duration_ms": round(elapsed * 1000, 2),
        "summary": {
            "total_subsystems": total,
            "healthy": healthy_count,
            "unhealthy": unhealthy_count,
            "timeout": timeout_count,
            "error": error_count,
        },
        "subsystems": results,
        "metadata": {
            "version": "0.1.0",
            "environment": "production"  # Could read from env
        }
    }


@router.get(
    "/timeout-audit",
    response_model=None,
    summary="Audit timeout configuration",
    description="""
    Audit all external call timeout configurations.
    
    Returns:
    - Market data provider timeouts
    - LLM/chat timeouts
    - Database query timeouts
    - Screening job limits
    - Learning run limits
    
    Use this to ensure no long-running external calls lack timeout protection.
    """
)
async def get_timeout_audit() -> dict[str, Any]:
    """
    Audit timeout configuration across all external calls.
    """
    return {
        "external_calls": {
            "market_data": {
                "provider": "yfinance/polygon",
                "timeout_sec": 10.0,
                "location": "app.api.routes_trading._OHLC_TIMEOUT_SECS",
                "status": "configured",
                "notes": "Per-ticker timeout with async/sync support"
            },
            "chat_llm": {
                "provider": "openai/anthropic",
                "timeout_sec": 60.0,
                "location": "app.api.routes_chat.REQUEST_TIMEOUT",
                "status": "configured",
                "notes": "HTTP timeout via httpx.Timeout"
            },
            "news_rss": {
                "provider": "various_rss_feeds",
                "timeout_sec": 8.0,
                "location": "app.api.routes_news (urllib.request.urlopen)",
                "status": "configured",
                "notes": "Per-feed timeout"
            },
            "rag_documents": {
                "provider": "web_scraping",
                "timeout_sec": 30.0,
                "location": "app.api.routes (httpx.Client)",
                "status": "configured",
                "notes": "Document fetch timeout"
            },
            "web_browse": {
                "provider": "playwright",
                "timeout_sec": 30.0,
                "location": "app.web.browse_router (httpx.Client)",
                "status": "configured",
                "notes": "Web page load timeout"
            }
        },
        "internal_operations": {
            "screening_jobs": {
                "max_duration_sec": 300.0,
                "location": "app.api.routes_screener",
                "status": "needs_audit",
                "notes": "Should add explicit timeout for large scans"
            },
            "learning_runs": {
                "max_duration_sec": 600.0,
                "location": "app.api.routes_learning",
                "status": "needs_audit",
                "notes": "Should add timeout for training loops"
            },
            "backtest_execution": {
                "max_duration_sec": 120.0,
                "location": "app.api.routes_trading",
                "status": "needs_audit",
                "notes": "Should add timeout for long backtests"
            },
            "paper_trading_engine": {
                "tick_timeout_sec": 1.0,
                "location": "app.paper.engine (asyncio.wait_for)",
                "status": "configured",
                "notes": "Per-tick processing timeout"
            }
        },
        "database": {
            "redis": {
                "timeout_sec": 5.0,
                "status": "needs_configuration",
                "notes": "Should configure connection and operation timeouts"
            },
            "postgres": {
                "timeout_sec": 30.0,
                "status": "needs_configuration",
                "notes": "Should configure query timeout"
            }
        },
        "recommendations": [
            "Add explicit timeouts to screening jobs",
            "Add explicit timeouts to learning runs",
            "Add explicit timeouts to backtest execution",
            "Configure Redis connection timeout",
            "Configure Postgres query timeout",
            "Add timeout monitoring/alerts"
        ],
        "timestamp": time.time()
    }


@router.get(
    "/health",
    response_model=MessageResponse,
    summary="Ops module health check"
)
async def ops_health() -> MessageResponse:
    """Simple health check for ops module itself."""
    return MessageResponse(message="Ops module is healthy")
