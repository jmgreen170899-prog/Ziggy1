"""
Service-Level Objectives (SLO) Definitions

Global SLO targets for ZiggyAI production monitoring.
These targets define the expected quality of service for critical subsystems.
"""

from dataclasses import dataclass


@dataclass
class SLOTarget:
    """Defines an SLO target with threshold and description."""

    name: str
    target_value: float
    unit: str
    description: str
    threshold_type: str  # "max" or "min"


# Global SLO targets as per requirements
WEBSOCKET_SLO = SLOTarget(
    name="ws_delivery_latency_p95",
    target_value=100.0,
    unit="ms",
    description="WebSocket message delivery latency at 95th percentile",
    threshold_type="max",
)

QUEUE_DROP_RATE_SLO = SLOTarget(
    name="queue_drop_rate",
    target_value=0.1,
    unit="%",
    description="Queue drop rate threshold",
    threshold_type="max",
)

PROVIDER_AVAILABILITY_SLO = SLOTarget(
    name="provider_availability",
    target_value=99.5,
    unit="%",
    description="Provider health availability",
    threshold_type="min",
)

# Collection of all SLO targets
SLO_TARGETS: dict[str, SLOTarget] = {
    "ws_delivery_latency_p95": WEBSOCKET_SLO,
    "queue_drop_rate": QUEUE_DROP_RATE_SLO,
    "provider_availability": PROVIDER_AVAILABILITY_SLO,
}


def get_slo_target(name: str) -> SLOTarget | None:
    """Get SLO target definition by name."""
    return SLO_TARGETS.get(name)


def get_all_slo_targets() -> dict[str, SLOTarget]:
    """Get all defined SLO targets."""
    return SLO_TARGETS.copy()


def check_slo_violation(name: str, current_value: float) -> bool:
    """
    Check if current value violates the SLO target.

    Args:
        name: SLO target name
        current_value: Current measured value

    Returns:
        True if SLO is violated, False otherwise
    """
    target = get_slo_target(name)
    if not target:
        return False

    if target.threshold_type == "max":
        return current_value > target.target_value
    else:  # "min"
        return current_value < target.target_value
