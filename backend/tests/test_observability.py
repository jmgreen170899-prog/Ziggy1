"""
Tests for observability metrics and SLO tracking.
"""

from app.observability import (
    get_all_metrics,
    get_provider_health_metrics,
    get_slo_status,
    get_websocket_metrics,
)
from app.observability.metrics import MetricsCollector, get_metrics_collector
from app.observability.slo_targets import (
    check_slo_violation,
    get_all_slo_targets,
    get_slo_target,
)


class TestMetricsCollector:
    """Test the MetricsCollector class."""

    def test_set_and_get_metric(self):
        """Test setting and getting a metric."""
        collector = MetricsCollector()
        collector.set_metric("test_metric", 42.5)
        assert collector.get_metric("test_metric") == 42.5

    def test_increment_metric(self):
        """Test incrementing a metric."""
        collector = MetricsCollector()
        collector.set_metric("counter", 10.0)
        collector.increment_metric("counter", 5.0)
        assert collector.get_metric("counter") == 15.0

    def test_increment_new_metric(self):
        """Test incrementing a non-existent metric starts at delta."""
        collector = MetricsCollector()
        collector.increment_metric("new_counter", 3.0)
        assert collector.get_metric("new_counter") == 3.0

    def test_get_all_custom_metrics(self):
        """Test getting all custom metrics."""
        collector = MetricsCollector()
        collector.set_metric("metric1", 1.0)
        collector.set_metric("metric2", 2.0)

        all_metrics = collector.get_all_custom_metrics()
        assert "metrics" in all_metrics
        assert "last_update" in all_metrics
        assert all_metrics["metrics"]["metric1"] == 1.0
        assert all_metrics["metrics"]["metric2"] == 2.0


class TestSLOTargets:
    """Test SLO target definitions and checks."""

    def test_all_slo_targets_defined(self):
        """Test that all required SLO targets are defined."""
        targets = get_all_slo_targets()
        assert "ws_delivery_latency_p95" in targets
        assert "queue_drop_rate" in targets
        assert "provider_availability" in targets

    def test_websocket_latency_slo(self):
        """Test WebSocket latency SLO target."""
        target = get_slo_target("ws_delivery_latency_p95")
        assert target is not None
        assert target.target_value == 100.0
        assert target.unit == "ms"
        assert target.threshold_type == "max"

    def test_queue_drop_rate_slo(self):
        """Test queue drop rate SLO target."""
        target = get_slo_target("queue_drop_rate")
        assert target is not None
        assert target.target_value == 0.1
        assert target.unit == "%"
        assert target.threshold_type == "max"

    def test_provider_availability_slo(self):
        """Test provider availability SLO target."""
        target = get_slo_target("provider_availability")
        assert target is not None
        assert target.target_value == 99.5
        assert target.unit == "%"
        assert target.threshold_type == "min"

    def test_check_slo_violation_max_threshold(self):
        """Test SLO violation check for max threshold."""
        # Above threshold - violation
        assert check_slo_violation("ws_delivery_latency_p95", 150.0) is True
        # At threshold - no violation
        assert check_slo_violation("ws_delivery_latency_p95", 100.0) is False
        # Below threshold - no violation
        assert check_slo_violation("ws_delivery_latency_p95", 50.0) is False

    def test_check_slo_violation_min_threshold(self):
        """Test SLO violation check for min threshold."""
        # Below threshold - violation
        assert check_slo_violation("provider_availability", 98.0) is True
        # At threshold - no violation
        assert check_slo_violation("provider_availability", 99.5) is False
        # Above threshold - no violation
        assert check_slo_violation("provider_availability", 99.9) is False

    def test_check_slo_violation_nonexistent(self):
        """Test SLO violation check for non-existent target."""
        assert check_slo_violation("nonexistent_slo", 100.0) is False


class TestWebSocketMetrics:
    """Test WebSocket metrics collection."""

    def test_get_websocket_metrics_structure(self):
        """Test that WebSocket metrics return expected structure."""
        metrics = get_websocket_metrics()
        assert isinstance(metrics, dict)
        assert "channels" in metrics
        assert isinstance(metrics["channels"], dict)

    def test_websocket_metrics_error_handling(self):
        """Test WebSocket metrics error handling."""
        # Should not raise exception even if websocket manager unavailable
        metrics = get_websocket_metrics()
        assert isinstance(metrics, dict)


class TestProviderHealthMetrics:
    """Test provider health metrics collection."""

    def test_get_provider_health_metrics_structure(self):
        """Test that provider health metrics return expected structure."""
        metrics = get_provider_health_metrics()
        assert isinstance(metrics, dict)
        assert "providers" in metrics
        assert isinstance(metrics["providers"], dict)

    def test_provider_health_metrics_error_handling(self):
        """Test provider health metrics error handling."""
        # Should not raise exception even if providers unavailable
        metrics = get_provider_health_metrics()
        assert isinstance(metrics, dict)


class TestSLOStatus:
    """Test SLO status checking."""

    def test_get_slo_status_structure(self):
        """Test that SLO status returns expected structure."""
        status = get_slo_status()
        assert isinstance(status, dict)
        assert "targets" in status
        assert "violations" in status
        assert "compliance_pct" in status
        assert "timestamp" in status

    def test_slo_status_targets_list(self):
        """Test that SLO status contains target information."""
        status = get_slo_status()
        assert isinstance(status["targets"], list)

    def test_slo_status_violations_list(self):
        """Test that SLO violations is a list."""
        status = get_slo_status()
        assert isinstance(status["violations"], list)

    def test_slo_compliance_percentage(self):
        """Test that compliance percentage is calculated."""
        status = get_slo_status()
        compliance = status["compliance_pct"]
        assert isinstance(compliance, (int, float))
        assert 0 <= compliance <= 100


class TestAllMetrics:
    """Test comprehensive metrics collection."""

    def test_get_all_metrics_structure(self):
        """Test that all metrics return expected structure."""
        metrics = get_all_metrics()
        assert isinstance(metrics, dict)
        assert "websocket" in metrics
        assert "providers" in metrics
        assert "slo" in metrics
        assert "custom" in metrics

    def test_all_metrics_subsystems(self):
        """Test that all subsystems are included in metrics."""
        metrics = get_all_metrics()

        # WebSocket metrics
        assert isinstance(metrics["websocket"], dict)

        # Provider metrics
        assert isinstance(metrics["providers"], dict)

        # SLO status
        assert isinstance(metrics["slo"], dict)
        assert "compliance_pct" in metrics["slo"]

        # Custom metrics
        assert isinstance(metrics["custom"], dict)


class TestGlobalMetricsCollector:
    """Test the global metrics collector instance."""

    def test_get_metrics_collector_singleton(self):
        """Test that get_metrics_collector returns same instance."""
        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()
        assert collector1 is collector2

    def test_global_collector_persistence(self):
        """Test that metrics persist in global collector."""
        collector = get_metrics_collector()
        collector.set_metric("test_persistence", 123.0)

        # Get collector again and verify metric persists
        collector2 = get_metrics_collector()
        assert collector2.get_metric("test_persistence") == 123.0
