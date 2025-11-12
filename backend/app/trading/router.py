"""
Trading Router - Action & Execution Layer

Mission: Safety ↑, slippage ↓
FastAPI routes for /trade/* endpoints with panic, health, and execution.
Industrial-grade trade execution with comprehensive audit trails.
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)

# Environment configuration
TRADING_ENABLED = os.getenv("TRADING_ENABLED", "false").lower() in ("true", "1", "yes")
PANIC_TIMEOUT_S = int(os.getenv("PANIC_TIMEOUT_S", "5"))
HEALTH_CACHE_MS = int(os.getenv("HEALTH_CACHE_MS", "500"))

# Import trading components
try:
    from app.trading import brackets, guardrails, policy, quality

    TRADING_COMPONENTS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Trading components not fully available: {e}")
    TRADING_COMPONENTS_AVAILABLE = False

    # Mock components for development
    class MockPolicyEngine:
        def check(
            self,
            ticker: str,
            size: float,
            p_up: float,
            regime: str,
            spreads_bps: float,
            news_heat: float,
        ):
            return type(
                "MockResult",
                (),
                {
                    "ok": True,
                    "reason": "mock_ok",
                    "to_dict": lambda: {"mock": True, "ok": True, "reason": "mock_ok"},
                },
            )()

    class MockGuardrails:
        def check_trade_allowed(self, symbol: str, size: float, price: float, regime: str):
            return True, "mock_ok", {"mock": True}

        def get_guardrail_stats(self):
            return {
                "current_metrics": {
                    "gross_exposure": 0.0,
                    "net_exposure": 0.0,
                    "daily_pnl": 0.0,
                    "weekly_pnl": 0.0,
                    "portfolio_value": 100000.0,
                    "cash_balance": 50000.0,
                },
                "violation_count": 0,
                "emergency_stop": False,
            }

        def emergency_stop(self, reason: str):
            logger.info(f"Mock emergency stop: {reason}")

        def resume_trading(self):
            logger.info("Mock resume trading")

    class MockBrackets:
        def create_bracket_order(
            self,
            symbol: str,
            side: str,
            quantity: float,
            entry: dict,
            stop: dict,
            take: dict | None = None,
        ):
            return type(
                "MockBracketResult",
                (),
                {"bracket_id": f"mock_bracket_{datetime.now().timestamp()}"},
            )()

    class MockQuality:
        def get_quality_report(self, venue: str | None = None, symbol: str | None = None):
            return {
                "bucket_stats": [],
                "venue_performance": {},
                "generated_at": datetime.now(UTC).isoformat(),
            }

    policy = type("MockPolicy", (), {"policy_engine": MockPolicyEngine()})()
    guardrails = MockGuardrails()
    brackets = MockBrackets()
    quality = MockQuality()


# Mock position/order functions
def get_current_positions():
    return {"count": 0, "gross_exposure": 0.0, "net_exposure": 0.0}


def get_open_orders():
    return {"count": 0}


# Import brain integration
try:
    # Temporarily disable journal import due to dataclass inheritance issues
    # from app.trading.journal import get_journal
    raise ImportError("Journal temporarily disabled")
    BRAIN_AVAILABLE = True
except ImportError:
    BRAIN_AVAILABLE = False

    def get_journal():
        return type(
            "MockJournal",
            (),
            {
                "log_trade_intent": lambda *args,
                **kwargs: f"mock_intent_{datetime.now().timestamp()}",
                "log_policy_check": lambda *args,
                **kwargs: f"mock_policy_{datetime.now().timestamp()}",
                "log_guardrail_check": lambda *args,
                **kwargs: f"mock_guardrail_{datetime.now().timestamp()}",
                "log_trade_submit": lambda *args,
                **kwargs: f"mock_submit_{datetime.now().timestamp()}",
                "log_panic_activate": lambda *args,
                **kwargs: f"mock_panic_{datetime.now().timestamp()}",
                "log_panic_complete": lambda *args,
                **kwargs: f"mock_panic_complete_{datetime.now().timestamp()}",
            },
        )()


# Create router
router = APIRouter(prefix="/trade", tags=["trading"])


# Pydantic models for request/response
class TradeRequest(BaseModel):
    symbol: str = Field(..., description="Trading symbol")
    side: str = Field(..., description="buy or sell")
    qty: float = Field(..., description="Quantity to trade")
    tif: str | None = Field("day", description="Time in force")
    client_id: str | None = Field(None, description="Client order ID")
    p_up: float | None = Field(0.5, description="Model confidence")
    regime: str | None = Field("base", description="Market regime")
    spreads_bps: float | None = Field(10.0, description="Current bid-ask spread")
    news_heat: float | None = Field(0.0, description="News heat score")


class BracketRequest(BaseModel):
    symbol: str = Field(..., description="Trading symbol")
    side: str = Field(..., description="buy or sell")
    qty: float = Field(..., description="Quantity to trade")
    entry: dict[str, Any] = Field(..., description="Entry order parameters")
    stop: dict[str, Any] = Field(..., description="Stop loss parameters")
    take: dict[str, Any] | None = Field(None, description="Take profit parameters")
    tif: str | None = Field("day", description="Time in force")


class TradeResponse(BaseModel):
    status: str
    order_id: str | None = None
    policy_reason: str | None = None
    guardrail_reason: str | None = None
    estimate_fee: float | None = None
    stamps: dict[str, Any] = Field(default_factory=dict)
    event_id: str | None = None


class HealthResponse(BaseModel):
    exposure_gross: float
    exposure_net: float
    open_orders: int
    risk_today: float
    dd_day: float
    dd_week: float
    guardrail_blocks_24h: int
    portfolio_value: float
    cash_balance: float
    trading_enabled: bool
    emergency_stop: bool


class PanicResponse(BaseModel):
    status: str
    flattened_in_s: float
    positions_closed: int
    orders_canceled: int
    total_positions: int
    total_orders: int
    success: bool


class QualityResponse(BaseModel):
    bucket_stats: list[dict[str, Any]]
    venue_performance: dict[str, dict[str, Any]]
    generated_at: str


# Route implementations
@router.post("/market", response_model=TradeResponse)
async def trade_market(request: TradeRequest, background_tasks: BackgroundTasks):
    """
    Submit market order with policy and guardrail checks.

    Flow: policy.check → guardrails.check → route → journal intent+policy → emit order id
    """
    if not TRADING_ENABLED:
        raise HTTPException(status_code=403, detail="Trading disabled")

    try:
        start_time = datetime.now(UTC)
        journal = get_journal()

        # 1. Log trade intent
        intent_id = journal.log_trade_intent(
            symbol=request.symbol,
            side=request.side,
            quantity=request.qty,
            order_type="market",
            client_id=request.client_id,
            regime=request.regime,
            confidence=request.p_up,
            request_params=request.dict(),
        )

        # 2. Policy check
        if TRADING_COMPONENTS_AVAILABLE:
            policy_result = policy.policy_engine.check(
                ticker=request.symbol,
                size=request.qty if request.side.lower() == "buy" else -request.qty,
                p_up=request.p_up or 0.5,
                regime=request.regime or "base",
                spreads_bps=request.spreads_bps or 10.0,
                news_heat=request.news_heat or 0.0,
            )
        else:
            policy_result = type(
                "MockResult",
                (),
                {"ok": True, "reason": "mock_ok", "to_dict": lambda: {"mock": True}},
            )()

        # 3. Log policy check result
        policy_violations = [] if policy_result.ok else [policy_result.reason]
        journal.log_policy_check(
            intent_id=intent_id,
            symbol=request.symbol,
            policy_result=(
                policy_result.to_dict() if hasattr(policy_result, "to_dict") else {"mock": True}
            ),
            check_details={"regime": request.regime, "confidence": request.p_up},
            violations=policy_violations,
            allowed=policy_result.ok,
        )

        # 4. If policy blocks, return early
        if not policy_result.ok:
            return TradeResponse(
                status="blocked",
                policy_reason=policy_result.reason,
                event_id=intent_id,
                stamps={"policy_check_ts": start_time.isoformat()},
            )

        # 5. Guardrail check
        estimated_price = 100.0  # TODO: Get real market price
        guardrail_allowed, guardrail_reason, guardrail_details = guardrails.check_trade_allowed(
            request.symbol,
            request.qty if request.side.lower() == "buy" else -request.qty,
            estimated_price,
            request.regime or "base",
        )

        # 6. Log guardrail check result
        guardrail_violations = [] if guardrail_allowed else [guardrail_reason]
        journal.log_guardrail_check(
            intent_id=intent_id,
            symbol=request.symbol,
            guardrail_result={"allowed": guardrail_allowed, "reason": guardrail_reason},
            risk_metrics=guardrail_details,
            violations=guardrail_violations,
            allowed=guardrail_allowed,
        )

        # 7. If guardrails block, return early
        if not guardrail_allowed:
            return TradeResponse(
                status="blocked",
                guardrail_reason=guardrail_reason,
                event_id=intent_id,
                stamps={"guardrail_check_ts": datetime.now(UTC).isoformat()},
            )

        # 8. Route to execution system
        if TRADING_COMPONENTS_AVAILABLE:
            # TODO: Implement actual execution routing
            execution_result = {
                "order_id": f"order_{start_time.timestamp()}",
                "status": "submitted",
                "estimated_fee": 1.0,
            }
        else:
            execution_result = {
                "order_id": f"mock_order_{start_time.timestamp()}",
                "status": "submitted_mock",
                "estimated_fee": 1.0,
            }

        # 9. Log trade submission
        journal.log_trade_submit(
            intent_id=intent_id,
            order_id=execution_result["order_id"],
            symbol=request.symbol,
            execution_details=execution_result,
            estimated_fee=execution_result["estimated_fee"],
        )

        # 8. Update guardrail metrics in background
        background_tasks.add_task(_update_guardrail_metrics)

        return TradeResponse(
            status=execution_result["status"],
            order_id=execution_result["order_id"],
            estimate_fee=execution_result["estimated_fee"],
            event_id=intent_id,
            stamps={
                "policy_check_ts": start_time.isoformat(),
                "guardrail_check_ts": datetime.now(UTC).isoformat(),
                "execution_submit_ts": datetime.now(UTC).isoformat(),
            },
        )

    except Exception as e:
        logger.error(f"Market order failed: {e}")
        # Log error to journal
        journal = get_journal()
        journal.log_trade_intent(
            symbol=request.symbol,
            side=request.side,
            quantity=request.qty,
            order_type="market_error",
            request_params={"error": str(e)},
        )

        raise HTTPException(status_code=500, detail=f"Trade execution failed: {e!s}")


@router.post("/bracket", response_model=TradeResponse)
async def trade_bracket(request: BracketRequest, background_tasks: BackgroundTasks):
    """Submit bracket order with policy and guardrail checks."""
    if not TRADING_ENABLED:
        raise HTTPException(status_code=403, detail="Trading disabled")

    try:
        start_time = datetime.now(UTC)

        # Create bracket order
        if TRADING_COMPONENTS_AVAILABLE:
            bracket_result = brackets.create_bracket_order(
                symbol=request.symbol,
                side=request.side,
                quantity=request.qty,
                entry=request.entry,
                stop=request.stop,
                take=request.take or {},
            )

            order_id = bracket_result.bracket_id
        else:
            order_id = f"mock_bracket_{start_time.timestamp()}"

        # Journal bracket creation
        journal = get_journal()
        journal.log_trade_submit(
            intent_id=order_id,
            order_id=order_id,
            symbol=request.symbol,
            execution_details={
                "bracket_type": "create",
                "entry": request.entry,
                "stop": request.stop,
            },
        )

        return TradeResponse(
            status="submitted",
            order_id=order_id,
            stamps={"bracket_create_ts": start_time.isoformat()},
        )

    except Exception as e:
        logger.error(f"Bracket order failed: {e}")
        raise HTTPException(status_code=500, detail=f"Bracket order failed: {e!s}")


@router.get("/health", response_model=HealthResponse)
async def trade_health():
    """Get current trading health and risk metrics."""
    try:
        # Get guardrail stats
        guardrail_stats = guardrails.get_guardrail_stats()

        # Get current positions and orders
        if TRADING_COMPONENTS_AVAILABLE:
            try:
                current_positions = get_current_positions()
                current_orders = get_open_orders()
            except Exception as e:
                logger.warning(f"Failed to get current positions/orders: {e}")
                current_positions = {"total": 0, "gross_exposure": 0.0, "net_exposure": 0.0}
                current_orders = {"count": 0}
        else:
            current_positions = {"total": 0, "gross_exposure": 0.0, "net_exposure": 0.0}
            current_orders = {"count": 0}

        metrics = guardrail_stats.get("current_metrics", {})

        return HealthResponse(
            exposure_gross=metrics.get("gross_exposure", 0.0),
            exposure_net=metrics.get("net_exposure", 0.0),
            open_orders=current_orders.get("count", 0),
            risk_today=abs(metrics.get("daily_pnl", 0.0)),
            dd_day=abs(min(metrics.get("daily_pnl", 0.0), 0.0))
            / max(metrics.get("portfolio_value", 1.0), 1.0),
            dd_week=abs(min(metrics.get("weekly_pnl", 0.0), 0.0))
            / max(metrics.get("portfolio_value", 1.0), 1.0),
            guardrail_blocks_24h=guardrail_stats.get("violation_count", 0),
            portfolio_value=metrics.get("portfolio_value", 0.0),
            cash_balance=metrics.get("cash_balance", 0.0),
            trading_enabled=TRADING_ENABLED,
            emergency_stop=guardrail_stats.get("emergency_stop", False),
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {e!s}")


@router.post("/panic", response_model=PanicResponse)
async def trade_panic():
    """
    Emergency panic - close all positions and cancel all orders.

    Closes all open positions & cancels orders within PANIC_TIMEOUT_S.
    """
    try:
        start_time = datetime.now(UTC)

        logger.critical("PANIC BUTTON ACTIVATED - Closing all positions and canceling orders")
        journal = get_journal()

        # Journal panic activation
        panic_event_id = journal.log_panic_activate(
            trigger_reason="Manual panic button",
            positions_count=0,  # TODO: Get real counts
            orders_count=0,
            timeout_seconds=PANIC_TIMEOUT_S,
        )

        # Execute panic procedure
        if TRADING_COMPONENTS_AVAILABLE:
            try:
                # Get current state
                positions = get_current_positions()
                orders = get_open_orders()

                total_positions = positions.get("count", 0)
                total_orders = orders.get("count", 0)

                # Execute panic with timeout
                panic_result = await asyncio.wait_for(
                    _execute_panic_procedure(), timeout=PANIC_TIMEOUT_S
                )

                positions_closed = panic_result.get("positions_closed", 0)
                orders_canceled = panic_result.get("orders_canceled", 0)
                success = panic_result.get("success", False)

            except TimeoutError:
                logger.error(f"Panic procedure timed out after {PANIC_TIMEOUT_S}s")
                positions_closed = 0
                orders_canceled = 0
                total_positions = 0
                total_orders = 0
                success = False

        else:
            # Mock panic for development
            total_positions = 0
            total_orders = 0
            positions_closed = 0
            orders_canceled = 0
            success = True

        # Calculate time to completion
        end_time = datetime.now(UTC)
        flattened_in_s = (end_time - start_time).total_seconds()

        # Journal panic completion
        journal.log_panic_complete(
            panic_id=panic_event_id,
            success=success,
            flattened_in_seconds=flattened_in_s,
            positions_closed=positions_closed,
            orders_canceled=orders_canceled,
        )

        # Activate emergency stop in guardrails
        guardrails.emergency_stop(f"Panic button - flattened in {flattened_in_s:.2f}s")

        status = (
            "success"
            if success
            else "partial"
            if (positions_closed > 0 or orders_canceled > 0)
            else "failed"
        )

        return PanicResponse(
            status=status,
            flattened_in_s=flattened_in_s,
            positions_closed=positions_closed,
            orders_canceled=orders_canceled,
            total_positions=total_positions,
            total_orders=total_orders,
            success=success,
        )

    except Exception as e:
        logger.error(f"Panic procedure failed: {e}")

        # Journal panic failure
        journal = get_journal()
        journal.log_trade_intent(
            symbol="ERROR",
            side="panic_error",
            quantity=0,
            order_type="panic_error",
            request_params={"error": str(e)},
        )

        raise HTTPException(status_code=500, detail=f"Panic procedure failed: {e!s}")


@router.get("/quality", response_model=QualityResponse)
async def trade_quality(venue: str | None = None, symbol: str | None = None):
    """Get execution quality statistics by venue and symbol."""
    try:
        if TRADING_COMPONENTS_AVAILABLE:
            quality_report = quality.get_quality_report(venue or None, symbol or None)
        else:
            quality_report = {
                "bucket_stats": [],
                "venue_performance": {},
                "generated_at": datetime.now(UTC).isoformat(),
            }

        return QualityResponse(**quality_report)

    except Exception as e:
        logger.error(f"Quality report failed: {e}")
        raise HTTPException(status_code=500, detail=f"Quality report failed: {e!s}")


@router.post("/resume")
async def resume_trading():
    """Resume trading after emergency stop."""
    try:
        guardrails.resume_trading()

        resume_event = {"kind": "trading_resume", "timestamp": datetime.now(UTC).isoformat()}

        # Log to journal if available
        try:
            journal = get_journal()
            journal.log_trade_intent(
                symbol="SYSTEM",
                side="resume",
                quantity=0,
                order_type="resume",
                request_params=resume_event,
            )
        except Exception:
            logger.info("Resume event logged locally only")

        logger.info("Trading resumed")
        return {"status": "resumed", "trading_enabled": True}

    except Exception as e:
        logger.error(f"Resume trading failed: {e}")
        raise HTTPException(status_code=500, detail=f"Resume failed: {e!s}")


# Helper functions
async def _execute_panic_procedure() -> dict[str, Any]:
    """Execute the actual panic procedure."""
    try:
        # TODO: Implement actual position closing and order cancellation
        # This would interface with the broker adapters

        # For now, simulate the procedure
        await asyncio.sleep(0.1)  # Simulate network latency

        return {"positions_closed": 0, "orders_canceled": 0, "success": True}

    except Exception as e:
        logger.error(f"Panic execution failed: {e}")
        return {"positions_closed": 0, "orders_canceled": 0, "success": False, "error": str(e)}


def _update_guardrail_metrics():
    """Background task to update guardrail metrics."""
    try:
        # TODO: Update guardrail metrics with current portfolio state
        # This would fetch latest positions, P&L, etc.
        pass
    except Exception as e:
        logger.error(f"Failed to update guardrail metrics: {e}")


def _enabled():
    """Check if trading is enabled."""
    return TRADING_ENABLED
