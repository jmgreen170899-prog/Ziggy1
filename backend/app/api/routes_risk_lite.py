# backend/app/api/routes_risk_lite.py
from __future__ import annotations

import os
import time
from typing import Any

import pandas as pd
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field


router = APIRouter()


# Response models
class CPCData(BaseModel):
    """Put/Call ratio data."""

    ticker: str = Field(..., description="Ticker symbol used (^CPC or ^CPCE)")
    last: float = Field(..., description="Most recent Put/Call ratio")
    ma20: float = Field(..., description="20-period moving average")
    z20: float = Field(..., description="Z-score relative to 20-period window")
    date: str = Field(..., description="Date of last data point")


class RiskLiteResponse(BaseModel):
    """Risk lite endpoint response."""

    cpc: CPCData | None = Field(None, description="Put/Call ratio data, null on error")
    error: str | None = Field(None, description="Error message if data unavailable")


# simple in-memory cache
_TTL = int(os.getenv("RISK_LITE_TTL", "300"))  # seconds
_CACHE: dict[str, Any] = {"ts": 0.0, "data": None}


def _download_series(ticker: str, period_days: int) -> pd.Series | None:
    """
    Returns a clean daily Close series for `ticker` or None when not available.
    Uses yfinance with threads disabled for deterministic behavior.
    """
    import yfinance as yf

    df = yf.download(
        ticker,
        period=f"{max(5, period_days)}d",
        interval="1d",
        auto_adjust=False,
        progress=False,
        threads=False,
    )
    if isinstance(df, pd.DataFrame) and not df.empty and "Close" in df.columns:
        s = pd.to_numeric(df["Close"], errors="coerce").dropna()
        if s.shape[0] >= 5:
            return s
    return None


def _compute_payload(series: pd.Series, window: int, used: str) -> RiskLiteResponse:
    last = float(series.iloc[-1])
    tail = series.tail(window)
    ma = float(tail.mean())
    std = float(tail.std()) or 1e-9
    z = (last - ma) / std
    date = str(series.index[-1].date())
    cpc_data = CPCData(ticker=used, last=last, ma20=ma, z20=z, date=date)
    return RiskLiteResponse(cpc=cpc_data, error=None)


@router.get("/market-risk-lite", response_model=RiskLiteResponse)
def risk_lite(
    period_days: int = Query(
        180, ge=30, le=720, description="Lookback window for downloads"
    ),
    window: int = Query(20, ge=5, le=60, description="Moving average / z-score window"),
    use_cache: bool = Query(True, description="Return cached value when fresh"),
) -> RiskLiteResponse:
    """
    Lightweight risk bar derived from CBOE Put/Call.

    Tries ^CPC (index) then falls back to ^CPCE (equity).
    Returns Put/Call ratio with z-score and moving average.
    On failure, returns error message with null data.

    Side effects: Updates in-memory cache on successful data fetch.
    """
    now = time.time()
    if use_cache and _CACHE["data"] and (now - _CACHE["ts"] < _TTL):
        return _CACHE["data"]

    series = None
    used = None
    for t in ("^CPC", "^CPCE"):
        try:
            s = _download_series(t, period_days)
            if s is not None:
                series, used = s, t
                break
        except Exception:
            # ignore and try next symbol
            continue

    if series is None:
        payload = RiskLiteResponse(
            cpc=None, error="No data for ^CPC/^CPCE (blocked or unavailable)"
        )
    else:
        payload = _compute_payload(series, window, used)

    _CACHE["ts"] = now
    _CACHE["data"] = payload
    return payload


# Backward-compatible alias: /market/risk-lite
@router.get(
    "/market/risk-lite",
    response_model=RiskLiteResponse,
    deprecated=True,
    summary="[DEPRECATED] Use /market-risk-lite instead",
)
def risk_lite_alias(
    period_days: int = Query(180, ge=30, le=720),
    window: int = Query(20, ge=5, le=60),
    use_cache: bool = Query(True),
) -> RiskLiteResponse:
    """
    **DEPRECATED:** This endpoint is maintained for backward compatibility only.
    Please use `/market-risk-lite` instead.

    This alias will be removed in a future version.
    """
    return risk_lite(period_days=period_days, window=window, use_cache=use_cache)
