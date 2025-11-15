"""
Event Store for ZiggyAI Memory & Knowledge System

Provides append-only storage for trading decisions and outcomes.
Supports both JSONL and SQLite backends with immutable audit fields.

Brain-first: All decision data must flow through this store for learning & recall.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
import uuid
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Any


# Configuration from environment
MODE = os.getenv("MEMORY_MODE", "JSONL")
SQLITE_PATH = os.getenv("SQLITE_PATH", "data/memory/events.db")


def _get_jsonl_path() -> str:
    """
    Get the JSONL file path from environment, checking multiple variables.

    Priority order:
    1. EVENT_STORE_PATH (for test isolation)
    2. MEMORY_PATH (legacy compatibility)
    3. Default path

    Returns:
        Path to the JSONL events file
    """
    return (
        os.getenv("EVENT_STORE_PATH")
        or os.getenv("MEMORY_PATH")
        or "data/memory/events.jsonl"
    )


# Thread-local storage for SQLite connections
_local = threading.local()

# Basic metrics for observability
_metrics: dict[str, Any] = {
    "backend": MODE,
    "writes_total": 0,
    "errors_total": 0,
    "last_write_ms": 0.0,
    "batch_writes_total": 0,
    "batch_events_total": 0,
    "last_batch_size": 0,
    "last_batch_ms": 0.0,
    "sqlite_wal": None,
    "sqlite_sync": None,
    "sqlite_path": SQLITE_PATH,
}


def _now_iso() -> str:
    """Generate current timestamp in ISO format with microseconds precision."""
    return datetime.utcnow().isoformat(timespec="microseconds") + "Z"


def _get_sqlite_conn() -> sqlite3.Connection:
    """Get thread-local SQLite connection, creating if needed."""
    if not hasattr(_local, "conn"):
        # Ensure directory exists
        db_path = Path(SQLITE_PATH)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        _local.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row

        # Pragmas to improve throughput and durability trade-offs
        try:
            _local.conn.execute("PRAGMA journal_mode=WAL;")
            _local.conn.execute("PRAGMA synchronous=NORMAL;")
            _local.conn.execute("PRAGMA temp_store=MEMORY;")
            _local.conn.execute("PRAGMA busy_timeout=5000;")
            # Capture effective settings
            wal_mode = _local.conn.execute("PRAGMA journal_mode;").fetchone()[0]
            sync_mode = _local.conn.execute("PRAGMA synchronous;").fetchone()[0]
            _metrics["sqlite_wal"] = wal_mode
            _metrics["sqlite_sync"] = sync_mode
        except Exception:
            pass

        # Create table if not exists
        _local.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                ts TEXT NOT NULL,
                event_data TEXT NOT NULL,
                event_type TEXT,
                correlation_id TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        _local.conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts)
        """
        )
        _local.conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at)
        """
        )
        _local.conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)
        """
        )
        _local.conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_events_correlation ON events(correlation_id)
        """
        )
        _local.conn.commit()

    return _local.conn


def append_event(payload: dict[str, Any]) -> str:
    """
    Append a new event to the store.

    Args:
        payload: Event data including durable fields

    Returns:
        Event ID (UUID if not provided)
    """
    # Ensure event has required fields
    event_id = payload.get("id") or str(uuid.uuid4())
    timestamp = payload.get("ts", _now_iso())

    # Build complete event with immutable audit fields
    event = {"id": event_id, "ts": timestamp, **payload}

    if MODE == "JSONL":
        # Ensure directory exists
        path = Path(_get_jsonl_path())
        path.parent.mkdir(parents=True, exist_ok=True)

        # Append to JSONL file
        t0 = time.perf_counter()
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
                f.flush()  # Ensure data is written
                os.fsync(f.fileno())  # Force sync to disk
            _metrics["writes_total"] = int(_metrics.get("writes_total", 0)) + 1
        except Exception:
            _metrics["errors_total"] = int(_metrics.get("errors_total", 0)) + 1
            raise
        finally:
            _metrics["last_write_ms"] = (time.perf_counter() - t0) * 1000.0

    elif MODE == "SQLITE":
        conn = _get_sqlite_conn()
        t0 = time.perf_counter()
        try:
            # Extract event_type and correlation_id for indexing
            event_type = event.get("event_type")
            correlation_id = event.get("correlation_id")

            conn.execute(
                "INSERT INTO events (id, ts, event_data, event_type, correlation_id) VALUES (?, ?, ?, ?, ?)",
                (
                    event_id,
                    timestamp,
                    json.dumps(event, ensure_ascii=False),
                    event_type,
                    correlation_id,
                ),
            )
            conn.commit()
            _metrics["writes_total"] = int(_metrics.get("writes_total", 0)) + 1
        except sqlite3.Error:
            _metrics["errors_total"] = int(_metrics.get("errors_total", 0)) + 1
            raise
        finally:
            latency_ms = (time.perf_counter() - t0) * 1000.0
            _metrics["last_write_ms"] = latency_ms

            # Emit telemetry for single write operations (periodically to avoid overhead)
            try:
                if (
                    int(_metrics.get("writes_total", 0)) % 10 == 0
                ):  # Sample every 10th write
                    from app.services.telemetry import emit_custom_metric

                    emit_custom_metric(
                        "event_store_write_latency_ms",
                        latency_ms,
                        tags={"backend": MODE},
                        metadata={
                            "component": "event_store",
                            "operation": "append_event",
                        },
                    )
            except ImportError:
                pass

    else:
        raise ValueError(f"Unsupported MEMORY_MODE: {MODE}")

    return event_id


def write_batch(events: list[dict[str, Any]]) -> list[str]:
    """
    Write a batch of events in a single transaction for improved throughput.

    This method is optimized for bulk inserts and provides significant performance
    improvements over individual append_event calls by:
    - Using a single transaction for all events
    - Reducing fsync overhead (WAL mode allows concurrent reads during batch)
    - Minimizing connection overhead

    Args:
        events: List of event dictionaries to append

    Returns:
        List of event IDs assigned to the events

    Raises:
        ValueError: If MODE is unsupported
        sqlite3.Error: For SQLite-specific errors
        Exception: For JSONL write errors
    """
    if not events:
        return []

    event_ids = []
    batch_size = len(events)
    t0 = time.perf_counter()

    try:
        if MODE == "JSONL":
            # Ensure directory exists
            path = Path(_get_jsonl_path())
            path.parent.mkdir(parents=True, exist_ok=True)

            # Prepare all events with IDs
            prepared_events = []
            for payload in events:
                event_id = payload.get("id") or str(uuid.uuid4())
                timestamp = payload.get("ts", _now_iso())
                event = {"id": event_id, "ts": timestamp, **payload}
                prepared_events.append((event_id, event))
                event_ids.append(event_id)

            # Batch write to JSONL
            with open(path, "a", encoding="utf-8") as f:
                for _, event in prepared_events:
                    f.write(json.dumps(event, ensure_ascii=False) + "\n")
                f.flush()
                os.fsync(f.fileno())

            _metrics["writes_total"] = int(_metrics.get("writes_total", 0)) + batch_size
            _metrics["batch_writes_total"] = (
                int(_metrics.get("batch_writes_total", 0)) + 1
            )
            _metrics["batch_events_total"] = (
                int(_metrics.get("batch_events_total", 0)) + batch_size
            )

        elif MODE == "SQLITE":
            conn = _get_sqlite_conn()

            # Prepare all events with IDs
            rows = []
            for payload in events:
                event_id = payload.get("id") or str(uuid.uuid4())
                timestamp = payload.get("ts", _now_iso())
                event = {"id": event_id, "ts": timestamp, **payload}

                # Extract indexed fields
                event_type = event.get("event_type")
                correlation_id = event.get("correlation_id")

                rows.append(
                    (
                        event_id,
                        timestamp,
                        json.dumps(event, ensure_ascii=False),
                        event_type,
                        correlation_id,
                    )
                )
                event_ids.append(event_id)

            # Single transaction for all inserts
            conn.executemany(
                "INSERT INTO events (id, ts, event_data, event_type, correlation_id) VALUES (?, ?, ?, ?, ?)",
                rows,
            )
            conn.commit()

            _metrics["writes_total"] = int(_metrics.get("writes_total", 0)) + batch_size
            _metrics["batch_writes_total"] = (
                int(_metrics.get("batch_writes_total", 0)) + 1
            )
            _metrics["batch_events_total"] = (
                int(_metrics.get("batch_events_total", 0)) + batch_size
            )

        else:
            raise ValueError(f"Unsupported MEMORY_MODE: {MODE}")

    except Exception:
        _metrics["errors_total"] = int(_metrics.get("errors_total", 0)) + 1
        raise
    finally:
        batch_latency_ms = (time.perf_counter() - t0) * 1000.0
        _metrics["last_batch_ms"] = batch_latency_ms
        _metrics["last_batch_size"] = batch_size

        # Emit telemetry metrics for batch operation
        try:
            from app.services.telemetry import emit_custom_metric

            emit_custom_metric(
                "event_store_batch_size",
                float(batch_size),
                tags={"backend": MODE},
                metadata={"component": "event_store", "operation": "write_batch"},
            )
            emit_custom_metric(
                "event_store_batch_latency_ms",
                batch_latency_ms,
                tags={"backend": MODE, "batch_size": str(batch_size)},
                metadata={"component": "event_store", "operation": "write_batch"},
            )
            # Calculate and emit throughput (events per second)
            throughput = batch_size / max(batch_latency_ms / 1000.0, 0.001)
            emit_custom_metric(
                "event_store_batch_throughput",
                throughput,
                tags={"backend": MODE},
                metadata={"component": "event_store", "operation": "write_batch"},
            )
        except ImportError:
            # Telemetry service not available, skip metrics emission
            pass

    return event_ids


def update_outcome(event_id: str, outcome: dict[str, Any]) -> None:
    """
    Update the outcome of an existing event.

    For JSONL: Appends a shadow record with update information
    For SQLite: Could be implemented as separate outcomes table

    Args:
        event_id: ID of the event to update
        outcome: Outcome data (horizon, label, pnl, mfe, mae, etc.)
    """
    update_payload = {
        "id": f"{event_id}_outcome_update",
        "_update_type": "outcome",
        "_target_event_id": event_id,
        "outcome": outcome,
        "updated_at": _now_iso(),
    }

    # Use the same append mechanism for immutability
    append_event(update_payload)


def iter_events(
    filter_dict: dict[str, Any] | None = None, include_updates: bool = False
) -> Iterator[dict[str, Any]]:
    """
    Iterate over all events in the store.

    Args:
        filter_dict: Optional filters (not implemented yet)
        include_updates: Whether to include outcome update records

    Yields:
        Event dictionaries
    """
    if MODE == "JSONL":
        path = Path(_get_jsonl_path())
        if not path.exists():
            return

        # Keep track of events and their updates
        events_map = {}
        updates_map = {}

        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    event = json.loads(line)

                    # Handle outcome updates
                    if event.get("_update_type") == "outcome":
                        target_id = event.get("_target_event_id")
                        if target_id:
                            updates_map[target_id] = event["outcome"]
                        if include_updates:
                            yield event
                    else:
                        events_map[event["id"]] = event

                except json.JSONDecodeError:
                    continue

        # Yield events with merged outcomes
        for event_id, event in events_map.items():
            if event_id in updates_map:
                event = {**event, "outcome": updates_map[event_id]}
            yield event

    elif MODE == "SQLITE":
        conn = _get_sqlite_conn()
        cursor = conn.execute("SELECT event_data FROM events ORDER BY created_at")

        events_map = {}
        updates_map = {}

        for row in cursor:
            try:
                event = json.loads(row[0])

                # Handle outcome updates
                if event.get("_update_type") == "outcome":
                    target_id = event.get("_target_event_id")
                    if target_id:
                        updates_map[target_id] = event["outcome"]
                    if include_updates:
                        yield event
                else:
                    events_map[event["id"]] = event

            except json.JSONDecodeError:
                continue

        # Yield events with merged outcomes
        for event_id, event in events_map.items():
            if event_id in updates_map:
                event = {**event, "outcome": updates_map[event_id]}
            yield event

    else:
        raise ValueError(f"Unsupported MEMORY_MODE: {MODE}")


def get_event_by_id(event_id: str) -> dict[str, Any] | None:
    """
    Get a specific event by its ID.

    Args:
        event_id: The event ID to look up

    Returns:
        Event dictionary or None if not found
    """
    for event in iter_events():
        if event.get("id") == event_id:
            return event
    return None


def count_events() -> int:
    """
    Count total number of events (excluding updates).

    Returns:
        Total event count
    """
    count = 0
    for _ in iter_events():
        count += 1
    return count


def get_recent_events(limit: int = 100) -> list[dict[str, Any]]:
    """
    Get the most recent events.

    Args:
        limit: Maximum number of events to return

    Returns:
        List of recent events, newest first
    """
    events = list(iter_events())
    # Sort by timestamp, newest first
    events.sort(key=lambda x: x.get("ts", ""), reverse=True)
    return events[:limit]


def get_event_store_metrics() -> dict[str, Any]:
    """Return basic event store metrics and (if SQLite) effective PRAGMAs."""
    return dict(_metrics)


# Validation helpers for durable fields
REQUIRED_DURABLE_FIELDS = ["ts", "ticker"]
OPTIONAL_DURABLE_FIELDS = [
    "features_v",
    "regime",
    "p_up",
    "decision",
    "size",
    "explain",
    "neighbors",
    "outcome",
]


def validate_event_schema(event: dict[str, Any]) -> bool:
    """
    Validate that an event contains required durable fields.

    Args:
        event: Event dictionary to validate

    Returns:
        True if valid, False otherwise
    """
    return all(field in event for field in REQUIRED_DURABLE_FIELDS)


def build_durable_event(
    ticker: str,
    features_v: str = "1.0.0",
    regime: str | None = None,
    p_up: float | None = None,
    decision: str | None = None,
    size: float | None = None,
    explain: dict[str, Any] | None = None,
    neighbors: list[dict[str, Any]] | None = None,
    **extra_fields,
) -> dict[str, Any]:
    """
    Build an event with proper durable field structure and brain-first enhancements.

    Args:
        ticker: Stock ticker symbol
        features_v: Feature version
        regime: Market regime
        p_up: Probability of upward movement
        decision: Trading decision (BUY/SELL/HOLD)
        size: Position size
        explain: Explanation data (SHAP values, etc.)
        neighbors: Similar past events for RAG
        **extra_fields: Additional fields to include

    Returns:
        Properly structured event dictionary with brain-first fields
    """
    event = {
        "ts": _now_iso(),
        "ticker": ticker,
        "features_v": features_v,
        **extra_fields,
    }

    # Add optional fields if provided
    if regime is not None:
        event["regime"] = regime
    if p_up is not None:
        event["p_up"] = p_up
    if decision is not None:
        event["decision"] = decision
    if size is not None:
        event["size"] = size
    if explain is not None:
        event["explain"] = explain
    if neighbors is not None:
        event["neighbors"] = neighbors

    # Add brain-first enhancements
    event.update(
        {
            "trace_id": extra_fields.get("trace_id"),
            "explain_snippet": _extract_explain_snippet(event),
            "learning_metadata": _build_learning_metadata(event),
            "decision_context": _extract_decision_context(event),
        }
    )

    return event


def _extract_explain_snippet(payload: dict[str, Any]) -> dict[str, Any] | None:
    """Extract key explanation data for quick retrieval."""
    explain_data = payload.get("explain", {})
    if not explain_data:
        return None

    return {
        "top_features": explain_data.get("shap_top", [])[:3],  # Top 3 features
        "regime": payload.get("regime"),
        "confidence": payload.get("confidence"),
        "p_up": payload.get("p_up"),
        "has_neighbors": bool(payload.get("neighbors")),
    }


def _build_learning_metadata(payload: dict[str, Any]) -> dict[str, Any]:
    """Build metadata for learning system integration."""
    return {
        "can_learn": bool(payload.get("p_up") and payload.get("ticker")),
        "has_features": bool(payload.get("explain", {}).get("shap_top")),
        "has_outcome": bool(payload.get("outcome")),
        "feature_count": len(payload.get("explain", {}).get("shap_top", [])),
        "learning_priority": _calculate_learning_priority(payload),
    }


def _extract_decision_context(payload: dict[str, Any]) -> dict[str, Any]:
    """Extract context for decision similarity search."""
    return {
        "ticker": payload.get("ticker"),
        "interval": payload.get("interval", "1D"),
        "regime": payload.get("regime"),
        "decision_type": payload.get("decision", payload.get("event_type")),
        "confidence_bucket": _bucket_confidence(payload.get("confidence")),
        "p_up_bucket": _bucket_probability(payload.get("p_up")),
    }


def _calculate_learning_priority(payload: dict[str, Any]) -> float:
    """Calculate learning priority score for this event."""
    priority = 0.0

    # High confidence decisions are more valuable for learning
    confidence = payload.get("confidence", 0.5)
    if confidence > 0.8:
        priority += 0.3
    elif confidence > 0.6:
        priority += 0.2

    # Events with outcomes are very valuable
    if payload.get("outcome"):
        priority += 0.4

    # Events with rich features are valuable
    feature_count = len(payload.get("explain", {}).get("shap_top", []))
    if feature_count >= 5:
        priority += 0.2
    elif feature_count >= 3:
        priority += 0.1

    # Recent events are more valuable
    if not payload.get("ts"):
        priority += 0.1  # Current timestamp

    return min(1.0, priority)


def _bucket_confidence(confidence: float | None) -> str | None:
    """Bucket confidence for similarity grouping."""
    if confidence is None:
        return None
    if confidence >= 0.8:
        return "high"
    elif confidence >= 0.6:
        return "medium"
    else:
        return "low"


def _bucket_probability(p_up: float | None) -> str | None:
    """Bucket probability for similarity grouping."""
    if p_up is None:
        return None
    if p_up >= 0.7:
        return "bullish"
    elif p_up >= 0.6:
        return "lean_bullish"
    elif p_up >= 0.4:
        return "neutral"
    elif p_up >= 0.3:
        return "lean_bearish"
    else:
        return "bearish"
