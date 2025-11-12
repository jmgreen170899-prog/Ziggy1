"""
Regression tests for event store performance and durability improvements.

Tests validate:
1. WAL mode is properly enabled for SQLite backend
2. Indices exist for event_type, correlation_id, and timestamp
3. write_batch() provides improved throughput over individual writes
4. Batch operations maintain durability (proper fsync/commit)
5. Metrics are properly tracked and exposed
"""

import tempfile
import time
from pathlib import Path

import pytest

from app.memory import events
from app.storage import event_store


@pytest.fixture
def temp_sqlite_db():
    """Create a temporary SQLite database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_events.db"
        yield db_path


@pytest.fixture
def sqlite_event_store(temp_sqlite_db, monkeypatch):
    """Configure event store to use temporary SQLite database."""
    monkeypatch.setenv("MEMORY_MODE", "SQLITE")
    monkeypatch.setenv("SQLITE_PATH", str(temp_sqlite_db))

    # Reset the thread-local connection to force recreation
    if hasattr(events._local, "conn"):
        events._local.conn.close()
        delattr(events._local, "conn")

    # Reset metrics
    events._metrics.update(
        {
            "writes_total": 0,
            "errors_total": 0,
            "batch_writes_total": 0,
            "batch_events_total": 0,
        }
    )

    yield temp_sqlite_db

    # Cleanup
    if hasattr(events._local, "conn"):
        events._local.conn.close()
        delattr(events._local, "conn")


class TestWALMode:
    """Test WAL mode configuration and durability."""

    def test_wal_mode_enabled(self, sqlite_event_store):
        """Verify that WAL mode is enabled on database initialization."""
        # Trigger connection initialization
        event_id = events.append_event({"ticker": "TEST", "event_type": "test"})
        assert event_id

        # Check metrics confirm WAL mode
        metrics = events.get_event_store_metrics()
        assert metrics["sqlite_wal"] == "wal", f"Expected WAL mode, got {metrics['sqlite_wal']}"
        assert metrics["sqlite_sync"] in ["1", "NORMAL"], "Expected NORMAL synchronous mode"

    def test_wal_files_created(self, sqlite_event_store):
        """Verify that WAL files are created when using WAL mode."""
        # Write an event to initialize database
        events.append_event({"ticker": "TEST", "event_type": "test"})

        # In WAL mode, -wal file should exist after writes
        # Force a checkpoint to ensure WAL is used
        conn = events._get_sqlite_conn()
        conn.execute("PRAGMA wal_checkpoint(PASSIVE)")

        # Verify WAL mode is active
        result = conn.execute("PRAGMA journal_mode").fetchone()
        assert result[0].lower() == "wal"

    def test_durability_with_wal(self, sqlite_event_store):
        """Test that writes are durable even with WAL mode."""
        test_events = [
            {"ticker": "AAPL", "event_type": "trade", "price": 150.0},
            {"ticker": "MSFT", "event_type": "trade", "price": 300.0},
        ]

        event_ids = events.write_batch(test_events)
        assert len(event_ids) == 2

        # Close connection to simulate crash
        if hasattr(events._local, "conn"):
            events._local.conn.close()
            delattr(events._local, "conn")

        # Reopen and verify events are still there
        retrieved_events = list(events.iter_events())
        retrieved_tickers = [e["ticker"] for e in retrieved_events]
        assert "AAPL" in retrieved_tickers
        assert "MSFT" in retrieved_tickers


class TestIndices:
    """Test that required indices are created."""

    def test_timestamp_index_exists(self, sqlite_event_store):
        """Verify timestamp index exists."""
        events.append_event({"ticker": "TEST", "event_type": "test"})

        conn = events._get_sqlite_conn()
        indices = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='events'"
        ).fetchall()

        index_names = [idx[0] for idx in indices]
        assert "idx_events_ts" in index_names, "Timestamp index not found"

    def test_event_type_index_exists(self, sqlite_event_store):
        """Verify event_type index exists."""
        events.append_event({"ticker": "TEST", "event_type": "test"})

        conn = events._get_sqlite_conn()
        indices = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='events'"
        ).fetchall()

        index_names = [idx[0] for idx in indices]
        assert "idx_events_type" in index_names, "Event type index not found"

    def test_correlation_id_index_exists(self, sqlite_event_store):
        """Verify correlation_id index exists."""
        events.append_event({"ticker": "TEST", "event_type": "test"})

        conn = events._get_sqlite_conn()
        indices = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='events'"
        ).fetchall()

        index_names = [idx[0] for idx in indices]
        assert "idx_events_correlation" in index_names, "Correlation ID index not found"

    def test_indexed_columns_in_schema(self, sqlite_event_store):
        """Verify that event_type and correlation_id columns exist in schema."""
        events.append_event({"ticker": "TEST", "event_type": "test"})

        conn = events._get_sqlite_conn()
        schema = conn.execute("PRAGMA table_info(events)").fetchall()
        column_names = [col[1] for col in schema]

        assert "event_type" in column_names, "event_type column not in schema"
        assert "correlation_id" in column_names, "correlation_id column not in schema"

    def test_indexed_fields_stored(self, sqlite_event_store):
        """Verify that indexed fields are properly stored and retrievable."""
        test_event = {
            "ticker": "AAPL",
            "event_type": "trade_execution",
            "correlation_id": "batch-123",
        }

        event_id = events.append_event(test_event)

        # Query directly to verify indexed fields are stored
        conn = events._get_sqlite_conn()
        row = conn.execute(
            "SELECT event_type, correlation_id FROM events WHERE id = ?", (event_id,)
        ).fetchone()

        assert row[0] == "trade_execution", "event_type not stored correctly"
        assert row[1] == "batch-123", "correlation_id not stored correctly"


class TestBatchPerformance:
    """Test batch write performance improvements."""

    def test_write_batch_success(self, sqlite_event_store):
        """Test that write_batch successfully writes multiple events."""
        test_events = [
            {"ticker": "AAPL", "event_type": "trade"},
            {"ticker": "MSFT", "event_type": "trade"},
            {"ticker": "GOOGL", "event_type": "trade"},
        ]

        event_ids = events.write_batch(test_events)

        assert len(event_ids) == 3
        assert all(isinstance(eid, str) for eid in event_ids)

        # Verify events are retrievable
        retrieved = list(events.iter_events())
        tickers = {e["ticker"] for e in retrieved}
        assert tickers >= {"AAPL", "MSFT", "GOOGL"}

    def test_write_batch_empty(self, sqlite_event_store):
        """Test that write_batch handles empty list."""
        event_ids = events.write_batch([])
        assert event_ids == []

    @pytest.mark.performance
    def test_batch_faster_than_individual(self, sqlite_event_store):
        """Test that batch writes are faster than individual writes."""
        num_events = 50

        # Time individual writes
        individual_events = [
            {"ticker": f"TICK{i}", "event_type": "individual"} for i in range(num_events)
        ]

        t0 = time.perf_counter()
        for event in individual_events:
            events.append_event(event)
        individual_time = time.perf_counter() - t0

        # Time batch write
        batch_events = [{"ticker": f"BATCH{i}", "event_type": "batch"} for i in range(num_events)]

        t0 = time.perf_counter()
        events.write_batch(batch_events)
        batch_time = time.perf_counter() - t0

        # Batch should be significantly faster (at least 1.5x, often 2-3x)
        speedup = individual_time / batch_time
        print(f"\nBatch speedup: {speedup:.2f}x")
        print(f"Individual: {individual_time * 1000:.2f}ms, Batch: {batch_time * 1000:.2f}ms")

        # Assert at least 1.3x speedup (conservative to account for variance)
        assert speedup > 1.3, f"Batch write not faster enough: {speedup:.2f}x speedup"

    @pytest.mark.performance
    def test_batch_latency_reasonable(self, sqlite_event_store):
        """Test that batch write latency is reasonable for moderate batch sizes."""
        batch_sizes = [10, 50, 100]

        for batch_size in batch_sizes:
            test_events = [
                {"ticker": f"TEST{i}", "event_type": "latency_test"} for i in range(batch_size)
            ]

            t0 = time.perf_counter()
            events.write_batch(test_events)
            latency_ms = (time.perf_counter() - t0) * 1000

            # Latency should be reasonable (< 1000ms for 100 events)
            per_event_ms = latency_ms / batch_size
            print(
                f"\nBatch size {batch_size}: {latency_ms:.2f}ms total, {per_event_ms:.2f}ms per event"
            )

            assert latency_ms < 1000, (
                f"Batch write too slow: {latency_ms:.2f}ms for {batch_size} events"
            )


class TestMetrics:
    """Test metrics tracking and exposure."""

    def test_metrics_track_batch_operations(self, sqlite_event_store):
        """Test that metrics properly track batch operations."""
        initial_metrics = events.get_event_store_metrics()
        initial_batches = initial_metrics.get("batch_writes_total", 0)

        # Write a batch
        test_events = [
            {"ticker": "A", "event_type": "test"},
            {"ticker": "B", "event_type": "test"},
            {"ticker": "C", "event_type": "test"},
        ]
        events.write_batch(test_events)

        # Check metrics updated
        metrics = events.get_event_store_metrics()
        assert metrics["batch_writes_total"] == initial_batches + 1
        assert metrics["batch_events_total"] >= 3
        assert metrics["last_batch_size"] == 3
        assert metrics["last_batch_ms"] > 0

    def test_metrics_track_individual_writes(self, sqlite_event_store):
        """Test that metrics track individual write operations."""
        initial_metrics = events.get_event_store_metrics()
        initial_writes = initial_metrics.get("writes_total", 0)

        events.append_event({"ticker": "TEST", "event_type": "metric_test"})

        metrics = events.get_event_store_metrics()
        assert metrics["writes_total"] == initial_writes + 1
        assert metrics["last_write_ms"] > 0

    def test_storage_wrapper_metrics(self, sqlite_event_store):
        """Test that storage wrapper exposes enhanced metrics."""
        # Write some data
        events.write_batch(
            [
                {"ticker": "X", "event_type": "test"},
                {"ticker": "Y", "event_type": "test"},
            ]
        )

        # Get metrics through wrapper
        metrics = event_store.get_metrics()

        # Verify computed metrics are included
        assert "backend" in metrics
        assert "writes_total" in metrics
        assert "batch_writes_total" in metrics

    def test_performance_summary(self, sqlite_event_store):
        """Test that performance summary is generated."""
        # Write some test data
        events.write_batch([{"ticker": "TEST", "event_type": "summary"}] * 10)

        summary = event_store.get_performance_summary()

        assert "Event Store Performance Summary" in summary
        assert "WAL Mode:" in summary
        assert "Total Events Written:" in summary
        assert "Batch" in summary


class TestTransactionalIntegrity:
    """Test that batch operations maintain transactional integrity."""

    def test_batch_atomic_success(self, sqlite_event_store):
        """Test that successful batch writes are atomic."""
        test_events = [{"ticker": f"ATOM{i}", "event_type": "atomic"} for i in range(5)]

        event_ids = events.write_batch(test_events)
        assert len(event_ids) == 5

        # All events should be in the database
        retrieved = list(events.iter_events())
        atom_events = [e for e in retrieved if e.get("ticker", "").startswith("ATOM")]
        assert len(atom_events) == 5

    def test_metrics_accuracy(self, sqlite_event_store):
        """Test that metrics accurately reflect operations."""
        # Clear metrics
        events._metrics["writes_total"] = 0
        events._metrics["batch_writes_total"] = 0
        events._metrics["batch_events_total"] = 0

        # Write 3 batches of different sizes
        events.write_batch([{"ticker": "A", "event_type": "t"}])
        events.write_batch([{"ticker": "B", "event_type": "t"}] * 5)
        events.write_batch([{"ticker": "C", "event_type": "t"}] * 10)

        metrics = events.get_event_store_metrics()
        assert metrics["batch_writes_total"] == 3
        assert metrics["batch_events_total"] == 16  # 1 + 5 + 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
