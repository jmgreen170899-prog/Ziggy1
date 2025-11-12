from __future__ import annotations

import json
import os
import threading
from collections import deque
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.logging import get_logger


logger = get_logger("ziggy.snapshotter")


class AuditLog:
    """Append-only JSONL audit log with periodic fsync for durability."""

    def __init__(self, path: str | Path, fsync_every: int = 50):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Using persistent file handle for append-only writes (intentional long-lived handle)
        self._fh = open(self.path, "a", buffering=1, encoding="utf-8")  # noqa: SIM115
        self._lock = threading.Lock()
        self._count_since_sync = 0
        self._fsync_every = max(1, fsync_every)
        self._buffer = deque(maxlen=1000)

    def append_event(self, event: dict[str, Any]) -> None:
        ev = dict(event)
        if "ts" not in ev:
            ev["ts"] = datetime.utcnow().isoformat()
        line = json.dumps(ev, separators=(",", ":"), ensure_ascii=False)
        with self._lock:
            self._fh.write(line + "\n")
            self._buffer.append(ev)
            self._count_since_sync += 1
            if self._count_since_sync >= self._fsync_every:
                try:
                    self._fh.flush()
                    os.fsync(self._fh.fileno())
                except Exception:
                    pass
                self._count_since_sync = 0

    def flush(self) -> None:
        with self._lock:
            try:
                self._fh.flush()
                os.fsync(self._fh.fileno())
            except Exception:
                pass
            self._count_since_sync = 0

    def close(self) -> None:
        from contextlib import suppress

        try:
            self.flush()
        finally:
            with suppress(Exception):
                self._fh.close()

    def replay_events(self, since_ts: datetime | None = None) -> Iterator[dict[str, Any]]:
        if not self.path.exists():
            return iter(())
        with open(self.path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                    if since_ts is not None:
                        ts = ev.get("ts")
                        if ts:
                            try:
                                d = datetime.fromisoformat(ts)
                                if d < since_ts:
                                    continue
                            except Exception:
                                pass
                    yield ev
                except Exception:
                    continue
