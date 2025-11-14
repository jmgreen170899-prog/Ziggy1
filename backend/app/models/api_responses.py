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
