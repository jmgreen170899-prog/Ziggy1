# backend/app/tasks/tg_log.py
from __future__ import annotations

import json
import os
import threading
import time
from collections import deque
from pathlib import Path
from typing import Any


# Resolve a stable data dir next to backend/
_THIS = Path(__file__).resolve()
DATA_DIR = _THIS.parents[2] / "data"  # .../backend/data
DATA_DIR.mkdir(parents=True, exist_ok=True)
FILE = DATA_DIR / "telegram_log.jsonl"

_LOCK = threading.Lock()


def log_path() -> str:
    return str(FILE)


def _safe_json(o: Any) -> Any:
    try:
        json.dumps(o)
        return o
    except Exception:
        return repr(o)


def log_telegram(
    *,
    ts: float | None = None,
    kind: str = "misc",
    text: str = "",
    ok: bool | None = None,
    error: str | None = None,
    meta: dict[str, Any] | None = None,
) -> None:
    """
    Append a single JSON line to the log, flushing and fsync'ing to make
    it immediately visible to the Alerts tab even on Windows.
    """
    rec = {
        "ts": float(ts if ts is not None else time.time()),
        "kind": kind,
        "text": text,
        "ok": bool(ok) if ok is not None else None,
        "error": error,
        "meta": _safe_json(meta) if meta is not None else None,
    }
    line = json.dumps(rec, ensure_ascii=False)

    with _LOCK, open(FILE, "a", encoding="utf-8", newline="\n") as f:
        f.write(line + "\n")
        f.flush()
        try:
            os.fsync(f.fileno())  # ensure it hits disk on Windows too
        except Exception:
            pass


def read_telegram(limit: int = 500) -> list[dict[str, Any]]:
    """
    Return the most recent `limit` records (newest first).
    """
    if not FILE.exists():
        return []
    out: list[dict[str, Any]] = []
    # read tail efficiently
    with _LOCK:
        try:
            with open(FILE, encoding="utf-8") as f:
                tail = deque(f, maxlen=int(limit))
        except Exception:
            return []
    for line in tail:
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    # newest last in deque → reverse to newest first for UI
    out.reverse()
    return out


def clear_telegram() -> None:
    with _LOCK, open(FILE, "w", encoding="utf-8") as f:
        f.write("")  # truncate
        f.flush()
        try:
            os.fsync(f.fileno())
        except Exception:
            pass
