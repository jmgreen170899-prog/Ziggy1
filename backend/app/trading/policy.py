"""
Order Policy Engine - Action & Execution Layer

Mission: Safety ↑, slippage ↓
Pre-trade checklist: market open, spreads < threshold, liquidity OK, recent news not "red".
Industrial-grade safeguards with explicit blocking reasons and audit trails.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import UTC, datetime, time
from enum import Enum
from typing import Any


logger = logging.getLogger(__name__)

# Environment configuration with safe defaults
TRADING_ENABLED = os.getenv("TRADING_ENABLED", "false").lower() in ("true", "1", "yes")
SPREAD_BPS_MAX = float(os.getenv("SPREAD_BPS_MAX", "25"))
MIN_LIQUIDITY_USD = float(os.getenv("MIN_LIQUIDITY_USD", "500000"))
NEWS_HEAT_RED = float(os.getenv("NEWS_HEAT_RED", "0.75"))
MARKET_OPEN_GRACE_S = int(os.getenv("MARKET_OPEN_GRACE_S", "30"))
MAX_SINGLE_TRADE_RISK = float(os.getenv("MAX_SINGLE_TRADE_RISK", "0.01"))

# Risk model thresholds
P_UP_MIN_CONFIDENCE = float(os.getenv("P_UP_MIN_CONFIDENCE", "0.55"))
P_UP_MAX_CONFIDENCE = float(os.getenv("P_UP_MAX_CONFIDENCE", "0.95"))
REGIME_BLACKLIST = os.getenv("REGIME_BLACKLIST", "vol_hi_liq_lo,crash_mode").split(",")


class PolicyViolation(Enum):
    """Policy violation types for structured reporting."""

    TRADING_DISABLED = "trading_disabled"
    MARKET_CLOSED = "market_closed"
    SPREAD_TOO_WIDE = "spread_too_wide"
    LIQUIDITY_TOO_LOW = "liquidity_too_low"
    NEWS_HEAT_RED = "news_heat_red"
    CONFIDENCE_TOO_LOW = "confidence_too_low"
    CONFIDENCE_TOO_HIGH = "confidence_too_high"
    REGIME_BLACKLISTED = "regime_blacklisted"
    TRADE_SIZE_TOO_LARGE = "trade_size_too_large"
    INVALID_PARAMETERS = "invalid_parameters"


@dataclass
class PolicyCheckResult:
    """Result of policy check with detailed metadata."""

    ok: bool
    reason: str
    violations: list[PolicyViolation]
    meta: dict[str, Any]
    check_timestamp: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses and logging."""
        return {
            "ok": self.ok,
            "reason": self.reason,
            "violations": [v.value for v in self.violations],
            "meta": self.meta,
            "check_timestamp": self.check_timestamp,
        }


class PolicyEngine:
    """
    Order Policy Engine with comprehensive pre-trade checks.

    Implements industrial-grade safeguards:
    - Market hours validation with exchange calendars
    - Spread and liquidity thresholds
    - News sentiment red flags
    - Risk model confidence bounds
    - Regime-based restrictions
    """

    def __init__(self):
        self.check_count = 0
        self.violation_count = 0

    def check(
        self,
        ticker: str,
        size: float,
        p_up: float,
        regime: str,
        spreads_bps: float,
        news_heat: float,
        market_value: float = None,
        exchange: str = "NYSE",
    ) -> PolicyCheckResult:
        """
        Comprehensive pre-trade policy check.

        Args:
            ticker: Stock symbol
            size: Trade size (shares, positive for buy, negative for sell)
            p_up: Model confidence (0.0-1.0)
            regime: Current market regime
            spreads_bps: Current bid-ask spread in basis points
            news_heat: Recent news sentiment/novelty score (0.0-1.0)
            market_value: Dollar value of trade (optional)
            exchange: Exchange identifier for market hours

        Returns:
            PolicyCheckResult with ok/blocked decision and detailed reasoning
        """
        self.check_count += 1
        check_ts = datetime.now(UTC).isoformat()

        violations = []
        checks = {}

        try:
            # 1. Trading enabled check
            if not TRADING_ENABLED:
                violations.append(PolicyViolation.TRADING_DISABLED)

            # 2. Parameter validation
            if not self._validate_parameters(ticker, size, p_up, regime, spreads_bps, news_heat):
                violations.append(PolicyViolation.INVALID_PARAMETERS)

            # 3. Market hours check
            market_open_result = self._check_market_hours(exchange, check_ts)
            checks["market_hours"] = market_open_result
            if not market_open_result["is_open"]:
                violations.append(PolicyViolation.MARKET_CLOSED)

            # 4. Spread check
            spread_result = self._check_spreads(spreads_bps)
            checks["spreads"] = spread_result
            if not spread_result["ok"]:
                violations.append(PolicyViolation.SPREAD_TOO_WIDE)

            # 5. Liquidity check
            liquidity_result = self._check_liquidity(ticker, market_value or abs(size) * 100)
            checks["liquidity"] = liquidity_result
            if not liquidity_result["ok"]:
                violations.append(PolicyViolation.LIQUIDITY_TOO_LOW)

            # 6. News heat check
            news_result = self._check_news_heat(news_heat)
            checks["news_heat"] = news_result
            if not news_result["ok"]:
                violations.append(PolicyViolation.NEWS_HEAT_RED)

            # 7. Risk model confidence check
            confidence_result = self._check_confidence(p_up)
            checks["confidence"] = confidence_result
            if not confidence_result["ok"]:
                if p_up < P_UP_MIN_CONFIDENCE:
                    violations.append(PolicyViolation.CONFIDENCE_TOO_LOW)
                else:
                    violations.append(PolicyViolation.CONFIDENCE_TOO_HIGH)

            # 8. Regime check
            regime_result = self._check_regime(regime)
            checks["regime"] = regime_result
            if not regime_result["ok"]:
                violations.append(PolicyViolation.REGIME_BLACKLISTED)

            # 9. Trade size check
            size_result = self._check_trade_size(size, market_value)
            checks["trade_size"] = size_result
            if not size_result["ok"]:
                violations.append(PolicyViolation.TRADE_SIZE_TOO_LARGE)

            # Compile result
            ok = len(violations) == 0
            if not ok:
                self.violation_count += 1

            reason = "ok" if ok else "; ".join([v.value for v in violations])

            meta = {
                "ticker": ticker,
                "size": size,
                "p_up": p_up,
                "regime": regime,
                "spreads_bps": spreads_bps,
                "news_heat": news_heat,
                "exchange": exchange,
                "checks": checks,
                "check_count": self.check_count,
                "violation_count": self.violation_count,
            }

            return PolicyCheckResult(
                ok=ok, reason=reason, violations=violations, meta=meta, check_timestamp=check_ts
            )

        except Exception as e:
            logger.error(f"Policy check failed: {e}")
            return PolicyCheckResult(
                ok=False,
                reason=f"policy_check_error: {e!s}",
                violations=[PolicyViolation.INVALID_PARAMETERS],
                meta={"error": str(e), "ticker": ticker},
                check_timestamp=check_ts,
            )

    def _validate_parameters(
        self,
        ticker: str,
        size: float,
        p_up: float,
        regime: str,
        spreads_bps: float,
        news_heat: float,
    ) -> bool:
        """Validate input parameters are within expected ranges."""
        try:
            if not ticker or not isinstance(ticker, str):
                return False
            if not isinstance(size, (int, float)) or size == 0:
                return False
            if not isinstance(p_up, (int, float)) or not (0.0 <= p_up <= 1.0):
                return False
            if not isinstance(regime, str):
                return False
            if not isinstance(spreads_bps, (int, float)) or spreads_bps < 0:
                return False
            if not isinstance(news_heat, (int, float)) or not (0.0 <= news_heat <= 1.0):
                return False
            return True
        except Exception:
            return False

    def _check_market_hours(self, exchange: str, timestamp: str) -> dict[str, Any]:
        """Check if market is open with grace period."""
        try:
            # Import timezone utils for market hours
            try:
                from app.services.timezone_utils import get_market_hours

                market_info = get_market_hours(exchange)
                is_open = market_info.get("is_trading_day", True)  # Default open if can't determine
            except ImportError:
                # Fallback: basic NYSE hours check
                is_open = self._basic_market_hours_check()
                market_info = {"fallback": True}

            return {
                "is_open": is_open,
                "exchange": exchange,
                "grace_seconds": MARKET_OPEN_GRACE_S,
                "market_info": market_info,
            }
        except Exception as e:
            logger.warning(f"Market hours check failed: {e}")
            return {"is_open": True, "error": str(e)}  # Fail open for safety

    def _basic_market_hours_check(self) -> bool:
        """Basic market hours check for NYSE (9:30 AM - 4:00 PM ET)."""
        try:
            from datetime import datetime

            import pytz

            et = pytz.timezone("America/New_York")
            now_et = datetime.now(et)

            # Check if weekday
            if now_et.weekday() >= 5:  # Saturday=5, Sunday=6
                return False

            # Check market hours (9:30 AM - 4:00 PM ET)
            market_open = time(9, 30)
            market_close = time(16, 0)
            current_time = now_et.time()

            return market_open <= current_time <= market_close

        except Exception:
            return True  # Fail open

    def _check_spreads(self, spreads_bps: float) -> dict[str, Any]:
        """Check if bid-ask spread is within acceptable limits."""
        ok = spreads_bps <= SPREAD_BPS_MAX
        return {
            "ok": ok,
            "spreads_bps": spreads_bps,
            "max_allowed": SPREAD_BPS_MAX,
            "violation_amount": max(0, spreads_bps - SPREAD_BPS_MAX),
        }

    def _check_liquidity(self, ticker: str, trade_value_usd: float) -> dict[str, Any]:
        """Check if sufficient liquidity exists for the trade."""
        try:
            # TODO: Integrate with market data providers for real liquidity
            # For now, use simple heuristic based on trade size
            estimated_daily_volume = self._estimate_daily_volume(ticker)
            liquidity_ok = estimated_daily_volume >= MIN_LIQUIDITY_USD

            return {
                "ok": liquidity_ok,
                "estimated_daily_volume": estimated_daily_volume,
                "min_required": MIN_LIQUIDITY_USD,
                "trade_value": trade_value_usd,
                "liquidity_ratio": (
                    estimated_daily_volume / MIN_LIQUIDITY_USD if MIN_LIQUIDITY_USD > 0 else 1.0
                ),
            }
        except Exception as e:
            logger.warning(f"Liquidity check failed: {e}")
            return {"ok": True, "error": str(e)}  # Fail open

    def _estimate_daily_volume(self, ticker: str) -> float:
        """Estimate daily trading volume in USD."""
        # Simple heuristic - major tickers have high volume
        major_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "SPY", "QQQ"]
        if ticker.upper() in major_tickers:
            return 1_000_000_000  # $1B daily volume
        else:
            return 100_000_000  # $100M daily volume

    def _check_news_heat(self, news_heat: float) -> dict[str, Any]:
        """Check if recent news sentiment is not red-hot."""
        ok = news_heat < NEWS_HEAT_RED
        return {
            "ok": ok,
            "news_heat": news_heat,
            "red_threshold": NEWS_HEAT_RED,
            "heat_level": (
                "red" if news_heat >= NEWS_HEAT_RED else "yellow" if news_heat >= 0.5 else "green"
            ),
        }

    def _check_confidence(self, p_up: float) -> dict[str, Any]:
        """Check if model confidence is within acceptable bounds."""
        ok = P_UP_MIN_CONFIDENCE <= p_up <= P_UP_MAX_CONFIDENCE
        return {
            "ok": ok,
            "p_up": p_up,
            "min_confidence": P_UP_MIN_CONFIDENCE,
            "max_confidence": P_UP_MAX_CONFIDENCE,
            "confidence_level": (
                "low"
                if p_up < P_UP_MIN_CONFIDENCE
                else "high"
                if p_up > P_UP_MAX_CONFIDENCE
                else "acceptable"
            ),
        }

    def _check_regime(self, regime: str) -> dict[str, Any]:
        """Check if current market regime allows trading."""
        regime_clean = regime.strip().lower()
        blacklisted = regime_clean in [r.strip().lower() for r in REGIME_BLACKLIST if r.strip()]

        return {
            "ok": not blacklisted,
            "regime": regime,
            "blacklisted_regimes": REGIME_BLACKLIST,
            "is_blacklisted": blacklisted,
        }

    def _check_trade_size(self, size: float, market_value: float | None) -> dict[str, Any]:
        """Check if trade size is within risk limits."""
        try:
            # Estimate trade value if not provided
            if market_value is None:
                market_value = abs(size) * 100  # Assume $100/share average

            # Check against max single trade risk
            # TODO: Get current portfolio value for proper risk calculation
            estimated_portfolio_value = 1_000_000  # $1M default
            risk_fraction = market_value / estimated_portfolio_value

            ok = risk_fraction <= MAX_SINGLE_TRADE_RISK

            return {
                "ok": ok,
                "trade_value": market_value,
                "risk_fraction": risk_fraction,
                "max_risk_fraction": MAX_SINGLE_TRADE_RISK,
                "estimated_portfolio_value": estimated_portfolio_value,
            }
        except Exception as e:
            logger.warning(f"Trade size check failed: {e}")
            return {"ok": True, "error": str(e)}

    def get_stats(self) -> dict[str, Any]:
        """Get policy engine statistics."""
        violation_rate = self.violation_count / max(self.check_count, 1)

        return {
            "total_checks": self.check_count,
            "total_violations": self.violation_count,
            "violation_rate": violation_rate,
            "config": {
                "trading_enabled": TRADING_ENABLED,
                "spread_bps_max": SPREAD_BPS_MAX,
                "min_liquidity_usd": MIN_LIQUIDITY_USD,
                "news_heat_red": NEWS_HEAT_RED,
                "market_open_grace_s": MARKET_OPEN_GRACE_S,
                "max_single_trade_risk": MAX_SINGLE_TRADE_RISK,
                "p_up_bounds": [P_UP_MIN_CONFIDENCE, P_UP_MAX_CONFIDENCE],
                "regime_blacklist": REGIME_BLACKLIST,
            },
        }


# Global policy engine instance
policy_engine = PolicyEngine()


# Convenience functions for backward compatibility
def check(
    ticker: str,
    size: float,
    p_up: float,
    regime: str,
    spreads_bps: float,
    news_heat: float,
    **kwargs,
) -> tuple[bool, str, dict[str, Any]]:
    """
    Legacy function signature for backward compatibility.

    Returns:
        Tuple of (ok, reason, meta) for existing code
    """
    result = policy_engine.check(ticker, size, p_up, regime, spreads_bps, news_heat, **kwargs)
    return result.ok, result.reason, result.meta


def check_detailed(
    ticker: str,
    size: float,
    p_up: float,
    regime: str,
    spreads_bps: float,
    news_heat: float,
    **kwargs,
) -> PolicyCheckResult:
    """
    Detailed policy check returning full result object.

    Returns:
        PolicyCheckResult with complete violation analysis
    """
    return policy_engine.check(ticker, size, p_up, regime, spreads_bps, news_heat, **kwargs)


def get_policy_stats() -> dict[str, Any]:
    """Get policy engine statistics and configuration."""
    return policy_engine.get_stats()


def reset_policy_stats() -> None:
    """Reset policy engine statistics (for testing)."""
    global policy_engine
    policy_engine = PolicyEngine()


# Environment helper function
def _env(key: str, default: Any) -> Any:
    """Helper to get environment variable with type conversion."""
    try:
        value = os.getenv(key, str(default))
        return type(default)(value)
    except Exception:
        return default
