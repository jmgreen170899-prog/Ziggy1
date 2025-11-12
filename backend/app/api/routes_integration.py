# backend/app/api/routes_integration.py
"""
Integration API endpoints for Ziggy unified system.
Provides endpoints for integrated decision making and system health.
"""

import logging
import time
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)

# Import integration hub
try:
    from ..services.integration_hub import (
        IntegratedDecision,
        enhance_data_with_intelligence,
        get_integrated_system_health,
        get_integration_hub,
        make_intelligent_decision,
    )

    INTEGRATION_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Integration hub not available: {e}")
    INTEGRATION_AVAILABLE = False

router = APIRouter(prefix="/integration", tags=["integration"])


# Pydantic models for API
class DecisionRequest(BaseModel):
    """Request model for making integrated decisions."""

    ticker: str = Field(..., description="Symbol to analyze")
    market_data: dict[str, Any] = Field(..., description="Current market data")
    signal_data: dict[str, Any] = Field(..., description="Signal generation data")
    decision_type: str = Field(default="signal", description="Type of decision")


class EnhanceDataRequest(BaseModel):
    """Request model for data enhancement."""

    data: dict[str, Any] = Field(..., description="Raw data to enhance")
    source: str = Field(..., description="Data source type")
    symbols: list[str] | None = Field(None, description="Optional symbol list")


class UpdateOutcomeRequest(BaseModel):
    """Request model for updating decision outcomes."""

    decision_timestamp: float = Field(..., description="Original decision timestamp")
    exit_price: float = Field(..., description="Exit price")
    realized_pnl: float = Field(..., description="Realized profit/loss")
    fees: float = Field(default=0.0, description="Trading fees paid")
    exit_reason: str = Field(default="manual", description="Reason for exit")


class IntegratedDecisionResponse(BaseModel):
    """Response model for integrated decisions."""

    timestamp: float
    ticker: str
    decision_type: str
    market_regime: str
    regime_confidence: float
    brain_features: dict[str, float]
    brain_insights: list[str]
    active_rules_version: str
    parameters_used: dict[str, Any]
    predicted_probability: float | None
    calibrated_probability: float | None
    action: str
    quantity: float
    confidence: float
    reasoning: list[str]
    stop_loss: float | None
    take_profit: float | None
    risk_score: float

    @classmethod
    def from_decision(cls, decision: "IntegratedDecision") -> "IntegratedDecisionResponse":
        """Create response from IntegratedDecision object."""
        return cls(
            timestamp=decision.timestamp,
            ticker=decision.ticker,
            decision_type=decision.decision_type,
            market_regime=decision.market_regime,
            regime_confidence=decision.regime_confidence,
            brain_features=decision.brain_features,
            brain_insights=decision.brain_insights,
            active_rules_version=decision.active_rules_version,
            parameters_used=decision.parameters_used,
            predicted_probability=decision.predicted_probability,
            calibrated_probability=decision.calibrated_probability,
            action=decision.action,
            quantity=decision.quantity,
            confidence=decision.confidence,
            reasoning=decision.reasoning,
            stop_loss=decision.stop_loss,
            take_profit=decision.take_profit,
            risk_score=decision.risk_score,
        )


@router.get("/health")
async def get_system_health():
    """
    Get integrated system health status.

    Returns:
        System health including component status and integration score
    """
    if not INTEGRATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Integration system not available")

    try:
        health = get_integrated_system_health()
        return {"status": "success", "data": health, "timestamp": time.time()}
    except Exception as e:
        logger.error(f"Failed to get system health: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get system health: {e!s}")


@router.post("/decision", response_model=IntegratedDecisionResponse)
async def make_decision(request: DecisionRequest):
    """
    Make an integrated trading decision using all systems.

    Args:
        request: Decision request with ticker, market data, and signal data

    Returns:
        Complete integrated decision with brain intelligence and learning context
    """
    if not INTEGRATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Integration system not available")

    try:
        decision = make_intelligent_decision(
            ticker=request.ticker, market_data=request.market_data, signal_data=request.signal_data
        )

        response = IntegratedDecisionResponse.from_decision(decision)
        return response

    except Exception as e:
        logger.error(f"Failed to make integrated decision: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to make decision: {e!s}")


@router.post("/enhance")
async def enhance_data(request: EnhanceDataRequest):
    """
    Enhance data with brain intelligence.

    Args:
        request: Data enhancement request with raw data and source type

    Returns:
        Brain-enhanced data with intelligent insights
    """
    if not INTEGRATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Integration system not available")

    try:
        enhanced_data = enhance_data_with_intelligence(
            data=request.data, source=request.source, symbols=request.symbols
        )

        return {
            "status": "success",
            "data": enhanced_data,
            "source": request.source,
            "timestamp": time.time(),
        }

    except Exception as e:
        logger.error(f"Failed to enhance data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to enhance data: {e!s}")


@router.get("/context/market")
async def get_market_context():
    """
    Get current market context from brain intelligence.

    Returns:
        Current market regime, confidence, and insights
    """
    if not INTEGRATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Integration system not available")

    try:
        hub = get_integration_hub()
        context = hub.get_current_market_context()

        return {"status": "success", "data": context, "timestamp": time.time()}

    except Exception as e:
        logger.error(f"Failed to get market context: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get market context: {e!s}")


@router.get("/rules/active")
async def get_active_rules():
    """
    Get currently active trading rules and parameters.

    Returns:
        Active rules version and parameters from learning system
    """
    if not INTEGRATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Integration system not available")

    try:
        hub = get_integration_hub()
        rules = hub.get_active_rules()

        return {"status": "success", "data": rules, "timestamp": time.time()}

    except Exception as e:
        logger.error(f"Failed to get active rules: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get active rules: {e!s}")


@router.post("/calibration/apply")
async def apply_calibration(probabilities: list[float]):
    """
    Apply learned probability calibration to raw probabilities.

    Args:
        probabilities: List of raw probabilities to calibrate

    Returns:
        Calibrated probabilities
    """
    if not INTEGRATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Integration system not available")

    try:
        hub = get_integration_hub()
        calibrated = hub.apply_probability_calibration(probabilities)

        return {
            "status": "success",
            "data": {"raw_probabilities": probabilities, "calibrated_probabilities": calibrated},
            "timestamp": time.time(),
        }

    except Exception as e:
        logger.error(f"Failed to apply calibration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to apply calibration: {e!s}")


@router.post("/outcome/update")
async def update_outcome(request: UpdateOutcomeRequest):
    """
    Update decision outcome for learning system.

    Args:
        request: Outcome update with exit details and P&L

    Returns:
        Confirmation of outcome update
    """
    if not INTEGRATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Integration system not available")

    try:
        # We need to use the learning system directly for outcome updates
        from ..services.data_log import update_trading_outcome

        update_trading_outcome(
            decision_timestamp=request.decision_timestamp,
            ticker="",  # Will be looked up from the log
            exit_price=request.exit_price,
            realized_pnl=request.realized_pnl,
            fees_paid=request.fees,
            exit_reason=request.exit_reason,
        )

        return {
            "status": "success",
            "message": "Decision outcome updated successfully",
            "decision_timestamp": request.decision_timestamp,
            "timestamp": time.time(),
        }

    except Exception as e:
        logger.error(f"Failed to update outcome: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update outcome: {e!s}")


@router.get("/status")
async def get_integration_status():
    """
    Get integration system status and capabilities.

    Returns:
        System status, available components, and capabilities
    """
    status = {"integration_available": INTEGRATION_AVAILABLE, "timestamp": time.time()}

    if INTEGRATION_AVAILABLE:
        try:
            hub = get_integration_hub()
            health = hub.get_system_health()

            status.update(
                {
                    "components": health["components"],
                    "integration_score": health["integration_score"],
                    "overall_status": health["overall_status"],
                    "capabilities": {
                        "brain_intelligence": health["components"]["brain_intelligence"][
                            "available"
                        ],
                        "learning_system": health["components"]["learning_system"]["available"],
                        "calibration_system": health["components"]["calibration_system"][
                            "available"
                        ],
                        "integrated_decisions": True,
                        "data_enhancement": True,
                        "automatic_logging": True,
                    },
                }
            )

        except Exception as e:
            status.update(
                {
                    "error": str(e),
                    "capabilities": {
                        "brain_intelligence": False,
                        "learning_system": False,
                        "calibration_system": False,
                        "integrated_decisions": False,
                        "data_enhancement": False,
                        "automatic_logging": False,
                    },
                }
            )

    return status


@router.post("/test/decision")
async def test_decision():
    """
    Test integrated decision making with sample data.

    Returns:
        Sample decision to verify integration is working
    """
    if not INTEGRATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Integration system not available")

    try:
        # Sample test data
        test_market_data = {"price": 150.0, "volume": 1000000, "timestamp": time.time()}

        test_signal_data = {
            "rsi": 25.0,
            "atr": 2.5,
            "volume_ratio": 1.2,
            "price_momentum": 0.05,
            "regime_strength": 0.7,
        }

        if INTEGRATION_AVAILABLE and "make_intelligent_decision" in globals():
            decision = make_intelligent_decision(
                ticker="TEST", market_data=test_market_data, signal_data=test_signal_data
            )

            response = IntegratedDecisionResponse.from_decision(decision)
        else:
            # Create a mock response for testing when integration is offline
            response = {
                "action": "hold",
                "confidence": 0.0,
                "reasoning": ["Integration system offline"],
            }

        return {
            "status": "success",
            "message": "Integration test completed successfully",
            "test_decision": response,
            "timestamp": time.time(),
        }

    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Integration test failed: {e!s}")


if __name__ == "__main__":
    # Quick test of endpoints
    import asyncio

    async def test_endpoints():
        if INTEGRATION_AVAILABLE:
            print("Testing integration endpoints...")

            # Test health endpoint
            health = await get_system_health()
            print(f"Health: {health['data']['overall_status']}")

            # Test status endpoint
            status = await get_integration_status()
            print(f"Integration score: {status.get('integration_score', 0):.1f}%")

            print("Integration endpoints test completed")
        else:
            print("Integration system not available for testing")

    asyncio.run(test_endpoints())
