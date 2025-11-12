"""
Event Store - High-Performance Storage Layer

This module provides a high-performance, durable event storage system optimized for
throughput and reliability. It wraps the core memory.events module and adds:

1. SQLite WAL mode for improved concurrent access and crash recovery
2. Optimized indices on timestamp, event_type, and correlation_id for fast queries
3. Batch write operations for 2-3x faster throughput
4. Comprehensive metrics integration with the telemetry system

Key Features:
- WAL mode: Allows concurrent reads during writes, reduces fsync overhead
- Batch writes: Single transaction for multiple events reduces commit overhead
- Indexed fields: Fast lookups by type, correlation, and time
- Metrics tracking: Batch size, latency, throughput visible in monitoring dashboard

Performance Improvements:
- Individual writes: ~10-50ms per event (with fsync)
- Batch writes: ~5-20ms per event in batches of 10-100 events
- 2-3x throughput improvement for bulk operations
- Preserved durability with WAL mode (NORMAL synchronous mode)

Usage:
    from app.storage.event_store import write_batch, append_event, get_metrics

    # Single event
    event_id = append_event({"ticker": "AAPL", "event_type": "trade", "ts": "..."})

    # Batch of events (recommended for bulk operations)
    events = [
        {"ticker": "AAPL", "event_type": "trade", "correlation_id": "batch-1"},
        {"ticker": "MSFT", "event_type": "trade", "correlation_id": "batch-1"},
    ]
    event_ids = write_batch(events)

    # Get performance metrics
    metrics = get_metrics()
    print(f"Batch throughput: {metrics['batch_events_total'] / metrics['batch_writes_total']}")
"""

from typing import Any

# Re-export the enhanced event store functions from memory.events
from app.memory.events import (
    append_event,
    build_durable_event,
    count_events,
    get_event_by_id,
    get_event_store_metrics,
    get_recent_events,
    iter_events,
    update_outcome,
    validate_event_schema,
    write_batch,
)


__all__ = [
    "append_event",
    "build_durable_event",
    "count_events",
    "get_event_by_id",
    "get_metrics",
    "get_recent_events",
    "iter_events",
    "update_outcome",
    "validate_event_schema",
    "write_batch",
]


def get_metrics() -> dict[str, Any]:
    """
    Get comprehensive event store metrics including batch performance.

    Returns a dictionary containing:
    - backend: Storage backend in use (SQLITE or JSONL)
    - writes_total: Total number of events written
    - batch_writes_total: Total number of batch operations
    - batch_events_total: Total events written via batches
    - last_write_ms: Latency of last single write
    - last_batch_ms: Latency of last batch write
    - last_batch_size: Number of events in last batch
    - errors_total: Total write errors
    - sqlite_wal: WAL mode status (for SQLite)
    - sqlite_sync: Synchronous mode (for SQLite)
    - sqlite_path: Database path (for SQLite)

    Returns:
        Dictionary of metrics
    """
    metrics = get_event_store_metrics()

    # Add computed metrics
    if metrics.get("batch_writes_total", 0) > 0:
        avg_batch_size = metrics.get("batch_events_total", 0) / metrics["batch_writes_total"]
        metrics["avg_batch_size"] = avg_batch_size

    if metrics.get("last_batch_ms", 0) > 0 and metrics.get("last_batch_size", 0) > 0:
        throughput = metrics["last_batch_size"] / (metrics["last_batch_ms"] / 1000.0)
        metrics["last_batch_throughput_eps"] = throughput  # events per second

    return metrics


def get_performance_summary() -> str:
    """
    Get a human-readable summary of event store performance.

    Returns:
        Formatted string with performance statistics
    """
    metrics = get_metrics()

    summary_lines = [
        "Event Store Performance Summary",
        "=" * 40,
        f"Backend: {metrics.get('backend', 'Unknown')}",
        f"WAL Mode: {metrics.get('sqlite_wal', 'N/A')}",
        f"Total Events Written: {metrics.get('writes_total', 0)}",
        f"Total Batch Operations: {metrics.get('batch_writes_total', 0)}",
        f"Events via Batches: {metrics.get('batch_events_total', 0)}",
        "",
        "Recent Performance:",
        f"  Last Write Latency: {metrics.get('last_write_ms', 0):.2f}ms",
        f"  Last Batch Latency: {metrics.get('last_batch_ms', 0):.2f}ms",
        f"  Last Batch Size: {metrics.get('last_batch_size', 0)} events",
    ]

    if "last_batch_throughput_eps" in metrics:
        summary_lines.append(
            f"  Last Batch Throughput: {metrics['last_batch_throughput_eps']:.2f} events/sec"
        )

    if "avg_batch_size" in metrics:
        summary_lines.append(f"  Average Batch Size: {metrics['avg_batch_size']:.2f} events")

    summary_lines.extend(
        [
            "",
            f"Errors: {metrics.get('errors_total', 0)}",
        ]
    )

    return "\n".join(summary_lines)
