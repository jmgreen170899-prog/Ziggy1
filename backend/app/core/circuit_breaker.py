# app/core/circuit_breaker.py
from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from enum import Enum
from functools import wraps
from typing import TypeVar


logger = logging.getLogger("ziggy.circuit_breaker")

T = TypeVar("T")


class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit is open, failing fast
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open"""

    pass


class CircuitBreaker:
    """Circuit breaker implementation for external service calls"""

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        recovery_timeout: float = 30.0,
        expected_exception: type[Exception] = Exception,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        # State
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: float | None = None
        self.last_success_time: float | None = None

        logger.info(f"Circuit breaker '{name}' initialized with threshold={failure_threshold}")

    def _current_time(self) -> float:
        return time.time()

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        return self._current_time() - self.last_failure_time >= self.recovery_timeout

    def _record_success(self) -> None:
        """Record successful call"""
        self.failure_count = 0
        self.last_success_time = self._current_time()
        if self.state != CircuitState.CLOSED:
            logger.info(f"Circuit breaker '{self.name}' reset to CLOSED")
            self.state = CircuitState.CLOSED

    def _record_failure(self) -> None:
        """Record failed call"""
        self.failure_count += 1
        self.last_failure_time = self._current_time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(
                f"Circuit breaker '{self.name}' opened after {self.failure_count} failures"
            )

    def call(self, func: Callable[[], T]) -> T:
        """Execute function with circuit breaker protection (sync)"""

        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                logger.info(f"Circuit breaker '{self.name}' attempting reset")
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerError(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Failing fast. Last failure: {self.last_failure_time}"
                )

        try:
            result = func()
            self._record_success()
            return result
        except self.expected_exception as e:
            self._record_failure()
            logger.warning(
                f"Circuit breaker '{self.name}' recorded failure: {e} "
                f"({self.failure_count}/{self.failure_threshold})"
            )
            raise

    async def acall(self, func: Callable[[], T]) -> T:
        """Execute async function with circuit breaker protection"""

        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                logger.info(f"Circuit breaker '{self.name}' attempting reset")
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerError(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Failing fast. Last failure: {self.last_failure_time}"
                )

        try:
            if asyncio.iscoroutinefunction(func):
                result = await func()
            else:
                result = func()
            self._record_success()
            return result
        except self.expected_exception as e:
            self._record_failure()
            logger.warning(
                f"Circuit breaker '{self.name}' recorded failure: {e} "
                f"({self.failure_count}/{self.failure_threshold})"
            )
            raise

    @property
    def status(self) -> dict:
        """Get circuit breaker status"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "last_failure_time": self.last_failure_time,
            "last_success_time": self.last_success_time,
        }


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    timeout: float = 60.0,
    recovery_timeout: float = 30.0,
    expected_exception: type[Exception] = Exception,
):
    """Decorator for circuit breaker protection"""
    breaker = CircuitBreaker(
        name=name,
        failure_threshold=failure_threshold,
        timeout=timeout,
        recovery_timeout=recovery_timeout,
        expected_exception=expected_exception,
    )

    def decorator(func):
        if asyncio.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await breaker.acall(lambda: func(*args, **kwargs))

            return async_wrapper
        else:

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return breaker.call(lambda: func(*args, **kwargs))

            return sync_wrapper

    return decorator


# Global circuit breaker registry
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str, **kwargs) -> CircuitBreaker:
    """Get or create circuit breaker by name"""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name=name, **kwargs)
    return _circuit_breakers[name]


def get_all_circuit_breakers() -> dict[str, dict]:
    """Get status of all circuit breakers"""
    return {name: breaker.status for name, breaker in _circuit_breakers.items()}
