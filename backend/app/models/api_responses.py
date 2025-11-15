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
    details: dict[str, Any] = Field(
        default_factory=dict, description="Health check details"
    )


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
    ref: float | None = Field(
        None, description="Reference price for change calculation"
    )


class MarketOverviewResponse(BaseModel):
    """Response for market overview endpoint."""

    asof: float = Field(..., description="Timestamp of data")
    since_open: bool = Field(..., description="Whether changes are since market open")
    symbols: dict[str, dict[str, float | None] | None] = Field(
        ..., description="Symbol price data"
    )
    source: dict[str, str | None] | None = Field(
        None, description="Data source per symbol (debug only)"
    )
    provider_chain: list[str] | None = Field(
        None, description="Provider chain (debug only)"
    )

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
    detail: dict[str, Any] | None = Field(
        None, description="Additional breadth details"
    )


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

    features: dict[str, dict[str, Any] | None] = Field(
        ..., description="Features by ticker"
    )
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

    signals: list[dict[str, Any]] = Field(
        ..., description="List of signals for watchlist"
    )
    total: int = Field(..., description="Total number of tickers processed")
    with_signals: int = Field(..., description="Number of tickers with signals")
    regime: dict[str, Any] | None = Field(None, description="Optional regime context")
    status: str = Field(..., description="Response status")


class TradePlanResponse(BaseModel):
    """Response for trade plan endpoint."""

    ticker: str = Field(..., description="Stock symbol")
    plan: dict[str, Any] = Field(..., description="Trade plan details")
    position_size: dict[str, Any] | None = Field(
        None, description="Position sizing recommendation"
    )
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
    validation_errors: list[str] | None = Field(
        None, description="Validation errors if any"
    )


class ExecutionHistoryResponse(BaseModel):
    """Response for execution history endpoint."""

    executions: list[dict[str, Any]] = Field(
        ..., description="List of execution records"
    )
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
    detailed_metrics: dict[str, Any] | None = Field(
        None, description="Detailed analysis"
    )
    error: str | None = Field(None, description="Error message if service unavailable")


class SystemStatusResponse(BaseModel):
    """Response for system status endpoint."""

    status: str = Field(..., description="Overall system status")
    components: dict[str, bool] = Field(
        ..., description="Component availability status"
    )
    current_regime: str | None = Field(None, description="Current market regime")
    regime_confidence: float | None = Field(
        None, description="Regime detection confidence"
    )
    timestamp: str | None = Field(None, description="Status timestamp")
    error: str | None = Field(None, description="Error message if degraded")


class SystemConfigResponse(BaseModel):
    """Response for system config endpoint."""

    regime_thresholds: dict[str, Any] = Field(
        ..., description="Regime detection thresholds"
    )
    signal_parameters: dict[str, Any] = Field(
        ..., description="Signal generation parameters"
    )
    position_sizing_config: dict[str, Any] = Field(
        ..., description="Position sizing configuration"
    )
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
    features: dict[str, Any] | None = Field(
        None, description="Features used for detection"
    )
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
    regime_percentages: dict[str, float] = Field(
        ..., description="Percentage by regime"
    )
    timestamp: str = Field(..., description="Analysis timestamp")


# ── Cognitive Endpoint Response Models ───────────────────────────────────────


class CognitiveStatusResponse(BaseModel):
    """Response for cognitive system status."""

    meta_learning: dict[str, Any] = Field(
        ..., description="Meta-learning system status"
    )
    episodic_memory: dict[str, Any] = Field(
        ..., description="Episodic memory statistics"
    )
    counterfactual: dict[str, Any] = Field(
        ..., description="Counterfactual analysis status"
    )
    timestamp: str = Field(..., description="Status timestamp")


class OutcomeRecordResponse(BaseModel):
    """Response for recording decision outcome."""

    status: str = Field(..., description="Recording status")
    message: str = Field(..., description="Status message")
    outcome_id: str | None = Field(None, description="Outcome record ID")


class MetaLearningStrategiesResponse(BaseModel):
    """Response for meta-learning strategies."""

    strategies: list[dict[str, Any]] = Field(..., description="Available strategies")
    current_strategy: str | None = Field(
        None, description="Currently selected strategy"
    )
    performance_history: dict[str, Any] | None = Field(
        None, description="Strategy performance"
    )


class CounterfactualInsightsResponse(BaseModel):
    """Response for counterfactual insights."""

    insights: list[dict[str, Any]] = Field(
        ..., description="Counterfactual analysis insights"
    )
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


# ── Trading Endpoint Response Models ─────────────────────────────────────────


class TradeHealthResponse(BaseModel):
    """Response for trade health endpoint."""

    ok: bool = Field(..., description="Overall health status")
    service: str = Field(..., description="Service name")
    scan: bool = Field(..., description="Whether scanning is enabled")
    providers: list[str] = Field(..., description="List of market data providers")
    provider_mode: str | None = Field(None, description="Provider mode (live/demo)")
    telegram: dict[str, Any] | None = Field(None, description="Telegram bot status")


class NotifyResponse(BaseModel):
    """Response for notification endpoints."""

    ok: bool = Field(..., description="Whether notification was successful")
    message: str | None = Field(None, description="Status message")
    error: str | None = Field(None, description="Error message if failed")


class ScanStatusResponse(BaseModel):
    """Response for scan status endpoint."""

    enabled: bool = Field(..., description="Whether scanning is enabled")
    status: str | None = Field(None, description="Status message")


class MarketCalendarResponse(BaseModel):
    """Response for market calendar endpoint."""

    is_open: bool | None = Field(None, description="Whether market is currently open")
    next_open: str | None = Field(None, description="Next market open time")
    next_close: str | None = Field(None, description="Next market close time")
    schedule: dict[str, Any] | None = Field(None, description="Market schedule")


class OHLCResponse(BaseModel):
    """Response for OHLC data endpoint."""

    symbol: str = Field(..., description="Stock symbol")
    data: list[dict[str, Any]] = Field(..., description="OHLC data points")
    count: int = Field(..., description="Number of data points")
    timeframe: str | None = Field(None, description="Data timeframe")
    provider: str | None = Field(None, description="Data provider")


class OrdersResponse(BaseModel):
    """Response for orders endpoint."""

    orders: list[dict[str, Any]] = Field(..., description="List of orders")
    count: int = Field(..., description="Number of orders")
    error: str | None = Field(None, description="Error message if unavailable")


class PositionsResponse(BaseModel):
    """Response for positions endpoint."""

    positions: list[dict[str, Any]] = Field(..., description="List of positions")
    count: int = Field(..., description="Number of positions")
    error: str | None = Field(None, description="Error message if unavailable")


class PortfolioResponse(BaseModel):
    """Response for portfolio endpoint."""

    portfolio: dict[str, Any] = Field(..., description="Portfolio summary")
    positions: list[dict[str, Any]] | None = Field(
        None, description="List of positions"
    )
    cash: float | None = Field(None, description="Available cash")
    equity: float | None = Field(None, description="Total equity")
    error: str | None = Field(None, description="Error message if unavailable")


class OrderCancelResponse(BaseModel):
    """Response for order cancellation."""

    ok: bool = Field(..., description="Whether cancellation was successful")
    order_id: str = Field(..., description="Order ID")
    message: str | None = Field(None, description="Status message")
    error: str | None = Field(None, description="Error message if failed")


class TradeExecutionResponse(BaseModel):
    """Response for trade execution endpoint."""

    ok: bool = Field(..., description="Whether execution was successful")
    order_id: str | None = Field(None, description="Order ID if successful")
    message: str | None = Field(None, description="Status message")
    symbol: str | None = Field(None, description="Stock symbol")
    quantity: int | None = Field(None, description="Order quantity")
    side: str | None = Field(None, description="Order side (buy/sell)")
    error: str | None = Field(None, description="Error message if failed")


class TradeModeResponse(BaseModel):
    """Response for trading mode update."""

    ok: bool = Field(..., description="Whether mode update was successful")
    mode: str = Field(..., description="Trading mode (paper/live)")
    message: str | None = Field(None, description="Status message")


# ── Paper Trading Endpoint Response Models ───────────────────────────────────


class PaperRunStopResponse(BaseModel):
    """Response for stopping a paper run."""

    status: str = Field(..., description="Stop status")
    ended_at: str | None = Field(None, description="Run end timestamp")


class TheoryPauseResponse(BaseModel):
    """Response for pausing a theory."""

    status: str = Field(..., description="Pause status")
    theory_name: str = Field(..., description="Theory name")


class PaperRunStatsResponse(BaseModel):
    """Response for paper run statistics."""

    run_id: int = Field(..., description="Run ID")
    stats: dict[str, Any] = Field(..., description="Detailed statistics")
    health: dict[str, Any] | None = Field(None, description="Health metrics")


class ModelSnapshotsResponse(BaseModel):
    """Response for model snapshots."""

    snapshots: list[dict[str, Any]] = Field(..., description="Model snapshots")
    count: int = Field(..., description="Number of snapshots")


class EmergencyStopResponse(BaseModel):
    """Response for emergency stop all."""

    stopped_count: int = Field(..., description="Number of runs stopped")
    message: str = Field(..., description="Status message")


class PaperLabHealthResponse(BaseModel):
    """Response for paper lab health check."""

    status: str = Field(..., description="Overall health status")
    active_runs: int | None = Field(None, description="Number of active runs")
    total_trades: int | None = Field(None, description="Total trades")
    db_connected: bool | None = Field(None, description="Database connection status")
    details: dict[str, Any] | None = Field(
        None, description="Additional health details"
    )


# ── News Endpoint Response Models ────────────────────────────────────────────


class NewsSourcesResponse(BaseModel):
    """Response for news sources endpoint."""

    sources: list[dict[str, Any]] = Field(..., description="List of news sources")
    count: int = Field(..., description="Number of sources")


class NewsHeadlinesResponse(BaseModel):
    """Response for news headlines endpoint."""

    headlines: list[dict[str, Any]] = Field(..., description="List of headlines")
    count: int = Field(..., description="Number of headlines")
    source: str | None = Field(None, description="News source")
    ticker: str | None = Field(None, description="Ticker symbol if filtered")


class FilingsResponse(BaseModel):
    """Response for SEC filings endpoint."""

    filings: list[dict[str, Any]] = Field(..., description="List of filings")
    count: int = Field(..., description="Number of filings")
    ticker: str | None = Field(None, description="Ticker symbol")


class RecentFilingsResponse(BaseModel):
    """Response for recent filings endpoint."""

    filings: list[dict[str, Any]] = Field(..., description="Recent filings")
    count: int = Field(..., description="Number of filings")
    days: int | None = Field(None, description="Days covered")


class NewsSearchResponse(BaseModel):
    """Response for news search endpoint."""

    results: list[dict[str, Any]] = Field(..., description="Search results")
    count: int = Field(..., description="Number of results")
    query: str | None = Field(None, description="Search query")


# ── Alerts Endpoint Response Models ──────────────────────────────────────────


class AlertsStatusResponse(BaseModel):
    """Response for alerts status endpoint."""

    status: str = Field(..., description="Alert system status")
    enabled: bool = Field(..., description="Whether alerts are enabled")
    active_alerts: int | None = Field(None, description="Number of active alerts")


class AlertCreateResponse(BaseModel):
    """Response for alert creation."""

    alert_id: str = Field(..., description="Created alert ID")
    message: str = Field(..., description="Creation status message")
    alert: dict[str, Any] | None = Field(None, description="Alert details")


class AlertListResponse(BaseModel):
    """Response for alert list endpoint."""

    alerts: list[dict[str, Any]] = Field(..., description="List of alerts")
    count: int = Field(..., description="Number of alerts")


class AlertHistoryResponse(BaseModel):
    """Response for alert history endpoint."""

    history: list[dict[str, Any]] = Field(..., description="Alert history entries")
    count: int = Field(..., description="Number of history entries")


class AlertDeleteResponse(BaseModel):
    """Response for alert deletion."""

    deleted: bool = Field(..., description="Whether deletion was successful")
    alert_id: str = Field(..., description="Deleted alert ID")
    message: str | None = Field(None, description="Status message")


class AlertUpdateResponse(BaseModel):
    """Response for alert enable/disable."""

    updated: bool = Field(..., description="Whether update was successful")
    alert_id: str = Field(..., description="Alert ID")
    enabled: bool = Field(..., description="New enabled status")


class AlertProductionStatusResponse(BaseModel):
    """Response for production status endpoint."""

    production: bool = Field(..., description="Whether in production mode")
    status: str | None = Field(None, description="Status message")


class AlertPingTestResponse(BaseModel):
    """Response for alert ping test."""

    success: bool = Field(..., description="Whether ping was successful")
    message: str | None = Field(None, description="Status message")


# ── Learning Endpoint Response Models ─────────────────────────────────────────


class LearningStatusResponse(BaseModel):
    """Response for learning status endpoint."""

    status: str = Field(..., description="Learning system status")
    enabled: bool = Field(..., description="Whether learning is enabled")
    last_run: str | None = Field(None, description="Last run timestamp")
    stats: dict[str, Any] | None = Field(None, description="Learning statistics")


class DataSummaryResponse(BaseModel):
    """Response for data summary endpoint."""

    summary: dict[str, Any] = Field(..., description="Data summary statistics")
    total_records: int | None = Field(None, description="Total records")
    date_range: dict[str, Any] | None = Field(None, description="Date range covered")


class RulesResponse(BaseModel):
    """Response for rules endpoints."""

    rules: list[dict[str, Any]] = Field(..., description="List of rules")
    count: int = Field(..., description="Number of rules")
    version: str | None = Field(None, description="Rules version")


class RulesHistoryResponse(BaseModel):
    """Response for rules history endpoint."""

    history: list[dict[str, Any]] = Field(..., description="Rules history")
    count: int = Field(..., description="Number of history entries")


class LearningRunResponse(BaseModel):
    """Response for learning run endpoint."""

    run_id: str = Field(..., description="Run ID")
    status: str = Field(..., description="Run status")
    message: str | None = Field(None, description="Status message")


class LearningResultsResponse(BaseModel):
    """Response for learning results endpoints."""

    results: dict[str, Any] | list[dict[str, Any]] = Field(
        ..., description="Learning results"
    )
    count: int | None = Field(None, description="Number of results if list")


class EvaluationResponse(BaseModel):
    """Response for evaluation endpoint."""

    evaluation: dict[str, Any] = Field(..., description="Evaluation metrics")
    accuracy: float | None = Field(None, description="Accuracy score")
    timestamp: str | None = Field(None, description="Evaluation timestamp")


class GatesResponse(BaseModel):
    """Response for gates endpoint."""

    gates: dict[str, Any] = Field(..., description="Gate configurations")
    count: int | None = Field(None, description="Number of gates")


class GatesUpdateResponse(BaseModel):
    """Response for gates update."""

    updated: bool = Field(..., description="Whether update was successful")
    gates: dict[str, Any] | None = Field(None, description="Updated gates")


class CalibrationStatusResponse(BaseModel):
    """Response for calibration status."""

    status: str = Field(..., description="Calibration status")
    last_calibration: str | None = Field(None, description="Last calibration timestamp")
    metrics: dict[str, Any] | None = Field(None, description="Calibration metrics")


class CalibrationBuildResponse(BaseModel):
    """Response for calibration build."""

    success: bool = Field(..., description="Whether build was successful")
    message: str | None = Field(None, description="Status message")
    calibration_id: str | None = Field(None, description="Calibration ID")


class LearningHealthResponse(BaseModel):
    """Response for learning health check."""

    status: str = Field(..., description="Overall health status")
    components: dict[str, bool] | None = Field(None, description="Component status")
    errors: list[str] | None = Field(None, description="Error messages if any")


# ── Integration Endpoint Response Models ──────────────────────────────────────


class IntegrationHealthResponse(BaseModel):
    """Response for integration health endpoint."""

    status: str = Field(..., description="Health status")
    data: dict[str, Any] = Field(..., description="Health data")
    timestamp: float = Field(..., description="Timestamp")


class EnhanceDataResponse(BaseModel):
    """Response for data enhancement endpoint."""

    status: str = Field(..., description="Response status")
    data: dict[str, Any] = Field(..., description="Enhanced data")
    source: str = Field(..., description="Data source")
    timestamp: float = Field(..., description="Timestamp")


class MarketContextResponse(BaseModel):
    """Response for market context endpoint."""

    status: str = Field(..., description="Response status")
    data: dict[str, Any] = Field(..., description="Market context data")
    timestamp: float = Field(..., description="Timestamp")


class ActiveRulesResponse(BaseModel):
    """Response for active rules endpoint."""

    status: str = Field(..., description="Response status")
    data: dict[str, Any] = Field(..., description="Active rules data")
    timestamp: float = Field(..., description="Timestamp")


class CalibrationApplyResponse(BaseModel):
    """Response for calibration apply endpoint."""

    status: str = Field(..., description="Response status")
    data: dict[str, Any] = Field(..., description="Calibration results")
    timestamp: float = Field(..., description="Timestamp")


class OutcomeUpdateResponse(BaseModel):
    """Response for outcome update endpoint."""

    status: str = Field(..., description="Response status")
    message: str = Field(..., description="Update message")
    decision_timestamp: float = Field(..., description="Decision timestamp")
    timestamp: float = Field(..., description="Response timestamp")


class IntegrationStatusResponse(BaseModel):
    """Response for integration status endpoint."""

    integration_available: bool = Field(
        ..., description="Whether integration is available"
    )
    timestamp: float = Field(..., description="Timestamp")
    components: dict[str, Any] | None = Field(None, description="Component status")
    integration_score: float | None = Field(None, description="Integration score")
    overall_status: str | None = Field(None, description="Overall system status")
    capabilities: dict[str, bool] | None = Field(
        None, description="Available capabilities"
    )
    error: str | None = Field(None, description="Error message if any")


class IntegrationTestResponse(BaseModel):
    """Response for integration test endpoint."""

    status: str = Field(..., description="Test status")
    message: str = Field(..., description="Test message")
    test_decision: dict[str, Any] | None = Field(
        None, description="Test decision result"
    )
    timestamp: float = Field(..., description="Timestamp")


# ── Feedback Endpoint Response Models ──────────────────────────────────────


class FeedbackStatsResponse(BaseModel):
    """Response for feedback stats endpoint."""

    enabled: bool = Field(..., description="Whether feedback is enabled")
    total_feedback: int = Field(..., description="Total feedback count")
    rating_distribution: dict[str, int] = Field(..., description="Rating distribution")
    top_tags: list[tuple[str, int]] = Field(..., description="Top feedback tags")
    recent_activity_7d: int = Field(..., description="Recent activity count (7 days)")
    feedback_coverage_pct: float = Field(
        ..., description="Feedback coverage percentage"
    )
    events_with_feedback: int = Field(..., description="Events with feedback count")
    total_decision_events: int = Field(..., description="Total decision events count")


class FeedbackHealthResponse(BaseModel):
    """Response for feedback health endpoint."""

    status: str = Field(..., description="Health status")
    enabled: bool = Field(..., description="Whether feedback is enabled")
    timestamp: str = Field(..., description="ISO timestamp")


# ── Ops Endpoint Response Models ──────────────────────────────────────


class OpsStatusResponse(BaseModel):
    """Response for ops status endpoint."""

    overall_status: str = Field(..., description="Overall operational status")
    timestamp: float = Field(..., description="Timestamp")
    check_duration_ms: float = Field(..., description="Health check duration in ms")
    summary: dict[str, int] = Field(..., description="Subsystem summary")
    subsystems: list[dict[str, Any]] = Field(
        ..., description="Individual subsystem statuses"
    )
    metadata: dict[str, str] = Field(..., description="System metadata")


class TimeoutAuditResponse(BaseModel):
    """Response for timeout audit endpoint."""

    external_calls: dict[str, Any] = Field(..., description="External call timeouts")
    internal_operations: dict[str, Any] = Field(
        ..., description="Internal operation timeouts"
    )
    database: dict[str, Any] = Field(..., description="Database timeouts")
    recommendations: list[str] = Field(..., description="Timeout recommendations")
    timestamp: float = Field(..., description="Timestamp")


# ── Performance Endpoint Response Models ──────────────────────────────────────


class PerformanceMetricsResponse(BaseModel):
    """Response for performance metrics endpoint."""

    ok: bool = Field(..., description="Request status")
    summary: dict[str, Any] = Field(..., description="Performance summary")
    recent_operations: list[dict[str, Any]] = Field(
        ..., description="Recent operations"
    )
    count: int = Field(..., description="Number of operations")


class MetricsSummaryResponse(BaseModel):
    """Response for metrics summary endpoint."""

    ok: bool = Field(..., description="Request status")
    metrics: dict[str, Any] = Field(..., description="Summary metrics")


class MetricsClearResponse(BaseModel):
    """Response for metrics clear endpoint."""

    ok: bool = Field(..., description="Request status")
    message: str = Field(..., description="Confirmation message")


class BenchmarkResultsResponse(BaseModel):
    """Response for benchmark results endpoint."""

    ok: bool = Field(..., description="Request status")
    benchmarks: list[dict[str, Any]] = Field(..., description="Benchmark results")
    count: int = Field(..., description="Number of benchmarks")


class BenchmarkRunResponse(BaseModel):
    """Response for benchmark run endpoints."""

    ok: bool = Field(..., description="Request status")
    comparison: dict[str, Any] = Field(..., description="Benchmark comparison results")


class BenchmarkClearResponse(BaseModel):
    """Response for benchmark clear endpoint."""

    ok: bool = Field(..., description="Request status")
    message: str = Field(..., description="Confirmation message")


class PerformanceHealthResponse(BaseModel):
    """Response for performance health endpoint."""

    ok: bool = Field(..., description="Request status")
    healthy: bool = Field(..., description="Whether system is healthy")
    status: str = Field(..., description="Health status")
    issues: list[str] = Field(..., description="Health issues")
    metrics: dict[str, Any] | None = Field(None, description="Performance metrics")
