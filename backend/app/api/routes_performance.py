"""
Performance and benchmarking API endpoints.

Provides access to async feature execution metrics, latency benchmarks,
and performance comparison reports.
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.core.logging import get_logger
from app.services.async_features import get_async_feature_computer
from app.services.latency_benchmark import (
    get_benchmark,
    run_feature_computation_benchmark,
    run_signal_generation_benchmark,
)


logger = get_logger("ziggy.api.performance")

router = APIRouter(prefix="/api/performance", tags=["performance"])


@router.get("/metrics", response_model=None)
async def get_performance_metrics(last_n: int = Query(100, ge=1, le=1000)) -> dict[str, Any]:
    """
    Get recent performance metrics from async feature computer.

    Args:
        last_n: Number of recent metrics to return (1-1000)

    Returns:
        Performance metrics including latencies and success rates
    """
    try:
        computer = get_async_feature_computer()
        metrics = computer.get_metrics(last_n=last_n)
        summary = computer.get_summary_metrics()

        return {
            "ok": True,
            "summary": summary,
            "recent_operations": metrics,
            "count": len(metrics),
        }

    except Exception as e:
        logger.error(f"Error fetching performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/summary", response_model=None)
async def get_metrics_summary() -> dict[str, Any]:
    """
    Get summary statistics for async feature execution.

    Returns:
        Aggregated performance statistics
    """
    try:
        computer = get_async_feature_computer()
        summary = computer.get_summary_metrics()

        return {
            "ok": True,
            "metrics": summary,
        }

    except Exception as e:
        logger.error(f"Error fetching metrics summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/metrics/clear", response_model=None)
async def clear_metrics() -> dict[str, Any]:
    """
    Clear collected performance metrics.

    Returns:
        Confirmation of metrics cleared
    """
    try:
        computer = get_async_feature_computer()
        computer.clear_metrics()

        return {
            "ok": True,
            "message": "Performance metrics cleared",
        }

    except Exception as e:
        logger.error(f"Error clearing metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/benchmarks", response_model=None)
async def get_benchmark_results() -> dict[str, Any]:
    """
    Get all benchmark results.

    Returns:
        List of all benchmark runs and their results
    """
    try:
        benchmark = get_benchmark()
        results = benchmark.get_all_results()

        return {
            "ok": True,
            "benchmarks": results,
            "count": len(results),
        }

    except Exception as e:
        logger.error(f"Error fetching benchmarks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/benchmarks/feature-computation", response_model=None)
async def run_feature_benchmark(num_operations: int = Query(100, ge=10, le=1000)) -> dict[str, Any]:
    """
    Run feature computation benchmark.

    Compares blocking vs async feature computation performance.

    Args:
        num_operations: Number of operations to benchmark (10-1000)

    Returns:
        Benchmark comparison results
    """
    try:
        logger.info(f"Running feature computation benchmark with {num_operations} operations")

        comparison = await run_feature_computation_benchmark(num_operations)

        return {
            "ok": True,
            "comparison": comparison.to_dict(),
        }

    except Exception as e:
        logger.error(f"Error running feature benchmark: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/benchmarks/signal-generation", response_model=None)
async def run_signal_benchmark(num_operations: int = Query(100, ge=10, le=1000)) -> dict[str, Any]:
    """
    Run signal generation benchmark.

    Compares blocking vs async signal generation performance.

    Args:
        num_operations: Number of operations to benchmark (10-1000)

    Returns:
        Benchmark comparison results
    """
    try:
        logger.info(f"Running signal generation benchmark with {num_operations} operations")

        comparison = await run_signal_generation_benchmark(num_operations)

        return {
            "ok": True,
            "comparison": comparison.to_dict(),
        }

    except Exception as e:
        logger.error(f"Error running signal benchmark: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/benchmarks/clear", response_model=None)
async def clear_benchmarks() -> dict[str, Any]:
    """
    Clear all benchmark results.

    Returns:
        Confirmation of benchmarks cleared
    """
    try:
        benchmark = get_benchmark()
        benchmark.clear_results()

        return {
            "ok": True,
            "message": "Benchmark results cleared",
        }

    except Exception as e:
        logger.error(f"Error clearing benchmarks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=None)
async def get_performance_health() -> dict[str, Any]:
    """
    Get health status of async feature execution system.

    Returns:
        Health metrics and status
    """
    try:
        computer = get_async_feature_computer()
        summary = computer.get_summary_metrics()

        # Determine health status based on metrics
        is_healthy = True
        issues = []

        # Check success rate
        if summary["success_rate"] < 95:
            is_healthy = False
            issues.append(f"Low success rate: {summary['success_rate']:.1f}%")

        # Check P95 latency
        if summary["p95_latency_ms"] > 100:
            is_healthy = False
            issues.append(f"High P95 latency: {summary['p95_latency_ms']:.1f}ms")

        # Check average latency
        if summary["avg_latency_ms"] > 50:
            is_healthy = False
            issues.append(f"High average latency: {summary['avg_latency_ms']:.1f}ms")

        return {
            "ok": True,
            "healthy": is_healthy,
            "status": "healthy" if is_healthy else "degraded",
            "issues": issues,
            "metrics": summary,
        }

    except Exception as e:
        logger.error(f"Error checking performance health: {e}")
        return {
            "ok": False,
            "healthy": False,
            "status": "unhealthy",
            "issues": ["Performance health check failed"],
        }
