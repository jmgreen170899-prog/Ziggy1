# backend/app/services/screener.py
from __future__ import annotations

import asyncio
import inspect
import logging
import math
import os
import traceback
from typing import Any

import numpy as np
import pandas as pd


# Market Brain Integration
try:
    from app.services.market_brain import (
        generate_ticker_signal,
        get_regime_state,
        get_ticker_features,
    )

    MARKET_BRAIN_AVAILABLE = True
except ImportError:
    MARKET_BRAIN_AVAILABLE = False
    logging.getLogger("ziggy").info("Market Brain not available for screener - using legacy logic")

# Prefer the new provider factory (fallback-aware). If unavailable, use legacy.
try:
    from app.services.provider_factory import (
        get_price_provider as _get_price_provider,  # type: ignore
    )
except Exception:  # factory not present
    _get_price_provider = None  # type: ignore
    try:
        from .market_providers import get_provider as _legacy_get_provider  # type: ignore
    except Exception:
        _legacy_get_provider = None  # type: ignore

# Default universe (can be overridden by SCAN_SYMBOLS env)
DEFAULT_TICKERS = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA"]


def _env_tickers() -> list[str]:
    s = (os.getenv("SCAN_SYMBOLS") or "").strip()
    if not s:
        return DEFAULT_TICKERS[:]
    return [t.strip().upper() for t in s.split(",") if t.strip()]


def _await_maybe(x):
    """Run an awaitable from sync code; otherwise return value."""
    if inspect.isawaitable(x):
        return asyncio.run(x)
    return x


def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce").dropna()
    delta = s.diff()
    up = delta.clip(lower=0.0)
    down = -delta.clip(upper=0.0)
    ma_up = up.ewm(com=period - 1, adjust=False).mean()
    ma_down = down.ewm(com=period - 1, adjust=False).mean()
    rs = ma_up / ma_down.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def _clamp(v: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _signal_from_indicators(close, sma20, sma50, rsi14):
    """
    Blend two ideas into a score in [-1,+1]:
      • MA spread: (SMA20 - SMA50) / SMA50  (scaled)
      • RSI bias around 50

    Thresholds: score > +0.10 → BUY, score < -0.10 → SELL, else NEUTRAL
    Confidence: NEUTRAL=0.50; BUY/SELL = 0.55..0.95 based on |score|
    """

    def _safe(x):
        try:
            return float(x)
        except Exception:
            return None

    c = _safe(close)
    s20 = _safe(sma20)
    s50 = _safe(sma50)
    rsi = _safe(rsi14)

    if any(v is None or (isinstance(v, float) and math.isnan(v)) for v in (c, s20, s50, rsi)):
        return {"signal": "NEUTRAL", "confidence": 0.50, "reason": "insufficient data"}

    spread = 0.0 if (s50 is None or s50 == 0.0) else (s20 - s50) / s50
    rsi_bias = (rsi - 50.0) / 50.0
    score = _clamp(0.6 * _clamp(spread * 5.0) + 0.4 * _clamp(rsi_bias))

    if score > 0.10:
        signal = "BUY"
    elif score < -0.10:
        signal = "SELL"
    else:
        signal = "NEUTRAL"

    if signal == "NEUTRAL":
        confidence = 0.50
    else:
        confidence = max(0.55, min(0.95, 0.55 + 0.40 * abs(score)))

    reasons = []
    if s20 > s50:
        reasons.append("SMA20>SMA50")
    elif s20 < s50:
        reasons.append("SMA20<SMA50")
    else:
        reasons.append("SMA20≈SMA50")

    if rsi >= 70:
        reasons.append("RSI>70")
    elif rsi >= 60:
        reasons.append("RSI>60")
    elif rsi <= 30:
        reasons.append("RSI<30")
    elif rsi <= 40:
        reasons.append("RSI<40")

    return {"signal": signal, "confidence": float(confidence), "reason": " & ".join(reasons)}


def _enhance_with_market_brain(legacy_item: dict[str, Any], ticker: str) -> dict[str, Any] | None:
    """
    Enhance legacy screener item with market brain intelligence.

    Args:
        legacy_item: Original screener result from legacy logic
        ticker: Ticker symbol

    Returns:
        Enhanced item with market brain data, or None if enhancement fails
    """
    if not MARKET_BRAIN_AVAILABLE:
        return None

    try:
        # Get market brain signal
        brain_signal = generate_ticker_signal(ticker)
        if not brain_signal:
            return None

        # Get current market regime for context
        regime_result = get_regime_state()
        current_regime = regime_result.regime.value if regime_result else "UNKNOWN"

        # Create enhanced item
        enhanced = legacy_item.copy()

        # Update signal and confidence with brain data
        enhanced["signal"] = brain_signal.direction.value
        enhanced["confidence"] = brain_signal.confidence or legacy_item.get("confidence", 0.5)

        # Enhance reason with market brain context
        brain_reason = brain_signal.reason or ""
        legacy_reason = legacy_item.get("reason", "")

        # Combine reasons intelligently
        if brain_reason and legacy_reason:
            if brain_reason != legacy_reason:
                enhanced["reason"] = f"{brain_reason} | {legacy_reason}"
            else:
                enhanced["reason"] = brain_reason
        else:
            enhanced["reason"] = brain_reason or legacy_reason or "Market analysis"

        # Add market brain specific data
        enhanced["brain_signal_type"] = brain_signal.signal_type.value
        enhanced["market_regime"] = current_regime
        enhanced["brain_confidence"] = brain_signal.confidence
        enhanced["legacy_confidence"] = legacy_item.get("confidence")

        # Add entry/exit levels if available
        if brain_signal.entry_price:
            enhanced["brain_entry"] = brain_signal.entry_price
        if brain_signal.stop_loss:
            enhanced["brain_stop_loss"] = brain_signal.stop_loss
        if brain_signal.take_profit:
            enhanced["brain_take_profit"] = brain_signal.take_profit

        logging.getLogger("ziggy").debug(
            f"Enhanced {ticker}: {legacy_item.get('signal')} -> {enhanced['signal']} "
            f"(conf: {legacy_item.get('confidence'):.2f} -> {enhanced['confidence']:.2f})"
        )

        return enhanced

    except Exception as e:
        logging.getLogger("ziggy").debug(f"Market brain enhancement failed for {ticker}: {e}")
        return None


def run_screener(market: str | None = None) -> list[dict[str, Any]]:
    """
    Sync screener; safe to call from the background scheduler and sync routes.
    Handles async providers internally. Uses provider factory (with fallback/
    cooldown) when available; otherwise falls back to legacy provider.
    """
    symbols = _env_tickers()
    # Choose provider manager
    provider = None
    if _get_price_provider:
        try:
            provider = _get_price_provider()  # factory returns a manager with fetch_ohlc()
        except Exception:
            provider = None
    if provider is None and "_legacy_get_provider" in globals():
        try:
            provider = _legacy_get_provider()  # legacy single-provider path
        except Exception:
            provider = None
    if not provider:
        return []

    # fetch_ohlc may be async — handle both
    try:
        frames = _await_maybe(provider.fetch_ohlc(symbols, period_days=180, adjusted=True))
    except Exception:
        # provider hiccup → return empty to keep UI/scheduler resilient
        return []

    results: list[dict[str, Any]] = []
    for t in symbols:
        try:
            df = (frames or {}).get(t)
            if df is None or getattr(df, "empty", True) or "Close" not in df.columns:
                results.append(
                    {"ticker": t, "signal": "NEUTRAL", "confidence": 0.50, "reason": "no data"}
                )
                continue

            close_series = pd.to_numeric(df["Close"], errors="coerce").dropna()
            if close_series.empty:
                results.append(
                    {"ticker": t, "signal": "NEUTRAL", "confidence": 0.50, "reason": "no data"}
                )
                continue

            sma20 = (
                close_series.rolling(20).mean().iloc[-1]
                if len(close_series) >= 20
                else float("nan")
            )
            sma50 = (
                close_series.rolling(50).mean().iloc[-1]
                if len(close_series) >= 50
                else float("nan")
            )
            rsi14 = _rsi(close_series, 14).iloc[-1] if len(close_series) >= 15 else float("nan")

            price = float(close_series.iloc[-1])
            item = {
                "ticker": t,
                "price": price,
                "sma20": None if math.isnan(sma20) else float(sma20),
                "sma50": None if math.isnan(sma50) else float(sma50),
                "rsi14": None if math.isnan(rsi14) else float(rsi14),
            }
            item.update(_signal_from_indicators(price, sma20, sma50, rsi14))

            # Enhance with Market Brain if available
            if MARKET_BRAIN_AVAILABLE:
                try:
                    enhanced_item = _enhance_with_market_brain(item, t)
                    if enhanced_item:
                        item = enhanced_item
                except Exception as e:
                    logging.getLogger("ziggy").debug(
                        f"Market brain enhancement failed for {t}: {e}"
                    )

            results.append(item)
        except Exception:
            # Protect the screener route from per-symbol processing errors.
            # Use the project logger rather than printing raw tracebacks.
            logger = logging.getLogger("ziggy")
            try:
                logger.warning("[screener] item error for %s — returning neutral", t)
                # full traceback at debug level for deeper inspection when needed
                logger.debug(traceback.format_exc())
            except Exception:
                # fallback to a minimal message if logging itself fails
                try:
                    logging.getLogger("ziggy").warning("[screener] item error fallback for %s", t)
                except Exception:
                    try:
                        print("[screener] item error", t)
                    except Exception:
                        pass
            results.append(
                {"ticker": t, "signal": "NEUTRAL", "confidence": 0.50, "reason": "error"}
            )

    return results
