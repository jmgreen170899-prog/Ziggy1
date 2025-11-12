"""
Lightweight time utilities.

- monotonic_now(): float seconds using time.monotonic() for backoff/caches
"""

from __future__ import annotations

import time


def monotonic_now() -> float:
    """Return monotonic time in seconds (not subject to wall-clock changes)."""
    return time.monotonic()
