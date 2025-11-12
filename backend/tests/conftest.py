"""
Pytest configuration for backend tests.

- Skips performance tests unless RUN_PERF_TESTS=1 is set.
- Isolates the event store to a fresh temporary path per test to avoid cross-test pollution.
"""

import os

import pytest


def pytest_collection_modifyitems(config, items):
    """
    Automatically skip tests marked `performance` unless RUN_PERF_TESTS=1.
    """
    if os.environ.get("RUN_PERF_TESTS") != "1":
        skip_perf = pytest.mark.skip(reason="Skip performance tests unless RUN_PERF_TESTS=1")
        for item in items:
            if "performance" in item.keywords:
                item.add_marker(skip_perf)


@pytest.fixture(autouse=True)
def _isolate_event_store(tmp_path, monkeypatch):
    """
    Point the event store to a unique temporary JSONL file for each test.

    This prevents tests from writing to a shared file and keeps runs hermetic.
    """
    test_events_path = tmp_path / "events.jsonl"
    monkeypatch.setenv("EVENT_STORE_PATH", str(test_events_path))
    yield
