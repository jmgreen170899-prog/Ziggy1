"""
Async-safe feature facade for ZiggyAI.

This module provides async wrappers for blocking feature computation operations
to prevent event-loop blocking under heavy load. All CPU-bound and blocking I/O
operations are offloaded to executor threads/processes.

Key features:
- run_in_executor wrappers for CPU-bound feature calculations
- Background TaskPool workers for concurrent feature computation
- Async-safe interfaces for trading engine and signal pipelines
- Latency monitoring and metrics collection
"""

import asyncio
import time
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.core.logging import get_logger


logger = get_logger("ziggy.async_features")


@dataclass
class LatencyMetrics:
    """Latency metrics for async operations."""

    operation: str
    start_time: float
    end_time: float | None = None
    duration_ms: float | None = None
    success: bool = True
    error: str | None = None

    def complete(self, success: bool = True, error: str | None = None) -> None:
        """Mark operation as complete and calculate duration."""
        self.end_time = time.perf_counter()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.success = success
        self.error = error


@dataclass
class TaskPoolConfig:
    """Configuration for async task pool."""

    max_workers: int = 4
    use_process_pool: bool = False
    queue_size: int = 1000


class AsyncFeatureComputer:
    """
    Async-safe wrapper for feature computation.

    Offloads blocking feature calculations to executor threads
    to keep the asyncio event loop responsive.
    """

    def __init__(self, config: TaskPoolConfig | None = None):
        self.config = config or TaskPoolConfig()
        self._thread_pool: ThreadPoolExecutor | None = None
        self._process_pool: ProcessPoolExecutor | None = None
        self._metrics: list[LatencyMetrics] = []
        self._task_queue: asyncio.Queue[tuple[str, Callable, tuple, dict]] = asyncio.Queue(
            maxsize=self.config.queue_size
        )
        self._worker_tasks: list[asyncio.Task] = []

    async def start(self) -> None:
        """Start the async feature computer and background workers."""
        # Create executor pools
        self._thread_pool = ThreadPoolExecutor(max_workers=self.config.max_workers)
        if self.config.use_process_pool:
            self._process_pool = ProcessPoolExecutor(
                max_workers=max(2, self.config.max_workers // 2)
            )

        # Start background worker tasks
        for i in range(self.config.max_workers):
            task = asyncio.create_task(self._worker(f"worker-{i}"))
            self._worker_tasks.append(task)

        logger.info(
            "AsyncFeatureComputer started",
            extra={
                "thread_workers": self.config.max_workers,
                "process_workers": max(2, self.config.max_workers // 2)
                if self.config.use_process_pool
                else 0,
            },
        )

    async def stop(self) -> None:
        """Stop background workers and shutdown executors."""
        # Cancel worker tasks
        for task in self._worker_tasks:
            task.cancel()

        if self._worker_tasks:
            await asyncio.gather(*self._worker_tasks, return_exceptions=True)

        # Shutdown executors
        if self._thread_pool:
            self._thread_pool.shutdown(wait=True)
        if self._process_pool:
            self._process_pool.shutdown(wait=True)

        logger.info("AsyncFeatureComputer stopped")

    async def compute_features_async(
        self, ticker: str, force_refresh: bool = False, use_process_pool: bool = False
    ) -> dict | None:
        """
        Compute features for a ticker asynchronously.

        Args:
            ticker: Stock symbol
            force_refresh: Skip cache and recompute
            use_process_pool: Use process pool for CPU-intensive work

        Returns:
            Feature dictionary or None if computation fails
        """
        metric = LatencyMetrics(
            operation=f"compute_features:{ticker}", start_time=time.perf_counter()
        )

        try:
            # Import here to avoid circular dependencies
            from app.services.market_brain.features import get_ticker_features

            # Select appropriate executor
            executor = (
                self._process_pool if use_process_pool and self._process_pool else self._thread_pool
            )

            # Run in executor to avoid blocking event loop
            loop = asyncio.get_running_loop()
            features = await loop.run_in_executor(
                executor, lambda: get_ticker_features(ticker, force_refresh)
            )

            metric.complete(success=True)
            self._metrics.append(metric)

            return features

        except Exception as e:
            metric.complete(success=False, error=str(e))
            self._metrics.append(metric)
            logger.error(f"Error computing features for {ticker}", extra={"error": str(e)})
            return None

    async def compute_features_batch(
        self, tickers: list[str], force_refresh: bool = False
    ) -> dict[str, dict | None]:
        """
        Compute features for multiple tickers concurrently.

        Args:
            tickers: List of stock symbols
            force_refresh: Skip cache and recompute

        Returns:
            Dictionary mapping ticker to features
        """
        metric = LatencyMetrics(
            operation=f"compute_features_batch:{len(tickers)}", start_time=time.perf_counter()
        )

        try:
            # Create concurrent tasks for all tickers
            tasks = [self.compute_features_async(ticker, force_refresh) for ticker in tickers]

            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Build result dictionary
            feature_dict = {}
            for ticker, result in zip(tickers, results):
                if isinstance(result, Exception):
                    logger.error(
                        f"Error computing features for {ticker}", extra={"error": str(result)}
                    )
                    feature_dict[ticker] = None
                else:
                    feature_dict[ticker] = result

            metric.complete(success=True)
            self._metrics.append(metric)

            return feature_dict

        except Exception as e:
            metric.complete(success=False, error=str(e))
            self._metrics.append(metric)
            logger.error("Error in batch feature computation", extra={"error": str(e)})
            return {}

    async def compute_signal_async(
        self, ticker: str, signal_type: str = "momentum", **kwargs: Any
    ) -> dict | None:
        """
        Generate trading signal asynchronously.

        Args:
            ticker: Stock symbol
            signal_type: Type of signal to generate
            **kwargs: Additional signal parameters

        Returns:
            Signal dictionary or None if generation fails
        """
        metric = LatencyMetrics(
            operation=f"compute_signal:{ticker}:{signal_type}", start_time=time.perf_counter()
        )

        try:
            # Import here to avoid circular dependencies
            from app.services.market_brain.signals import (
                generate_mean_reversion_signal,
                generate_momentum_signal,
            )

            # Select signal generation function
            signal_func = (
                generate_momentum_signal
                if signal_type == "momentum"
                else generate_mean_reversion_signal
            )

            # Run in executor to avoid blocking
            loop = asyncio.get_running_loop()
            signal = await loop.run_in_executor(
                self._thread_pool, lambda: signal_func(ticker, **kwargs)
            )

            metric.complete(success=True)
            self._metrics.append(metric)

            return signal.to_dict() if signal else None

        except Exception as e:
            metric.complete(success=False, error=str(e))
            self._metrics.append(metric)
            logger.error(
                f"Error computing signal for {ticker}",
                extra={"signal_type": signal_type, "error": str(e)},
            )
            return None

    async def execute_blocking_operation(
        self, operation_name: str, func: Callable, *args: Any, **kwargs: Any
    ) -> Any:
        """
        Execute a blocking operation asynchronously.

        Generic wrapper for any blocking function that needs to run
        without blocking the event loop.

        Args:
            operation_name: Name for metrics tracking
            func: Blocking function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result of func execution
        """
        metric = LatencyMetrics(operation=operation_name, start_time=time.perf_counter())

        try:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(self._thread_pool, lambda: func(*args, **kwargs))

            metric.complete(success=True)
            self._metrics.append(metric)

            return result

        except Exception as e:
            metric.complete(success=False, error=str(e))
            self._metrics.append(metric)
            logger.error(
                f"Error executing blocking operation: {operation_name}", extra={"error": str(e)}
            )
            raise

    async def enqueue_task(self, task_id: str, func: Callable, *args: Any, **kwargs: Any) -> None:
        """
        Enqueue a task for background processing.

        Args:
            task_id: Unique identifier for the task
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
        """
        try:
            await self._task_queue.put((task_id, func, args, kwargs))
        except asyncio.QueueFull:
            logger.warning(f"Task queue full, dropping task: {task_id}")

    async def _worker(self, worker_id: str) -> None:
        """Background worker for processing queued tasks."""
        logger.info(f"Worker {worker_id} started")

        try:
            while True:
                try:
                    # Get task from queue with timeout
                    task_id, func, args, kwargs = await asyncio.wait_for(
                        self._task_queue.get(), timeout=1.0
                    )

                    # Execute task
                    metric = LatencyMetrics(
                        operation=f"worker_task:{task_id}", start_time=time.perf_counter()
                    )

                    try:
                        loop = asyncio.get_running_loop()
                        await loop.run_in_executor(self._thread_pool, lambda: func(*args, **kwargs))
                        metric.complete(success=True)

                    except Exception as e:
                        metric.complete(success=False, error=str(e))
                        logger.error(
                            f"Worker {worker_id} task failed",
                            extra={"task_id": task_id, "error": str(e)},
                        )

                    self._metrics.append(metric)

                except TimeoutError:
                    continue

        except asyncio.CancelledError:
            logger.info(f"Worker {worker_id} cancelled")
            raise

    def get_metrics(self, last_n: int = 100) -> list[dict[str, Any]]:
        """
        Get recent latency metrics.

        Args:
            last_n: Number of recent metrics to return

        Returns:
            List of metric dictionaries
        """
        recent_metrics = self._metrics[-last_n:] if last_n > 0 else self._metrics

        return [
            {
                "operation": m.operation,
                "duration_ms": m.duration_ms,
                "success": m.success,
                "error": m.error,
                "timestamp": datetime.fromtimestamp(m.start_time).isoformat(),
            }
            for m in recent_metrics
        ]

    def get_summary_metrics(self) -> dict[str, Any]:
        """
        Get summary statistics for latency metrics.

        Returns:
            Dictionary with summary statistics
        """
        if not self._metrics:
            return {
                "total_operations": 0,
                "success_rate": 0.0,
                "avg_latency_ms": 0.0,
                "p50_latency_ms": 0.0,
                "p95_latency_ms": 0.0,
                "p99_latency_ms": 0.0,
                "max_latency_ms": 0.0,
            }

        successful = [m for m in self._metrics if m.success and m.duration_ms is not None]
        durations = sorted([m.duration_ms for m in successful if m.duration_ms is not None])

        if not durations:
            return {
                "total_operations": len(self._metrics),
                "success_rate": 0.0,
                "avg_latency_ms": 0.0,
                "p50_latency_ms": 0.0,
                "p95_latency_ms": 0.0,
                "p99_latency_ms": 0.0,
                "max_latency_ms": 0.0,
            }

        return {
            "total_operations": len(self._metrics),
            "success_rate": len(successful) / len(self._metrics) * 100,
            "avg_latency_ms": sum(durations) / len(durations),
            "p50_latency_ms": durations[len(durations) // 2],
            "p95_latency_ms": durations[int(len(durations) * 0.95)]
            if len(durations) > 1
            else durations[0],
            "p99_latency_ms": durations[int(len(durations) * 0.99)]
            if len(durations) > 1
            else durations[0],
            "max_latency_ms": max(durations),
        }

    def clear_metrics(self) -> None:
        """Clear collected metrics."""
        self._metrics.clear()


# Global instance
_async_feature_computer: AsyncFeatureComputer | None = None


def get_async_feature_computer() -> AsyncFeatureComputer:
    """Get the global async feature computer instance."""
    global _async_feature_computer
    if _async_feature_computer is None:
        _async_feature_computer = AsyncFeatureComputer()
    return _async_feature_computer


async def init_async_features(config: TaskPoolConfig | None = None) -> None:
    """
    Initialize the async feature computation system.

    Args:
        config: Task pool configuration
    """
    global _async_feature_computer
    if _async_feature_computer is not None:
        await _async_feature_computer.stop()

    _async_feature_computer = AsyncFeatureComputer(config)
    await _async_feature_computer.start()


async def shutdown_async_features() -> None:
    """Shutdown the async feature computation system."""
    global _async_feature_computer
    if _async_feature_computer is not None:
        await _async_feature_computer.stop()
        _async_feature_computer = None
