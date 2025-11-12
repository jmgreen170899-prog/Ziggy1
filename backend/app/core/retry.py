"""
Lightweight retry/backoff utilities with jitter and optional rate budget.

Usage patterns:
- backoff = JitterBackoff(min_delay=0.5, max_delay=10.0, factor=2.0, jitter=0.2)
- delay = backoff.next_delay(error)
- backoff.reset() on success

Also includes a simple async retry wrapper for transient operations.
"""

from __future__ import annotations

import asyncio
import random
import time
from collections.abc import Awaitable, Callable
from typing import Any

from app.core.config import get_settings


class JitterBackoff:
    def __init__(
        self,
        *,
        min_delay: float = 0.5,
        max_delay: float = 10.0,
        factor: float = 2.0,
        jitter: float = 0.2,
        max_attempts: int | None = None,
        budget_per_min: int | None = None,
    ) -> None:
        self.min_delay = float(min_delay)
        self.max_delay = float(max_delay)
        self.factor = float(factor)
        self.jitter = float(jitter)
        self.max_attempts = max_attempts
        self.budget_per_min = budget_per_min
        self._attempts = 0
        self._delay = self.min_delay
        self._window_start = time.monotonic()
        self._spent_in_window = 0

    def reset(self) -> None:
        self._attempts = 0
        self._delay = self.min_delay
        self._window_start = time.monotonic()
        self._spent_in_window = 0

    def _apply_budget(self, delay: float) -> float:
        if self.budget_per_min is None:
            return delay
        now = time.monotonic()
        if now - self._window_start >= 60.0:
            self._window_start = now
            self._spent_in_window = 0
        # Cap the sum of delays in the rolling minute window
        remaining = max(self.budget_per_min - self._spent_in_window, 0)
        capped = min(delay, remaining) if self.budget_per_min is not None else delay
        self._spent_in_window += capped
        return max(capped, 0.0)

    def next_delay(self, error: BaseException | None = None) -> float:
        self._attempts += 1
        base = min(self._delay, self.max_delay)
        # Full jitter in +/- jitter range
        jitter_span = base * self.jitter
        delay = max(self.min_delay, base + random.uniform(-jitter_span, jitter_span))
        # Increase delay for next time
        self._delay = min(self.max_delay, max(self.min_delay, base * self.factor))
        # Respect attempts cap
        if self.max_attempts is not None and self._attempts > self.max_attempts:
            return 0.0
        return self._apply_budget(delay)


async def retry_async(
    func: Callable[[], Awaitable[Any]],
    *,
    backoff: JitterBackoff | None = None,
    retry_on: tuple[type[BaseException], ...] = (Exception,),
    max_attempts: int = 5,
) -> Any:
    """Retry an async function using backoff policy.

    Returns func() result or raises last exception after attempts.
    """
    if backoff is None:
        s = get_settings()
        policy = JitterBackoff(
            min_delay=max(0.0, float(getattr(s, "BACKOFF_MIN_MS", 200)) / 1000.0),
            max_delay=max(0.0, float(getattr(s, "BACKOFF_MAX_MS", 3000)) / 1000.0),
            factor=float(getattr(s, "BACKOFF_FACTOR", 2.0)),
            jitter=float(getattr(s, "BACKOFF_JITTER", 0.2)),
        )
    else:
        policy = backoff
    last_exc: BaseException | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            result = await func()
            policy.reset()
            return result
        except retry_on as e:  # type: ignore[misc]
            last_exc = e
            delay = policy.next_delay(e)
            if attempt >= max_attempts or delay <= 0:
                break
            try:
                await asyncio.sleep(delay)
            except asyncio.CancelledError:
                raise
    assert last_exc is not None
    raise last_exc
