"""
Centralized Metrics Collection

Provides unified interface for collecting and exposing metrics from all subsystems.
Includes WebSocket metrics, provider health, and SLO compliance.
"""

from __future__ import annotations

import time
from typing import Any

from app.observability.slo_targets import SLO_TARGETS, check_slo_violation


class MetricsCollector:
    """Centralized metrics collection for observability."""

    def __init__(self):
        self._custom_metrics: dict[str, float] = {}
        self._last_update: dict[str, float] = {}

    def set_metric(self, name: str, value: float) -> None:
        """Set a custom metric value."""
        self._custom_metrics[name] = value
        self._last_update[name] = time.time()

    def get_metric(self, name: str) -> float | None:
        """Get a custom metric value."""
        return self._custom_metrics.get(name)

    def increment_metric(self, name: str, delta: float = 1.0) -> None:
        """Increment a metric by delta."""
        current = self._custom_metrics.get(name, 0.0)
        self._custom_metrics[name] = current + delta
        self._last_update[name] = time.time()

    def get_all_custom_metrics(self) -> dict[str, Any]:
        """Get all custom metrics."""
        return {
            "metrics": self._custom_metrics.copy(),
            "last_update": self._last_update.copy(),
        }


# Global metrics collector instance
_metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    return _metrics_collector


def get_websocket_metrics() -> dict[str, Any]:
    """
    Get WebSocket metrics including queue length, dropped messages, and latency.

    Returns:
        Dictionary with WebSocket metrics per channel:
        - queue_len: Current queue length
        - dropped_msgs: Total messages dropped
        - send_latency: Average send latency in ms
        - subscribers: Number of active subscribers
        - broadcasts_attempted: Total broadcast attempts
        - broadcasts_failed: Total broadcast failures
    """
    try:
        from app.core.websocket import connection_manager

        stats = connection_manager.get_connection_stats()

        # Transform stats to include standardized metric names
        metrics = {
            "total_connections": stats.get("total_connections", 0),
            "channels": {},
        }

        per_channel = stats.get("per_channel", {})
        for channel, channel_stats in per_channel.items():
            metrics["channels"][channel] = {
                "queue_len": channel_stats.get("queue_len", 0),
                "dropped_msgs": channel_stats.get("queue_dropped", 0),
                "send_latency_ms": channel_stats.get("broadcast_latency_ms", 0.0),
                "subscribers": channel_stats.get("subscribers", 0),
                "broadcasts_attempted": channel_stats.get("broadcasts_attempted", 0),
                "broadcasts_failed": channel_stats.get("broadcasts_failed", 0),
                "avg_uptime_s": channel_stats.get("avg_uptime_s", 0.0),
            }

        return metrics
    except Exception as e:
        return {"error": str(e), "channels": {}}


def get_provider_health_metrics() -> dict[str, Any]:
    """
    Get provider health metrics for all tracked providers.

    Returns:
        Dictionary with health metrics for each provider:
        - Polygon: API key status and health score
        - Alpaca: API key status and health score
        - News: RSS/News provider health
        - FRED: Economic data provider health
        - IEX Cloud: Alternative market data provider
    """
    try:
        from app.services.provider_health import get_provider_metrics

        all_metrics = get_provider_metrics()

        # Calculate availability percentages
        gauges = {}
        for provider, metrics in all_metrics.items():
            if provider == "_global":
                continue

            success_rate = metrics.get("success_rate", 0.0)
            availability_pct = success_rate * 100.0

            gauges[provider] = {
                "availability_pct": round(availability_pct, 2),
                "health_score": round(metrics.get("score", 0.0), 3),
                "avg_latency_ms": round(metrics.get("avg_latency_ms", 0.0), 2),
                "p95_latency_ms": round(metrics.get("p95_latency_ms", 0.0), 2),
                "success_rate": round(success_rate, 3),
                "consecutive_failures": int(metrics.get("consecutive_failures", 0)),
                "total_events": int(metrics.get("total_events", 0)),
            }

        # Add global metrics
        global_metrics = all_metrics.get("_global", {})
        result = {
            "providers": gauges,
            "global": {
                "failover_count": int(global_metrics.get("failover_count", 0)),
                "tracked_providers": int(global_metrics.get("tracked_providers", 0)),
            },
        }

        return result
    except Exception as e:
        return {"error": str(e), "providers": {}, "global": {}}


def get_slo_status() -> dict[str, Any]:
    """
    Check SLO compliance for all defined targets.

    Returns:
        Dictionary with SLO status:
        - targets: List of all SLO targets with current values
        - violations: List of current SLO violations
        - compliance_pct: Overall compliance percentage
    """
    ws_metrics = get_websocket_metrics()
    provider_metrics = get_provider_health_metrics()

    results = []
    violations = []

    # Check WebSocket delivery latency SLO
    ws_p95_latencies = []
    for channel, stats in ws_metrics.get("channels", {}).items():
        latency = stats.get("send_latency_ms", 0.0)
        ws_p95_latencies.append(latency)

    if ws_p95_latencies:
        avg_p95_latency = sum(ws_p95_latencies) / len(ws_p95_latencies)
        ws_slo_violated = check_slo_violation(
            "ws_delivery_latency_p95", avg_p95_latency
        )
        results.append(
            {
                "name": "ws_delivery_latency_p95",
                "current_value": round(avg_p95_latency, 2),
                "target_value": SLO_TARGETS["ws_delivery_latency_p95"].target_value,
                "unit": "ms",
                "violated": ws_slo_violated,
            }
        )
        if ws_slo_violated:
            violations.append("ws_delivery_latency_p95")

    # Check queue drop rate SLO
    total_dropped = 0
    total_attempted = 0
    for channel, stats in ws_metrics.get("channels", {}).items():
        total_dropped += stats.get("dropped_msgs", 0)
        total_attempted += stats.get("broadcasts_attempted", 0)

    if total_attempted > 0:
        drop_rate_pct = (total_dropped / total_attempted) * 100.0
        drop_slo_violated = check_slo_violation("queue_drop_rate", drop_rate_pct)
        results.append(
            {
                "name": "queue_drop_rate",
                "current_value": round(drop_rate_pct, 3),
                "target_value": SLO_TARGETS["queue_drop_rate"].target_value,
                "unit": "%",
                "violated": drop_slo_violated,
            }
        )
        if drop_slo_violated:
            violations.append("queue_drop_rate")

    # Check provider availability SLO
    provider_availabilities = []
    for provider, metrics in provider_metrics.get("providers", {}).items():
        availability = metrics.get("availability_pct", 0.0)
        provider_availabilities.append(availability)

    if provider_availabilities:
        avg_availability = sum(provider_availabilities) / len(provider_availabilities)
        availability_slo_violated = check_slo_violation(
            "provider_availability", avg_availability
        )
        results.append(
            {
                "name": "provider_availability",
                "current_value": round(avg_availability, 2),
                "target_value": SLO_TARGETS["provider_availability"].target_value,
                "unit": "%",
                "violated": availability_slo_violated,
            }
        )
        if availability_slo_violated:
            violations.append("provider_availability")

    # Calculate compliance percentage
    total_slos = len(results)
    compliant_slos = total_slos - len(violations)
    compliance_pct = (compliant_slos / total_slos * 100.0) if total_slos > 0 else 100.0

    return {
        "targets": results,
        "violations": violations,
        "compliance_pct": round(compliance_pct, 2),
        "timestamp": time.time(),
    }


def get_all_metrics() -> dict[str, Any]:
    """
    Get all metrics from all subsystems.

    Returns:
        Comprehensive metrics dictionary including:
        - websocket: WebSocket metrics
        - providers: Provider health metrics
        - slo: SLO compliance status
        - custom: Custom application metrics
    """
    return {
        "websocket": get_websocket_metrics(),
        "providers": get_provider_health_metrics(),
        "slo": get_slo_status(),
        "custom": _metrics_collector.get_all_custom_metrics(),
    }
