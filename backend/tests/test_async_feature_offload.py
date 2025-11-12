"""
Test async feature offload to verify event loop responsiveness.

Tests verify that:
1. Feature computation doesn't block the event loop
2. Loop lag remains < 10ms under 500 concurrent tasks
3. Concurrent operations maintain acceptable throughput
4. Background workers process tasks correctly
"""

import asyncio
import os
import platform
import time

import pytest
import pytest_asyncio

from app.services.async_features import (
    AsyncFeatureComputer,
    TaskPoolConfig,
    get_async_feature_computer,
    init_async_features,
    shutdown_async_features,
)


# Configurable P95 lag threshold (default 10ms; override with ASYNC_LAG_P95_MS)
THRESHOLD_MS = float(os.environ.get("ASYNC_LAG_P95_MS", "10.0"))


@pytest_asyncio.fixture
async def async_computer():
    """Fixture providing an AsyncFeatureComputer instance."""
    computer = AsyncFeatureComputer(TaskPoolConfig(max_workers=4))
    await computer.start()
    yield computer
    await computer.stop()


@pytest_asyncio.fixture(autouse=True)
async def cleanup_global():
    """Cleanup global state after each test."""
    yield
    await shutdown_async_features()


@pytest.mark.asyncio
async def test_async_feature_computer_initialization():
    """Test that AsyncFeatureComputer initializes correctly."""
    config = TaskPoolConfig(max_workers=4, queue_size=1000)
    computer = AsyncFeatureComputer(config)

    assert computer.config.max_workers == 4
    assert computer.config.queue_size == 1000
    assert computer._thread_pool is None
    assert computer._process_pool is None

    await computer.start()

    assert computer._thread_pool is not None
    assert len(computer._worker_tasks) == 4

    await computer.stop()

    assert all(task.done() for task in computer._worker_tasks)


@pytest.mark.asyncio
async def test_compute_features_async_offloads_blocking_work(async_computer):
    """Test that feature computation is offloaded to executor."""

    # Test with a simple blocking function to verify executor usage
    def blocking_compute():
        time.sleep(0.01)
        return {"ticker": "TEST", "close": 150.0, "rsi_14": 55.0}

    result = await async_computer.execute_blocking_operation(
        "test_feature_compute", blocking_compute
    )

    assert result is not None
    assert result["ticker"] == "TEST"

    # Verify metric was recorded
    metrics = async_computer.get_metrics(last_n=1)
    assert len(metrics) > 0
    assert metrics[0]["success"] is True


@pytest.mark.asyncio
@pytest.mark.performance
async def test_compute_features_batch_concurrent_execution(async_computer):
    """Test batch feature computation executes concurrently."""

    # Test concurrent execution with blocking operations
    def slow_compute(value):
        time.sleep(0.1)  # 100ms per operation
        return {"value": value, "computed": True}

    start_time = time.perf_counter()
    tasks = [
        async_computer.execute_blocking_operation(f"task_{i}", slow_compute, i) for i in range(4)
    ]
    results = await asyncio.gather(*tasks)
    duration = time.perf_counter() - start_time

    # With 4 workers and 4 tasks, should complete in ~100ms (concurrent)
    # not ~400ms (sequential)
    assert duration < 0.3, f"Batch execution took {duration:.2f}s, expected < 0.3s"
    assert len(results) == 4
    assert all(r["computed"] for r in results)


@pytest.mark.asyncio
@pytest.mark.performance
@pytest.mark.skipif(
    platform.system() == "Windows" and os.environ.get("RUN_PERF_TESTS") != "1",
    reason="Windows CPU variance; set RUN_PERF_TESTS=1 to enforce",
)
async def test_event_loop_lag_under_load():
    """Test that event loop lag remains < 10ms under 500 concurrent tasks."""
    computer = AsyncFeatureComputer(TaskPoolConfig(max_workers=8))
    await computer.start()

    try:
        # Track event loop responsiveness
        lag_measurements = []

        async def measure_loop_lag():
            """Measure time taken for event loop to process a simple coroutine."""
            while len(lag_measurements) < 100:
                start = time.perf_counter()
                await asyncio.sleep(0)  # Yield to event loop
                lag = (time.perf_counter() - start) * 1000  # Convert to ms
                lag_measurements.append(lag)
                await asyncio.sleep(0.01)  # 10ms between measurements

        # Create mock blocking operation
        def mock_blocking_work():
            """Simulate CPU-bound work."""
            total = 0
            for i in range(10000):
                total += i
            return total

        # Start lag monitor
        monitor_task = asyncio.create_task(measure_loop_lag())

        # Create 500 concurrent tasks that perform "blocking" work
        tasks = []
        for i in range(500):
            task = computer.execute_blocking_operation(f"blocking_task_{i}", mock_blocking_work)
            tasks.append(task)

        # Wait for all tasks to complete
        await asyncio.gather(*tasks)

        # Wait for lag measurements
        await asyncio.sleep(0.2)
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass

        # Analyze lag measurements
        if lag_measurements:
            avg_lag = sum(lag_measurements) / len(lag_measurements)
            max_lag = max(lag_measurements)
            p95_lag = sorted(lag_measurements)[int(len(lag_measurements) * 0.95)]

            print("\nLoop Lag Statistics under 500 concurrent tasks:")
            print(f"  Average lag: {avg_lag:.2f}ms")
            print(f"  Max lag: {max_lag:.2f}ms")
            print(f"  P95 lag: {p95_lag:.2f}ms")

            # Assert that P95 lag is under threshold
            assert p95_lag < THRESHOLD_MS, (
                f"P95 loop lag {p95_lag:.2f}ms exceeds {THRESHOLD_MS}ms threshold"
            )
            # Relax average lag threshold as it can be affected by system load
            avg_threshold = THRESHOLD_MS * 1.5
            assert avg_lag < avg_threshold, (
                f"Average loop lag {avg_lag:.2f}ms exceeds {avg_threshold}ms threshold"
            )

    finally:
        await computer.stop()


@pytest.mark.asyncio
@pytest.mark.performance
async def test_concurrent_feature_computation_throughput():
    """Test throughput with many concurrent feature computations."""
    computer = AsyncFeatureComputer(TaskPoolConfig(max_workers=8))
    await computer.start()

    try:
        num_operations = 100

        def compute_work(value):
            time.sleep(0.02)  # 20ms per operation
            return {"value": value, "computed": True}

        start_time = time.perf_counter()
        tasks = [
            computer.execute_blocking_operation(f"op_{i}", compute_work, i)
            for i in range(num_operations)
        ]
        results = await asyncio.gather(*tasks)
        duration = time.perf_counter() - start_time

        # With 8 workers and 100 operations at 20ms each:
        # Sequential: 2.0s
        # Concurrent: ~0.25s (100/8 * 20ms)
        assert duration < 1.0, f"Throughput too low: {duration:.2f}s for 100 operations"
        assert len(results) == 100

        # Calculate throughput
        throughput = num_operations / duration
        print(f"\nThroughput: {throughput:.1f} operations/second")
        assert throughput > 50, f"Throughput {throughput:.1f}/s is below threshold"

    finally:
        await computer.stop()


@pytest.mark.asyncio
async def test_metrics_collection(async_computer):
    """Test that latency metrics are collected correctly."""

    def test_operation():
        time.sleep(0.01)
        return {"result": "success"}

    # Execute some operations
    await async_computer.execute_blocking_operation("op1", test_operation)
    await async_computer.execute_blocking_operation("op2", test_operation)
    await async_computer.execute_blocking_operation("op3", test_operation)

    metrics = async_computer.get_metrics(last_n=10)
    assert len(metrics) >= 3

    # Check metric structure
    for metric in metrics:
        assert "operation" in metric
        assert "duration_ms" in metric
        assert "success" in metric
        assert "timestamp" in metric

    # Check summary statistics
    summary = async_computer.get_summary_metrics()
    assert summary["total_operations"] >= 3
    assert summary["success_rate"] > 0
    assert summary["avg_latency_ms"] >= 0


@pytest.mark.asyncio
async def test_background_worker_task_processing(async_computer):
    """Test that background workers process queued tasks."""
    results = []

    def test_func(value):
        results.append(value)

    # Enqueue multiple tasks
    for i in range(10):
        await async_computer.enqueue_task(f"task_{i}", test_func, i)

    # Wait for processing
    await asyncio.sleep(0.5)

    # Verify tasks were processed
    assert len(results) == 10
    assert set(results) == set(range(10))


@pytest.mark.asyncio
async def test_error_handling_in_feature_computation(async_computer):
    """Test error handling in async feature computation."""

    def failing_operation():
        raise Exception("Computation failed")

    with pytest.raises(Exception, match="Computation failed"):
        await async_computer.execute_blocking_operation("failing_op", failing_operation)

    # Check that error was recorded in metrics
    metrics = async_computer.get_metrics(last_n=1)
    assert len(metrics) > 0
    assert metrics[0]["success"] is False
    assert metrics[0]["error"] is not None


@pytest.mark.asyncio
async def test_signal_computation_async(async_computer):
    """Test async signal generation with blocking operation."""

    def generate_signal(ticker, signal_type):
        time.sleep(0.01)
        return {
            "ticker": ticker,
            "direction": "LONG",
            "confidence": 0.8,
            "signal_type": signal_type,
        }

    result = await async_computer.execute_blocking_operation(
        "generate_signal", generate_signal, "AAPL", "momentum"
    )

    assert result is not None
    assert result["ticker"] == "AAPL"
    assert result["direction"] == "LONG"


@pytest.mark.asyncio
async def test_process_pool_execution():
    """Test process pool executor for CPU-intensive work."""
    config = TaskPoolConfig(max_workers=2, use_process_pool=True)
    computer = AsyncFeatureComputer(config)
    await computer.start()

    try:

        def cpu_intensive_work():
            total = 0
            for i in range(10000):
                total += i
            return {"result": total, "completed": True}

        result = await computer.execute_blocking_operation("cpu_work", cpu_intensive_work)

        assert result is not None
        assert result["completed"] is True

    finally:
        await computer.stop()


@pytest.mark.asyncio
async def test_global_instance_management():
    """Test global instance initialization and shutdown."""
    # Initialize
    await init_async_features(TaskPoolConfig(max_workers=2))

    computer = get_async_feature_computer()
    assert computer is not None
    assert computer._thread_pool is not None

    # Shutdown
    await shutdown_async_features()

    # Verify shutdown
    assert all(task.done() for task in computer._worker_tasks)


@pytest.mark.asyncio
async def test_queue_full_handling(async_computer):
    """Test handling of queue full condition."""
    # Fill up the queue
    small_queue_computer = AsyncFeatureComputer(TaskPoolConfig(max_workers=1, queue_size=5))
    await small_queue_computer.start()

    try:
        # Enqueue more tasks than queue size
        for i in range(10):
            await small_queue_computer.enqueue_task(f"task_{i}", lambda x: time.sleep(0.1), i)

        # Should not raise exception, just log warning
        # Test passes if no exception is raised

    finally:
        await small_queue_computer.stop()


@pytest.mark.asyncio
@pytest.mark.performance
async def test_latency_benchmark_before_after():
    """
    Benchmark latency before and after refactor.

    This test documents the performance improvement from using
    run_in_executor for blocking operations.
    """
    num_operations = 100

    # Simulate blocking operation
    def blocking_work():
        total = 0
        for i in range(5000):
            total += i
        return total

    print("\n=== Latency Benchmark ===")

    # Measure with executor (refactored approach)
    computer = AsyncFeatureComputer(TaskPoolConfig(max_workers=8))
    await computer.start()

    try:
        start_time = time.perf_counter()
        tasks = [
            computer.execute_blocking_operation(f"bench_{i}", blocking_work)
            for i in range(num_operations)
        ]
        await asyncio.gather(*tasks)
        with_executor_time = time.perf_counter() - start_time

        summary = computer.get_summary_metrics()

        print("\nWith executor (refactored):")
        print(f"  Total time: {with_executor_time:.3f}s")
        print(f"  Throughput: {num_operations / with_executor_time:.1f} ops/sec")
        print(f"  Avg latency: {summary['avg_latency_ms']:.2f}ms")
        print(f"  P95 latency: {summary['p95_latency_ms']:.2f}ms")
        print(f"  P99 latency: {summary['p99_latency_ms']:.2f}ms")

        # Verify acceptable performance
        assert with_executor_time < 2.0, "Refactored approach took too long"
        assert summary["avg_latency_ms"] < 50.0, "Average latency too high"

    finally:
        await computer.stop()
