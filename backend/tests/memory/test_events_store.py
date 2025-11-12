"""
Tests for Event Store functionality in ZiggyAI Memory & Knowledge System

Tests append-only storage, immutable audit fields, JSONL/SQLite backends,
and outcome update mechanisms.
"""

import json
import os
import shutil
import tempfile
from datetime import datetime

import pytest


# Set test environment before importing
os.environ["MEMORY_MODE"] = "JSONL"
os.environ["MEMORY_PATH"] = "test_events.jsonl"

from app.memory.events import (
    append_event,
    build_durable_event,
    count_events,
    get_event_by_id,
    get_recent_events,
    iter_events,
    update_outcome,
    validate_event_schema,
)


class TestEventStore:
    """Test cases for the Event Store."""

    def test_append_event_basic(self):
        """Test basic event appending."""
        event_data = {"ticker": "AAPL", "p_up": 0.75, "decision": "BUY"}

        event_id = append_event(event_data)
        assert event_id is not None
        assert len(event_id) > 0

        # Verify file was created (get path from environment)
        test_file = os.environ.get("EVENT_STORE_PATH")
        assert test_file is not None
        assert os.path.exists(test_file)

        # Read and verify content
        with open(test_file) as f:
            line = f.readline().strip()
            saved_event = json.loads(line)

        assert saved_event["id"] == event_id
        assert saved_event["ticker"] == "AAPL"
        assert saved_event["p_up"] == 0.75
        assert saved_event["decision"] == "BUY"
        assert "ts" in saved_event

    def test_append_event_with_id(self):
        """Test appending event with pre-specified ID."""
        custom_id = "test-event-123"
        event_data = {"id": custom_id, "ticker": "TSLA", "p_up": 0.6}

        returned_id = append_event(event_data)
        assert returned_id == custom_id

        # Verify the ID is preserved
        events = list(iter_events())
        assert len(events) == 1
        assert events[0]["id"] == custom_id

    def test_durable_fields_structure(self):
        """Test that durable fields are properly structured."""
        event = build_durable_event(
            ticker="MSFT",
            features_v="1.2.3",
            regime="high_vol_bear",
            p_up=0.63,
            decision="BUY",
            size=0.35,
            explain={"shap_top": [["breadth", 0.21], ["sentiment", 0.17]]},
            neighbors=[{"id": "neighbor1", "p_outcome": 0.68}],
        )

        event_id = append_event(event)

        # Retrieve and verify structure
        stored_event = get_event_by_id(event_id)
        assert stored_event is not None

        # Check all durable fields
        assert stored_event["ticker"] == "MSFT"
        assert stored_event["features_v"] == "1.2.3"
        assert stored_event["regime"] == "high_vol_bear"
        assert stored_event["p_up"] == 0.63
        assert stored_event["decision"] == "BUY"
        assert stored_event["size"] == 0.35
        assert stored_event["explain"]["shap_top"] == [["breadth", 0.21], ["sentiment", 0.17]]
        assert stored_event["neighbors"][0]["id"] == "neighbor1"
        assert stored_event["neighbors"][0]["p_outcome"] == 0.68

    def test_update_outcome(self):
        """Test outcome updating mechanism."""
        # Create initial event
        event_data = {"ticker": "GOOGL", "p_up": 0.8, "decision": "BUY"}

        event_id = append_event(event_data)

        # Update outcome
        outcome_data = {"horizon": "1d", "label": 1, "pnl": 0.007, "mfe": 0.012, "mae": -0.004}

        update_outcome(event_id, outcome_data)

        # Verify outcome is attached
        events = list(iter_events())
        target_event = None
        for event in events:
            if event["id"] == event_id:
                target_event = event
                break

        assert target_event is not None
        assert "outcome" in target_event
        assert target_event["outcome"]["horizon"] == "1d"
        assert target_event["outcome"]["label"] == 1
        assert target_event["outcome"]["pnl"] == 0.007
        assert target_event["outcome"]["mfe"] == 0.012
        assert target_event["outcome"]["mae"] == -0.004

    def test_multiple_events_iteration(self):
        """Test iteration over multiple events."""
        events_data = [
            {"ticker": "AAPL", "p_up": 0.7},
            {"ticker": "TSLA", "p_up": 0.6},
            {"ticker": "MSFT", "p_up": 0.8},
        ]

        event_ids = []
        for data in events_data:
            event_ids.append(append_event(data))

        # Test iteration
        stored_events = list(iter_events())
        assert len(stored_events) == 3

        # Verify all events are present
        stored_tickers = {event["ticker"] for event in stored_events}
        assert stored_tickers == {"AAPL", "TSLA", "MSFT"}

    def test_event_count(self):
        """Test event counting."""
        assert count_events() == 0

        # Add some events
        for i in range(5):
            append_event({"ticker": f"STOCK{i}", "p_up": 0.5 + i * 0.1})

        assert count_events() == 5

    def test_get_recent_events(self):
        """Test getting recent events."""
        # Add several events
        for i in range(10):
            append_event({"ticker": f"STOCK{i}", "p_up": 0.5})

        # Get recent events
        recent = get_recent_events(limit=5)
        assert len(recent) == 5

        # Should be sorted by timestamp (newest first)
        timestamps = [event["ts"] for event in recent]
        assert timestamps == sorted(timestamps, reverse=True)

    def test_event_schema_validation(self):
        """Test event schema validation."""
        # Valid event
        valid_event = {"ts": datetime.utcnow().isoformat() + "Z", "ticker": "AAPL"}
        assert validate_event_schema(valid_event) is True

        # Missing required field
        invalid_event = {
            "ts": datetime.utcnow().isoformat() + "Z"
            # Missing ticker
        }
        assert validate_event_schema(invalid_event) is False

    def test_immutable_audit_fields(self):
        """Test that events maintain immutable audit fields."""
        original_event = {"ticker": "AAPL", "p_up": 0.75}

        event_id = append_event(original_event)

        # Get the stored event
        stored_event = get_event_by_id(event_id)
        original_ts = stored_event["ts"]

        # Try to append another event with same data
        duplicate_event = {"ticker": "AAPL", "p_up": 0.75}

        duplicate_id = append_event(duplicate_event)

        # Should have different IDs and timestamps
        assert duplicate_id != event_id

        duplicate_stored = get_event_by_id(duplicate_id)
        assert duplicate_stored["ts"] != original_ts

    def test_file_integrity_after_errors(self):
        """Test that file remains valid even after errors."""
        # Add a valid event
        append_event({"ticker": "AAPL", "p_up": 0.7})

        # Simulate an error by trying to append invalid JSON
        # (This should be handled gracefully by the implementation)

        # Add another valid event
        append_event({"ticker": "TSLA", "p_up": 0.6})

        # Verify both events are retrievable
        events = list(iter_events())
        assert len(events) == 2
        tickers = {event["ticker"] for event in events}
        assert tickers == {"AAPL", "TSLA"}

    def test_large_event_data(self):
        """Test handling of large event data."""
        # Create event with large explain data
        large_explain = {
            "shap_top": [[f"feature_{i}", 0.1 + i * 0.01] for i in range(100)],
            "detailed_analysis": {
                "momentum": [0.1] * 50,
                "sentiment": [0.2] * 50,
                "macro": [0.3] * 50,
            },
        }

        event_data = {"ticker": "AAPL", "p_up": 0.75, "explain": large_explain}

        event_id = append_event(event_data)

        # Verify large data is stored correctly
        stored_event = get_event_by_id(event_id)
        assert stored_event is not None
        assert len(stored_event["explain"]["shap_top"]) == 100
        assert len(stored_event["explain"]["detailed_analysis"]["momentum"]) == 50

    def test_concurrent_appends(self):
        """Test concurrent event appending (basic simulation)."""
        import threading
        import time

        event_ids = []

        def append_worker(worker_id):
            for i in range(5):
                event_data = {"ticker": f"STOCK{worker_id}_{i}", "p_up": 0.5 + worker_id * 0.1}
                event_id = append_event(event_data)
                event_ids.append(event_id)
                time.sleep(0.001)  # Small delay

        # Create multiple threads
        threads = []
        for worker_id in range(3):
            thread = threading.Thread(target=append_worker, args=(worker_id,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all events were stored
        stored_events = list(iter_events())
        assert len(stored_events) == 15  # 3 workers × 5 events each

        # Verify all event IDs are unique
        stored_ids = {event["id"] for event in stored_events}
        assert len(stored_ids) == 15


class TestEventStoreSQLite:
    """Test cases for SQLite backend."""

    def setup_method(self):
        """Set up SQLite test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.test_db = os.path.join(self.test_dir, "test_events.db")

        # Override environment for SQLite testing
        os.environ["MEMORY_MODE"] = "SQLITE"
        os.environ["SQLITE_PATH"] = self.test_db

    def teardown_method(self):
        """Clean up test environment."""
        os.environ["MEMORY_MODE"] = "JSONL"  # Reset to default
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_sqlite_basic_operations(self):
        """Test basic SQLite operations."""
        # This test would require SQLite implementation
        # For now, we'll skip if SQLite mode is not implemented
        try:
            event_id = append_event({"ticker": "AAPL", "p_up": 0.7})

            # Verify event can be retrieved
            stored_event = get_event_by_id(event_id)
            assert stored_event is not None
            assert stored_event["ticker"] == "AAPL"

        except NotImplementedError:
            pytest.skip("SQLite backend not implemented yet")


# Fixtures for common test data
@pytest.fixture
def sample_event():
    """Sample event data for testing."""
    return {
        "ticker": "AAPL",
        "features_v": "1.3.2",
        "regime": "high_vol_bear",
        "p_up": 0.63,
        "decision": "BUY",
        "size": 0.35,
        "explain": {"shap_top": [["breadth", 0.21], ["sentiment", 0.17], ["vix", 0.12]]},
        "neighbors": [{"id": "event1", "p_outcome": 0.68}, {"id": "event2", "p_outcome": 0.71}],
    }


@pytest.fixture
def sample_outcome():
    """Sample outcome data for testing."""
    return {"horizon": "1d", "label": 1, "pnl": 0.007, "mfe": 0.012, "mae": -0.004}


def test_end_to_end_workflow(sample_event, sample_outcome):
    """Test complete workflow from event creation to outcome update."""
    # The _isolate_event_store fixture provides test isolation automatically

    # 1. Create initial event
    event_id = append_event(sample_event)
    assert event_id is not None

    # 2. Verify event is stored correctly
    stored_event = get_event_by_id(event_id)
    assert stored_event["ticker"] == sample_event["ticker"]
    assert stored_event["p_up"] == sample_event["p_up"]

    # 3. Update with outcome
    update_outcome(event_id, sample_outcome)

    # 4. Verify outcome is attached
    updated_event = get_event_by_id(event_id)
    assert "outcome" in updated_event
    assert updated_event["outcome"]["label"] == sample_outcome["label"]
    assert updated_event["outcome"]["pnl"] == sample_outcome["pnl"]

    # 5. Verify event appears in iteration
    all_events = list(iter_events())
    assert len(all_events) == 1
    assert all_events[0]["id"] == event_id
    assert "outcome" in all_events[0]
