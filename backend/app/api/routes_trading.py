from __future__ import annotations

import asyncio
import contextlib
import inspect
import json
import logging
import math
import os
import time
from datetime import UTC, datetime, timedelta
from math import isfinite as _isfinite
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.screener import run_screener
from app.tasks.scheduler import get_scan_enabled, set_scan_enabled
from app.tasks.telegram import tg_diag, tg_send


# Market Brain System Integration (import robust + type-safe fallbacks)
try:
    # BacktestPeriod is defined under backtest module; quick_backtest is re-exported but import directly for clarity
    from app.services.market_brain import (  # type: ignore
        generate_ticker_signal,
        get_regime_state,
        get_ticker_features,
    )
    from app.services.market_brain.backtest import BacktestPeriod, quick_backtest  # type: ignore

    MARKET_BRAIN_AVAILABLE = True
except Exception:
    MARKET_BRAIN_AVAILABLE = False
    logging.getLogger("ziggy").warning("Market Brain system not available - using legacy logic")
    # Stubs to satisfy type checkers when Market Brain package is absent
    from typing import Any as _Any

    BacktestPeriod = None  # type: ignore[assignment]

    def generate_ticker_signal(*args: _Any, **kwargs: _Any) -> _Any:  # type: ignore[no-redef]
        return None

    def get_regime_state(*args: _Any, **kwargs: _Any) -> _Any:  # type: ignore[no-redef]
        return None

    def get_ticker_features(*args: _Any, **kwargs: _Any) -> _Any:  # type: ignore[no-redef]
        return None

    def quick_backtest(*args: _Any, **kwargs: _Any) -> _Any:  # type: ignore[no-redef]
        return None


# Prefer provider factory when available; fall back to legacy single provider
try:
    from app.services.provider_factory import (
        get_price_provider as _factory_get_price_provider,  # type: ignore
    )
except Exception:  # factory not present in some codebases
    _factory_get_price_provider = None  # type: ignore
try:
    # legacy single provider
    from app.services.market_providers import get_provider as _legacy_get_provider  # type: ignore
except Exception:
    _legacy_get_provider = None  # type: ignore


def _price_provider():
    """Return a provider manager if available, else a single legacy provider."""
    if callable(_factory_get_price_provider):
        try:
            return _factory_get_price_provider()  # may be a manager or single
        except Exception:
            pass
    if callable(_legacy_get_provider):
        try:
            return _legacy_get_provider()
        except Exception:
            pass
    return None


def _get_provider_names() -> list[str]:
    """Get list of provider names for metadata."""
    provider_names: list[str] = []
    mp = _price_provider()
    if mp is not None:
        chain = getattr(mp, "providers", None)
        if isinstance(chain, (list, tuple)) and chain:
            provider_names = [
                str(getattr(p, "name", getattr(p, "__class__", type("x", (), {})).__name__)).lower()
                for p in chain
            ]
        else:
            provider_names = [
                str(
                    getattr(mp, "name", getattr(mp, "__class__", type("x", (), {})).__name__)
                ).lower()
            ]
    return provider_names


router = APIRouter()

# Default timeout (seconds) for upstream OHLC provider calls; can be monkeypatched in tests
_OHLC_TIMEOUT_SECS = 5.0


# ───────────────────────────────────────────────────────────────────────────────
# small helper: run sync **or** async callables from a sync route
# ───────────────────────────────────────────────────────────────────────────────
def _run_maybe_async(target, *args, **kwargs):
    if inspect.iscoroutinefunction(target):
        return asyncio.run(target(*args, **kwargs))
    if inspect.isawaitable(target):
        from collections.abc import Coroutine
        from typing import Any, cast

        return asyncio.run(cast(Coroutine[Any, Any, Any], target))
    if callable(target):
        return target(*args, **kwargs)
    return target


# ───────────────────────────────────────────────────────────────────────────────
# Models
# ───────────────────────────────────────────────────────────────────────────────
class ScreenerItem(BaseModel):
    ticker: str = Field(..., description="Ticker symbol")
    price: float | None = Field(None, description="Last close price")
    sma20: float | None = None
    sma50: float | None = None
    rsi14: float | None = None
    signal: str = Field(..., description="BUY | SELL | NEUTRAL")
    confidence: float = Field(..., ge=0.0, le=1.0)
    reason: str = ""


class ScreenerResponse(BaseModel):
    ran_at: float
    market: str
    count: int
    results: list[ScreenerItem]


class NotifyIn(BaseModel):
    text: str


# NEW: Explain Signal models (non-breaking; only used by /trade/explain)
class ExplainIn(BaseModel):
    ticker: str = Field(..., description="Ticker symbol")
    signal: str | None = Field(None, description="BUY | SELL | NEUTRAL")
    confidence: float | None = Field(None, ge=0.0, le=1.0)
    reason: str | None = Field(None, description="Short free-text reason if available")
    indicators: dict[str, Any] = Field(default_factory=dict)
    price: float | None = None
    change: float | None = Field(
        None, description="Session % change as raw percent (e.g., 1.23 for +1.23%)"
    )


class ExplainBullet(BaseModel):
    label: str
    impact: str = Field("neutral", description="positive | negative | neutral | bullish | bearish")
    weight: float | None = Field(None, ge=0.0, le=1.0)
    detail: str | None = None


class ExplainRisk(BaseModel):
    stopLossPct: float | None = None  # noqa: N815
    takeProfitPct: float | None = None  # noqa: N815
    rrr: float | None = None
    note: str | None = None


class ExplainOut(BaseModel):
    ticker: str
    signal: str | None = None
    confidence: float | None = None
    rationale: str = ""
    bullets: list[ExplainBullet] = Field(default_factory=list)
    indicators: dict[str, Any] = Field(default_factory=dict)
    price: float | None = None
    change: float | None = None
    risk: ExplainRisk | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


# ───────────────────────────────────────────────────────────────────────────────
# Health (for frontend "backend" status chip) — lightweight, no upstream calls
# ───────────────────────────────────────────────────────────────────────────────
@router.get("/trade/health")
def trade_health():
    """
    Minimal health: do not hit upstream markets. Report scan toggle,
    provider chain (names only), and Telegram readiness flags.
    """
    try:
        mp = _price_provider()
        providers: list[str] = []
        if mp is not None:
            # Manager style with .providers or single object with .name
            chain = getattr(mp, "providers", None)
            if isinstance(chain, (list, tuple)) and chain:
                providers = [
                    str(
                        getattr(p, "name", getattr(p, "__class__", type("x", (), {})).__name__)
                    ).lower()
                    for p in chain
                ]
            else:
                nm = str(
                    getattr(mp, "name", getattr(mp, "__class__", type("x", (), {})).__name__)
                ).lower()
                providers = [nm]
        d = tg_diag()
        provider_mode = (os.getenv("PROVIDER_MODE") or "live").strip().lower()
        return {
            "ok": True,
            "service": "trade",
            "scan": get_scan_enabled(),
            "providers": providers,
            "provider_mode": provider_mode,
            "telegram": {
                "token_set": d.get("token_set"),
                "chat_set": d.get("chat_set"),
                "getme_ok": d.get("getme_ok"),
            },
        }
    except Exception:
        logging.getLogger("ziggy").exception("TRADE_HEALTH_ERROR")
        # Keep shape stable; UI treats ok:false as down.
        return {"ok": False, "service": "trade", "scan": False, "providers": []}


# ───────────────────────────────────────────────────────────────────────────────
# Screener (view-only; notify optional)
# ───────────────────────────────────────────────────────────────────────────────
@router.get("/trade/screener", response_model=ScreenerResponse)
def get_screener(
    market: str = Query("nyse"),
    notify: bool = Query(False, description="If true, also emit Telegram alerts from this call"),
):
    try:
        results = _run_maybe_async(run_screener) or []
        if not isinstance(results, (list, tuple)):
            results = list(results or [])
    except Exception:
        logging.getLogger("ziggy").exception("SCREENER_ERROR")
        return {"ran_at": time.time(), "market": market, "count": 0, "results": []}

    if notify:
        noteworthy = [
            s for s in results if isinstance(s, dict) and s.get("signal") in {"BUY", "SELL"}
        ]
        if noteworthy:
            lines = [
                f"{s['ticker']}: {s['signal']} ({int(float(s.get('confidence', 0)) * 100)}% conf)"
                + (f" — {s.get('reason', '')}" if s.get("reason") else "")
                for s in noteworthy
            ]
            with contextlib.suppress(Exception):
                tg_send("Ziggy Screener Alerts:\n" + "\n".join(lines), kind="screener")

    return {"ran_at": time.time(), "market": market, "count": len(results), "results": results}


# ───────────────────────────────────────────────────────────────────────────────
# Explain Signal (for TickerCard “Why?” modal)
# ───────────────────────────────────────────────────────────────────────────────
@router.post("/trade/explain", response_model=ExplainOut)
def explain_signal(body: ExplainIn):
    """
    Generate an explanation/rationale for a given signal payload.
    Now enhanced with Market Brain intelligence when available.
    - Accepts indicators from the frontend and optionally enriches them.
    - Uses Market Brain for advanced signal analysis and reasoning.
    - Falls back to legacy heuristic logic if Market Brain unavailable.
    """
    t0 = time.time()

    # Try Market Brain enhancement first
    if MARKET_BRAIN_AVAILABLE:
        try:
            enhanced_explanation = _explain_with_market_brain(body)
            if enhanced_explanation:
                return enhanced_explanation
        except Exception as e:
            logging.getLogger("ziggy").debug(
                f"Market Brain explanation failed for {body.ticker}: {e}"
            )

    # Fallback to legacy logic
    return _explain_with_legacy_logic(body, t0)


def _explain_with_market_brain(body: ExplainIn) -> ExplainOut | None:
    """Generate explanation using Market Brain system."""
    t0 = time.time()
    try:
        # Get market brain signal and features
        from typing import cast

        brain_signal = cast(Any, generate_ticker_signal(body.ticker))
        features = cast(Any, get_ticker_features(body.ticker))
        regime_result = cast(Any, get_regime_state())

        # Start with provided indicators, enhance with brain features
        ind = dict(body.indicators or {})

        if features:
            # Add brain-computed indicators
            ind.update(
                {
                    "rsi14": features.rsi_14,
                    "sma20": features.sma_20,
                    "sma50": features.sma_50,
                    "atr_14": features.atr_14,
                    "z_score": features.z_score_20,
                    "volatility_20d": features.volatility_20d,
                }
            )

        # Build enhanced bullets with brain data
        bullets: list[ExplainBullet] = []

        # Market regime context
        if regime_result:
            regime_name = getattr(getattr(regime_result, "regime", None), "value", "")
            regime_impact = "positive" if regime_name in ["RISK_ON", "CHOP"] else "negative"
            bullets.append(
                ExplainBullet(
                    label=f"Market Regime: {regime_name}",
                    impact=regime_impact,
                    weight=getattr(regime_result, "confidence", None),
                    detail=f"Current market environment. {getattr(regime_result, 'reason', '')}",
                )
            )

        # Brain signal analysis
        if brain_signal:
            dir_val = getattr(getattr(brain_signal, "direction", None), "value", "")
            signal_impact = "positive" if dir_val == "LONG" else "negative"
            bullets.append(
                ExplainBullet(
                    label=f"Brain Signal: {dir_val} ({getattr(getattr(brain_signal, 'signal_type', None), 'value', '')})",
                    impact=signal_impact,
                    weight=getattr(brain_signal, "confidence", 0.5) or 0.5,
                    detail=getattr(brain_signal, "reason", "Advanced signal analysis"),
                )
            )

        # Technical indicators with brain context
        if features:
            # RSI with market context
            if getattr(features, "rsi_14", None) is not None:
                rsi_val = float(getattr(features, "rsi_14", 0.0))
                rsi_impact = (
                    "positive" if rsi_val > 60 else "negative" if rsi_val < 40 else "neutral"
                )
                bullets.append(
                    ExplainBullet(
                        label=f"RSI14: {rsi_val:.1f}",
                        impact=rsi_impact,
                        weight=min(max(rsi_val / 100.0, 0.0), 1.0),
                        detail="Momentum oscillator (30/70 oversold/overbought)",
                    )
                )

            # Z-Score for mean reversion
            if getattr(features, "z_score_20", None) is not None:
                z_val = float(getattr(features, "z_score_20", 0.0))
                z_impact = "negative" if abs(z_val) > 2 else "neutral"
                bullets.append(
                    ExplainBullet(
                        label=f"Z-Score: {z_val:.2f}",
                        impact=z_impact,
                        weight=min(abs(z_val) / 3.0, 1.0),
                        detail="Price deviation from 20-day mean (>2 extreme)",
                    )
                )

            # Volatility context
            if getattr(features, "volatility_20d", None) is not None:
                vol_val = float(getattr(features, "volatility_20d", 0.0))
                vol_impact = "negative" if vol_val > 30 else "neutral"
                bullets.append(
                    ExplainBullet(
                        label=f"Volatility: {vol_val:.1f}%",
                        impact=vol_impact,
                        weight=min(vol_val / 50.0, 1.0),
                        detail="20-day rolling volatility",
                    )
                )

        # Compose enhanced rationale
        parts: list[str] = []

        # Start with brain signal if available
        if brain_signal:
            parts.append(
                f"Market Brain recommends {getattr(getattr(brain_signal, 'direction', None), 'value', '')} "
                f"({int((getattr(brain_signal, 'confidence', 0.5) or 0.5) * 100)}% confidence)"
            )
            reason_txt = getattr(brain_signal, "reason", None)
            if reason_txt:
                parts.append(f"Reasoning: {reason_txt}")

        # Add regime context
        if regime_result:
            parts.append(
                f"Current market regime: {getattr(getattr(regime_result, 'regime', None), 'value', '')}"
            )

        # Add technical context
        if features and getattr(features, "rsi_14", None) is not None:
            rsi_desc = (
                "bullish"
                if float(getattr(features, "rsi_14", 0.0)) > 60
                else "bearish"
                if float(getattr(features, "rsi_14", 0.0)) < 40
                else "neutral"
            )
            parts.append(
                f"Momentum: {rsi_desc} (RSI {float(getattr(features, 'rsi_14', 0.0)):.1f})"
            )

        if features and getattr(features, "z_score_20", None) is not None:
            z_val2 = float(getattr(features, "z_score_20", 0.0))
            z_desc = "extreme" if abs(z_val2) > 2 else "normal"
            parts.append(f"Price position: {z_desc} (Z-score {z_val2:.2f})")

        # Enhanced risk levels using brain data
        risk: ExplainRisk | None = None
        if brain_signal and features:
            try:
                # Use brain signal's stop/target if available
                if getattr(brain_signal, "stop_loss", None) and getattr(
                    brain_signal, "entry_price", None
                ):
                    sl_pct = (
                        abs(
                            float(getattr(brain_signal, "entry_price", 0.0))
                            - float(getattr(brain_signal, "stop_loss", 0.0))
                        )
                        / float(getattr(brain_signal, "entry_price", 1.0) or 1.0)
                        * 100
                    )
                else:
                    # Fallback to ATR-based stop
                    sl_pct = float(getattr(features, "atr_14", 2.0) or 2.0)

                if getattr(brain_signal, "take_profit", None) and getattr(
                    brain_signal, "entry_price", None
                ):
                    tp_pct = (
                        abs(
                            float(getattr(brain_signal, "take_profit", 0.0))
                            - float(getattr(brain_signal, "entry_price", 1.0))
                        )
                        / float(getattr(brain_signal, "entry_price", 1.0) or 1.0)
                        * 100
                    )
                    rrr = float(tp_pct) / float(sl_pct) if sl_pct and sl_pct > 0 else 1.5
                else:
                    # Dynamic RRR based on regime and confidence
                    regime_name2 = getattr(getattr(regime_result, "regime", None), "value", "")
                    base_rrr = 2.0 if regime_result and regime_name2 == "RISK_ON" else 1.5
                    conf_boost = (getattr(brain_signal, "confidence", 0.5) or 0.5) * 0.5
                    rrr = base_rrr + conf_boost
                    tp_pct = sl_pct * rrr

                risk = ExplainRisk(
                    stopLossPct=sl_pct,
                    takeProfitPct=tp_pct,
                    rrr=rrr,
                    note="Brain-calculated levels using ATR and market regime",
                )
            except Exception:
                risk = None

        # Get provider names
        provider_names = _get_provider_names()

        return ExplainOut(
            ticker=body.ticker,
            signal=(
                getattr(getattr(brain_signal, "direction", None), "value", None)
                if brain_signal
                else body.signal
            ),
            confidence=(
                getattr(brain_signal, "confidence", None) if brain_signal else body.confidence
            ),
            rationale=" ".join(parts),
            bullets=bullets,
            indicators=ind,
            price=body.price,
            risk=risk,
            meta={
                "provider": ", ".join(provider_names) + " + Market Brain",
                "asOf": datetime.now().isoformat(),
                "model": "market_brain_v1",
                "latencyMs": int((time.time() - t0) * 1000),
            },
        )

    except Exception as e:
        logging.getLogger("ziggy").error(f"Market Brain explanation error for {body.ticker}: {e}")
        return None


def _explain_with_legacy_logic(body: ExplainIn, t0: float) -> ExplainOut:
    """Fallback legacy explanation logic."""
    provider_names = _get_provider_names()

    # Start with provided indicators
    ind = dict(body.indicators or {})

    # Optional quick enrich: compute SMA spread if both present
    try:
        sma20 = _to_num(ind.get("sma20"))
        sma50 = _to_num(ind.get("sma50"))
        if sma20 is not None and sma50 is not None and sma50 != 0:
            ind["sma_spread_pct"] = (sma20 - sma50) / sma50 * 100.0
    except Exception:
        pass

    # Build bullets heuristically; keep lightweight and deterministic
    bullets: list[ExplainBullet] = []
    rsi = _to_num(ind.get("rsi14"))
    if rsi is not None:
        bullets.append(
            ExplainBullet(
                label=f"RSI14 at {rsi:.1f}",
                impact="positive" if rsi > 60 else "negative" if rsi < 40 else "neutral",
                weight=min(max(rsi / 100.0, 0.0), 1.0),
                detail="Momentum context (70/30 overbought/oversold bands)",
            )
        )

    sma_spread = _to_num(ind.get("sma_spread_pct"))
    if sma_spread is not None:
        bullets.append(
            ExplainBullet(
                label=f"SMA20 vs SMA50 spread {sma_spread:+.2f}%",
                impact=(
                    "positive" if sma_spread > 0 else "negative" if sma_spread < 0 else "neutral"
                ),
                weight=min(abs(sma_spread) / 20.0, 1.0),
                detail="Short-term trend relative to medium-term trend",
            )
        )

    if body.change is not None:
        ch = float(body.change)
        bullets.append(
            ExplainBullet(
                label=f"Session change {ch:+.2f}%",
                impact="positive" if ch >= 0 else "negative",
                weight=min(abs(ch) / 5.0, 1.0),
                detail="Intraday performance",
            )
        )

    # Compose rationale text
    parts: list[str] = []
    sig = (body.signal or "").upper() if body.signal else None
    if sig:
        if body.confidence is not None:
            percent_conf = round(float(body.confidence) * 100)
            parts.append(f"Signal {sig} ({percent_conf}% confidence).")
        else:
            parts.append(f"Signal {sig}.")
    if body.price is not None:
        parts.append(f"Last price ~ {float(body.price):.2f}.")
    if rsi is not None:
        parts.append(
            f"RSI14 at {rsi:.1f} suggests {'bullish' if rsi > 60 else 'bearish' if rsi < 40 else 'neutral'} momentum."
        )
    if sma_spread is not None:
        parts.append(f"Short/medium trend spread {sma_spread:+.2f}% (SMA20 vs SMA50).")
    if body.change is not None:
        parts.append(f"Session move {float(body.change):+.2f}%.")

    rationale = " ".join(parts) or (body.reason or "")

    # Simple risk suggestion: tie SL/TP to volatility proxies when available
    risk: ExplainRisk | None = None
    try:
        # Use RSI & spread to modulate suggested RRR
        base_rrr = 1.5
        if sig == "BUY" and sma_spread and sma_spread > 0:
            base_rrr = 2.0
        if sig == "SELL" and sma_spread and sma_spread < 0:
            base_rrr = 2.0
        sl = 0.02  # 2%
        tp = sl * base_rrr
        risk = ExplainRisk(
            stopLossPct=sl * 100.0, takeProfitPct=tp * 100.0, rrr=base_rrr, note="Heuristic levels"
        )
    except Exception:
        risk = None

    t1 = time.time()
    out = ExplainOut(
        ticker=body.ticker,
        signal=body.signal,
        confidence=body.confidence,
        rationale=rationale or (body.reason or ""),
        bullets=bullets,
        indicators=ind,
        price=body.price,
        change=body.change,
        risk=risk,
        meta={
            "provider": " / ".join(provider_names) if provider_names else None,
            "asOf": datetime.utcnow().isoformat(),
            "latencyMs": int((t1 - t0) * 1000),
            "model": "heuristic-v1",
        },
    )
    return out


# ───────────────────────────────────────────────────────────────────────────────
# Telegram Notify API
# ───────────────────────────────────────────────────────────────────────────────
@router.post("/trade/notify")
def trade_notify(body: NotifyIn):
    try:
        ok = tg_send(body.text, kind="manual")
    except Exception:
        ok = False

    d = tg_diag()
    delivered = bool(d.get("last_raw", {}).get("json", {}).get("ok") is True)

    if ok or delivered:
        return {"ok": True, "diag": d}

    detail = {
        "error": "Telegram send failed",
        "reason": d.get("last_error", "unknown"),
        "token_set": d.get("token_set"),
        "chat_set": d.get("chat_set"),
        "getme_ok": d.get("getme_ok"),
        "last_raw": d.get("last_raw"),
    }
    raise HTTPException(status_code=500, detail=detail)


@router.get("/trade/notify/diag")
def trade_notify_diag():
    return tg_diag()


@router.get("/trade/notify/probe")
def trade_notify_probe():
    return tg_diag()


@router.post("/trade/notify/test")
def trade_notify_test():
    try:
        ok = tg_send("✅ Ziggy test ping", kind="manual-test")
    except Exception:
        ok = False

    d = tg_diag()
    delivered = bool(d.get("last_raw", {}).get("json", {}).get("ok") is True)

    if ok or delivered:
        return {"ok": True, "diag": d}
    raise HTTPException(status_code=500, detail=d)


# ───────────────────────────────────────────────────────────────────────────────
# Scan Toggle
# ───────────────────────────────────────────────────────────────────────────────
@router.get("/trade/scan/status")
def scan_status():
    return {"enabled": get_scan_enabled()}


@router.post("/trade/scan/enable")
def scan_enable(enabled: bool = Query(..., description="true/false")):
    set_scan_enabled(enabled)
    return {"enabled": get_scan_enabled()}


# ───────────────────────────────────────────────────────────────────────────────
# Market Calendar (stub with optional external file)
# ───────────────────────────────────────────────────────────────────────────────
@router.get("/market/calendar")
def market_calendar(days: int = Query(14, ge=1, le=60)):
    now = datetime.now(UTC)
    try:
        data_path = Path(__file__).resolve().parents[2] / "data" / "calendar.json"
        if data_path.exists():
            with data_path.open("r", encoding="utf-8") as f:
                doc = json.load(f)
            cutoff = (now + timedelta(days=days)).date().isoformat()
            macro = [m for m in (doc.get("macro") or []) if m.get("date") and m["date"] <= cutoff]
            earnings = doc.get("earnings") or {}
            return {"asof": time.time(), "macro": macro, "earnings": earnings}
    except Exception:
        pass

    def d_in(n: int) -> str:
        return (now + timedelta(days=n)).date().isoformat()

    stub_macro = [
        {
            "code": "CPI",
            "label": "CPI",
            "date": d_in(2),
            "time": "08:30",
            "tz": "ET",
            "note": "Monthly CPI",
        },
        {
            "code": "NFP",
            "label": "NFP",
            "date": d_in(5),
            "time": "08:30",
            "tz": "ET",
            "note": "Nonfarm Payrolls",
        },
        {
            "code": "FOMC",
            "label": "FOMC",
            "date": d_in(9),
            "time": "14:00",
            "tz": "ET",
            "note": "Rate decision",
        },
        {
            "code": "PMI",
            "label": "PMI",
            "date": d_in(12),
            "time": "09:45",
            "tz": "ET",
            "note": "Manufacturing PMI",
        },
    ]
    stub_earnings = {
        "AAPL": {"date": d_in(3), "time": "AMC"},
        "MSFT": {"date": d_in(1), "time": "BMO"},
        "NVDA": {"date": d_in(7), "time": "AMC"},
        "AMZN": {"date": d_in(10), "time": "AMC"},
        "META": {"date": d_in(6), "time": "BMO"},
        "GOOGL": {"date": d_in(11), "time": "AMC"},
        "TSLA": {"date": d_in(4), "time": "AMC"},
    }

    cutoff = (now + timedelta(days=days)).date().isoformat()
    stub_macro = [m for m in stub_macro if m["date"] <= cutoff]
    return {"asof": time.time(), "macro": stub_macro, "earnings": stub_earnings}


# ───────────────────────────────────────────────────────────────────────────────
# OHLC for Mini Charts (normalized via factory + debug source)
# ───────────────────────────────────────────────────────────────────────────────
@router.get("/trade/ohlc")
async def get_ohlc(
    tickers: str = Query(..., description="Comma-separated tickers"),
    period_days: int = Query(60, ge=1, le=3650),
    debug_source: bool = Query(
        False, description="If true, include provider source and provider_chain."
    ),
    batch: bool = Query(
        False,
        description="If true, returns a summary + per-ticker results with ok/error and records. Backward-compatible mapping when false.",
    ),
    timeout_s: float = Query(
        None, description="Per-ticker timeout in seconds for batch mode (defaults to internal)."
    ),
):
    try:
        tickers_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
        mp = _price_provider()
        if mp is None:
            raise RuntimeError("No market data provider available")

        frames: dict[str, pd.DataFrame] = {}
        src: dict[str, Any] = {}

        # Some providers support return_source, some do not; handle both.
        async def _call_with_timeout(fn, *args, **kwargs):
            # Execute provider call with a timeout guard supporting async and sync functions
            timeout = float(kwargs.pop("_timeout", _OHLC_TIMEOUT_SECS))
            if inspect.iscoroutinefunction(fn):
                return await asyncio.wait_for(fn(*args, **kwargs), timeout=timeout)
            res = fn(*args, **kwargs)
            if inspect.isawaitable(res):
                return await asyncio.wait_for(res, timeout=timeout)
            # Synchronous fast return; cannot enforce timeout retroactively
            return res

        # Helper to normalize and validate tickers
        def _valid_ticker(s: str) -> bool:
            import re

            return bool(re.fullmatch(r"[A-Za-z0-9.\-]{1,20}", s))

        # When batch=true, perform per-ticker guarded calls and return structured results
        if batch:
            valids: list[str] = []
            invalids: list[str] = []
            for t in tickers_list:
                (valids if _valid_ticker(t) else invalids).append(t)

            results: list[dict[str, Any]] = []
            succeeded = failed = 0
            per_timeout = float(timeout_s) if (timeout_s and timeout_s > 0) else _OHLC_TIMEOUT_SECS

            def _extract_chain() -> list[str]:
                chain = getattr(mp, "providers", None)
                if isinstance(chain, (list, tuple)) and chain:
                    return [
                        str(
                            getattr(p, "name", getattr(p, "__class__", type("x", (), {})).__name__)
                        ).lower()
                        for p in chain
                    ]
                return [
                    str(
                        getattr(mp, "name", getattr(mp, "__class__", type("x", (), {})).__name__)
                    ).lower()
                ]

            # Invalid tickers first
            for t in invalids:
                results.append(
                    {
                        "ticker": t,
                        "ok": False,
                        "error": "invalid_ticker",
                        "records": [],
                    }
                )
                failed += 1

            # Valid tickers: per-ticker guarded fetch
            for t in valids:
                t0 = time.time()
                err: str | None = None
                recs: list[dict[str, Any]] = []
                try:
                    returned = await _call_with_timeout(
                        mp.fetch_ohlc,
                        [t],
                        period_days=period_days,
                        adjusted=True,
                        _timeout=per_timeout,
                    )
                    # Normalize returned mapping
                    if isinstance(returned, dict):
                        df = returned.get(t)
                        if isinstance(df, pd.DataFrame):
                            recs = []

                            # reuse mapping logic below by transient assignment
                            def _records(df_: pd.DataFrame) -> list[dict[str, Any]]:
                                out: list[dict[str, Any]] = []
                                if df_ is None or getattr(df_, "empty", True):
                                    return out
                                cols = {c.lower().replace(" ", "_"): c for c in df_.columns}
                                for _, row in df_.iterrows():
                                    d = row[cols.get("date", "Date")]
                                    try:
                                        ds = (
                                            d.strftime("%Y-%m-%d")
                                            if hasattr(d, "strftime")
                                            else str(d)
                                        )
                                    except Exception:
                                        ds = str(d)

                                    def _num(key, default=None, _row=row):
                                        val = _row.get(
                                            cols.get(key, key.title().replace("_", " ")), default
                                        )
                                        return float(val) if pd.notna(val) else None

                                    out.append(
                                        {
                                            "date": ds,
                                            "open": _num("open"),
                                            "high": _num("high"),
                                            "low": _num("low"),
                                            "close": _num("close"),
                                            "adj_close": _num("adj_close"),
                                            "volume": _num("volume"),
                                        }
                                    )
                                return out

                            recs = _records(df)
                        else:
                            recs = []
                    else:
                        recs = []
                except TimeoutError:
                    err = "timeout"
                except Exception as e:  # provider errors should not crash the batch
                    msg = str(e).split("\n", 1)[0]
                    err = f"provider_error: {msg}" if msg else "provider_error"

                ok = (
                    err is None and len(recs) >= 0
                )  # success even if empty data (no_data handled below)
                if ok and not recs:
                    # mark as no_data explicitly to help UI/debug
                    err = "no_data"
                    ok = False

                if ok:
                    succeeded += 1
                else:
                    failed += 1

                results.append(
                    {
                        "ticker": t,
                        "ok": ok,
                        "error": None if ok else err,
                        "records": recs,
                        "duration_ms": round((time.time() - t0) * 1000, 2),
                    }
                )

            out = {
                "summary": {
                    "requested": len(tickers_list),
                    "valid": len(valids),
                    "invalid": len(invalids),
                    "succeeded": succeeded,
                    "failed": failed,
                    "timeout_s": per_timeout,
                    "provider_chain": _extract_chain(),
                },
                "results": results,
            }

            return out

        called = False
        if debug_source:
            # Try with return_source first if supported by provider signature
            try:
                supports_return = False
                try:
                    sig = inspect.signature(mp.fetch_ohlc)
                    supports_return = "return_source" in sig.parameters
                except Exception:
                    supports_return = False
                kw = {"period_days": period_days, "adjusted": True}
                if supports_return:
                    kw["return_source"] = True
                result = await _call_with_timeout(mp.fetch_ohlc, tickers_list, **kw)
                if isinstance(result, tuple) and len(result) == 2:
                    frames, src = result
                    called = True
            except TypeError:
                called = False
            except Exception:
                called = False
        if not called:
            kw2 = {"period_days": period_days, "adjusted": True}
            result = await _call_with_timeout(mp.fetch_ohlc, tickers_list, **kw2)
            if isinstance(result, dict):
                frames = result
            elif isinstance(result, tuple) and result:
                # Some odd providers might still return (frames, src)
                try:
                    frames = result[0] or {}
                    src = result[1] or {}
                except Exception:
                    frames = {}
            else:
                frames = {}
            if not debug_source:
                src = {}

        def _records(df: pd.DataFrame) -> list[dict[str, Any]]:
            out: list[dict[str, Any]] = []
            if df is None or getattr(df, "empty", True):
                return out
            cols = {c.lower().replace(" ", "_"): c for c in df.columns}
            for _, row in df.iterrows():
                d = row[cols.get("date", "Date")]
                try:
                    ds = d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d)
                except Exception:
                    ds = str(d)

                def _num(key, default=None, _row=row):
                    val = _row.get(cols.get(key, key.title().replace("_", " ")), default)
                    return float(val) if pd.notna(val) else None

                out.append(
                    {
                        "date": ds,
                        "open": _num("open"),
                        "high": _num("high"),
                        "low": _num("low"),
                        "close": _num("close"),
                        "adj_close": _num("adj_close"),
                        "volume": _num("volume"),
                    }
                )
            return out

        mapping: dict[str, list[dict[str, Any]]] = {}
        for t in tickers_list:
            df = (frames or {}).get(t)
            mapping[t] = _records(df) if df is not None else []

        if not debug_source:
            return mapping

        return {
            "symbols": mapping,
            "source": src,
            "provider_chain": [
                getattr(p, "name", getattr(p, "__class__", type("x", (), {})).__name__).lower()
                for p in (getattr(mp, "providers", []) or [])
            ]
            or [
                str(
                    getattr(mp, "name", getattr(mp, "__class__", type("x", (), {})).__name__)
                ).lower()
            ],
        }

    except Exception:
        logging.getLogger("ziggy").exception("OHLC_ERROR")
        safe_keys = [t.strip().upper() for t in tickers.split(",") if t.strip()]
        if not debug_source and not batch:
            return {k: [] for k in safe_keys}
        return {
            "symbols": {k: [] for k in safe_keys},
            "source": dict.fromkeys(safe_keys, "<error>"),
            "provider_chain": [],
        }


# ───────────────────────────────────────────────────────────────────────────────
# Market Breadth KPIs
# ───────────────────────────────────────────────────────────────────────────────
@router.get("/market/breadth")
def market_breadth(
    symbols: str | None = Query(
        None, description="Comma-separated tickers; default internal watchlist"
    ),
    period_days: int = Query(260, ge=30, le=2000),
):
    """
    Market breadth over a watchlist:
    - Advance/Decline/Unch
    - % above 50/200DMA
    - New highs/lows (≈52w using 252 trading days)
    - TRIN (Arms Index) using end-of-day volume
    """
    from app.services.market_providers import YFinanceProvider

    try:
        try:
            from app.services.screener import DEFAULT_TICKERS as _DEF
        except Exception:
            _DEF = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA"]

        tickers = [t.strip().upper() for t in symbols.split(",") if t.strip()] if symbols else _DEF

        provider = YFinanceProvider()
        frames = provider.fetch_ohlc(tickers, period_days=period_days)
        if inspect.isawaitable(frames):
            from collections.abc import Coroutine
            from typing import Any, cast

            frames = asyncio.run(cast(Coroutine[Any, Any, Any], frames))

        adv = dec = unch = 0
        vol_adv = vol_dec = 0.0
        above50 = above200 = 0
        nh = nl = 0
        total = 0

        for _t, df in (frames or {}).items():
            if df is None or df.empty or "Close" not in df.columns:
                continue

            close = pd.to_numeric(df["Close"], errors="coerce").dropna()
            if close.shape[0] < 2:
                continue

            last = float(close.iloc[-1])
            prev = float(close.iloc[-2])

            vol_last = (
                float(df["Volume"].iloc[-1])
                if "Volume" in df.columns and pd.notna(df["Volume"].iloc[-1])
                else 0.0
            )
            if last > prev:
                adv += 1
                vol_adv += vol_last
            elif last < prev:
                dec += 1
                vol_dec += vol_last
            else:
                unch += 1

            if close.shape[0] >= 50:
                sma50_val = close.rolling(window=50).mean().iloc[-1]
                if pd.notna(sma50_val) and last > float(sma50_val):
                    above50 += 1
            if close.shape[0] >= 200:
                sma200_val = close.rolling(window=200).mean().iloc[-1]
                if pd.notna(sma200_val) and last > float(sma200_val):
                    above200 += 1

            look = min(close.shape[0], 252)
            window = close.iloc[-look:]
            if last >= float(window.max()) * 0.999:
                nh += 1
            if last <= float(window.min()) * 1.001:
                nl += 1

            total += 1

        trin = None
        if adv > 0 and dec > 0 and vol_adv > 0 and vol_dec > 0:
            trin = (adv / dec) / (vol_adv / vol_dec)

        return {
            "asof": time.time(),
            "universe": {"count": total, "symbols": tickers},
            "ad": {"adv": adv, "dec": dec, "unch": unch},
            "pct_above": {
                "dma50": (above50 / total) if total else None,
                "dma200": (above200 / total) if total else None,
            },
            "nh_nl": {"highs": nh, "lows": nl},
            "trin": trin,
            "period_days": period_days,
        }
    except Exception:
        logging.getLogger("ziggy").exception("BREADTH_ERROR")
        return {
            "asof": time.time(),
            "universe": {"count": 0, "symbols": []},
            "ad": {"adv": 0, "dec": 0},
            "pct_above": {"dma50": None, "dma200": None},
            "nh_nl": {"highs": 0, "lows": 0},
            "trin": None,
            "period_days": period_days,
        }


# ───────────────────────────────────────────────────────────────────────────────
# Risk Lite (CPC with CPCE fallback + cache)
# ───────────────────────────────────────────────────────────────────────────────
_CPC_CACHE: dict[str, Any] = {"ts": 0.0, "data": None}
_CPC_TTL = 300  # 5 minutes


@router.get("/market/risk-lite")
def risk_lite():
    """
    Lightweight risk bar feed: CBOE Put/Call Index (^CPC).
    Falls back to ^CPCE (equity-only P/C) if ^CPC is unavailable.
    Returns last value, 20-day mean, 20-day z-score, last date, and which ticker was used.
    """
    import yfinance as yf

    now = time.time()
    if _CPC_CACHE["data"] and (now - _CPC_CACHE["ts"] < _CPC_TTL):
        return _CPC_CACHE["data"]

    payload: dict[str, Any]
    tickers_try = ["^CPC", "^CPCE"]

    series = None
    used = None
    for t in tickers_try:
        try:
            df = yf.download(
                t, period="6mo", interval="1d", auto_adjust=False, progress=False, threads=False
            )
            if isinstance(df, pd.DataFrame) and not df.empty and "Close" in df.columns:
                s = pd.to_numeric(df["Close"], errors="coerce").dropna()
                if s.shape[0] >= 5:
                    series = s
                    used = t
                    break
        except Exception:
            continue

    if series is None:
        payload = {"cpc": None, "error": "No data for ^CPC/^CPCE (blocked or unavailable)"}
    else:
        last = float(series.iloc[-1])
        tail = series.tail(20)
        ma20 = float(tail.mean())
        std20 = float(tail.std()) or 1e-9
        z20 = (last - ma20) / std20
        date = str(series.index[-1].date())
        payload = {"cpc": {"ticker": used, "last": last, "ma20": ma20, "z20": z20, "date": date}}

    _CPC_CACHE["ts"] = now
    _CPC_CACHE["data"] = payload
    return payload


# Backward-compatibility aliases (frontends might hit either)
@router.get("/market-risk-lite")
def risk_lite_alias():
    return risk_lite()


@router.get("/market/risk")
def risk_lite_alias2():
    return risk_lite()


# ───────────────────────────────────────────────────────────────────────────────
# QUICK ACTIONS ++ Simple Backtest API (SMA 50 cross, long-only)
# ───────────────────────────────────────────────────────────────────────────────
class BacktestIn(BaseModel):
    symbol: str | None = None
    ticker: str | None = None
    strategy: str = Field(default="sma50_cross", description="Strategy key")
    timeframe: str | None = Field(
        default=None, description="UI timeframe label, e.g. 1M, 6M, 1Y, 5Y, Max"
    )
    period_days: int | None = Field(default=None, ge=5, le=3650)


class BacktestOut(BaseModel):
    ok: bool = True
    symbol: str
    strategy: str
    metrics: dict[str, Any] = Field(default_factory=dict)
    summary: str | None = None
    url: str | None = None
    report_url: str | None = None
    html_url: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)
    # Extended fields for richer UI rendering (optional in legacy clients)
    period: str | int | None = None
    trades: list[dict[str, Any]] = Field(default_factory=list)
    returns: list[float] = Field(default_factory=list)
    equity: list[float] = Field(default_factory=list)
    notes: str | None = None


_TF_TO_DAYS = {
    "1D": 10,  # use small cushion to include enough candles
    "5D": 15,
    "1M": 30,
    "6M": 180,
    "1Y": 365,
    "5Y": 365 * 5,
    "MAX": 3650,
    "Max": 3650,
}


def _norm_symbol(sym: str | None, alt: str | None) -> str:
    s = (sym or alt or "").strip().upper()
    return s


def _tf_to_days(tf: str | None, explicit: int | None) -> int:
    if explicit and explicit >= 5:
        return int(explicit)
    if not tf:
        return 365  # default 1Y
    return int(_TF_TO_DAYS.get(tf.upper(), 365))


def _series_from_df(df: pd.DataFrame) -> pd.Series:
    if df is None or getattr(df, "empty", True):
        return pd.Series(dtype=float)
    # Prefer Adj Close if present
    if "Adj Close" in df.columns:
        s = pd.to_numeric(df["Adj Close"], errors="coerce").dropna()
    else:
        s = (
            pd.to_numeric(df["Close"], errors="coerce").dropna()
            if "Close" in df.columns
            else pd.Series(dtype=float)
        )
    return s


def _sma_cross_long_only(close: pd.Series, window: int = 50):
    """
    Very small SMA cross strategy:
    - Long when close crosses ABOVE SMA(window)
    - Exit when close crosses BELOW SMA(window)
    - Fully invested/not invested; no short, no fees/slippage
    Returns dict with metrics & trades list.
    """
    if close is None or close.shape[0] < max(5, window + 2):
        return {"trades": [], "returns": [], "equity": [], "metrics": {}}

    sma = close.rolling(window=window).mean()
    # Signals: +1 long, 0 flat
    long_signal = (close > sma).astype(int)
    # Cross points
    cross = long_signal.diff().fillna(0)
    # Enter on +1, exit on -1
    entries = list(close.index[cross > 0])
    exits = list(close.index[cross < 0])

    # If we end long, close at last bar
    if len(entries) > len(exits):
        exits.append(close.index[-1])

    trades = []
    pnl = []
    eq = []
    equity = 1.0
    last_price = float(close.iloc[0])

    # Build daily returns for Sharpe
    daily_rets = [0.0]

    for i in range(1, len(close)):
        p = float(close.iloc[i])
        r = (p / last_price) - 1.0
        last_price = p
        # If invested, equity follows price; else flat (keep equity)
        invested = any(
            e <= close.index[i] and close.index[i] < x for e, x in zip(entries, exits, strict=False)
        )
        if invested:
            equity *= 1.0 + r
            daily_rets.append(r)
        else:
            daily_rets.append(0.0)
        eq.append(equity)

    for ent, ex in zip(entries, exits, strict=False):
        pe = float(close.loc[ent])
        px = float(close.loc[ex])
        ret = (px / pe) - 1.0
        trades.append(
            {
                "entry": str(getattr(ent, "date", ent)),
                "exit": str(getattr(ex, "date", ex)),
                "ret": ret,
            }
        )
        pnl.append(ret)

    # Metrics
    total_ret = equity - 1.0 if eq else 0.0
    days = (
        max((close.index[-1] - close.index[0]).days, 1)
        if hasattr(close.index, "freq") or hasattr(close.index, "inferred_type")
        else max(len(close), 1)
    )
    yrs = days / 365.0 if isinstance(days, (int, float)) else 1.0
    cagr = (equity ** (1.0 / max(yrs, 1e-9)) - 1.0) if equity > 0 else None
    wins = sum(1 for x in pnl if x > 0)
    win_rate = (wins / len(pnl)) if pnl else None

    # Max drawdown from equity curve
    if eq:
        import numpy as np

        arr = np.array(eq, dtype=float)
        peak = np.maximum.accumulate(arr)
        dd = (arr / np.maximum(peak, 1e-12)) - 1.0
        max_dd = float(dd.min())
    else:
        max_dd = None

    # Sharpe using daily returns (assume 252 trading days)
    try:
        import numpy as np

        dr = np.array(daily_rets[1:], dtype=float)
        if dr.size > 1 and dr.std() > 0:
            sharpe = float(dr.mean() / dr.std() * math.sqrt(252))
        else:
            sharpe = None
    except Exception:
        sharpe = None

    metrics = {
        "total_return": total_ret,
        "cagr": cagr,
        "win_rate": win_rate,
        "trades": len(trades),
        "max_drawdown": max_dd,
        "sharpe": sharpe,
        "window": window,
    }
    return {"trades": trades, "returns": pnl, "equity": eq, "metrics": metrics}


def _provider_names(mp) -> list[str]:
    if mp is None:
        return []
    chain = getattr(mp, "providers", None)
    if isinstance(chain, (list, tuple)) and chain:
        return [
            str(getattr(p, "name", getattr(p, "__class__", type("x", (), {})).__name__)).lower()
            for p in chain
        ]
    return [str(getattr(mp, "name", getattr(mp, "__class__", type("x", (), {})).__name__)).lower()]


# ───────────────────────────────────────────────────────────────────────────────
# Global throttle (risk-lite) helpers — backend hints for position sizing
# ───────────────────────────────────────────────────────────────────────────────
def _norm_guard(v: str | None) -> str:
    k = (v or "").strip().lower()
    return "hard" if k == "hard" else "off" if k == "off" else "soft"


def _clamp(n: float, lo: float, hi: float) -> float:
    try:
        return max(lo, min(hi, float(n)))
    except Exception:
        return lo


def _compute_global_throttle(
    guardrails: str | None,
    risk_used_pct: float | None,
    daily_max_pct: float | None,
) -> dict[str, Any]:
    """
    Mirror of frontend risk-lite profile:
      guardrails off      -> factor 1
      used <50% of cap    -> 1
      50..75%             -> 0.5
      75..<100%           -> 0.25
      >=100%              -> 0 (hard) / 0.1 (soft)
    Returns {factor, reason}.
    """
    g = _norm_guard(guardrails)
    if g == "off":
        return {"factor": 1.0, "reason": None}
    used = _clamp(float(risk_used_pct or 0.0), 0.0, 100.0)
    cap = _clamp(float(daily_max_pct or 100.0), 1.0, 100.0)
    ratio = used / cap if cap > 0 else 0.0
    if ratio >= 1.0:
        return {"factor": 0.0 if g == "hard" else 0.1, "reason": "daily-limit-reached"}
    if ratio >= 0.75:
        return {"factor": 0.25, "reason": "over-75%"}
    if ratio >= 0.5:
        return {"factor": 0.5, "reason": "over-50%"}
    return {"factor": 1.0, "reason": None}


def _read_throttle_from_meta_or_headers(
    meta: dict[str, Any], hdrs: dict[str, Any]
) -> dict[str, Any]:
    # precedence: body.meta > headers
    tf = meta.get("throttleFactor")
    ru = meta.get("riskUsed")
    gr = meta.get("guardrails")
    dm = meta.get("dailyMaxPct")

    def _to_opt_float(x: Any) -> float | None:
        try:
            if x is None:
                return None
            return float(x)
        except Exception:
            return None

    tf = _to_opt_float(tf) if tf is not None else _to_opt_float(hdrs.get("X-Ziggy-Throttle"))
    ru = _to_opt_float(ru) if ru is not None else _to_opt_float(hdrs.get("X-Ziggy-Risk-Used"))
    gr = str(gr) if gr is not None else (hdrs.get("X-Ziggy-Guardrails"))
    dm = _to_opt_float(dm) if dm is not None else _to_opt_float(hdrs.get("X-Ziggy-Daily-Max-Pct"))
    # if explicit factor is present, use it; else derive from components
    if tf is not None and _isfinite(tf):
        return {"factor": _clamp(tf, 0.0, 1.0), "reason": "client-supplied"}
    comp = _compute_global_throttle(gr, ru, dm)
    comp["reason"] = comp.get("reason") or "derived"
    return comp


@router.post("/backtest")
def trading_backtest(body: BacktestIn):
    """
    Lightweight backtest intended for quick UI feedback.
    Now enhanced with Market Brain when available.
    Falls back to legacy SMA cross strategy if brain unavailable.
    """
    try:
        symbol = _norm_symbol(body.symbol, body.ticker)
        if not symbol:
            raise HTTPException(status_code=400, detail={"error": "symbol required"})

        # Try Market Brain backtest first
        if MARKET_BRAIN_AVAILABLE:
            try:
                brain_result = _backtest_with_market_brain(symbol, body)
                if brain_result:
                    return brain_result
            except Exception as e:
                logging.getLogger("ziggy").debug(f"Market Brain backtest failed for {symbol}: {e}")

        # Fallback to legacy backtest
        return _backtest_with_legacy_logic(symbol, body)

    except HTTPException:
        raise
    except Exception as e:
        logging.getLogger("ziggy").exception("BACKTEST_ERROR")
        raise HTTPException(
            status_code=500, detail={"error": "backtest failed", "reason": str(e)}
        ) from e


def _backtest_with_market_brain(symbol: str, body: BacktestIn) -> BacktestOut | None:
    """Run backtest using Market Brain system."""
    try:
        # Narrow types for type checker and runtime safety
        if not MARKET_BRAIN_AVAILABLE or BacktestPeriod is None:
            return None
        # Map timeframe to backtest period
        period_map = {
            "1M": BacktestPeriod.ONE_MONTH,
            "3M": BacktestPeriod.THREE_MONTHS,
            "6M": BacktestPeriod.SIX_MONTHS,
            "1Y": BacktestPeriod.ONE_YEAR,
            "2Y": BacktestPeriod.TWO_YEARS,
            "5Y": BacktestPeriod.FIVE_YEARS,
        }

        # Default to 3 months if timeframe not specified or not found
        timeframe = (body.timeframe or "3M").upper()
        period = period_map.get(timeframe, BacktestPeriod.THREE_MONTHS)

        # Run market brain backtest
        brain_results = quick_backtest(symbol, period)

        if not brain_results or not brain_results.trades:
            return None

        # Convert brain results to legacy format for UI compatibility
        msg_bits = []

        # Performance metrics
        if brain_results.annual_return:
            msg_bits.append(f"CAGR {brain_results.annual_return * 100:.1f}%")
        if brain_results.win_rate:
            msg_bits.append(f"Win {brain_results.win_rate * 100:.0f}%")
        if brain_results.total_trades:
            msg_bits.append(f"{brain_results.total_trades} trades")
        if brain_results.sharpe_ratio:
            msg_bits.append(f"Sharpe {brain_results.sharpe_ratio:.2f}")

        summary = " | ".join(msg_bits) or "Market Brain backtest complete"

        # Convert trades to legacy format
        legacy_trades = []
        for trade in brain_results.trades:
            legacy_trades.append(
                {
                    "entry": trade.entry_date.strftime("%Y-%m-%d") if trade.entry_date else "",
                    "exit": trade.exit_date.strftime("%Y-%m-%d") if trade.exit_date else "",
                    "ret": trade.pnl_percent / 100.0 if trade.pnl_percent else 0.0,
                }
            )

        # Enhanced metrics with brain data
        brain_metrics = {
            "cagr": brain_results.annual_return,
            "win_rate": brain_results.win_rate,
            "trades": brain_results.total_trades,
            "total_return": brain_results.total_return,
            "sharpe_ratio": brain_results.sharpe_ratio,
            "max_drawdown": brain_results.max_drawdown,
            "volatility": brain_results.volatility,
            # Market Brain specific metrics
            "avg_win": brain_results.avg_win,
            "avg_loss": brain_results.avg_loss,
            "winning_trades": brain_results.winning_trades,
            "losing_trades": brain_results.losing_trades,
            "calmar_ratio": brain_results.calmar_ratio,
            "var_95": brain_results.var_95,
            # Strategy info
            "strategy": "market_brain_signals",
            "period": period.value,
            "enhanced": True,
        }

        return BacktestOut(
            symbol=symbol,
            strategy="market_brain_signals",
            period=period.value,
            summary=summary,
            trades=legacy_trades,
            returns=brain_results.daily_returns,
            equity=brain_results.equity_curve,
            metrics=brain_metrics,
            notes=f"Enhanced backtest using Market Brain v1. Total return: {brain_results.total_return:.2%}",
        )

    except Exception as e:
        logging.getLogger("ziggy").error(f"Market Brain backtest error for {symbol}: {e}")
        return None


def _backtest_with_legacy_logic(symbol: str, body: BacktestIn) -> BacktestOut:
    """Fallback legacy backtest logic."""
    days = _tf_to_days(body.timeframe, body.period_days)
    mp = _price_provider()
    if mp is None:
        raise HTTPException(status_code=503, detail={"error": "no market data provider"})

    # Fetch OHLC for one symbol
    def _fetch():
        res = mp.fetch_ohlc([symbol], period_days=days, adjusted=True)  # type: ignore
        if inspect.isawaitable(res):
            from collections.abc import Coroutine
            from typing import Any, cast

            return asyncio.run(cast(Coroutine[Any, Any, Any], res))
        return res

    frames = _fetch()
    df = (frames or {}).get(symbol)
    if df is None or getattr(df, "empty", True):
        raise HTTPException(status_code=404, detail={"error": f"no data for {symbol}"})

    close = _series_from_df(df)
    strat = (body.strategy or "sma50_cross").strip().lower()

    if strat in ("sma50_cross", "sma50", "dma50"):
        result = _sma_cross_long_only(close, window=50)
    elif strat in ("sma20_cross", "sma20"):
        result = _sma_cross_long_only(close, window=20)
    else:
        # Unknown: fall back to sma50
        result = _sma_cross_long_only(close, window=50)

    metrics = dict(result.get("metrics") or {})
    cagr = metrics.get("cagr")
    win = metrics.get("win_rate")
    trades = metrics.get("trades")
    msg_bits = []
    if cagr is not None:
        msg_bits.append(f"CAGR {cagr * 100:.1f}%")
    if win is not None:
        msg_bits.append(f"Win% {win * 100:.1f}%")
    if trades is not None:
        msg_bits.append(f"Trades {int(trades)}")
    summary = " | ".join(msg_bits) or "Backtest complete"

    return BacktestOut(
        symbol=symbol,
        strategy=strat,
        period=body.timeframe or f"{days}d",
        summary=summary,
        trades=result.get("trades", []),
        returns=result.get("returns", []),
        equity=result.get("equity", []),
        metrics=metrics,
        notes=f"Legacy SMA cross strategy. Period: {days} days",
    )


# Aliases for flexibility (frontends may call these)
# Note: /backtest is already defined above (line 1497)

@router.post("/strategy/backtest")
def backtest_alias2(body: BacktestIn):
    return trading_backtest(body)


# ───────────────────────────────────────────────────────────────────────────────
# NEW: One-click Paper Trade (ATR-based sizing) — safe stub
# ───────────────────────────────────────────────────────────────────────────────
class TradeSizing(BaseModel):
    method: str | None = Field(default=None, description="atr | fixed | none")
    atr: float | None = None
    period: int | None = Field(default=14, ge=1, le=1000)
    atrMult: float | None = Field(default=1.5, ge=0.01, le=1000)  # noqa: N815
    riskAmount: float | None = Field(default=None, ge=0.0)  # noqa: N815
    rMultiple: float | None = Field(default=2.0, ge=0.1, le=1000)  # noqa: N815


class TradeIn(BaseModel):
    symbol: str | None = None
    ticker: str | None = None
    side: str = Field(..., description="BUY | SELL")
    qty: int | None = Field(None, ge=0)
    entry: float | None = None
    stop: float | None = None
    target: float | None = None
    sizing: TradeSizing | None = None
    meta: dict[str, Any] = Field(default_factory=dict)
    type: str = Field(default="MARKET")
    mode: str = Field(default="paper")


class TradeOut(BaseModel):
    ok: bool = True
    symbol: str
    side: str
    qty: int
    entry: float
    stop: float
    target: float
    sizing: dict[str, Any] = Field(default_factory=dict)
    risk: dict[str, Any] = Field(default_factory=dict)
    message: str | None = None
    provider_chain: list[str] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)


def _compute_atr_for(symbol: str, days: int = 60, period: int = 14) -> float | None:
    mp = _price_provider()
    if mp is None:
        return None
    try:
        res = mp.fetch_ohlc([symbol], period_days=days, adjusted=True)  # type: ignore
        if inspect.isawaitable(res):
            from collections.abc import Coroutine
            from typing import Any, cast

            frames = asyncio.run(cast(Coroutine[Any, Any, Any], res))
        else:
            frames = res
        df = (frames or {}).get(symbol)
        if df is None or getattr(df, "empty", True):
            return None
        hi = pd.to_numeric(df.get("High") or df.get("high"), errors="coerce")
        lo = pd.to_numeric(df.get("Low") or df.get("low"), errors="coerce")
        cl = pd.to_numeric(df.get("Close") or df.get("close"), errors="coerce")
        if (
            any(s is None for s in (hi, lo, cl))
            or hi.isna().all()
            or lo.isna().all()
            or cl.isna().all()
        ):
            return None
        prev_close = cl.shift(1)
        tr = pd.concat(
            [(hi - lo).abs(), (hi - prev_close).abs(), (lo - prev_close).abs()], axis=1
        ).max(axis=1)
        tr = tr.dropna()
        if tr.empty:
            return None
        n = max(1, min(int(period), tr.shape[0]))
        return float(tr.tail(n).mean())
    except Exception:
        logging.getLogger("ziggy").exception("ATR_COMPUTE_ERROR")
        return None


@router.post("/trade/market", response_model=TradeOut)
def trade_market(
    body: TradeIn,
    x_idempotency_key: str | None = Header(default=None, convert_underscores=True),
    # Optional throttle hints via headers (frontend also sends in body.meta)
    x_ziggy_throttle: float | None = Header(default=None, convert_underscores=True),
    x_ziggy_risk_used: float | None = Header(default=None, convert_underscores=True),
    x_ziggy_guardrails: str | None = Header(default=None, convert_underscores=True),
    x_ziggy_daily_max_pct: float | None = Header(default=None, convert_underscores=True),
):
    """
    Paper trade stub: echoes computed ATR sizing and projected stops/targets.
    Does NOT route to a broker. Safe for UI one-click experiments.
    """
    try:
        symbol = _norm_symbol(body.symbol, body.ticker)
        if not symbol:
            raise HTTPException(status_code=400, detail={"error": "symbol required"})
        side = (body.side or "").upper()
        if side not in {"BUY", "SELL"}:
            raise HTTPException(status_code=400, detail={"error": "side must be BUY or SELL"})

        entry = _to_num(body.entry)
        stop = _to_num(body.stop)
        target = _to_num(body.target)
        qty = None if body.qty is None else int(max(0, int(body.qty)))
        sizing = body.sizing or TradeSizing()
        mp = _price_provider()
        # If no entry provided, try to infer from provider's last close
        if entry is None and mp is not None:
            try:
                res = mp.fetch_ohlc([symbol], period_days=5, adjusted=True)  # type: ignore
                if inspect.isawaitable(res):
                    from collections.abc import Coroutine
                    from typing import Any, cast

                    frames = asyncio.run(cast(Coroutine[Any, Any, Any], res))
                else:
                    frames = res
                df = (frames or {}).get(symbol)
                if df is not None and not getattr(df, "empty", True):
                    close_col = "Adj Close" if "Adj Close" in df.columns else "Close"
                    entry = float(pd.to_numeric(df[close_col], errors="coerce").dropna().iloc[-1])
            except Exception:
                entry = entry  # leave as is

        if entry is None or not math.isfinite(entry):
            raise HTTPException(
                status_code=400, detail={"error": "entry price required or unavailable"}
            )

        # Resolve throttle (risk-lite) from meta/headers; default factor=1.0
        header_map = {
            "X-Ziggy-Throttle": x_ziggy_throttle,
            "X-Ziggy-Risk-Used": x_ziggy_risk_used,
            "X-Ziggy-Guardrails": x_ziggy_guardrails,
            "X-Ziggy-Daily-Max-Pct": x_ziggy_daily_max_pct,
        }
        meta_in: dict[str, Any] = dict(body.meta or {})
        throttle_info = _read_throttle_from_meta_or_headers(meta_in, header_map)
        throttle_factor = float(throttle_info.get("factor", 1.0))
        if not _isfinite(throttle_factor):
            throttle_factor = 1.0

        # ATR sizing path
        if (sizing.method or "").lower() == "atr":
            # compute ATR if not provided
            atr_val = _to_num(sizing.atr)
            if atr_val is None:
                atr_val = _compute_atr_for(
                    symbol, days=max(30, (sizing.period or 14) * 4), period=sizing.period or 14
                )

            atr_mult = sizing.atrMult or 1.5
            if atr_val is None or not math.isfinite(atr_val):
                raise HTTPException(
                    status_code=422, detail={"error": "atr unavailable to size position"}
                )

            # derive stop if absent
            if stop is None or not math.isfinite(stop):
                stop = entry - atr_val * atr_mult if side == "BUY" else entry + atr_val * atr_mult

            # derive target if absent
            if target is None or not math.isfinite(target):
                r_mult = sizing.rMultiple or 2.0
                stop_dist = abs(entry - float(stop))
                target = entry + stop_dist * r_mult if side == "BUY" else entry - stop_dist * r_mult

            # derive qty from riskAmount if not provided
            if qty is None:
                risk_amt = _to_num(sizing.riskAmount)
                if risk_amt is not None and risk_amt > 0:
                    stop_dist = abs(entry - float(stop))
                    # APPLY GLOBAL THROTTLE to riskAmount before qty calculation
                    eff_risk_amt = float(risk_amt) * float(_clamp(throttle_factor, 0.0, 1.0))
                    qty_calc = int(max(0, math.floor(eff_risk_amt / max(stop_dist, 1e-12))))
                    qty = qty_calc
            else:
                # qty was explicitly provided; do not override, but provide a suggestedQty hint
                if _clamp(throttle_factor, 0.0, 1.0) < 1.0:
                    try:
                        suggested_qty = int(
                            max(0, math.floor(int(qty) * float(_clamp(throttle_factor, 0.0, 1.0))))
                        )
                    except Exception:
                        suggested_qty = None
                    meta_in.setdefault("throttle", {})
                    meta_in["throttle"]["suggestedQty"] = suggested_qty
                    meta_in["throttle"]["note"] = "global throttle suggests reduced size"

            sizing_dict = sizing.dict()
            sizing_dict["atr"] = atr_val
        else:
            sizing_dict = sizing.dict() if sizing else {}

        if qty is None:
            qty = 0  # explicit

        # risk summary
        stop_dist = abs(entry - float(stop)) if (stop is not None and math.isfinite(stop)) else None
        r_multiple = None
        if stop_dist and stop_dist > 0 and target is not None and math.isfinite(target):
            if side == "BUY":
                r_multiple = (target - entry) / stop_dist
            else:
                r_multiple = (entry - target) / stop_dist

        out = TradeOut(
            ok=True,
            symbol=symbol,
            side=side,
            qty=int(qty),
            entry=float(entry),
            stop=float(stop) if stop is not None else float("nan"),
            target=float(target) if target is not None else float("nan"),
            sizing=sizing_dict,
            risk={
                "stopDistance": stop_dist,
                "rMultiple": r_multiple,
            },
            message=(
                f"paper {side.lower()} {qty} {symbol} @ ~{entry:.4f} (ATR sizing)"
                if (sizing_dict.get("method") == "atr")
                else f"paper {side.lower()} {qty} {symbol} @ ~{entry:.4f}"
            ),
            provider_chain=_provider_names(_price_provider()),
            meta={
                **(body.meta or {}),
                # Attach throttle details for UI diagnostics
                "throttle": {
                    "factor": float(_clamp(throttle_factor, 0.0, 1.0)),
                    "reason": throttle_info.get("reason"),
                    "source": (
                        "meta"
                        if "throttleFactor" in (body.meta or {})
                        else (
                            "headers"
                            if header_map.get("X-Ziggy-Throttle") is not None
                            or header_map.get("X-Ziggy-Risk-Used") is not None
                            else "derived"
                        )
                    ),
                    "appliedTo": (
                        "riskAmount"
                        if (sizing.method or "").lower() == "atr" and (body.qty is None)
                        else "suggestion"
                    ),
                },
                "idempotencyKey": x_idempotency_key,
                "receivedAt": datetime.utcnow().isoformat(),
                "mode": body.mode or "paper",
                "type": body.type or "MARKET",
            },
        )

        # Best-effort Telegram note (do not fail the trade if this errors)
        with contextlib.suppress(Exception):
            tg_send(
                f"🧪 Paper trade: {out.message}\nSL {out.stop:.4f} • TP {out.target:.4f} • qty {out.qty}",
                kind="paper",
            )

        return out

    except HTTPException:
        raise
    except Exception as e:
        logging.getLogger("ziggy").exception("TRADE_MARKET_ERROR")
        raise HTTPException(
            status_code=500, detail={"error": "paper trade failed", "reason": str(e)}
        ) from e


# ───────────────────────────────────────────────────────────────────────────────
# local helpers (module-private)
# ───────────────────────────────────────────────────────────────────────────────
def _to_num(v) -> float | None:
    try:
        n = float(v)
        if math.isfinite(n):
            return n
    except Exception:
        pass
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# Enhanced Trading System Endpoints
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/trade/orders")
def get_orders(status: str | None = Query(None, description="Filter by order status")):
    """Get all orders, optionally filtered by status."""
    try:
        from app.trading.signals import get_orders

        return {"orders": get_orders(status)}
    except Exception as e:
        logging.getLogger("ziggy").exception("Error getting orders")
        return {"orders": [], "error": str(e)}


@router.get("/trade/positions")
def get_positions():
    """Get all current positions."""
    try:
        from app.trading.signals import get_positions

        return {"positions": get_positions()}
    except Exception as e:
        logging.getLogger("ziggy").exception("Error getting positions")
        return {"positions": [], "error": str(e)}


@router.get("/trade/portfolio")
def get_portfolio():
    """Get portfolio summary with total values and P&L."""
    try:
        from app.trading.signals import get_portfolio_summary

        return get_portfolio_summary()
    except Exception as e:
        logging.getLogger("ziggy").exception("Error getting portfolio")
        return {"error": str(e), "total_value": 0, "total_pnl": 0}


@router.delete("/trade/orders/{order_id}")
def cancel_order(order_id: str):
    """Cancel a specific order."""
    try:
        # Note: This is async but we're calling from sync route
        # In production, you'd want to make this route async
        import asyncio

        from app.trading.signals import cancel_signal

        try:
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(cancel_signal(order_id))
        except RuntimeError:
            # If no event loop is running, create a new one
            result = asyncio.run(cancel_signal(order_id))
        return result
    except Exception as e:
        logging.getLogger("ziggy").exception(f"Error cancelling order {order_id}")
        return {"ok": False, "error": str(e)}


@router.post("/trade/execute")
async def execute_trade(body: TradeIn):
    """Execute a trade with enhanced signal data."""
    try:
        from app.trading.signals import enqueue_execute

        # Convert TradeIn to signal data
        signal_data = {
            "symbol": body.symbol or body.ticker,
            "side": body.side,
            "qty": body.qty,
            "quantity": body.qty,
            "order_type": "market",  # Default to market orders
            "entry": body.entry,
            "stop": body.stop,
            "target": body.target,
            "sizing": body.sizing.dict() if body.sizing else {},
            "meta": body.meta or {},
        }

        signal_id = f"trade_{int(time.time() * 1000)}"
        result = await enqueue_execute(signal_id, signal_data)
        return result

    except Exception as e:
        logging.getLogger("ziggy").exception("Error executing enhanced trade")
        return {"ok": False, "error": str(e)}


@router.post("/trade/mode/{mode}")
def set_trading_mode(mode: str):
    """Set trading mode: 'paper' or 'live'."""
    try:
        from app.trading.signals import get_trading_manager

        manager = get_trading_manager()

        if mode.lower() == "paper":
            manager.enable_paper_trading()
            return {"ok": True, "mode": "paper", "message": "Paper trading enabled"}
        elif mode.lower() == "live":
            # Note: This would require broker connector setup
            return {"ok": False, "error": "Live trading requires broker connector setup"}
        else:
            return {"ok": False, "error": "Mode must be 'paper' or 'live'"}

    except Exception as e:
        logging.getLogger("ziggy").exception(f"Error setting trading mode {mode}")
        return {"ok": False, "error": str(e)}
