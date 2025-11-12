# app/core/health.py
from __future__ import annotations

import asyncio
import time
from datetime import datetime
from typing import Any


try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

from app.core.config.time_tuning import TIMEOUTS
from app.core.logging import get_logger


logger = get_logger("ziggy.health")


class HealthChecker:
    """Comprehensive health checking system"""

    def __init__(self):
        self.checks: dict[str, Any] = {}
        self.results_cache: dict[str, dict[str, Any]] = {}
        self.cache_ttl = 30  # seconds

    def register_check(self, name: str, check_func: Any, timeout: float = 5.0):
        """Register a health check function"""
        self.checks[name] = {"func": check_func, "timeout": timeout}

    async def run_check(self, name: str) -> dict[str, Any]:
        """Run a single health check"""
        if name not in self.checks:
            return {
                "status": "ERROR",
                "message": f"Unknown health check: {name}",
                "timestamp": datetime.utcnow().isoformat(),
            }

        check_info = self.checks[name]
        start_time = time.time()

        try:
            # Run check with timeout
            result = await asyncio.wait_for(check_info["func"](), timeout=check_info["timeout"])

            response_time = (time.time() - start_time) * 1000  # ms

            return {
                "status": "OK",
                "response_time_ms": round(response_time, 2),
                "result": result,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except TimeoutError:
            return {
                "status": "ERROR",
                "message": f"Health check timeout after {check_info['timeout']}s",
                "response_time_ms": (time.time() - start_time) * 1000,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.exception(f"Health check '{name}' failed")
            return {
                "status": "ERROR",
                "message": str(e),
                "response_time_ms": (time.time() - start_time) * 1000,
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def run_all_checks(self) -> dict[str, Any]:
        """Run all registered health checks"""
        results = {}

        # Run checks in parallel
        tasks = {name: self.run_check(name) for name in self.checks.keys()}

        completed = await asyncio.gather(*tasks.values(), return_exceptions=True)

        for name, result in zip(tasks.keys(), completed, strict=False):
            if isinstance(result, Exception):
                results[name] = {
                    "status": "ERROR",
                    "message": f"Check execution failed: {result}",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            else:
                results[name] = result

        # Calculate overall health
        overall_status = "OK"
        error_count = sum(1 for r in results.values() if r.get("status") == "ERROR")
        warning_count = sum(1 for r in results.values() if r.get("status") == "WARNING")

        if error_count > 0:
            overall_status = "ERROR"
        elif warning_count > 0:
            overall_status = "WARNING"

        return {
            "overall_status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": results,
            "summary": {
                "total_checks": len(results),
                "ok_count": len(results) - error_count - warning_count,
                "warning_count": warning_count,
                "error_count": error_count,
            },
        }


# System health checks
async def check_system_resources() -> dict[str, Any]:
    """Check system CPU, memory, and disk usage"""
    try:
        if not PSUTIL_AVAILABLE:
            return {
                "cpu_usage_percent": 0,
                "memory_usage_percent": 0,
                "memory_available_mb": 0,
                "disk_usage_percent": 0,
                "disk_free_gb": 0,
                "note": "psutil not available",
            }

        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        return {
            "cpu_usage_percent": cpu_percent,
            "memory_usage_percent": memory.percent,
            "memory_available_mb": memory.available // (1024 * 1024),
            "disk_usage_percent": disk.percent,
            "disk_free_gb": disk.free // (1024 * 1024 * 1024),
        }
    except Exception as e:
        raise Exception(f"Failed to get system resources: {e}")


async def check_database() -> dict[str, Any]:
    """Check database connectivity"""
    try:
        from app.models.base import engine

        if not engine:
            return {"status": "Not configured"}

        # Test connection
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            result.fetchone()

        return {"status": "Connected", "engine": str(engine.url).split("@")[0] + "@***"}
    except Exception as e:
        raise Exception(f"Database check failed: {e}")


async def check_redis() -> dict[str, Any]:
    """Check Redis connectivity"""
    try:
        import os

        redis_url = os.getenv("REDIS_URL")

        if not redis_url:
            return {"status": "Not configured"}

        import redis

        r = redis.from_url(redis_url)
        r.ping()

        info = r.info()
        return {
            "status": "Connected",
            "memory_usage_mb": info.get("used_memory", 0) // (1024 * 1024),
            "connected_clients": info.get("connected_clients", 0),
        }
    except ImportError:
        return {"status": "Redis not available"}
    except Exception as e:
        raise Exception(f"Redis check failed: {e}")


async def check_external_apis() -> dict[str, Any]:
    """Check external API connectivity"""
    import os

    import httpx

    results = {}

    # Check if we have API keys configured
    api_keys = {
        "polygon": os.getenv("POLYGON_API_KEY"),
        "alpaca_key": os.getenv("ALPACA_KEY_ID"),
        "alpaca_secret": os.getenv("ALPACA_SECRET_KEY"),
        "openai": os.getenv("OPENAI_API_KEY"),
        "news_api": os.getenv("NEWS_API_KEY"),
    }

    configured_apis = {k: v for k, v in api_keys.items() if v}

    # Test basic connectivity to public endpoints
    test_urls = {
        "polygon": "https://api.polygon.io/v1/marketstatus/now",
        "yahoo_finance": "https://query1.finance.yahoo.com/v8/finance/chart/AAPL",
    }

    async with httpx.AsyncClient(timeout=TIMEOUTS["health_check"]) as client:
        for service, url in test_urls.items():
            try:
                response = await client.get(url)
                results[service] = {
                    "status": "Reachable" if response.status_code < 500 else "Error",
                    "status_code": response.status_code,
                }
            except Exception as e:
                results[service] = {"status": "Unreachable", "error": str(e)}

    return {"configured_apis": list(configured_apis.keys()), "connectivity_tests": results}


async def check_market_data_providers() -> dict[str, Any]:
    """Check market data provider status"""
    try:
        from app.core.circuit_breaker import get_all_circuit_breakers
        from app.services.provider_factory import get_price_provider

        provider = get_price_provider()
        circuit_breakers = get_all_circuit_breakers()

        provider_info = {
            "available": provider is not None,
            "type": type(provider).__name__ if provider else None,
        }

        if hasattr(provider, "providers"):
            provider_info["chain_length"] = len(provider.providers)
            provider_info["provider_names"] = [type(p).__name__ for p in provider.providers]

        return {"provider_info": provider_info, "circuit_breakers": circuit_breakers}
    except Exception as e:
        raise Exception(f"Provider check failed: {e}")


# Global health checker instance
health_checker = HealthChecker()

# Register default health checks
health_checker.register_check("system", check_system_resources)
health_checker.register_check("database", check_database)
health_checker.register_check("redis", check_redis)
health_checker.register_check("external_apis", check_external_apis)
health_checker.register_check("market_providers", check_market_data_providers)
