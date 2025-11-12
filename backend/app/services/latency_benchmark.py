"""
Latency benchmarking utilities for async feature execution.

This module provides tools to measure and compare event loop responsiveness
before and after the async refactoring, demonstrating the performance improvements.
"""

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.core.logging import get_logger


logger = get_logger("ziggy.benchmark")


@dataclass
class BenchmarkResult:
    """Results from a latency benchmark run."""

    name: str
    description: str
    num_operations: int
    total_duration_ms: float
    avg_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    throughput_ops_per_sec: float
    event_loop_lag_avg_ms: float
    event_loop_lag_p95_ms: float
    success_rate: float
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "name": self.name,
            "description": self.description,
            "metrics": {
                "total_operations": self.num_operations,
                "total_duration_ms": self.total_duration_ms,
                "throughput_ops_per_sec": self.throughput_ops_per_sec,
                "success_rate": self.success_rate,
            },
            "latency": {
                "avg_ms": self.avg_latency_ms,
                "min_ms": self.min_latency_ms,
                "max_ms": self.max_latency_ms,
                "p50_ms": self.p50_latency_ms,
                "p95_ms": self.p95_latency_ms,
                "p99_ms": self.p99_latency_ms,
            },
            "event_loop": {
                "avg_lag_ms": self.event_loop_lag_avg_ms,
                "p95_lag_ms": self.event_loop_lag_p95_ms,
            },
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ComparisonResult:
    """Comparison between two benchmark results."""

    baseline: BenchmarkResult
    optimized: BenchmarkResult

    @property
    def latency_improvement_pct(self) -> float:
        """Calculate percentage improvement in average latency."""
        if self.baseline.avg_latency_ms == 0:
            return 0.0
        return (
            (self.baseline.avg_latency_ms - self.optimized.avg_latency_ms)
            / self.baseline.avg_latency_ms
            * 100
        )

    @property
    def throughput_improvement_pct(self) -> float:
        """Calculate percentage improvement in throughput."""
        if self.baseline.throughput_ops_per_sec == 0:
            return 0.0
        return (
            (self.optimized.throughput_ops_per_sec - self.baseline.throughput_ops_per_sec)
            / self.baseline.throughput_ops_per_sec
            * 100
        )

    @property
    def loop_lag_improvement_pct(self) -> float:
        """Calculate percentage improvement in event loop lag."""
        if self.baseline.event_loop_lag_p95_ms == 0:
            return 0.0
        return (
            (self.baseline.event_loop_lag_p95_ms - self.optimized.event_loop_lag_p95_ms)
            / self.baseline.event_loop_lag_p95_ms
            * 100
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "baseline": self.baseline.to_dict(),
            "optimized": self.optimized.to_dict(),
            "improvements": {
                "latency_reduction_pct": round(self.latency_improvement_pct, 2),
                "throughput_increase_pct": round(self.throughput_improvement_pct, 2),
                "loop_lag_reduction_pct": round(self.loop_lag_improvement_pct, 2),
            },
            "summary": self._generate_summary(),
        }

    def _generate_summary(self) -> str:
        """Generate human-readable summary of improvements."""
        parts = []

        if self.latency_improvement_pct > 0:
            parts.append(f"Latency reduced by {self.latency_improvement_pct:.1f}%")

        if self.throughput_improvement_pct > 0:
            parts.append(f"Throughput increased by {self.throughput_improvement_pct:.1f}%")

        if self.loop_lag_improvement_pct > 0:
            parts.append(f"Event loop lag reduced by {self.loop_lag_improvement_pct:.1f}%")

        return ". ".join(parts) if parts else "No significant improvements"


class LatencyBenchmark:
    """Benchmarking tool for measuring async operation performance."""

    def __init__(self):
        self.results: list[BenchmarkResult] = []

    async def benchmark_operation(
        self,
        name: str,
        description: str,
        operation: Callable,
        num_operations: int = 100,
        concurrent: bool = True,
        monitor_loop_lag: bool = True,
    ) -> BenchmarkResult:
        """
        Benchmark a specific operation.

        Args:
            name: Name of the benchmark
            description: Description of what's being benchmarked
            operation: Async callable to benchmark
            num_operations: Number of operations to perform
            concurrent: Whether to run operations concurrently
            monitor_loop_lag: Whether to monitor event loop lag

        Returns:
            BenchmarkResult with metrics
        """
        logger.info(
            f"Starting benchmark: {name}",
            extra={"num_operations": num_operations, "concurrent": concurrent},
        )

        # Track latencies
        latencies: list[float] = []
        loop_lags: list[float] = []
        success_count = 0

        # Start loop lag monitor if requested
        monitor_task = None
        if monitor_loop_lag:
            monitor_task = asyncio.create_task(self._monitor_loop_lag(loop_lags, duration_sec=10))

        # Run benchmark
        start_time = time.perf_counter()

        if concurrent:
            # Run all operations concurrently
            tasks = []
            for i in range(num_operations):
                task_start = time.perf_counter()

                async def wrapped_operation(start_t=task_start):
                    try:
                        await operation()
                        latency = (time.perf_counter() - start_t) * 1000
                        latencies.append(latency)
                        return True
                    except Exception as e:
                        logger.error(f"Operation failed: {e}")
                        return False

                tasks.append(wrapped_operation())

            results = await asyncio.gather(*tasks, return_exceptions=True)
            success_count = sum(1 for r in results if r is True)

        else:
            # Run operations sequentially
            for i in range(num_operations):
                task_start = time.perf_counter()
                try:
                    await operation()
                    latencies.append((time.perf_counter() - task_start) * 1000)
                    success_count += 1
                except Exception as e:
                    logger.error(f"Operation failed: {e}")

        total_duration = (time.perf_counter() - start_time) * 1000  # Convert to ms

        # Stop loop lag monitor
        if monitor_task:
            monitor_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass

        # Calculate statistics
        if not latencies:
            latencies = [0.0]

        latencies_sorted = sorted(latencies)

        result = BenchmarkResult(
            name=name,
            description=description,
            num_operations=num_operations,
            total_duration_ms=total_duration,
            avg_latency_ms=sum(latencies) / len(latencies),
            min_latency_ms=min(latencies),
            max_latency_ms=max(latencies),
            p50_latency_ms=latencies_sorted[len(latencies_sorted) // 2],
            p95_latency_ms=latencies_sorted[int(len(latencies_sorted) * 0.95)]
            if len(latencies_sorted) > 1
            else latencies_sorted[0],
            p99_latency_ms=latencies_sorted[int(len(latencies_sorted) * 0.99)]
            if len(latencies_sorted) > 1
            else latencies_sorted[0],
            throughput_ops_per_sec=num_operations / (total_duration / 1000)
            if total_duration > 0
            else 0,
            event_loop_lag_avg_ms=sum(loop_lags) / len(loop_lags) if loop_lags else 0,
            event_loop_lag_p95_ms=sorted(loop_lags)[int(len(loop_lags) * 0.95)]
            if len(loop_lags) > 1
            else (loop_lags[0] if loop_lags else 0),
            success_rate=(success_count / num_operations * 100) if num_operations > 0 else 0,
        )

        self.results.append(result)

        logger.info(
            f"Benchmark complete: {name}",
            extra={
                "avg_latency_ms": result.avg_latency_ms,
                "throughput": result.throughput_ops_per_sec,
                "success_rate": result.success_rate,
            },
        )

        return result

    async def _monitor_loop_lag(
        self, lag_measurements: list[float], duration_sec: float = 10
    ) -> None:
        """Monitor event loop lag during benchmark."""
        end_time = time.perf_counter() + duration_sec

        while time.perf_counter() < end_time:
            start = time.perf_counter()
            await asyncio.sleep(0)  # Yield to event loop
            lag = (time.perf_counter() - start) * 1000  # Convert to ms
            lag_measurements.append(lag)
            await asyncio.sleep(0.01)  # 10ms between measurements

    async def compare_approaches(
        self,
        baseline_op: Callable,
        optimized_op: Callable,
        num_operations: int = 100,
        description: str = "Performance Comparison",
    ) -> ComparisonResult:
        """
        Compare baseline and optimized approaches.

        Args:
            baseline_op: Baseline operation (blocking)
            optimized_op: Optimized operation (async)
            num_operations: Number of operations to test
            description: Description of comparison

        Returns:
            ComparisonResult with comparison metrics
        """
        logger.info(f"Running comparison: {description}")

        # Run baseline
        baseline_result = await self.benchmark_operation(
            name="Baseline (Blocking)",
            description=f"{description} - baseline approach",
            operation=baseline_op,
            num_operations=num_operations,
            concurrent=True,
        )

        # Run optimized
        optimized_result = await self.benchmark_operation(
            name="Optimized (Async)",
            description=f"{description} - optimized approach",
            operation=optimized_op,
            num_operations=num_operations,
            concurrent=True,
        )

        comparison = ComparisonResult(baseline=baseline_result, optimized=optimized_result)

        logger.info(
            f"Comparison complete: {description}",
            extra={
                "latency_improvement_pct": comparison.latency_improvement_pct,
                "throughput_improvement_pct": comparison.throughput_improvement_pct,
            },
        )

        return comparison

    def get_all_results(self) -> list[dict[str, Any]]:
        """Get all benchmark results."""
        return [result.to_dict() for result in self.results]

    def clear_results(self) -> None:
        """Clear all stored results."""
        self.results.clear()


# Global instance
_benchmark = LatencyBenchmark()


def get_benchmark() -> LatencyBenchmark:
    """Get the global benchmark instance."""
    return _benchmark


async def run_feature_computation_benchmark(
    num_operations: int = 100,
) -> ComparisonResult:
    """
    Run benchmark comparing blocking vs async feature computation.

    Args:
        num_operations: Number of feature computations to test

    Returns:
        ComparisonResult showing improvements
    """
    from app.services.async_features import get_async_feature_computer

    benchmark = get_benchmark()

    # Simulated blocking feature computation
    def blocking_compute():
        total = 0
        for i in range(5000):
            total += i
        return {"computed": True, "value": total}

    async def baseline_operation():
        """Simulate blocking operation in event loop."""
        blocking_compute()

    async def optimized_operation():
        """Use async feature computer."""
        computer = get_async_feature_computer()
        await computer.execute_blocking_operation("feature_compute", blocking_compute)

    return await benchmark.compare_approaches(
        baseline_op=baseline_operation,
        optimized_op=optimized_operation,
        num_operations=num_operations,
        description="Feature Computation",
    )


async def run_signal_generation_benchmark(
    num_operations: int = 100,
) -> ComparisonResult:
    """
    Run benchmark comparing blocking vs async signal generation.

    Args:
        num_operations: Number of signal generations to test

    Returns:
        ComparisonResult showing improvements
    """
    from app.services.async_features import get_async_feature_computer

    benchmark = get_benchmark()

    # Simulated blocking signal generation
    def blocking_signal():
        total = 0
        for i in range(3000):
            total += i
        return {"signal": "LONG", "confidence": 0.8}

    async def baseline_operation():
        """Simulate blocking operation in event loop."""
        blocking_signal()

    async def optimized_operation():
        """Use async feature computer."""
        computer = get_async_feature_computer()
        await computer.execute_blocking_operation("signal_gen", blocking_signal)

    return await benchmark.compare_approaches(
        baseline_op=baseline_operation,
        optimized_op=optimized_operation,
        num_operations=num_operations,
        description="Signal Generation",
    )
