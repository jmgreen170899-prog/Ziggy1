"""
Global Guardrails - Action & Execution Layer

Mission: Safety ↑, slippage ↓
Budget caps by day/week; max concurrent risk; kill-switches by regime.
Industrial-grade risk management with audit trails and emergency controls.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)

# Environment configuration
MAX_DD_DAY = float(os.getenv("MAX_DD_DAY", "0.03"))  # 3% daily drawdown
MAX_DD_WEEK = float(os.getenv("MAX_DD_WEEK", "0.06"))  # 6% weekly drawdown
MAX_EXPOSURE = float(os.getenv("MAX_EXPOSURE", "1.50"))  # 150% gross exposure
MAX_SINGLE_TRADE_RISK = float(
    os.getenv("MAX_SINGLE_TRADE_RISK", "0.01")
)  # 1% per trade
MAX_DAILY_TRADES = int(os.getenv("MAX_DAILY_TRADES", "100"))
MAX_CONCURRENT_ORDERS = int(os.getenv("MAX_CONCURRENT_ORDERS", "50"))

# Portfolio configuration
INITIAL_PORTFOLIO_VALUE = float(os.getenv("INITIAL_PORTFOLIO_VALUE", "1000000"))  # $1M
MIN_CASH_RESERVE = float(os.getenv("MIN_CASH_RESERVE", "0.05"))  # 5% cash reserve

# Regime-based controls
REGIME_KILL_SWITCHES = os.getenv(
    "REGIME_KILL_SWITCHES", "crash_mode,vol_hi_liq_lo"
).split(",")
REGIME_EXPOSURE_LIMITS = json.loads(
    os.getenv("REGIME_EXPOSURE_LIMITS", '{"vol_hi": 0.75, "liq_lo": 0.50}')
)

# Data persistence
GUARDRAILS_DATA_PATH = os.getenv("GUARDRAILS_DATA_PATH", "data/trading/guardrails.json")


class GuardrailViolation(Enum):
    """Types of guardrail violations."""

    DAILY_DRAWDOWN_EXCEEDED = "daily_drawdown_exceeded"
    WEEKLY_DRAWDOWN_EXCEEDED = "weekly_drawdown_exceeded"
    EXPOSURE_LIMIT_EXCEEDED = "exposure_limit_exceeded"
    SINGLE_TRADE_RISK_EXCEEDED = "single_trade_risk_exceeded"
    DAILY_TRADE_LIMIT_EXCEEDED = "daily_trade_limit_exceeded"
    CONCURRENT_ORDER_LIMIT_EXCEEDED = "concurrent_order_limit_exceeded"
    CASH_RESERVE_INSUFFICIENT = "cash_reserve_insufficient"
    REGIME_KILL_SWITCH_ACTIVE = "regime_kill_switch_active"
    REGIME_EXPOSURE_LIMIT_EXCEEDED = "regime_exposure_limit_exceeded"


@dataclass
class RiskMetrics:
    """Current risk and exposure metrics."""

    portfolio_value: float = INITIAL_PORTFOLIO_VALUE
    cash_balance: float = 0.0
    gross_exposure: float = 0.0
    net_exposure: float = 0.0
    daily_pnl: float = 0.0
    weekly_pnl: float = 0.0
    daily_trades: int = 0
    concurrent_orders: int = 0
    last_updated: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def gross_exposure_ratio(self) -> float:
        """Calculate gross exposure as ratio of portfolio value."""
        return self.gross_exposure / max(self.portfolio_value, 1.0)

    def net_exposure_ratio(self) -> float:
        """Calculate net exposure as ratio of portfolio value."""
        return abs(self.net_exposure) / max(self.portfolio_value, 1.0)

    def daily_drawdown(self) -> float:
        """Calculate daily drawdown ratio."""
        return abs(min(self.daily_pnl, 0.0)) / max(self.portfolio_value, 1.0)

    def weekly_drawdown(self) -> float:
        """Calculate weekly drawdown ratio."""
        return abs(min(self.weekly_pnl, 0.0)) / max(self.portfolio_value, 1.0)

    def cash_reserve_ratio(self) -> float:
        """Calculate cash reserve ratio."""
        return self.cash_balance / max(self.portfolio_value, 1.0)


@dataclass
class GuardrailCheck:
    """Result of guardrail validation."""

    allowed: bool
    violations: list[GuardrailViolation]
    risk_metrics: RiskMetrics
    check_details: dict[str, Any]
    check_timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API/logging."""
        return {
            "allowed": self.allowed,
            "violations": [v.value for v in self.violations],
            "risk_metrics": {
                "portfolio_value": self.risk_metrics.portfolio_value,
                "gross_exposure": self.risk_metrics.gross_exposure,
                "net_exposure": self.risk_metrics.net_exposure,
                "gross_exposure_ratio": self.risk_metrics.gross_exposure_ratio(),
                "net_exposure_ratio": self.risk_metrics.net_exposure_ratio(),
                "daily_pnl": self.risk_metrics.daily_pnl,
                "weekly_pnl": self.risk_metrics.weekly_pnl,
                "daily_drawdown": self.risk_metrics.daily_drawdown(),
                "weekly_drawdown": self.risk_metrics.weekly_drawdown(),
                "daily_trades": self.risk_metrics.daily_trades,
                "concurrent_orders": self.risk_metrics.concurrent_orders,
                "cash_balance": self.risk_metrics.cash_balance,
                "cash_reserve_ratio": self.risk_metrics.cash_reserve_ratio(),
            },
            "check_details": self.check_details,
            "check_timestamp": self.check_timestamp,
        }


class GuardrailSystem:
    """
    Global guardrail system for risk management.

    Enforces:
    - Daily/weekly drawdown limits
    - Exposure limits (gross/net)
    - Per-trade risk limits
    - Trade count limits
    - Cash reserve requirements
    - Regime-based restrictions
    """

    def __init__(self):
        self.current_metrics = RiskMetrics()
        self.violation_count = 0
        self.check_count = 0
        self.emergency_stop = False
        self._load_state()

    def check_trade(
        self, symbol: str, quantity: float, estimated_price: float, regime: str = "base"
    ) -> GuardrailCheck:
        """
        Check if a trade is allowed under current risk limits.

        Args:
            symbol: Trading symbol
            quantity: Shares to trade (positive=buy, negative=sell)
            estimated_price: Estimated execution price
            regime: Current market regime

        Returns:
            GuardrailCheck with allowed/blocked decision and details
        """
        self.check_count += 1
        violations = []
        check_details = {}

        try:
            # Calculate trade impact
            trade_value = abs(quantity * estimated_price)
            is_opening = self._is_opening_trade(symbol, quantity)

            # 1. Check daily drawdown limit
            dd_check = self._check_daily_drawdown()
            check_details["daily_drawdown"] = dd_check
            if not dd_check["ok"]:
                violations.append(GuardrailViolation.DAILY_DRAWDOWN_EXCEEDED)

            # 2. Check weekly drawdown limit
            wd_check = self._check_weekly_drawdown()
            check_details["weekly_drawdown"] = wd_check
            if not wd_check["ok"]:
                violations.append(GuardrailViolation.WEEKLY_DRAWDOWN_EXCEEDED)

            # 3. Check exposure limits
            exposure_check = self._check_exposure_limits(
                symbol, quantity, estimated_price
            )
            check_details["exposure"] = exposure_check
            if not exposure_check["ok"]:
                violations.append(GuardrailViolation.EXPOSURE_LIMIT_EXCEEDED)

            # 4. Check single trade risk
            risk_check = self._check_single_trade_risk(trade_value)
            check_details["single_trade_risk"] = risk_check
            if not risk_check["ok"]:
                violations.append(GuardrailViolation.SINGLE_TRADE_RISK_EXCEEDED)

            # 5. Check daily trade limit
            trade_limit_check = self._check_daily_trade_limit()
            check_details["daily_trades"] = trade_limit_check
            if not trade_limit_check["ok"]:
                violations.append(GuardrailViolation.DAILY_TRADE_LIMIT_EXCEEDED)

            # 6. Check concurrent order limit
            order_limit_check = self._check_concurrent_order_limit()
            check_details["concurrent_orders"] = order_limit_check
            if not order_limit_check["ok"]:
                violations.append(GuardrailViolation.CONCURRENT_ORDER_LIMIT_EXCEEDED)

            # 7. Check cash reserve (for buy orders)
            if quantity > 0 and is_opening:  # Opening buy position
                cash_check = self._check_cash_reserve(trade_value)
                check_details["cash_reserve"] = cash_check
                if not cash_check["ok"]:
                    violations.append(GuardrailViolation.CASH_RESERVE_INSUFFICIENT)

            # 8. Check regime restrictions
            regime_check = self._check_regime_restrictions(regime, symbol, quantity)
            check_details["regime"] = regime_check
            if not regime_check["ok"]:
                if regime_check.get("kill_switch_active"):
                    violations.append(GuardrailViolation.REGIME_KILL_SWITCH_ACTIVE)
                if regime_check.get("exposure_limit_exceeded"):
                    violations.append(GuardrailViolation.REGIME_EXPOSURE_LIMIT_EXCEEDED)

            # 9. Emergency stop check
            check_details["emergency_stop"] = {"active": self.emergency_stop}
            if self.emergency_stop:
                violations.append(GuardrailViolation.REGIME_KILL_SWITCH_ACTIVE)

            # Compile result
            allowed = len(violations) == 0
            if not allowed:
                self.violation_count += 1

            return GuardrailCheck(
                allowed=allowed,
                violations=violations,
                risk_metrics=self.current_metrics,
                check_details=check_details,
            )

        except Exception as e:
            logger.error(f"Guardrail check failed: {e}")
            self.violation_count += 1
            return GuardrailCheck(
                allowed=False,
                violations=[GuardrailViolation.DAILY_DRAWDOWN_EXCEEDED],  # Fail safe
                risk_metrics=self.current_metrics,
                check_details={"error": str(e)},
            )

    def _check_daily_drawdown(self) -> dict[str, Any]:
        """Check daily drawdown limit."""
        current_dd = self.current_metrics.daily_drawdown()
        ok = current_dd <= MAX_DD_DAY

        return {
            "ok": ok,
            "current_drawdown": current_dd,
            "max_allowed": MAX_DD_DAY,
            "daily_pnl": self.current_metrics.daily_pnl,
            "portfolio_value": self.current_metrics.portfolio_value,
        }

    def _check_weekly_drawdown(self) -> dict[str, Any]:
        """Check weekly drawdown limit."""
        current_wd = self.current_metrics.weekly_drawdown()
        ok = current_wd <= MAX_DD_WEEK

        return {
            "ok": ok,
            "current_drawdown": current_wd,
            "max_allowed": MAX_DD_WEEK,
            "weekly_pnl": self.current_metrics.weekly_pnl,
            "portfolio_value": self.current_metrics.portfolio_value,
        }

    def _check_exposure_limits(
        self, symbol: str, quantity: float, price: float
    ) -> dict[str, Any]:
        """Check exposure limits after proposed trade."""
        trade_value = quantity * price  # Signed value

        # Estimate new exposure (simplified)
        new_gross = self.current_metrics.gross_exposure + abs(trade_value)
        new_net = self.current_metrics.net_exposure + trade_value

        gross_ratio = new_gross / self.current_metrics.portfolio_value
        net_ratio = abs(new_net) / self.current_metrics.portfolio_value

        ok = gross_ratio <= MAX_EXPOSURE

        return {
            "ok": ok,
            "current_gross_exposure": self.current_metrics.gross_exposure,
            "current_net_exposure": self.current_metrics.net_exposure,
            "projected_gross_exposure": new_gross,
            "projected_net_exposure": new_net,
            "projected_gross_ratio": gross_ratio,
            "projected_net_ratio": net_ratio,
            "max_exposure_ratio": MAX_EXPOSURE,
            "trade_value": trade_value,
        }

    def _check_single_trade_risk(self, trade_value: float) -> dict[str, Any]:
        """Check single trade risk limit."""
        risk_ratio = trade_value / self.current_metrics.portfolio_value
        ok = risk_ratio <= MAX_SINGLE_TRADE_RISK

        return {
            "ok": ok,
            "trade_value": trade_value,
            "risk_ratio": risk_ratio,
            "max_risk_ratio": MAX_SINGLE_TRADE_RISK,
            "portfolio_value": self.current_metrics.portfolio_value,
        }

    def _check_daily_trade_limit(self) -> dict[str, Any]:
        """Check daily trade count limit."""
        ok = self.current_metrics.daily_trades < MAX_DAILY_TRADES

        return {
            "ok": ok,
            "current_trades": self.current_metrics.daily_trades,
            "max_trades": MAX_DAILY_TRADES,
            "remaining": max(0, MAX_DAILY_TRADES - self.current_metrics.daily_trades),
        }

    def _check_concurrent_order_limit(self) -> dict[str, Any]:
        """Check concurrent order limit."""
        ok = self.current_metrics.concurrent_orders < MAX_CONCURRENT_ORDERS

        return {
            "ok": ok,
            "current_orders": self.current_metrics.concurrent_orders,
            "max_orders": MAX_CONCURRENT_ORDERS,
            "remaining": max(
                0, MAX_CONCURRENT_ORDERS - self.current_metrics.concurrent_orders
            ),
        }

    def _check_cash_reserve(self, required_cash: float) -> dict[str, Any]:
        """Check cash reserve requirements."""
        min_cash_required = self.current_metrics.portfolio_value * MIN_CASH_RESERVE
        available_cash = self.current_metrics.cash_balance - required_cash
        ok = available_cash >= min_cash_required

        return {
            "ok": ok,
            "current_cash": self.current_metrics.cash_balance,
            "required_for_trade": required_cash,
            "available_after_trade": available_cash,
            "min_required": min_cash_required,
            "reserve_ratio": MIN_CASH_RESERVE,
        }

    def _check_regime_restrictions(
        self, regime: str, symbol: str, quantity: float
    ) -> dict[str, Any]:
        """Check regime-based trading restrictions."""
        regime_lower = regime.lower().strip()

        # Check kill switches
        kill_switch_active = any(
            ks.strip().lower() in regime_lower
            for ks in REGIME_KILL_SWITCHES
            if ks.strip()
        )

        # Check regime exposure limits
        exposure_limit_exceeded = False
        applicable_limit = None

        for regime_pattern, limit in REGIME_EXPOSURE_LIMITS.items():
            if regime_pattern.lower() in regime_lower:
                current_ratio = self.current_metrics.gross_exposure_ratio()
                if current_ratio > limit:
                    exposure_limit_exceeded = True
                    applicable_limit = limit
                    break

        ok = not kill_switch_active and not exposure_limit_exceeded

        return {
            "ok": ok,
            "regime": regime,
            "kill_switch_active": kill_switch_active,
            "exposure_limit_exceeded": exposure_limit_exceeded,
            "applicable_limit": applicable_limit,
            "current_exposure_ratio": self.current_metrics.gross_exposure_ratio(),
            "regime_kill_switches": REGIME_KILL_SWITCHES,
            "regime_exposure_limits": REGIME_EXPOSURE_LIMITS,
        }

    def _is_opening_trade(self, symbol: str, quantity: float) -> bool:
        """Determine if trade is opening a new position (simplified)."""
        # TODO: Integrate with actual position tracking
        # For now, assume all trades are opening
        return True

    def update_metrics(
        self,
        portfolio_value: float | None = None,
        cash_balance: float | None = None,
        gross_exposure: float | None = None,
        net_exposure: float | None = None,
        daily_pnl: float | None = None,
        weekly_pnl: float | None = None,
        concurrent_orders: int | None = None,
    ) -> None:
        """Update current risk metrics."""
        if portfolio_value is not None:
            self.current_metrics.portfolio_value = portfolio_value
        if cash_balance is not None:
            self.current_metrics.cash_balance = cash_balance
        if gross_exposure is not None:
            self.current_metrics.gross_exposure = gross_exposure
        if net_exposure is not None:
            self.current_metrics.net_exposure = net_exposure
        if daily_pnl is not None:
            self.current_metrics.daily_pnl = daily_pnl
        if weekly_pnl is not None:
            self.current_metrics.weekly_pnl = weekly_pnl
        if concurrent_orders is not None:
            self.current_metrics.concurrent_orders = concurrent_orders

        self.current_metrics.last_updated = datetime.now(UTC).isoformat()
        self._save_state()

    def record_trade(self) -> None:
        """Record a trade execution for daily limit tracking."""
        self.current_metrics.daily_trades += 1
        self._save_state()

    def reset_daily_metrics(self) -> None:
        """Reset daily metrics (called at start of new trading day)."""
        self.current_metrics.daily_trades = 0
        self.current_metrics.daily_pnl = 0.0
        self._save_state()

    def reset_weekly_metrics(self) -> None:
        """Reset weekly metrics (called at start of new trading week)."""
        self.current_metrics.weekly_pnl = 0.0
        self._save_state()

    def activate_emergency_stop(self, reason: str = "Manual activation") -> None:
        """Activate emergency stop - blocks all new trades."""
        self.emergency_stop = True
        logger.critical(f"EMERGENCY STOP ACTIVATED: {reason}")
        self._save_state()

    def deactivate_emergency_stop(self) -> None:
        """Deactivate emergency stop."""
        self.emergency_stop = False
        logger.info("Emergency stop deactivated")
        self._save_state()

    def get_stats(self) -> dict[str, Any]:
        """Get guardrail system statistics."""
        violation_rate = self.violation_count / max(self.check_count, 1)

        return {
            "check_count": self.check_count,
            "violation_count": self.violation_count,
            "violation_rate": violation_rate,
            "emergency_stop": self.emergency_stop,
            "current_metrics": self.current_metrics.__dict__,
            "limits": {
                "max_dd_day": MAX_DD_DAY,
                "max_dd_week": MAX_DD_WEEK,
                "max_exposure": MAX_EXPOSURE,
                "max_single_trade_risk": MAX_SINGLE_TRADE_RISK,
                "max_daily_trades": MAX_DAILY_TRADES,
                "max_concurrent_orders": MAX_CONCURRENT_ORDERS,
                "min_cash_reserve": MIN_CASH_RESERVE,
            },
        }

    def _save_state(self) -> None:
        """Save current state to disk."""
        try:
            data = {
                "metrics": self.current_metrics.__dict__,
                "violation_count": self.violation_count,
                "check_count": self.check_count,
                "emergency_stop": self.emergency_stop,
                "saved_at": datetime.now(UTC).isoformat(),
            }

            Path(GUARDRAILS_DATA_PATH).parent.mkdir(parents=True, exist_ok=True)
            with open(GUARDRAILS_DATA_PATH, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save guardrail state: {e}")

    def _load_state(self) -> None:
        """Load state from disk."""
        try:
            if Path(GUARDRAILS_DATA_PATH).exists():
                with open(GUARDRAILS_DATA_PATH) as f:
                    data = json.load(f)

                # Load metrics
                metrics_data = data.get("metrics", {})
                for key, value in metrics_data.items():
                    if hasattr(self.current_metrics, key):
                        setattr(self.current_metrics, key, value)

                # Load counters
                self.violation_count = data.get("violation_count", 0)
                self.check_count = data.get("check_count", 0)
                self.emergency_stop = data.get("emergency_stop", False)

                logger.info("Loaded guardrail state from disk")

        except Exception as e:
            logger.warning(f"Failed to load guardrail state: {e}")


# Global guardrail system instance
guardrail_system = GuardrailSystem()


# Convenience functions
def check_trade_allowed(
    symbol: str, quantity: float, estimated_price: float, regime: str = "base"
) -> tuple[bool, str, dict[str, Any]]:
    """
    Check if trade is allowed under guardrails.

    Returns:
        Tuple of (allowed, reason, details)
    """
    result = guardrail_system.check_trade(symbol, quantity, estimated_price, regime)
    reason = "ok" if result.allowed else "; ".join([v.value for v in result.violations])
    return result.allowed, reason, result.to_dict()


def update_risk_metrics(**kwargs) -> None:
    """Update current risk metrics."""
    guardrail_system.update_metrics(**kwargs)


def record_trade_execution() -> None:
    """Record a trade execution."""
    guardrail_system.record_trade()


def get_guardrail_stats() -> dict[str, Any]:
    """Get guardrail statistics."""
    return guardrail_system.get_stats()


def emergency_stop(reason: str = "API call") -> None:
    """Activate emergency stop."""
    guardrail_system.activate_emergency_stop(reason)


def resume_trading() -> None:
    """Deactivate emergency stop."""
    guardrail_system.deactivate_emergency_stop()
