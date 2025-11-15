"""
Provider Health Tracking - Perception Layer

Tracks provider success rates, latencies, and contract compliance
for intelligent failover and redundancy decisions.
"""

from __future__ import annotations

import logging
import os
import time
from collections import deque
from dataclasses import dataclass, field
from threading import Lock


logger = logging.getLogger(__name__)

# Environment configuration
PROVIDER_HEALTH_DECAY = float(os.getenv("PROVIDER_HEALTH_DECAY", "0.2"))
PROVIDER_TIMEOUT_MS = int(os.getenv("PROVIDER_TIMEOUT_MS", "1500"))
HEALTH_WINDOW_SIZE = int(os.getenv("HEALTH_WINDOW_SIZE", "100"))
HEALTH_THRESHOLD = float(os.getenv("HEALTH_THRESHOLD", "0.7"))


@dataclass
class HealthTracker:
    """
    Tracks provider health metrics with exponential decay.

    Metrics tracked:
    - Success rate (request success/failure)
    - Latency percentiles
    - Contract compliance rate
    - Recent error patterns
    """

    window: int = field(default_factory=lambda: HEALTH_WINDOW_SIZE)
    decay: float = field(default_factory=lambda: PROVIDER_HEALTH_DECAY)
    events: deque[tuple[bool, int, bool]] = field(
        default_factory=lambda: deque(maxlen=200)
    )
    last_success_ts: float | None = None
    consecutive_failures: int = 0
    _lock: Lock = field(default_factory=Lock)

    def record(self, ok: bool, latency_ms: int, contract_ok: bool = True) -> None:
        """
        Record a provider event.

        Args:
            ok: Whether the request succeeded
            latency_ms: Request latency in milliseconds
            contract_ok: Whether data passed contract validation
        """
        with self._lock:
            self.events.append((ok, latency_ms, contract_ok))

            if ok and contract_ok:
                self.last_success_ts = time.time()
                self.consecutive_failures = 0
            else:
                self.consecutive_failures += 1

    def score(self) -> float:
        """
        Calculate health score (0.0 to 1.0, higher is better).

        Factors:
        - Success rate (70% weight)
        - Latency penalty (20% weight)
        - Contract compliance (10% weight)
        """
        with self._lock:
            if not self.events:
                return 1.0  # No data = assume healthy

            # Calculate weighted metrics
            recent_events = list(self.events)[-self.window :]

            # Success rate component
            success_count = sum(
                1 for ok, _, contract_ok in recent_events if ok and contract_ok
            )
            success_rate = success_count / len(recent_events)

            # Latency penalty component
            latencies = [lat for _, lat, _ in recent_events]
            avg_latency = sum(latencies) / len(latencies)
            latency_penalty = 1.0 / (
                1.0 + avg_latency / 1000.0
            )  # Penalty for high latency

            # Contract compliance component
            contract_rate = sum(
                1 for _, _, contract_ok in recent_events if contract_ok
            ) / len(recent_events)

            # Consecutive failure penalty
            failure_penalty = max(0.0, 1.0 - (self.consecutive_failures * 0.1))

            # Weighted score
            score = (
                0.7 * success_rate + 0.2 * latency_penalty + 0.1 * contract_rate
            ) * failure_penalty

            return min(1.0, max(0.0, score))

    def is_healthy(self) -> bool:
        """Check if provider is above health threshold."""
        return self.score() >= HEALTH_THRESHOLD

    def get_metrics(self) -> dict[str, float]:
        """Get detailed health metrics."""
        with self._lock:
            if not self.events:
                return {
                    "score": 1.0,
                    "success_rate": 1.0,
                    "avg_latency_ms": 0.0,
                    "p95_latency_ms": 0.0,
                    "contract_rate": 1.0,
                    "consecutive_failures": 0,
                }

            recent_events = list(self.events)[-self.window :]

            # Success metrics
            success_count = sum(
                1 for ok, _, contract_ok in recent_events if ok and contract_ok
            )
            success_rate = success_count / len(recent_events)

            # Latency metrics
            latencies = sorted([lat for _, lat, _ in recent_events])
            avg_latency = sum(latencies) / len(latencies)
            p95_idx = int(len(latencies) * 0.95)
            p95_latency = latencies[p95_idx] if latencies else 0.0

            # Contract compliance
            contract_rate = sum(
                1 for _, _, contract_ok in recent_events if contract_ok
            ) / len(recent_events)

            return {
                "score": self.score(),
                "success_rate": success_rate,
                "avg_latency_ms": avg_latency,
                "p95_latency_ms": p95_latency,
                "contract_rate": contract_rate,
                "consecutive_failures": self.consecutive_failures,
                "total_events": len(self.events),
                "window_events": len(recent_events),
            }


class ProviderHealthManager:
    """
    Manages health tracking for multiple providers.
    """

    def __init__(self):
        self.trackers: dict[str, HealthTracker] = {}
        self._lock = Lock()
        self.failover_count = 0

    def get_tracker(self, provider: str) -> HealthTracker:
        """Get or create health tracker for provider."""
        with self._lock:
            if provider not in self.trackers:
                self.trackers[provider] = HealthTracker()
            return self.trackers[provider]

    def record_event(
        self, provider: str, ok: bool, latency_ms: int, contract_ok: bool = True
    ) -> None:
        """Record an event for a provider."""
        tracker = self.get_tracker(provider)
        tracker.record(ok, latency_ms, contract_ok)

        # Log significant events
        if not ok:
            logger.warning(
                f"Provider {provider} failed request (latency: {latency_ms}ms)"
            )
        elif latency_ms > PROVIDER_TIMEOUT_MS:
            logger.warning(
                f"Provider {provider} slow response (latency: {latency_ms}ms)"
            )
        elif not contract_ok:
            logger.warning(f"Provider {provider} contract violation")

    def record_failover(self) -> None:
        """Record a failover event."""
        self.failover_count += 1
        logger.info(f"Provider failover #{self.failover_count}")

    def get_best_provider(self, providers: list[str]) -> str | None:
        """
        Select the best provider based on health scores.

        Args:
            providers: List of provider names to consider

        Returns:
            Best provider name or None if all unhealthy
        """
        if not providers:
            return None

        # Get health scores for all providers
        scored_providers = []
        for provider in providers:
            tracker = self.get_tracker(provider)
            score = tracker.score()
            scored_providers.append((provider, score))

        # Sort by score (descending)
        scored_providers.sort(key=lambda x: x[1], reverse=True)

        # Return best provider if above threshold
        best_provider, best_score = scored_providers[0]
        if best_score >= HEALTH_THRESHOLD:
            return best_provider

        return None

    def get_provider_order(self, primary: str, secondary: str) -> list[str]:
        """
        Get provider order for failover strategy.

        Args:
            primary: Primary provider name
            secondary: Secondary provider name

        Returns:
            Ordered list of providers to try
        """
        primary_tracker = self.get_tracker(primary)
        secondary_tracker = self.get_tracker(secondary)

        if primary_tracker.is_healthy():
            return [primary, secondary]
        elif secondary_tracker.is_healthy():
            self.record_failover()
            return [secondary, primary]
        else:
            # Both unhealthy - try primary first anyway
            logger.warning(
                f"Both providers unhealthy: {primary}={primary_tracker.score():.3f}, {secondary}={secondary_tracker.score():.3f}"
            )
            return [primary, secondary]

    def get_all_metrics(self) -> dict[str, dict[str, float]]:
        """Get metrics for all tracked providers."""
        with self._lock:
            metrics = {}
            for provider, tracker in self.trackers.items():
                metrics[provider] = tracker.get_metrics()

            # Add global metrics
            metrics["_global"] = {
                "failover_count": float(self.failover_count),
                "tracked_providers": float(len(self.trackers)),
            }

            return metrics


# Global health manager instance
health_manager = ProviderHealthManager()


def get_health_manager() -> ProviderHealthManager:
    """Get the global health manager instance."""
    return health_manager


def record_provider_event(
    provider: str, ok: bool, latency_ms: int, contract_ok: bool = True
) -> None:
    """Convenience function to record provider events."""
    health_manager.record_event(provider, ok, latency_ms, contract_ok)


def get_provider_metrics(provider: str | None = None) -> dict[str, dict[str, float]]:
    """
    Get provider health metrics.

    Args:
        provider: Specific provider name or None for all providers

    Returns:
        Provider metrics dictionary
    """
    all_metrics = health_manager.get_all_metrics()

    if provider:
        return {provider: all_metrics.get(provider, {})}

    return all_metrics
