# app/models/api_responses.py
"""
Standardized API response models for consistent contract across all endpoints.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standardized error response for all API errors."""

    detail: str = Field(..., description="Human-readable error message")
    code: str = Field(..., description="Machine-readable error code")
    meta: dict[str, Any] = Field(
        default_factory=dict, description="Additional error context and metadata"
    )


class AckResponse(BaseModel):
    """Simple acknowledgment response for operations that don't return data."""

    ok: bool = Field(True, description="Operation succeeded")
    message: str | None = Field(None, description="Optional success message")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Health status (ok, degraded, error)")
    details: dict[str, Any] = Field(default_factory=dict, description="Health check details")


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str = Field(..., description="Response message")
    data: dict[str, Any] | None = Field(None, description="Optional response data")


# ── Market Endpoint Response Models ──────────────────────────────────────────


class SymbolData(BaseModel):
    """Price data for a single symbol."""

    last: float | None = Field(None, description="Last price")
    chg1d: float | None = Field(None, description="1-day percentage change")
    chg5d: float | None = Field(None, description="5-day percentage change")
    chg20d: float | None = Field(None, description="20-day percentage change")
    ref: float | None = Field(None, description="Reference price for change calculation")


class MarketOverviewResponse(BaseModel):
    """Response for market overview endpoint."""

    asof: float = Field(..., description="Timestamp of data")
    since_open: bool = Field(..., description="Whether changes are since market open")
    symbols: dict[str, dict[str, float | None] | None] = Field(..., description="Symbol price data")
    source: dict[str, str | None] | None = Field(None, description="Data source per symbol (debug only)")
    provider_chain: list[str] | None = Field(None, description="Provider chain (debug only)")
    
    class Config:
        extra = "allow"  # Allow market brain to add additional fields


class MarketBreadthResponse(BaseModel):
    """Response for market breadth endpoint."""

    advancing: int | None = Field(None, description="Number of advancing stocks")
    declining: int | None = Field(None, description="Number of declining stocks")
    unchanged: int | None = Field(None, description="Number of unchanged stocks")
    advancers: int | None = Field(None, description="Advancers count (alias)")
    decliners: int | None = Field(None, description="Decliners count (alias)")
    ad_ratio: float | None = Field(None, description="Advance/decline ratio")
    new_highs: int | None = Field(None, description="Number of new highs")
    new_lows: int | None = Field(None, description="Number of new lows")
    detail: dict[str, Any] | None = Field(None, description="Additional breadth details")


class CPCData(BaseModel):
    """Put/Call ratio data."""

    ticker: str = Field(..., description="Ticker symbol (^CPC or ^CPCE)")
    last: float = Field(..., description="Current Put/Call ratio")
    ma20: float = Field(..., description="20-day moving average")
    z20: float = Field(..., description="Z-score relative to 20-day period")
    date: str = Field(..., description="Date of data")


class MarketRiskLiteResponse(BaseModel):
    """Response for market risk-lite endpoint."""

    cpc: CPCData | None = Field(None, description="Put/Call ratio data")
    error: str | None = Field(None, description="Error message if data unavailable")


class MarketHolidaysResponse(BaseModel):
    """Response for market holidays endpoint."""

    holidays: list[dict[str, Any]] = Field(..., description="List of market holidays")
    year: int = Field(..., description="Year of holidays")


class EarningsCalendarResponse(BaseModel):
    """Response for earnings calendar endpoint."""

    earnings: list[dict[str, Any]] = Field(..., description="List of earnings events")
    start_date: str = Field(..., description="Start date of range")
    end_date: str = Field(..., description="End date of range")


class MarketCalendarResponse(BaseModel):
    """Response for market calendar endpoint."""

    holidays: list[dict[str, Any]] | None = Field(None, description="Market holidays")
    earnings: list[dict[str, Any]] | None = Field(None, description="Earnings events")
    economic: list[dict[str, Any]] | None = Field(None, description="Economic events")


class MarketScheduleResponse(BaseModel):
    """Response for market schedule endpoint."""

    schedule: dict[str, Any] = Field(..., description="Market trading schedule")


class MarketIndicatorsResponse(BaseModel):
    """Response for market indicators endpoint."""

    indicators: dict[str, Any] = Field(..., description="Market indicators data")


class FREDDataResponse(BaseModel):
    """Response for FRED data series endpoint."""

    series_id: str = Field(..., description="FRED series ID")
    data: list[dict[str, Any]] = Field(..., description="Time series data points")
    observations: int | None = Field(None, description="Number of observations")


class MacroHistoryResponse(BaseModel):
    """Response for macro history endpoint."""

    data: dict[str, Any] = Field(..., description="Macro economic history data")


# ── Signals Endpoint Response Models ─────────────────────────────────────────


class TickerFeaturesResponse(BaseModel):
    """Response for ticker features endpoint."""

    ticker: str = Field(..., description="Stock symbol")
    features: dict[str, Any] = Field(..., description="Technical features")
    status: str = Field(..., description="Response status")
    
    class Config:
        extra = "allow"


class BulkFeaturesResponse(BaseModel):
    """Response for bulk features endpoint."""

    features: dict[str, dict[str, Any] | None] = Field(..., description="Features by ticker")
    count: int = Field(..., description="Number of tickers with features")
    status: str = Field(..., description="Response status")


class RegimeResponse(BaseModel):
    """Response for current regime endpoint."""

    regime: dict[str, Any] = Field(..., description="Current market regime information")
    status: str = Field(..., description="Response status")


class RegimeHistoryResponse(BaseModel):
    """Response for regime history endpoint."""

    history: list[dict[str, Any]] = Field(..., description="Historical regime data")
    days: int = Field(..., description="Number of days of history")
    count: int = Field(..., description="Number of history records")
    status: str = Field(..., description="Response status")


class TickerSignalResponse(BaseModel):
    """Response for ticker signal endpoint."""

    ticker: str = Field(..., description="Stock symbol")
    signal: dict[str, Any] | None = Field(None, description="Trading signal data")
    has_signal: bool = Field(..., description="Whether signal is available")
    features: dict[str, Any] | None = Field(None, description="Optional raw features")
    regime: dict[str, Any] | None = Field(None, description="Optional regime context")
    explanation: str | None = Field(None, description="Optional signal explanation")
    status: str = Field(..., description="Response status")
    
    class Config:
        extra = "allow"


class WatchlistSignalsResponse(BaseModel):
    """Response for watchlist signals endpoint."""

    signals: list[dict[str, Any]] = Field(..., description="List of signals for watchlist")
    total: int = Field(..., description="Total number of tickers processed")
    with_signals: int = Field(..., description="Number of tickers with signals")
    regime: dict[str, Any] | None = Field(None, description="Optional regime context")
    status: str = Field(..., description="Response status")


class TradePlanResponse(BaseModel):
    """Response for trade plan endpoint."""

    ticker: str = Field(..., description="Stock symbol")
    plan: dict[str, Any] = Field(..., description="Trade plan details")
    position_size: dict[str, Any] | None = Field(None, description="Position sizing recommendation")
    risk_assessment: dict[str, Any] | None = Field(None, description="Risk assessment")
    status: str = Field(..., description="Response status")


class TradeExecutionResponse(BaseModel):
    """Response for trade execution endpoint."""

    request_id: str = Field(..., description="Execution request ID")
    ticker: str = Field(..., description="Stock symbol")
    status: str = Field(..., description="Execution status")
    order_id: str | None = Field(None, description="Broker order ID if executed")
    filled_quantity: int | None = Field(None, description="Number of shares filled")
    filled_price: float | None = Field(None, description="Average fill price")
    executed_value: float | None = Field(None, description="Total execution value")
    message: str | None = Field(None, description="Status message")


class ExecutionStatusResponse(BaseModel):
    """Response for execution status endpoint."""

    request_id: str = Field(..., description="Execution request ID")
    status: str = Field(..., description="Current status")
    ticker: str = Field(..., description="Stock symbol")
    filled_quantity: int = Field(..., description="Number of shares filled")
    filled_price: float | None = Field(None, description="Average fill price")
    executed_value: float | None = Field(None, description="Total execution value")
    timestamp: str | None = Field(None, description="Last update timestamp")
    validation_errors: list[str] | None = Field(None, description="Validation errors if any")


class ExecutionHistoryResponse(BaseModel):
    """Response for execution history endpoint."""

    executions: list[dict[str, Any]] = Field(..., description="List of execution records")
    total_count: int = Field(..., description="Total number of executions")
    error: str | None = Field(None, description="Error message if service unavailable")


class ExecutionStatsResponse(BaseModel):
    """Response for execution statistics endpoint."""

    daily_stats: dict[str, Any] = Field(..., description="Daily execution statistics")
    error: str | None = Field(None, description="Error message if service unavailable")


class BacktestResponse(BaseModel):
    """Response for backtest endpoint."""

    ticker: str = Field(..., description="Stock symbol")
    period: str = Field(..., description="Backtest period")
    performance: dict[str, Any] = Field(..., description="Performance metrics")
    trades: list[dict[str, Any]] | None = Field(None, description="Trade history")
    error: str | None = Field(None, description="Error message if service unavailable")


class BacktestAnalysisResponse(BaseModel):
    """Response for backtest analysis endpoint."""

    ticker: str = Field(..., description="Stock symbol")
    period: str = Field(..., description="Analysis period")
    signal_quality: dict[str, Any] = Field(..., description="Signal quality metrics")
    detailed_metrics: dict[str, Any] | None = Field(None, description="Detailed analysis")
    error: str | None = Field(None, description="Error message if service unavailable")


class SystemStatusResponse(BaseModel):
    """Response for system status endpoint."""

    status: str = Field(..., description="Overall system status")
    components: dict[str, bool] = Field(..., description="Component availability status")
    current_regime: str | None = Field(None, description="Current market regime")
    regime_confidence: float | None = Field(None, description="Regime detection confidence")
    timestamp: str | None = Field(None, description="Status timestamp")
    error: str | None = Field(None, description="Error message if degraded")


class SystemConfigResponse(BaseModel):
    """Response for system config endpoint."""

    regime_thresholds: dict[str, Any] = Field(..., description="Regime detection thresholds")
    signal_parameters: dict[str, Any] = Field(..., description="Signal generation parameters")
    position_sizing_config: dict[str, Any] = Field(..., description="Position sizing configuration")
    account_size: float = Field(..., description="Account size for position sizing")


class ConfigUpdateResponse(BaseModel):
    """Response for config update endpoint."""

    status: str = Field(..., description="Update status")
    updated_components: list[str] = Field(..., description="List of updated components")
    message: str = Field(..., description="Status message")


class CognitiveBulkResponse(BaseModel):
    """Response for cognitive bulk signal generation."""

    signals: list[dict[str, Any]] = Field(..., description="List of cognitive signals")
    total: int = Field(..., description="Total symbols processed")
    successful: int = Field(..., description="Number of successful signals")
    failed: int = Field(..., description="Number of failed signals")


class CognitiveRegimeResponse(BaseModel):
    """Response for cognitive regime detection."""

    symbol: str = Field(..., description="Stock symbol")
    regime: str = Field(..., description="Detected regime")
    confidence: float = Field(..., description="Regime confidence")
    features: dict[str, Any] | None = Field(None, description="Features used for detection")
    timestamp: str = Field(..., description="Detection timestamp")


# ── Screener Endpoint Response Models ────────────────────────────────────────


class UniverseResponse(BaseModel):
    """Response for universe endpoints."""

    universe: str = Field(..., description="Universe name (sp500, nasdaq100, etc)")
    symbols: list[str] = Field(..., description="List of symbols in universe")
    count: int = Field(..., description="Number of symbols")
    last_updated: str = Field(..., description="Last update timestamp")


class RegimeSummaryResponse(BaseModel):
    """Response for regime summary endpoint."""

    universe: str = Field(..., description="Universe analyzed")
    total_symbols: int = Field(..., description="Total symbols analyzed")
    regime_breakdown: dict[str, int] = Field(..., description="Count by regime")
    regime_percentages: dict[str, float] = Field(..., description="Percentage by regime")
    timestamp: str = Field(..., description="Analysis timestamp")


# ── Cognitive Endpoint Response Models ───────────────────────────────────────


class CognitiveStatusResponse(BaseModel):
    """Response for cognitive system status."""

    meta_learning: dict[str, Any] = Field(..., description="Meta-learning system status")
    episodic_memory: dict[str, Any] = Field(..., description="Episodic memory statistics")
    counterfactual: dict[str, Any] = Field(..., description="Counterfactual analysis status")
    timestamp: str = Field(..., description="Status timestamp")


class OutcomeRecordResponse(BaseModel):
    """Response for recording decision outcome."""

    status: str = Field(..., description="Recording status")
    message: str = Field(..., description="Status message")
    outcome_id: str | None = Field(None, description="Outcome record ID")


class MetaLearningStrategiesResponse(BaseModel):
    """Response for meta-learning strategies."""

    strategies: list[dict[str, Any]] = Field(..., description="Available strategies")
    current_strategy: str | None = Field(None, description="Currently selected strategy")
    performance_history: dict[str, Any] | None = Field(None, description="Strategy performance")


class CounterfactualInsightsResponse(BaseModel):
    """Response for counterfactual insights."""

    insights: list[dict[str, Any]] = Field(..., description="Counterfactual analysis insights")
    total: int = Field(..., description="Total insights available")
    timestamp: str = Field(..., description="Analysis timestamp")


class EpisodicMemoryStatsResponse(BaseModel):
    """Response for episodic memory statistics."""

    total_episodes: int = Field(..., description="Total episodes stored")
    memory_size_mb: float | None = Field(None, description="Memory size in megabytes")
    oldest_episode: str | None = Field(None, description="Oldest episode timestamp")
    newest_episode: str | None = Field(None, description="Newest episode timestamp")
    statistics: dict[str, Any] = Field(..., description="Additional statistics")


class CognitiveHealthResponse(BaseModel):
    """Response for cognitive health check."""

    status: str = Field(..., description="Overall health status")
    components: dict[str, bool] = Field(..., description="Component availability")
    uptime_seconds: float | None = Field(None, description="System uptime")
    timestamp: str = Field(..., description="Health check timestamp")
