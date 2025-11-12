from app.memory import events


def test_event_store_metrics_accessible(tmp_path, monkeypatch):
    # Use a temp sqlite path to avoid touching real data
    sqlite_path = tmp_path / "events.db"
    monkeypatch.setenv("MEMORY_MODE", "SQLITE")
    monkeypatch.setenv("SQLITE_PATH", str(sqlite_path))

    # Append a couple of events
    evt_id = events.append_event({"ticker": "TEST", "ts": "2025-01-01T00:00:00Z"})
    assert isinstance(evt_id, str)

    evt_id2 = events.append_event({"ticker": "TEST", "ts": "2025-01-01T00:00:01Z"})
    assert isinstance(evt_id2, str)

    # Fetch metrics
    metrics = events.get_event_store_metrics()
    assert isinstance(metrics, dict)
    assert "backend" in metrics
    assert "writes_total" in metrics and int(metrics["writes_total"]) >= 2
    assert "last_write_ms" in metrics

    # Confirm WAL setting keys exist when using sqlite
    assert metrics.get("sqlite_path")
