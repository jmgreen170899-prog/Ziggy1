"""
Screener API Routes for ZiggyAI Cognitive Core

Provides market screening and scanning functionality using the cognitive core.
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/screener", tags=["screening"])

# Import cognitive core components
try:
    from ..data.features import compute_features
    from ..services.fusion import fused_probability
    from ..services.position_sizing import compute_position
    from ..services.regime import detect_regime

    COGNITIVE_CORE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Cognitive core components not available: {e}")
    COGNITIVE_CORE_AVAILABLE = False


class ScreenerRequest(BaseModel):
    """Request for market screening."""

    universe: list[str] = Field(..., description="List of symbols to screen")
    min_confidence: float = Field(0.6, description="Minimum signal confidence")
    min_probability: float | None = Field(None, description="Minimum probability threshold")
    max_probability: float | None = Field(None, description="Maximum probability threshold")
    regimes: list[str] | None = Field(None, description="Filter by specific regimes")
    sort_by: str = Field("confidence", description="Sort by: confidence, probability, regime")
    limit: int = Field(50, description="Maximum results to return")


class ScreenerResult(BaseModel):
    """Screener result for a single symbol."""

    symbol: str
    p_up: float
    confidence: float
    regime: str
    top_features: list[tuple]
    score: float  # Combined score for ranking
    position_size: dict[str, Any] | None = None


class ScreenerResponse(BaseModel):
    """Response from screener."""

    results: list[ScreenerResult]
    total_screened: int
    filters_applied: dict[str, Any]
    execution_time_ms: float
    regime_breakdown: dict[str, int]


class ScreenerHealthResponse(BaseModel):
    """Screener health check response."""

    cognitive_core_available: bool = Field(
        ..., description="Whether cognitive core is available"
    )
    supported_universes: list[str] = Field(..., description="Supported symbol universes")
    max_symbols_per_request: int = Field(..., description="Maximum symbols per request")
    available_presets: list[str] = Field(..., description="Available screening presets")
    timestamp: str = Field(..., description="Response timestamp")


@router.post("/scan", response_model=ScreenerResponse)
async def screen_market(request: ScreenerRequest):
    """
    Screen market using cognitive core for high-quality signals.

    Processes multiple symbols and returns those meeting criteria,
    sorted by signal quality and confidence.
    """
    if not COGNITIVE_CORE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Cognitive core components not available")

    start_time = datetime.now()

    try:
        if len(request.universe) > 500:
            raise HTTPException(status_code=400, detail="Maximum 500 symbols per screening request")

        results = []
        regime_counts = {}
        dt = datetime.now()

        # Process each symbol
        for symbol in request.universe:
            try:
                # Compute features
                features = compute_features(ticker=symbol, dt=dt)

                # Detect regime
                regime_info = detect_regime(features)
                regime = regime_info["regime"]

                # Count regimes
                regime_counts[regime] = regime_counts.get(regime, 0) + 1

                # Apply regime filter
                if request.regimes and regime not in request.regimes:
                    continue

                # Generate signal
                signal_result = fused_probability(features, regime)
                p_up = signal_result["p_up"]
                confidence = signal_result["confidence"]

                # Apply filters
                if confidence < request.min_confidence:
                    continue

                if request.min_probability and p_up < request.min_probability:
                    continue

                if request.max_probability and p_up > request.max_probability:
                    continue

                # Calculate combined score for ranking
                signal_strength = abs(p_up - 0.5) * 2  # 0 to 1
                score = confidence * 0.6 + signal_strength * 0.4

                # Get top features for explanation
                top_features = signal_result["shap_top"][:3]

                # Optional position sizing for high-confidence signals
                position_size = None
                if confidence > 0.8:
                    try:
                        position_size = compute_position(
                            account_equity=100000.0,  # Default account size
                            symbol=symbol,
                            current_price=100.0,  # Mock price
                            signal_probability=p_up,
                            signal_confidence=confidence,
                        )
                    except Exception as e:
                        logger.warning(f"Position sizing failed for {symbol}: {e}")

                results.append(
                    ScreenerResult(
                        symbol=symbol,
                        p_up=p_up,
                        confidence=confidence,
                        regime=regime,
                        top_features=top_features,
                        score=score,
                        position_size=position_size,
                    )
                )

            except Exception as e:
                logger.warning(f"Failed to process {symbol}: {e}")
                continue

        # Sort results
        if request.sort_by == "confidence":
            results.sort(key=lambda x: x.confidence, reverse=True)
        elif request.sort_by == "probability":
            results.sort(key=lambda x: abs(x.p_up - 0.5), reverse=True)
        elif request.sort_by == "regime":
            results.sort(key=lambda x: x.regime)
        else:  # score (default)
            results.sort(key=lambda x: x.score, reverse=True)

        # Apply limit
        results = results[: request.limit]

        # Calculate execution time
        end_time = datetime.now()
        execution_time_ms = (end_time - start_time).total_seconds() * 1000

        return ScreenerResponse(
            results=results,
            total_screened=len(request.universe),
            filters_applied={
                "min_confidence": request.min_confidence,
                "min_probability": request.min_probability,
                "max_probability": request.max_probability,
                "regimes": request.regimes,
                "limit": request.limit,
            },
            execution_time_ms=execution_time_ms,
            regime_breakdown=regime_counts,
        )

    except Exception as e:
        logger.error(f"Market screening failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/universe/sp500")
async def get_sp500_universe():
    """Get S&P 500 universe for screening."""
    # Mock S&P 500 symbols - in production, this would come from a data provider
    sp500_symbols = [
        "AAPL",
        "MSFT",
        "GOOGL",
        "AMZN",
        "TSLA",
        "META",
        "NVDA",
        "BRK-B",
        "UNH",
        "V",
        "JNJ",
        "WMT",
        "JPM",
        "PG",
        "MA",
        "CVX",
        "HD",
        "BAC",
        "ABBV",
        "PFE",
        "KO",
        "AVGO",
        "PEP",
        "TMO",
        "COST",
        "DIS",
        "ABT",
        "NFLX",
        "ADBE",
        "CRM",
        "ACN",
        "VZ",
        "CSCO",
        "INTC",
        "TXN",
        "QCOM",
        "ORCL",
        "LLY",
        "XOM",
        "DHR",
        "NKE",
        "CMCSA",
        "BMY",
        "PM",
        "UPS",
        "HON",
        "NEE",
        "T",
        "AMGN",
        "COP",
    ]

    return {
        "universe": "sp500",
        "symbols": sp500_symbols,
        "count": len(sp500_symbols),
        "last_updated": datetime.now().isoformat(),
    }


@router.get("/universe/nasdaq100")
async def get_nasdaq100_universe():
    """Get NASDAQ 100 universe for screening."""
    # Mock NASDAQ 100 symbols
    nasdaq100_symbols = [
        "AAPL",
        "MSFT",
        "GOOGL",
        "GOOG",
        "AMZN",
        "TSLA",
        "META",
        "NVDA",
        "ADBE",
        "NFLX",
        "CRM",
        "ORCL",
        "CSCO",
        "INTC",
        "TXN",
        "QCOM",
        "AVGO",
        "AMD",
        "INTU",
        "ISRG",
        "BKNG",
        "CMCSA",
        "TMUS",
        "AMAT",
        "MU",
        "ADI",
        "LRCX",
        "MDLZ",
        "REGN",
        "GILD",
        "ATVI",
        "PYPL",
        "CHTR",
        "MRVL",
        "NXPI",
        "KLAC",
        "MRNA",
        "DXCM",
        "ILMN",
        "BIIB",
        "KDP",
        "SNPS",
        "CDNS",
        "MCHP",
        "ASML",
        "CSX",
        "ORLY",
        "WDAY",
        "FTNT",
        "MNST",
    ]

    return {
        "universe": "nasdaq100",
        "symbols": nasdaq100_symbols,
        "count": len(nasdaq100_symbols),
        "last_updated": datetime.now().isoformat(),
    }


@router.get("/presets/momentum")
async def momentum_screen(
    universe: str = Query("sp500", description="Universe to screen"),
    min_confidence: float = Query(0.7, description="Minimum confidence"),
):
    """Pre-configured momentum screening."""
    if not COGNITIVE_CORE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Cognitive core components not available")

    # Get universe
    if universe == "sp500":
        symbols = (await get_sp500_universe())["symbols"]
    elif universe == "nasdaq100":
        symbols = (await get_nasdaq100_universe())["symbols"]
    else:
        raise HTTPException(status_code=400, detail="Invalid universe")

    # Configure momentum screen
    request = ScreenerRequest(
        universe=symbols,
        min_confidence=min_confidence,
        min_probability=0.65,  # Bullish bias
        regimes=["base", "vol_lo_liq_hi"],  # Favorable regimes for momentum
        sort_by="confidence",
        limit=20,
    )

    return await screen_market(request)


@router.get("/presets/mean_reversion")
async def mean_reversion_screen(
    universe: str = Query("sp500", description="Universe to screen"),
    min_confidence: float = Query(0.7, description="Minimum confidence"),
):
    """Pre-configured mean reversion screening."""
    if not COGNITIVE_CORE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Cognitive core components not available")

    # Get universe
    if universe == "sp500":
        symbols = (await get_sp500_universe())["symbols"]
    elif universe == "nasdaq100":
        symbols = (await get_nasdaq100_universe())["symbols"]
    else:
        raise HTTPException(status_code=400, detail="Invalid universe")

    # Configure mean reversion screen
    request = ScreenerRequest(
        universe=symbols,
        min_confidence=min_confidence,
        min_probability=0.3,  # Look for oversold
        max_probability=0.7,  # But not overbought
        regimes=["vol_hi_liq_lo", "stress"],  # Regimes where mean reversion works
        sort_by="confidence",
        limit=20,
    )

    return await screen_market(request)


@router.get("/regime_summary")
async def get_regime_summary(universe: str = Query("sp500", description="Universe to analyze")):
    """Get regime breakdown for a universe."""
    if not COGNITIVE_CORE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Cognitive core components not available")

    try:
        # Get universe
        if universe == "sp500":
            symbols = (await get_sp500_universe())["symbols"]
        elif universe == "nasdaq100":
            symbols = (await get_nasdaq100_universe())["symbols"]
        else:
            raise HTTPException(status_code=400, detail="Invalid universe")

        # Sample subset for performance
        sample_symbols = symbols[:50]  # Sample 50 symbols

        regime_counts = {}
        regime_examples = {}
        dt = datetime.now()

        for symbol in sample_symbols:
            try:
                features = compute_features(ticker=symbol, dt=dt)
                regime_info = detect_regime(features)
                regime = regime_info["regime"]

                regime_counts[regime] = regime_counts.get(regime, 0) + 1

                if regime not in regime_examples:
                    regime_examples[regime] = []
                if len(regime_examples[regime]) < 3:
                    regime_examples[regime].append(
                        {
                            "symbol": symbol,
                            "confidence": regime_info["confidence"],
                            "description": regime_info["description"],
                        }
                    )

            except Exception as e:
                logger.warning(f"Failed to analyze regime for {symbol}: {e}")
                continue

        # Calculate percentages
        total = sum(regime_counts.values())
        regime_percentages = {
            regime: (count / total * 100) if total > 0 else 0
            for regime, count in regime_counts.items()
        }

        return {
            "universe": universe,
            "sample_size": len(sample_symbols),
            "regime_counts": regime_counts,
            "regime_percentages": regime_percentages,
            "regime_examples": regime_examples,
            "timestamp": dt.isoformat(),
        }

    except Exception as e:
        logger.error(f"Regime summary failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=ScreenerHealthResponse)
async def screener_health_check() -> ScreenerHealthResponse:
    """
    Health check for screener functionality.
    
    Returns availability status and configuration information.
    """
    return ScreenerHealthResponse(
        cognitive_core_available=COGNITIVE_CORE_AVAILABLE,
        supported_universes=["sp500", "nasdaq100"],
        max_symbols_per_request=500,
        available_presets=["momentum", "mean_reversion"],
        timestamp=datetime.now().isoformat(),
    )
