"""
Trading Brain Integration - Action & Execution Layer

Mission: Safety ↑, slippage ↓
Complete audit trails for all trade intents, policy decisions, and execution outcomes.
Brain-first journaling of trading system events with structured data.
"""

from __future__ import annotations

import logging
import os
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any


logger = logging.getLogger(__name__)

# Environment configuration
BRAIN_JOURNALING_ENABLED = bool(int(os.getenv("BRAIN_JOURNALING_ENABLED", "1")))
EVENT_RETENTION_DAYS = int(os.getenv("EVENT_RETENTION_DAYS", "90"))

# Try to import brain components
try:
    from app.memory.events import append_event, get_recent_events

    BRAIN_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Brain components not available: {e}")
    BRAIN_AVAILABLE = False

    def append_event(event_data: dict[str, Any]) -> str:
        """Mock event appender for development."""
        logger.info(f"Mock event: {event_data.get('kind', 'unknown')}")
        return f"mock_event_{datetime.now().timestamp()}"

    def get_recent_events(limit: int = 100, kind: str = None) -> list[dict[str, Any]]:
        """Mock event retrieval for development."""
        return []


@dataclass
class TradeEvent:
    """Base class for all trading events."""

    kind: str = ""
    timestamp: str = ""
    session_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TradeIntentEvent:
    """Trade intent with request parameters."""

    kind: str = ""
    timestamp: str = ""
    session_id: str | None = None
    symbol: str = ""
    side: str = ""
    quantity: float = 0.0
    order_type: str = ""
    client_id: str | None = None
    regime: str | None = None
    confidence: float | None = None
    request_params: dict[str, Any] | None = None

    def __post_init__(self):
        if not self.kind:
            self.kind = "trade_intent"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# Apply similar pattern to all dataclasses - remove inheritance and give all fields defaults


@dataclass
class PolicyCheckEvent:
    """Policy engine validation result."""

    kind: str = ""
    timestamp: str = ""
    session_id: str | None = None
    intent_id: str = ""
    symbol: str = ""
    policy_result: dict[str, Any] | None = None
    check_details: dict[str, Any] | None = None
    violations: list[str] | None = None
    allowed: bool = False

    def __post_init__(self):
        if not self.kind:
            self.kind = "policy_check"
        if self.policy_result is None:
            self.policy_result = {}
        if self.check_details is None:
            self.check_details = {}
        if self.violations is None:
            self.violations = []

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GuardrailCheckEvent:
    """Guardrail system validation result."""

    kind: str = ""
    timestamp: str = ""
    session_id: str | None = None
    intent_id: str = ""
    symbol: str = ""
    guardrail_result: dict[str, Any] | None = None
    risk_metrics: dict[str, Any] | None = None
    violations: list[str] | None = None
    allowed: bool = False

    def __post_init__(self):
        if not self.kind:
            self.kind = "guardrail_check"
        if self.guardrail_result is None:
            self.guardrail_result = {}
        if self.risk_metrics is None:
            self.risk_metrics = {}
        if self.violations is None:
            self.violations = []

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TradeSubmitEvent(TradeEvent):
    """Trade submission to execution layer."""

    intent_id: str
    order_id: str
    symbol: str
    execution_details: dict[str, Any]
    estimated_fee: float | None = None
    venue: str | None = None

    def __post_init__(self):
        if not self.kind:
            self.kind = "trade_submit"


@dataclass
class TradeFillEvent(TradeEvent):
    """Trade execution fill notification."""

    order_id: str
    fill_id: str
    symbol: str
    quantity_filled: float
    price: float
    fee: float
    venue: str
    is_partial: bool
    remaining_quantity: float

    def __post_init__(self):
        if not self.kind:
            self.kind = "trade_fill"


@dataclass
class PanicEvent(TradeEvent):
    """Emergency panic activation."""

    trigger_reason: str
    positions_count: int
    orders_count: int
    timeout_seconds: int

    def __post_init__(self):
        if not self.kind:
            self.kind = "panic_activate"


@dataclass
class PanicCompleteEvent(TradeEvent):
    """Panic procedure completion."""

    panic_id: str
    success: bool
    flattened_in_seconds: float
    positions_closed: int
    orders_canceled: int
    error_details: dict[str, Any] | None = None

    def __post_init__(self):
        if not self.kind:
            self.kind = "panic_complete"


@dataclass
class QualityUpdateEvent(TradeEvent):
    """Execution quality metrics update."""

    order_id: str
    symbol: str
    venue: str
    slippage_bps: float
    execution_time_ms: int
    against_benchmark: str
    quality_score: float

    def __post_init__(self):
        if not self.kind:
            self.kind = "quality_update"


class TradingBrainJournal:
    """
    Brain integration for trading system events.

    Provides structured logging of all trading activities for audit trails,
    performance analysis, and regulatory compliance.
    """

    def __init__(self):
        self.enabled = BRAIN_JOURNALING_ENABLED and BRAIN_AVAILABLE
        self.session_id = f"trading_session_{datetime.now().timestamp()}"

        if self.enabled:
            self._log_session_start()

    def _log_session_start(self):
        """Log the start of a trading session."""
        session_event = {
            "kind": "trading_session_start",
            "session_id": self.session_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "environment": {
                "trading_enabled": bool(int(os.getenv("TRADING_ENABLED", "0"))),
                "brain_journaling": self.enabled,
                "retention_days": EVENT_RETENTION_DAYS,
            },
        }

        if self.enabled:
            append_event(session_event)

    def log_trade_intent(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = "market",
        client_id: str | None = None,
        regime: str | None = None,
        confidence: float | None = None,
        request_params: dict[str, Any] | None = None,
    ) -> str:
        """Log a trade intent event."""
        event = TradeIntentEvent(
            kind="trade_intent",
            timestamp=datetime.now(UTC).isoformat(),
            session_id=self.session_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=order_type,
            client_id=client_id,
            regime=regime,
            confidence=confidence,
            request_params=request_params or {},
        )

        if self.enabled:
            return append_event(event.to_dict())
        else:
            logger.info(f"Trade intent: {symbol} {side} {quantity}")
            return f"mock_intent_{datetime.now().timestamp()}"

    def log_policy_check(
        self,
        intent_id: str,
        symbol: str,
        policy_result: dict[str, Any],
        check_details: dict[str, Any],
        violations: list[str],
        allowed: bool,
    ) -> str:
        """Log a policy check result."""
        event = PolicyCheckEvent(
            kind="policy_check",
            timestamp=datetime.now(UTC).isoformat(),
            session_id=self.session_id,
            intent_id=intent_id,
            symbol=symbol,
            policy_result=policy_result,
            check_details=check_details,
            violations=violations,
            allowed=allowed,
        )

        if self.enabled:
            return append_event(event.to_dict())
        else:
            logger.info(f"Policy check: {symbol} {'ALLOWED' if allowed else 'BLOCKED'}")
            return f"mock_policy_{datetime.now().timestamp()}"

    def log_guardrail_check(
        self,
        intent_id: str,
        symbol: str,
        guardrail_result: dict[str, Any],
        risk_metrics: dict[str, Any],
        violations: list[str],
        allowed: bool,
    ) -> str:
        """Log a guardrail check result."""
        event = GuardrailCheckEvent(
            kind="guardrail_check",
            timestamp=datetime.now(UTC).isoformat(),
            session_id=self.session_id,
            intent_id=intent_id,
            symbol=symbol,
            guardrail_result=guardrail_result,
            risk_metrics=risk_metrics,
            violations=violations,
            allowed=allowed,
        )

        if self.enabled:
            return append_event(event.to_dict())
        else:
            logger.info(f"Guardrail check: {symbol} {'ALLOWED' if allowed else 'BLOCKED'}")
            return f"mock_guardrail_{datetime.now().timestamp()}"

    def log_trade_submit(
        self,
        intent_id: str,
        order_id: str,
        symbol: str,
        execution_details: dict[str, Any],
        estimated_fee: float | None = None,
        venue: str | None = None,
    ) -> str:
        """Log a trade submission to execution."""
        event = TradeSubmitEvent(
            kind="trade_submit",
            timestamp=datetime.now(UTC).isoformat(),
            session_id=self.session_id,
            intent_id=intent_id,
            order_id=order_id,
            symbol=symbol,
            execution_details=execution_details,
            estimated_fee=estimated_fee,
            venue=venue,
        )

        if self.enabled:
            return append_event(event.to_dict())
        else:
            logger.info(f"Trade submit: {order_id} for {symbol}")
            return f"mock_submit_{datetime.now().timestamp()}"

    def log_trade_fill(
        self,
        order_id: str,
        fill_id: str,
        symbol: str,
        quantity_filled: float,
        price: float,
        fee: float,
        venue: str,
        is_partial: bool = False,
        remaining_quantity: float = 0.0,
    ) -> str:
        """Log a trade execution fill."""
        event = TradeFillEvent(
            kind="trade_fill",
            timestamp=datetime.now(UTC).isoformat(),
            session_id=self.session_id,
            order_id=order_id,
            fill_id=fill_id,
            symbol=symbol,
            quantity_filled=quantity_filled,
            price=price,
            fee=fee,
            venue=venue,
            is_partial=is_partial,
            remaining_quantity=remaining_quantity,
        )

        if self.enabled:
            return append_event(event.to_dict())
        else:
            logger.info(f"Trade fill: {fill_id} {quantity_filled}@{price} for {symbol}")
            return f"mock_fill_{datetime.now().timestamp()}"

    def log_panic_activate(
        self, trigger_reason: str, positions_count: int, orders_count: int, timeout_seconds: int
    ) -> str:
        """Log emergency panic activation."""
        event = PanicEvent(
            kind="panic_activate",
            timestamp=datetime.now(UTC).isoformat(),
            session_id=self.session_id,
            trigger_reason=trigger_reason,
            positions_count=positions_count,
            orders_count=orders_count,
            timeout_seconds=timeout_seconds,
        )

        if self.enabled:
            return append_event(event.to_dict())
        else:
            logger.critical(f"PANIC ACTIVATED: {trigger_reason}")
            return f"mock_panic_{datetime.now().timestamp()}"

    def log_panic_complete(
        self,
        panic_id: str,
        success: bool,
        flattened_in_seconds: float,
        positions_closed: int,
        orders_canceled: int,
        error_details: dict[str, Any] | None = None,
    ) -> str:
        """Log panic procedure completion."""
        event = PanicCompleteEvent(
            kind="panic_complete",
            timestamp=datetime.now(UTC).isoformat(),
            session_id=self.session_id,
            panic_id=panic_id,
            success=success,
            flattened_in_seconds=flattened_in_seconds,
            positions_closed=positions_closed,
            orders_canceled=orders_canceled,
            error_details=error_details,
        )

        if self.enabled:
            return append_event(event.to_dict())
        else:
            status = "SUCCESS" if success else "FAILED"
            logger.critical(f"PANIC COMPLETE: {status} in {flattened_in_seconds:.2f}s")
            return f"mock_panic_complete_{datetime.now().timestamp()}"

    def log_quality_update(
        self,
        order_id: str,
        symbol: str,
        venue: str,
        slippage_bps: float,
        execution_time_ms: int,
        against_benchmark: str = "mid",
        quality_score: float = 0.0,
    ) -> str:
        """Log execution quality metrics update."""
        event = QualityUpdateEvent(
            kind="quality_update",
            timestamp=datetime.now(UTC).isoformat(),
            session_id=self.session_id,
            order_id=order_id,
            symbol=symbol,
            venue=venue,
            slippage_bps=slippage_bps,
            execution_time_ms=execution_time_ms,
            against_benchmark=against_benchmark,
            quality_score=quality_score,
        )

        if self.enabled:
            return append_event(event.to_dict())
        else:
            logger.info(f"Quality update: {symbol} slippage {slippage_bps:.1f}bps on {venue}")
            return f"mock_quality_{datetime.now().timestamp()}"

    def get_trading_history(
        self, symbol: str | None = None, limit: int = 100, event_kinds: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """Get recent trading events for analysis."""
        if not self.enabled:
            return []

        try:
            # Get recent events and filter by trading events
            events = get_recent_events(limit=limit * 2)  # Get more to account for filtering

            trading_events = []
            for event in events:
                # Filter by event kind
                if event_kinds and event.get("kind") not in event_kinds:
                    continue

                # Filter by symbol
                if symbol and event.get("symbol") != symbol:
                    continue

                # Only include trading-related events
                if event.get("kind", "").startswith(
                    ("trade_", "policy_", "guardrail_", "panic_", "quality_")
                ):
                    trading_events.append(event)

                if len(trading_events) >= limit:
                    break

            return trading_events

        except Exception as e:
            logger.error(f"Failed to get trading history: {e}")
            return []

    def get_audit_trail(self, order_id: str) -> list[dict[str, Any]]:
        """Get complete audit trail for a specific order."""
        if not self.enabled:
            return []

        try:
            # Get all events and filter by order_id or related fields
            events = get_recent_events(limit=1000)

            audit_trail = []
            for event in events:
                # Check if event is related to this order
                if (
                    event.get("order_id") == order_id
                    or event.get("intent_id") == order_id
                    or any(order_id in str(v) for v in event.values() if isinstance(v, (str, dict)))
                ):
                    audit_trail.append(event)

            # Sort by timestamp
            audit_trail.sort(key=lambda x: x.get("timestamp", ""))

            return audit_trail

        except Exception as e:
            logger.error(f"Failed to get audit trail for {order_id}: {e}")
            return []


# Global journal instance
trading_journal = TradingBrainJournal()


def get_journal() -> TradingBrainJournal:
    """Get the global trading journal instance."""
    return trading_journal
