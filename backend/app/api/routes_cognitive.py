"""
API routes for cognitive enhancement systems.

Exposes advanced cognitive capabilities:
- Meta-learning status and strategy selection
- Counterfactual analysis insights
- Episodic memory recall
- Integrated cognitive decision enhancement
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.cognitive.cognitive_hub import CognitiveHub
from app.core.logging import get_logger


logger = get_logger(__name__)
router = APIRouter(prefix="/cognitive", tags=["cognitive"])

# Global cognitive hub instance
_cognitive_hub: CognitiveHub | None = None


def get_cognitive_hub() -> CognitiveHub:
    """Get or create cognitive hub instance."""
    global _cognitive_hub
    if _cognitive_hub is None:
        _cognitive_hub = CognitiveHub()
    return _cognitive_hub


# Request/Response Models
class DecisionRequest(BaseModel):
    """Request for cognitive decision enhancement."""

    ticker: str = Field(..., description="Stock symbol")
    proposed_action: str = Field(..., description="Proposed action (buy/sell/hold)")
    market_context: dict[str, Any] = Field(..., description="Current market context")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Initial confidence")


class DecisionResponse(BaseModel):
    """Enhanced decision with cognitive insights."""

    ticker: str
    proposed_action: str
    original_confidence: float
    adjusted_confidence: float | None = None
    meta_learning: dict[str, Any] | None = None
    episodic_memory: dict[str, Any] | None = None
    cognitive_insights: list[str] = Field(default_factory=list)
    timestamp: str


class OutcomeRecord(BaseModel):
    """Record of decision outcome."""

    ticker: str
    action: str
    entry_price: float
    quantity: float
    market_context: dict[str, Any]
    confidence: float
    reasoning: list[str]
    outcome_pnl: float
    outcome_pnl_percent: float
    holding_period_hours: float
    current_prices: dict[str, float]


# API Endpoints
@router.get("/status", response_model=None)
async def get_cognitive_status() -> dict[str, Any]:
    """
    Get status of all cognitive systems.

    Returns comprehensive status including:
    - Meta-learning strategies and performance
    - Counterfactual analysis insights
    - Episodic memory statistics
    """
    try:
        hub = get_cognitive_hub()
        return hub.get_system_status()
    except Exception as e:
        logger.error(f"Error getting cognitive status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enhance-decision", response_model=DecisionResponse)
async def enhance_decision(request: DecisionRequest) -> DecisionResponse:
    """
    Enhance a trading decision with cognitive intelligence.

    Applies:
    - Meta-learning to select optimal strategy
    - Episodic memory to recall similar situations
    - Confidence adjustment based on historical success

    Args:
        request: Decision to enhance with market context

    Returns:
        Enhanced decision with cognitive insights
    """
    try:
        hub = get_cognitive_hub()

        enhanced = hub.enhance_decision(
            ticker=request.ticker,
            proposed_action=request.proposed_action,
            market_context=request.market_context,
            confidence=request.confidence,
        )

        return DecisionResponse(**enhanced)
    except Exception as e:
        logger.error(f"Error enhancing decision: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/record-outcome", response_model=None)
async def record_outcome(record: OutcomeRecord) -> dict[str, str]:
    """
    Record the outcome of a trading decision.

    Updates all cognitive systems with the result:
    - Meta-learner tracks strategy performance
    - Counterfactual engine analyzes alternatives
    - Episodic memory stores the episode

    Args:
        record: Complete decision and outcome information

    Returns:
        Confirmation message
    """
    try:
        hub = get_cognitive_hub()

        hub.record_decision_outcome(
            ticker=record.ticker,
            action=record.action,
            entry_price=record.entry_price,
            quantity=record.quantity,
            market_context=record.market_context,
            confidence=record.confidence,
            reasoning=record.reasoning,
            outcome_pnl=record.outcome_pnl,
            outcome_pnl_percent=record.outcome_pnl_percent,
            holding_period_hours=record.holding_period_hours,
            current_prices=record.current_prices,
        )

        return {"status": "success", "message": f"Outcome recorded for {record.ticker}"}
    except Exception as e:
        logger.error(f"Error recording outcome: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/meta-learning/strategies", response_model=None)
async def get_meta_learning_strategies() -> dict[str, Any]:
    """
    Get all meta-learning strategies and their performance.

    Returns:
        Dictionary of strategies with performance metrics
    """
    try:
        hub = get_cognitive_hub()
        if hub.meta_learner is None:
            raise HTTPException(status_code=503, detail="Meta-learning not enabled")

        status = hub.meta_learner.get_status()
        return status.get("strategies", {})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/counterfactual/insights", response_model=None)
async def get_counterfactual_insights() -> dict[str, Any]:
    """
    Get aggregate insights from counterfactual analysis.

    Returns:
        Insights about opportunities missed, regret, and alternative actions
    """
    try:
        hub = get_cognitive_hub()
        if hub.counterfactual_engine is None:
            raise HTTPException(
                status_code=503, detail="Counterfactual reasoning not enabled"
            )

        return hub.counterfactual_engine.get_aggregate_insights()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting counterfactual insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/episodic-memory/stats", response_model=None)
async def get_episodic_memory_stats() -> dict[str, Any]:
    """
    Get statistics about episodic memory.

    Returns:
        Memory statistics including episode counts and success rates
    """
    try:
        hub = get_cognitive_hub()
        if hub.episodic_memory is None:
            raise HTTPException(status_code=503, detail="Episodic memory not enabled")

        return hub.episodic_memory.get_stats()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting memory stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=None)
async def health_check() -> dict[str, str]:
    """Health check for cognitive systems."""
    try:
        hub = get_cognitive_hub()
        subsystems_active = []

        if hub.meta_learner:
            subsystems_active.append("meta_learning")
        if hub.counterfactual_engine:
            subsystems_active.append("counterfactual")
        if hub.episodic_memory:
            subsystems_active.append("episodic_memory")

        return {"status": "healthy", "subsystems": ",".join(subsystems_active)}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}
