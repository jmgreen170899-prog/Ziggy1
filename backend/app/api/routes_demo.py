"""
Demo mode endpoints.

Provides demo status and configuration information.
"""
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.demo import is_demo_mode
from app.demo.data_generators import (
    get_demo_backtest_result,
    get_demo_cognitive_response,
    get_demo_market_data,
    get_demo_news,
    get_demo_portfolio,
    get_demo_screener_results,
    get_demo_signals,
)

router = APIRouter(prefix="/demo", tags=["demo"])


class DemoStatusResponse(BaseModel):
    """Demo mode status response."""
    demo_mode: bool
    message: str
    safe_actions_only: bool
    features_disabled: list[str]


class DemoDataResponse(BaseModel):
    """Demo data sample response."""
    data_type: str
    sample_data: dict[str, Any]


@router.get("/status", response_model=DemoStatusResponse)
async def get_demo_status() -> DemoStatusResponse:
    """
    Get current demo mode status.
    
    Returns information about whether demo mode is active and what features are disabled.
    """
    demo_active = is_demo_mode()
    
    features_disabled = []
    if demo_active:
        features_disabled = [
            "real_trading",
            "data_ingestion",
            "system_modifications",
            "live_market_data",
        ]
    
    return DemoStatusResponse(
        demo_mode=demo_active,
        message="Demo mode is active - using deterministic demo data" if demo_active else "Demo mode is disabled - using live data",
        safe_actions_only=demo_active,
        features_disabled=features_disabled,
    )


@router.get("/data/market", response_model=DemoDataResponse)
async def get_demo_market_sample(ticker: str = "AAPL") -> DemoDataResponse:
    """Get demo market data sample."""
    return DemoDataResponse(
        data_type="market_data",
        sample_data=get_demo_market_data(ticker),
    )


@router.get("/data/portfolio", response_model=DemoDataResponse)
async def get_demo_portfolio_sample() -> DemoDataResponse:
    """Get demo portfolio sample."""
    return DemoDataResponse(
        data_type="portfolio",
        sample_data=get_demo_portfolio(),
    )


@router.get("/data/signals", response_model=DemoDataResponse)
async def get_demo_signals_sample(ticker: str = "AAPL") -> DemoDataResponse:
    """Get demo signals sample."""
    return DemoDataResponse(
        data_type="signals",
        sample_data=get_demo_signals(ticker),
    )


@router.get("/data/news", response_model=DemoDataResponse)
async def get_demo_news_sample(ticker: str | None = None) -> DemoDataResponse:
    """Get demo news sample."""
    return DemoDataResponse(
        data_type="news",
        sample_data={"articles": get_demo_news(ticker)},
    )


@router.get("/data/backtest", response_model=DemoDataResponse)
async def get_demo_backtest_sample(symbol: str = "AAPL", strategy: str = "sma50_cross") -> DemoDataResponse:
    """Get demo backtest sample."""
    return DemoDataResponse(
        data_type="backtest",
        sample_data=get_demo_backtest_result(symbol, strategy),
    )


@router.get("/data/screener", response_model=DemoDataResponse)
async def get_demo_screener_sample(preset: str = "momentum") -> DemoDataResponse:
    """Get demo screener results sample."""
    return DemoDataResponse(
        data_type="screener",
        sample_data={"results": get_demo_screener_results(preset)},
    )


@router.get("/data/cognitive", response_model=DemoDataResponse)
async def get_demo_cognitive_sample(question: str = "What should I know about AAPL?") -> DemoDataResponse:
    """Get demo cognitive response sample."""
    return DemoDataResponse(
        data_type="cognitive",
        sample_data=get_demo_cognitive_response(question),
    )
