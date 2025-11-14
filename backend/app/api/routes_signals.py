# isort: skip_file
"""
Market Brain API Routes

FastAPI routes for the market intelligence system:
- Feature computation endpoints
- Regime detection
- Signal generation
- Position sizing
- Trade planning and execution
"""

import logging
import os
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

# Optional sandbox signals provider (fixtures via provider_factory)
try:
    from ..services.provider_factory import get_signals_provider  # type: ignore

    _SIG_SANDBOX = get_signals_provider
except Exception:
    _SIG_SANDBOX = None  # type: ignore


# Rate limiting imports
try:
    from ..core.rate_limiting import limiter

    RATE_LIMITING_AVAILABLE = True
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("Rate limiting not available")
    RATE_LIMITING_AVAILABLE = False

    # Create a no-op decorator
    class NoOpLimiter:
        def limit(self, rate_limit: str):
            def decorator(func):
                return func

            return decorator

    limiter = NoOpLimiter()

# Core services imports
# Memory & Knowledge imports
from ..memory.events import append_event, build_durable_event
from ..memory.vecdb import build_embedding, search_similar, upsert_event
from ..services.market_brain.features import get_multiple_ticker_features, get_ticker_features
from ..services.market_brain.regime import get_regime_state, regime_detector
from ..services.market_brain.signals import (
    generate_signals_for_watchlist,
    generate_ticker_signal,
    signal_generator,
)
from ..services.market_brain.sizer import (
    SizingMethod,
    calculate_position_for_signal,
    position_sizer,
)


# Initialize logger
logger = logging.getLogger(__name__)

# Try to import trading components - make them optional
try:
    from ..services.market_brain.executor import (
        execute_trade_signal,
        get_execution_status,
        trade_executor,
    )
except ImportError:
    logger.warning("Trading executor not available")
    execute_trade_signal = None
    get_execution_status = None
    trade_executor = None

try:
    from ..services.market_brain.backtest import (
        BacktestPeriod,
        analyze_signals,
        backtester,
        quick_backtest,
    )
except ImportError:
    logger.warning("Backtesting components not available")
    quick_backtest = None
    analyze_signals = None
    BacktestPeriod = None
    backtester = None

# Try to import cognitive functions - make them optional
try:
    from ..data.features import compute_features
except ImportError:
    logger.warning("Feature computation not available")

    def compute_features(*args, **kwargs):
        return {"mock": True}


try:
    from ..services.regime import detect_regime
except ImportError:
    logger.warning("Regime detection not available")

    def detect_regime(*args, **kwargs):
        return {"regime": "unknown", "confidence": 0.0}


try:
    from ..services.fusion.ensemble import fused_probability
except ImportError:
    logger.warning("Signal fusion not available")

    def fused_probability(*args, **kwargs):
        return {"signal": 0.0, "confidence": 0.0}


try:
    from ..services.position_sizing import compute_position
except ImportError:
    logger.warning("Position sizing not available")

    def compute_position(*args, **kwargs) -> dict[str, Any]:
        return {
            "quantity": 0,
            "dollar_amount": 0.0,
            "position_pct": 0.0,
            "stop_loss": 0.0,
            "take_profit": 0.0,
            "risk_per_trade": 0.0,
            "reasoning": "Position sizing service unavailable",
        }


# Configuration
KNN_K = int(os.getenv("KNN_K", "10"))
RAG_ENABLED = os.getenv("VECDB_BACKEND", "OFF") != "OFF"
RAG_PRIOR_WEIGHT = float(os.getenv("RAG_PRIOR_WEIGHT", "0.25"))


# Request models
class BulkFeaturesRequest(BaseModel):
    tickers: list[str] = Field(..., description="List of tickers")
    force_refresh: bool = Field(False, description="Force refresh of cached data")


class WatchlistSignalsRequest(BaseModel):
    tickers: list[str] = Field(..., description="List of tickers for signal generation")
    include_regime: bool = Field(True, description="Include regime context")


# Router
router = APIRouter(prefix="/signals", tags=["market_brain"])


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic Models
# ──────────────────────────────────────────────────────────────────────────────


class TradePlanRequest(BaseModel):
    """Request for trade plan validation."""

    ticker: str = Field(..., description="Stock symbol")
    account_size: float | None = Field(100000, description="Account size in dollars")
    sizing_method: str | None = Field("VolatilityTarget", description="Position sizing method")
    force_refresh: bool | None = Field(False, description="Force refresh of features")


class TradeExecutionRequest(BaseModel):
    """Request for trade execution."""

    ticker: str = Field(..., description="Stock symbol")
    quantity: int = Field(..., description="Number of shares")
    direction: str = Field(..., description="LONG or SHORT")
    entry_price: float = Field(..., description="Entry price")
    stop_loss: float | None = Field(None, description="Stop loss price")
    take_profit: float | None = Field(None, description="Take profit price")
    dry_run: bool | None = Field(True, description="Dry run (no actual execution)")


# ──────────────────────────────────────────────────────────────────────────────
# Feature Endpoints
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/features/{ticker}", response_model=None)
@limiter.limit("60/minute")
def get_ticker_features_endpoint(
    request: Request,
    ticker: str,
    force_refresh: bool = Query(False, description="Force refresh of cached data"),
):
    """Get technical features for a ticker."""
    try:
        features = get_ticker_features(ticker.upper(), force_refresh)

        if not features:
            raise HTTPException(status_code=404, detail=f"No features available for {ticker}")

        return {"ticker": ticker.upper(), "features": features.to_dict(), "status": "success"}

    except Exception as e:
        logger.error(f"Error getting features for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/features/bulk", response_model=None)
def get_bulk_features(request: BulkFeaturesRequest):
    """Get features for multiple tickers."""
    try:
        tickers = request.tickers
        # Note: force_refresh from request available if needed for future implementation

        # Limit to reasonable number of tickers
        if len(tickers) > 50:
            raise HTTPException(status_code=400, detail="Maximum 50 tickers allowed per request")

        tickers_upper = [t.upper() for t in tickers]
        features_dict = get_multiple_ticker_features(tickers_upper)

        # Convert to serializable format
        result = {}
        for ticker, features in features_dict.items():
            if features:
                result[ticker] = features.to_dict()
            else:
                result[ticker] = None

        return {
            "features": result,
            "count": len([f for f in result.values() if f is not None]),
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Error getting bulk features: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# ──────────────────────────────────────────────────────────────────────────────
# Regime Detection Endpoints
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/regime", response_model=None)
def get_current_regime(
    force_refresh: bool = Query(False, description="Force refresh of regime calculation"),
):
    """Get current market regime."""
    try:
        regime_result = get_regime_state(force_refresh)

        return {"regime": regime_result.to_dict(), "status": "success"}

    except Exception as e:
        logger.error(f"Error getting regime: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/regime/history", response_model=None)
def get_regime_history(days: int = Query(5, ge=1, le=30, description="Number of days of history")):
    """Get regime history."""
    try:
        history = regime_detector.get_regime_history(days)

        return {"history": history, "days": days, "count": len(history), "status": "success"}

    except Exception as e:
        logger.error(f"Error getting regime history: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# ──────────────────────────────────────────────────────────────────────────────
# Signal Generation Endpoints
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/signal/{ticker}", response_model=None)
@limiter.limit("20/minute")
def get_ticker_signal(
    request: Request,
    ticker: str,
    include_features: bool = Query(False, description="Include raw features in response"),
    include_regime: bool = Query(True, description="Include regime context"),
):
    """Get trading signal for a ticker with complete analysis."""
    try:
        # Sandbox fixtures override (offline mode)
        if callable(_SIG_SANDBOX):
            prov = _SIG_SANDBOX()
            if prov is not None and hasattr(prov, "get_ticker_signal"):
                data = prov.get_ticker_signal(ticker)
                return {
                    "ticker": ticker.upper(),
                    "signal": data,
                    "has_signal": bool(data),
                }

        ticker = ticker.upper()

        # Get signal
        signal = generate_ticker_signal(ticker)

        # Get additional context if requested
        response = {
            "ticker": ticker,
            "signal": signal.to_dict() if signal else None,
            "has_signal": signal is not None,
        }

        if include_features:
            features = get_ticker_features(ticker)
            response["features"] = features.to_dict() if features else None

        if include_regime:
            regime = get_regime_state()
            response["regime"] = regime.to_dict()

        # Add signal explanation if signal exists
        if signal:
            response["explanation"] = signal_generator.get_signal_explanation(signal)

        response["status"] = "success"
        return response

    except Exception as e:
        logger.error(f"Error generating signal for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/watchlist", response_model=None)
def get_watchlist_signals(request: WatchlistSignalsRequest):
    """Generate signals for a watchlist of tickers."""
    try:
        # Sandbox fixtures override (offline mode)
        if callable(_SIG_SANDBOX):
            prov = _SIG_SANDBOX()
            if prov is not None and hasattr(prov, "generate_watchlist_signals"):
                tickers_upper = [t.upper() for t in request.tickers]
                items = prov.generate_watchlist_signals(tickers_upper)
                return {
                    "asof": datetime.utcnow().timestamp(),
                    "count": len(items),
                    "results": items,
                    "status": "success",
                }

        tickers = request.tickers
        include_regime = request.include_regime

        # Limit to reasonable number
        if len(tickers) > 25:
            raise HTTPException(
                status_code=400, detail="Maximum 25 tickers allowed for signal generation"
            )

        tickers_upper = [t.upper() for t in tickers]
        signals_dict = generate_signals_for_watchlist(tickers_upper)

        # Convert to serializable format
        result = {}
        signal_count = 0

        for ticker, signal in signals_dict.items():
            if signal:
                result[ticker] = {
                    "signal": signal.to_dict(),
                    "explanation": signal_generator.get_signal_explanation(signal),
                }
                signal_count += 1
            else:
                result[ticker] = {"signal": None, "explanation": None}

        response = {
            "signals": result,
            "signal_count": signal_count,
            "total_tickers": len(tickers_upper),
            "status": "success",
        }

        if include_regime:
            regime = get_regime_state()
            response["regime_context"] = regime.to_dict()

        return response

    except Exception as e:
        logger.error(f"Error generating watchlist signals: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# ──────────────────────────────────────────────────────────────────────────────
# Position Sizing and Trade Planning
# ──────────────────────────────────────────────────────────────────────────────


@router.post("/trade/plan", response_model=None)
def create_trade_plan(request: TradePlanRequest):
    """Validate and create a complete trade plan with position sizing."""
    try:
        ticker = request.ticker.upper()

        # Update position sizer account size if provided
        if request.account_size:
            position_sizer.update_account_size(request.account_size)

        # Get signal
        signal = generate_ticker_signal(ticker)
        if not signal:
            return {
                "ticker": ticker,
                "has_signal": False,
                "message": "No trading signal generated",
                "status": "no_signal",
            }

        # Get features for position sizing
        features = get_ticker_features(ticker, request.force_refresh or False)
        if not features:
            raise HTTPException(
                status_code=404, detail=f"No market features available for {ticker}"
            )

        # Parse sizing method
        try:
            sizing_method = SizingMethod(request.sizing_method)
        except ValueError:
            sizing_method = SizingMethod.VOLATILITY_TARGET

        # Calculate position size
        position = calculate_position_for_signal(signal, features, sizing_method)

        # Get regime context
        regime = get_regime_state()

        return {
            "ticker": ticker,
            "trade_plan": {
                "signal": signal.to_dict(),
                "position": position.to_dict(),
                "regime_context": regime.to_dict(),
                "features_summary": {
                    "close": features.close,
                    "volatility_20d": features.volatility_20d,
                    "atr_14": features.atr_14,
                    "rsi_14": features.rsi_14,
                },
            },
            "is_valid": position.is_valid,
            "validation_errors": position.validation_errors,
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Error creating trade plan for {request.ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/trade/execute", response_model=None)
def execute_trade(request: TradeExecutionRequest):
    """Execute a trade (integration with existing trading system)."""
    try:
        # This would integrate with the existing trading execution system
        # For now, return a mock response

        if request.dry_run:
            return {
                "execution_id": f"DRY_RUN_{request.ticker}_{int(datetime.now().timestamp())}",
                "ticker": request.ticker.upper(),
                "status": "dry_run_success",
                "message": f"Dry run: {request.direction} {request.quantity} shares of {request.ticker} at ${request.entry_price}",
                "details": {
                    "quantity": request.quantity,
                    "direction": request.direction,
                    "entry_price": request.entry_price,
                    "stop_loss": request.stop_loss,
                    "take_profit": request.take_profit,
                    "estimated_cost": request.quantity * request.entry_price,
                },
            }
        else:
            # Integration point with existing trading system
            # This would call the actual trading execution endpoints
            return {
                "execution_id": None,
                "status": "not_implemented",
                "message": "Live trading execution not yet implemented",
                "next_steps": "Implement integration with existing /trade/* endpoints",
            }

    except Exception as e:
        logger.error(f"Error executing trade: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# ──────────────────────────────────────────────────────────────────────────────
# System Configuration and Status
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/status", response_model=None)
def get_system_status():
    """Get market brain system status."""
    try:
        # Test key components
        regime = get_regime_state()
        features_test = get_ticker_features("SPY")

        return {
            "status": "operational",
            "components": {
                "feature_computer": features_test is not None,
                "regime_detector": True,
                "signal_generator": True,
                "position_sizer": True,
            },
            "current_regime": regime.regime.value,
            "regime_confidence": regime.confidence,
            "timestamp": regime.timestamp.isoformat(),
        }

    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return {
            "status": "error",
            "error": str(e),
            "components": {
                "feature_computer": False,
                "regime_detector": False,
                "signal_generator": False,
                "position_sizer": False,
            },
        }


@router.get("/config", response_model=None)
def get_system_config():
    """Get current system configuration."""
    return {
        "regime_thresholds": regime_detector.thresholds,
        "signal_parameters": signal_generator.params,
        "position_sizing_config": position_sizer.config,
        "account_size": position_sizer.account_size,
    }


@router.put("/config", response_model=None)
def update_system_config(config_updates: dict[str, Any]):
    """Update system configuration."""
    try:
        updated_components = []

        if "regime_thresholds" in config_updates:
            regime_detector.update_thresholds(config_updates["regime_thresholds"])
            updated_components.append("regime_detector")

        if "signal_parameters" in config_updates:
            signal_generator.update_parameters(config_updates["signal_parameters"])
            updated_components.append("signal_generator")

        if "position_sizing_config" in config_updates:
            position_sizer.update_config(config_updates["position_sizing_config"])
            updated_components.append("position_sizer")

        if "account_size" in config_updates:
            position_sizer.update_account_size(config_updates["account_size"])
            updated_components.append("account_size")

        return {
            "status": "success",
            "updated_components": updated_components,
            "message": f"Updated {len(updated_components)} components",
        }

    except Exception as e:
        logger.error(f"Error updating config: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# ═══════════════════════════════════════════════════════════════════════════════
# EXECUTION ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════


class ExecuteTradeRequest(BaseModel):
    """Request to execute a trade signal."""

    ticker: str
    dry_run: bool = True
    order_type: str = "market"
    limit_price: float | None = None
    time_in_force: str = "DAY"
    skip_risk_checks: bool = False


@router.post("/execute/trade", response_model=None)
def execute_trade_from_signal(request: ExecuteTradeRequest):
    """Execute a trade based on current signal."""
    try:
        # Generate signal
        signal = generate_ticker_signal(request.ticker)
        if not signal:
            raise HTTPException(status_code=400, detail=f"No signal available for {request.ticker}")

        # Get features for position sizing
        features = get_ticker_features(request.ticker)
        if not features:
            raise HTTPException(
                status_code=400, detail=f"Could not get features for {request.ticker}"
            )

        # Calculate position size
        position_size = calculate_position_for_signal(signal, features)

        # Execute trade if executor is available
        if execute_trade_signal is None:
            return {
                "execution_result": {
                    "request_id": "mock_" + request.ticker,
                    "status": "simulated",
                    "ticker": request.ticker,
                    "filled_quantity": 0,
                    "filled_price": 0.0,
                    "executed_value": 0.0,
                    "commission": 0.0,
                    "error": "Trade execution service not available",
                }
            }

        result = execute_trade_signal(signal, position_size, request.dry_run)

        return {
            "execution_result": {
                "request_id": result.request_id,
                "status": result.status.value,
                "ticker": result.ticker,
                "filled_quantity": result.filled_quantity,
                "filled_price": result.filled_price,
                "executed_value": result.executed_value,
                "commission": result.commission,
                "timestamp": result.timestamp.isoformat() if result.timestamp else None,
                "warnings": result.warnings,
                "validation_errors": result.validation_errors,
            },
            "signal_used": {
                "direction": signal.direction.value,
                "confidence": signal.confidence,
                "entry_price": signal.entry_price,
                "signal_type": signal.signal_type.value,
            },
            "position_size_used": {
                "quantity": position_size.quantity,
                "risk_percent": position_size.total_risk_percent,
                "method": position_size.sizing_method.value,
            },
        }

    except Exception as e:
        logger.error(f"Error executing trade for {request.ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/execute/status/{request_id}", response_model=None)
def get_trade_execution_status(request_id: str):
    """Get status of a trade execution."""
    try:
        if get_execution_status is None:
            return {
                "request_id": request_id,
                "status": "unavailable",
                "ticker": "unknown",
                "filled_quantity": 0,
                "filled_price": 0.0,
                "error": "Execution status service not available",
            }

        result = get_execution_status(request_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Execution {request_id} not found")

        return {
            "request_id": result.request_id,
            "status": result.status.value,
            "ticker": result.ticker,
            "filled_quantity": result.filled_quantity,
            "filled_price": result.filled_price,
            "executed_value": result.executed_value,
            "commission": result.commission,
            "timestamp": result.timestamp.isoformat() if result.timestamp else None,
            "warnings": result.warnings,
            "validation_errors": result.validation_errors,
        }

    except Exception as e:
        logger.error(f"Error getting execution status {request_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/execute/history", response_model=None)
def get_execution_history(ticker: str | None = None, limit: int = 50):
    """Get execution history."""
    try:
        if trade_executor is None:
            return {"executions": [], "total": 0, "error": "Trade executor service not available"}

        history = trade_executor.get_execution_history(ticker, limit)

        return {
            "executions": [
                {
                    "request_id": result.request_id,
                    "ticker": result.ticker,
                    "status": result.status.value,
                    "filled_quantity": result.filled_quantity,
                    "filled_price": result.filled_price,
                    "executed_value": result.executed_value,
                    "timestamp": result.timestamp.isoformat() if result.timestamp else None,
                }
                for result in history
            ],
            "total_count": len(history),
        }

    except Exception as e:
        logger.error(f"Error getting execution history: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/execute/stats", response_model=None)
def get_execution_stats():
    """Get daily execution statistics."""
    try:
        if trade_executor is None:
            return {
                "daily_stats": {
                    "total_trades": 0,
                    "successful_trades": 0,
                    "failed_trades": 0,
                    "total_volume": 0.0,
                    "avg_execution_time": 0.0,
                },
                "error": "Trade executor service not available",
            }

        stats = trade_executor.get_daily_stats()
        return stats

    except Exception as e:
        logger.error(f"Error getting execution stats: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# ═══════════════════════════════════════════════════════════════════════════════
# BACKTESTING ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/backtest/quick/{ticker}", response_model=None)
@limiter.limit("5/minute")
def run_quick_backtest(request: Request, ticker: str, period: str = "3M"):
    """Run quick backtest for a ticker."""
    try:
        if quick_backtest is None or BacktestPeriod is None:
            return {
                "ticker": ticker,
                "period": period,
                "error": "Backtesting service not available",
                "performance": {
                    "total_return": 0.0,
                    "sharpe_ratio": 0.0,
                    "max_drawdown": 0.0,
                    "trades": 0,
                },
            }

        # Map period string to enum
        period_map = {
            "1M": BacktestPeriod.ONE_MONTH,
            "3M": BacktestPeriod.THREE_MONTHS,
            "6M": BacktestPeriod.SIX_MONTHS,
            "1Y": BacktestPeriod.ONE_YEAR,
            "2Y": BacktestPeriod.TWO_YEARS,
            "5Y": BacktestPeriod.FIVE_YEARS,
        }

        if period not in period_map:
            raise HTTPException(
                status_code=400, detail=f"Invalid period: {period}. Use: {list(period_map.keys())}"
            )

        results = quick_backtest(ticker, period_map[period])

        return {
            "ticker": ticker,
            "period": period,
            "performance": {
                "total_return": results.total_return,
                "annual_return": results.annual_return,
                "sharpe_ratio": results.sharpe_ratio,
                "max_drawdown": results.max_drawdown,
                "volatility": results.volatility,
            },
            "trades": {
                "total_trades": results.total_trades,
                "winning_trades": results.winning_trades,
                "losing_trades": results.losing_trades,
                "win_rate": results.win_rate,
                "avg_win": results.avg_win,
                "avg_loss": results.avg_loss,
            },
            "config": {
                "initial_capital": results.config.initial_capital,
                "max_position_size": results.config.max_position_size,
                "commission_per_trade": results.config.commission_per_trade,
            },
        }

    except Exception as e:
        logger.error(f"Error running backtest for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/backtest/analysis/{ticker}", response_model=None)
def analyze_signal_quality(ticker: str, period: str = "3M"):
    """Analyze signal quality for a ticker."""
    try:
        if analyze_signals is None or BacktestPeriod is None:
            return {
                "ticker": ticker,
                "period": period,
                "error": "Signal analysis service not available",
                "signal_quality": {
                    "accuracy": 0.0,
                    "precision": 0.0,
                    "recall": 0.0,
                    "signals_analyzed": 0,
                },
            }

        # Map period string to enum
        period_map = {
            "1M": BacktestPeriod.ONE_MONTH,
            "3M": BacktestPeriod.THREE_MONTHS,
            "6M": BacktestPeriod.SIX_MONTHS,
            "1Y": BacktestPeriod.ONE_YEAR,
            "2Y": BacktestPeriod.TWO_YEARS,
            "5Y": BacktestPeriod.FIVE_YEARS,
        }

        if period not in period_map:
            raise HTTPException(
                status_code=400, detail=f"Invalid period: {period}. Use: {list(period_map.keys())}"
            )

        analysis = analyze_signals(ticker, period_map[period])
        return analysis

    except Exception as e:
        logger.error(f"Error analyzing signals for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# ──────────────────────────────────────────────────────────────────────────────
# Cognitive Core Endpoints (ZiggyAI Enhancement)
# ──────────────────────────────────────────────────────────────────────────────

# Import cognitive core components
try:
    from ..data.features import compute_features
    from ..services.fusion import fused_probability
    from ..services.regime import detect_regime

    COGNITIVE_CORE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Cognitive core components not available: {e}")
    COGNITIVE_CORE_AVAILABLE = False


class CognitiveSignalRequest(BaseModel):
    """Request for cognitive core signal generation."""

    symbol: str = Field(..., description="Stock symbol")
    interval: str = Field("1D", description="Time interval")
    dt: str | None = Field(None, description="Date/time for signal (ISO format)")
    include_explanations: bool = Field(True, description="Include feature attributions")


class CognitiveSignalResponse(BaseModel):
    """Response from cognitive core signal generation."""

    symbol: str
    p_up: float = Field(..., description="Probability of upward movement")
    p_up_model: float | None = Field(None, description="Raw model probability")
    p_up_prior: float | None = Field(None, description="Prior from similar events")
    p_up_blend: float | None = Field(None, description="Blended probability")
    confidence: float = Field(..., description="Signal confidence (0-1)")
    regime: str = Field(..., description="Market regime")
    shap_top: list[tuple] = Field(..., description="Top feature attributions")
    neighbors: list[dict[str, Any]] = Field(default_factory=list, description="Similar past events")
    position_size: dict[str, Any] | None = Field(None, description="Position sizing recommendation")
    latency_ms: float = Field(..., description="Processing latency in milliseconds")
    cache_hit: bool = Field(..., description="Whether features were cached")
    event_id: str | None = Field(None, description="Event ID for this decision")


@router.post("/cognitive/signal", response_model=CognitiveSignalResponse)
async def generate_cognitive_signal(request: CognitiveSignalRequest):
    """
    Generate signal using ZiggyAI Cognitive Core with RAG integration.

    This endpoint integrates:
    - Feature computation with caching
    - Regime detection
    - Signal fusion with explainability
    - Retrieval-Augmented Generation (RAG) for prior probabilities
    - Position sizing recommendations
    - Event logging for continuous learning
    """
    if not COGNITIVE_CORE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Cognitive core components not available")

    start_time = datetime.now()

    try:
        # Parse datetime
        if request.dt:
            dt = datetime.fromisoformat(request.dt.replace("Z", "+00:00"))
        else:
            dt = datetime.now()

        # Compute features
        features = compute_features(ticker=request.symbol, dt=dt, interval=request.interval)

        # Detect regime
        regime_info = detect_regime(features)
        regime = regime_info["regime"]

        # Generate raw model probability
        signal_result = fused_probability(features, regime)
        p_up_model = signal_result["p_up"]

        # RAG: Retrieve similar past events and compute prior
        neighbors = []
        p_up_prior = None
        p_up_blend = p_up_model  # Default to model prediction

        if RAG_ENABLED:
            try:
                # Build event for similarity search
                event_context = {
                    "ticker": request.symbol,
                    "regime": regime,
                    "explain": {"shap_top": signal_result.get("shap_top", [])},
                }

                # Create embedding and search for similar events
                embedding = build_embedding(event_context)
                neighbors = search_similar(embedding, k=KNN_K)

                # Compute prior from neighbors with outcomes
                neighbor_outcomes = []
                for neighbor in neighbors:
                    metadata = neighbor.get("metadata", {})
                    p_outcome = metadata.get("p_outcome")
                    if p_outcome is not None:
                        neighbor_outcomes.append(p_outcome)

                # Calculate prior as average of neighbor outcomes
                if neighbor_outcomes:
                    p_up_prior = sum(neighbor_outcomes) / len(neighbor_outcomes)

                    # Blend model prediction with prior
                    p_up_blend = RAG_PRIOR_WEIGHT * p_up_prior + (1 - RAG_PRIOR_WEIGHT) * p_up_model

                    logger.info(
                        f"RAG blending for {request.symbol}: "
                        f"model={p_up_model:.3f}, prior={p_up_prior:.3f}, "
                        f"blend={p_up_blend:.3f}, neighbors={len(neighbors)}"
                    )

            except Exception as e:
                logger.warning(f"RAG retrieval failed: {e}")

        # Build event for storage (without outcome yet)
        event_data = build_durable_event(
            ticker=request.symbol,
            features_v="1.0.0",  # Should come from features metadata
            regime=regime,
            p_up=p_up_blend,
            decision=None,  # Will be set if user acts on signal
            size=None,  # Will be set if user acts on signal
            explain={"shap_top": signal_result.get("shap_top", [])},
            neighbors=[
                {"id": n.get("id"), "p_outcome": n.get("metadata", {}).get("p_outcome")}
                for n in neighbors
            ],
        )

        # Store event and get ID
        event_id = append_event(event_data)

        # Upsert vector for future retrieval (if RAG enabled)
        if RAG_ENABLED:
            try:
                # Prepare metadata for vector storage
                vector_metadata = {
                    "ticker": request.symbol,
                    "regime": regime,
                    "ts": event_data["ts"],
                    "p_up": p_up_blend,
                }

                embedding = build_embedding(event_data)
                upsert_event(event_id, embedding, vector_metadata)

            except Exception as e:
                logger.warning(f"Vector upsert failed: {e}")

        # Position sizing (optional)
        position_size = None
        if signal_result["confidence"] > 0.5:  # Only size if confident
            try:
                # Mock current price for position sizing
                current_price = 100.0  # In production, get real price
                account_equity = 100000.0  # In production, get from user account

                position_size = compute_position(
                    account_equity=account_equity,
                    symbol=request.symbol,
                    current_price=current_price,
                    signal_probability=p_up_blend,
                    signal_confidence=signal_result["confidence"],
                )
            except Exception as e:
                logger.warning(f"Position sizing failed: {e}")

        # Calculate latency
        end_time = datetime.now()
        latency_ms = (end_time - start_time).total_seconds() * 1000

        # Check for cache hit (simplified)
        cache_hit = latency_ms < 50  # Assume cache hit if very fast

        # Ensure shap_top is a list of tuples
        shap_top = signal_result.get("shap_top", [])
        if not isinstance(shap_top, list):
            shap_top = []  # Default to empty list if not proper format

        return CognitiveSignalResponse(
            symbol=request.symbol,
            p_up=p_up_blend,
            p_up_model=p_up_model,
            p_up_prior=p_up_prior,
            p_up_blend=p_up_blend,
            confidence=signal_result["confidence"],
            regime=regime,
            shap_top=shap_top,
            neighbors=neighbors,
            position_size=position_size,
            latency_ms=latency_ms,
            cache_hit=cache_hit,
            event_id=event_id,
        )

    except Exception as e:
        logger.error(f"Cognitive signal generation failed for {request.symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/cognitive/regime/{symbol}", response_model=None)
async def get_regime_analysis(
    symbol: str,
    interval: str = Query("1D", description="Time interval"),
    dt: str | None = Query(None, description="Date/time (ISO format)"),
):
    """Get detailed regime analysis for a symbol."""
    if not COGNITIVE_CORE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Cognitive core components not available")

    try:
        # Parse datetime
        dt_parsed = datetime.fromisoformat(dt.replace("Z", "+00:00")) if dt else datetime.now()

        # Compute features
        features = compute_features(ticker=symbol, dt=dt_parsed, interval=interval)

        # Get detailed regime analysis
        regime_analysis = detect_regime(features)

        return {
            "symbol": symbol,
            "regime_analysis": regime_analysis,
            "features_used": {
                k: v
                for k, v in features.items()
                if k in ["volatility_20d", "liquidity_score", "vix_level"]
            },
            "timestamp": dt_parsed.isoformat(),
        }

    except Exception as e:
        logger.error(f"Regime analysis failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/cognitive/bulk", response_model=None)
async def generate_bulk_cognitive_signals(
    symbols: list[str] = Query(..., description="List of symbols"),
    interval: str = Query("1D", description="Time interval"),
    dt: str | None = Query(None, description="Date/time (ISO format)"),
):
    """Generate cognitive signals for multiple symbols efficiently."""
    if not COGNITIVE_CORE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Cognitive core components not available")

    if len(symbols) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 symbols per bulk request")

    start_time = datetime.now()

    try:
        # Parse datetime
        dt_parsed = datetime.fromisoformat(dt.replace("Z", "+00:00")) if dt else datetime.now()

        results = []
        feature_list = []
        regime_list = []

        # Compute features for all symbols
        for symbol in symbols:
            try:
                features = compute_features(ticker=symbol, dt=dt_parsed, interval=interval)
                regime_info = detect_regime(features)

                feature_list.append(features)
                regime_list.append(regime_info["regime"])

            except Exception as e:
                logger.warning(f"Failed to compute features for {symbol}: {e}")
                feature_list.append({})
                regime_list.append("base")

        # Bulk signal generation
        try:
            from ..services.fusion import bulk_predict

            signal_results = bulk_predict(feature_list, regime_list)
        except ImportError:
            # Fallback to individual predictions
            signal_results = []
            for features, regime in zip(feature_list, regime_list, strict=False):
                if features:
                    signal_results.append(fused_probability(features, regime))
                else:
                    signal_results.append(
                        {"p_up": 0.5, "confidence": 0.0, "shap_top": [], "regime": regime}
                    )

        # Format results
        for i, symbol in enumerate(symbols):
            if i < len(signal_results):
                result = signal_results[i]
                results.append(
                    {
                        "symbol": symbol,
                        "p_up": result["p_up"],
                        "confidence": result["confidence"],
                        "regime": result["regime"],
                        "shap_top": result["shap_top"][:3],  # Top 3 only for bulk
                    }
                )
            else:
                results.append(
                    {
                        "symbol": symbol,
                        "p_up": 0.5,
                        "confidence": 0.0,
                        "regime": "base",
                        "shap_top": [],
                        "error": "Processing failed",
                    }
                )

        # Calculate total latency
        end_time = datetime.now()
        total_latency_ms = (end_time - start_time).total_seconds() * 1000

        return {
            "results": results,
            "total_symbols": len(symbols),
            "successful_symbols": len([r for r in results if "error" not in r]),
            "total_latency_ms": total_latency_ms,
            "avg_latency_per_symbol": total_latency_ms / len(symbols),
            "timestamp": dt_parsed.isoformat(),
        }

    except Exception as e:
        logger.error(f"Bulk cognitive signals failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/cognitive/health", response_model=None)
async def cognitive_health_check():
    """Health check for cognitive core components."""

    health_status = {
        "cognitive_core_available": COGNITIVE_CORE_AVAILABLE,
        "components": {},
        "timestamp": datetime.now().isoformat(),
    }

    if COGNITIVE_CORE_AVAILABLE:
        # Test each component
        try:
            from ..data.features import compute_features

            # Quick test
            test_features = compute_features("AAPL", datetime.now())
            health_status["components"]["feature_store"] = {
                "status": "healthy",
                "test_feature_count": len(test_features),
            }
        except Exception as e:
            health_status["components"]["feature_store"] = {"status": "error", "error": str(e)}

        try:
            from ..services.regime import detect_regime

            test_regime = detect_regime(
                {"volatility_20d": 0.2, "liquidity_score": 0.5, "vix_level": 20}
            )
            health_status["components"]["regime_detection"] = {
                "status": "healthy",
                "test_regime": test_regime["regime"],
            }
        except Exception as e:
            health_status["components"]["regime_detection"] = {"status": "error", "error": str(e)}

        try:
            from ..services.fusion import fused_probability

            test_signal = fused_probability({"momentum_20d": 0.1}, "base")
            health_status["components"]["signal_fusion"] = {
                "status": "healthy",
                "test_probability": test_signal["p_up"],
            }
        except Exception as e:
            health_status["components"]["signal_fusion"] = {"status": "error", "error": str(e)}

    return health_status
