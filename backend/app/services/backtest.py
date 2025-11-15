# backend/app/services/backtest.py
"""
Lightweight backtesting & ATR utilities.

This module is intentionally dependency-light (pandas/numpy only) and
provider-agnostic. It can be used by API routes for quick feedback,
UI previews, and paper-trade sizing.

Exports
-------
- get_price_provider()  -> provider manager or single provider (if available)
- fetch_ohlc(symbols, period_days, adjusted=True, provider=None) -> Dict[str, pd.DataFrame]
- series_from_df(df)    -> pd.Series of closing prices (Adj Close preferred)
- compute_atr_from_df(df, period=14) -> float | None
- compute_atr(symbol, period=14, lookback_days=60, provider=None) -> float | None
- atr_position_plan(entry, side, atr, atr_mult=1.5, r_multiple=2.0, risk_amount=None) -> dict
- sma_cross_backtest(close, window=50) -> dict(metrics, trades, equity, returns)
- run_backtest(symbol, strategy="sma50_cross", period_days=365, provider=None) -> dict

Notes
-----
- All computations are deterministic and run in-memory.
- No external network I/O happens in this module directly except
  through a provider you pass in (or the optional factory discovery).
"""

from __future__ import annotations

import inspect
import math
from collections.abc import Iterable
from typing import Any

import numpy as np
import pandas as pd


# Optional provider discovery (manager or single provider)
try:
    # Newer codebases
    from app.services.provider_factory import (
        get_price_provider as _factory_get_price_provider,  # type: ignore
    )
except Exception:
    _factory_get_price_provider = None  # type: ignore

try:
    # Legacy single-provider accessor
    from app.services.market_providers import get_provider as _legacy_get_provider  # type: ignore
except Exception:
    _legacy_get_provider = None  # type: ignore

__all__ = [
    "atr_position_plan",
    "compute_atr",
    "compute_atr_from_df",
    "fetch_ohlc",
    "get_price_provider",
    "run_backtest",
    "series_from_df",
    "sma_cross_backtest",
]


# ───────────────────────────────────────────────────────────────────────────────
# Provider discovery & OHLC fetch
# ───────────────────────────────────────────────────────────────────────────────


def get_price_provider():
    """
    Returns a provider manager if available, else a single legacy provider, else None.
    """
    if callable(_factory_get_price_provider):
        try:
            return _factory_get_price_provider()
        except Exception:
            pass
    if callable(_legacy_get_provider):
        try:
            return _legacy_get_provider()
        except Exception:
            pass
    return None


def _await_maybe(x):
    if inspect.isawaitable(x):
        # Avoid creating nested loops; this function should be called from sync
        import asyncio

        return asyncio.run(x)
    return x


def fetch_ohlc(
    symbols: Iterable[str],
    period_days: int = 365,
    adjusted: bool = True,
    provider=None,
) -> dict[str, pd.DataFrame]:
    """
    Fetch OHLC frames for a list of symbols using a provider.
    The provider is expected to expose `fetch_ohlc(symbols, period_days=..., adjusted=...)`
    and may be async or sync.

    Returns a dict: { symbol -> DataFrame }
    """
    syms = [str(s).strip().upper() for s in symbols if str(s).strip()]
    if not syms:
        return {}
    mp = provider or get_price_provider()
    if mp is None:
        return {s: pd.DataFrame() for s in syms}
    try:
        res = mp.fetch_ohlc(syms, period_days=period_days, adjusted=adjusted)  # type: ignore
        res = _await_maybe(res)
        if isinstance(res, dict):
            return res
        if isinstance(res, tuple) and res:
            # Some providers may return (frames, meta)
            try:
                return res[0] or {}
            except Exception:
                return {}
        return {}
    except Exception:
        return {s: pd.DataFrame() for s in syms}


# ───────────────────────────────────────────────────────────────────────────────
# Series & indicators
# ───────────────────────────────────────────────────────────────────────────────


def series_from_df(df: pd.DataFrame) -> pd.Series:
    """
    Extract a numeric closing price series from a DataFrame.
    Prefers 'Adj Close' when present; else falls back to 'Close'.
    Returns an empty float series on failure.
    """
    if df is None or getattr(df, "empty", True):
        return pd.Series(dtype=float)
    if "Adj Close" in df.columns:
        s = pd.to_numeric(df["Adj Close"], errors="coerce").dropna()
    elif "Close" in df.columns:
        s = pd.to_numeric(df["Close"], errors="coerce").dropna()
    else:
        return pd.Series(dtype=float)
    return s.astype(float)


def compute_atr_from_df(df: pd.DataFrame, period: int = 14) -> float | None:
    """
    Compute ATR from a DataFrame with columns High/Low/Close (case-insensitive ok).
    Returns the simple moving average of True Range over the last `period` bars.
    """
    if df is None or getattr(df, "empty", True):
        return None

    def _pick(col: str):
        if col in df.columns:
            return df[col]
        # allow lowercase variants (depending on provider normalization)
        alt = col.lower().capitalize()
        if alt in df.columns:
            return df[alt]
        lower = col.lower()
        if lower in df.columns:
            return df[lower]
        return None

    hi = _pick("High")
    lo = _pick("Low")
    cl = _pick("Close")
    if hi is None or lo is None or cl is None:
        return None

    hi = pd.to_numeric(hi, errors="coerce")
    lo = pd.to_numeric(lo, errors="coerce")
    cl = pd.to_numeric(cl, errors="coerce")
    if hi.isna().all() or lo.isna().all() or cl.isna().all():
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


def compute_atr(
    symbol: str,
    period: int = 14,
    lookback_days: int = 60,
    provider=None,
) -> float | None:
    """
    Convenience: fetch recent OHLC for `symbol` and compute ATR(period).
    """
    frames = fetch_ohlc(
        [symbol],
        period_days=max(lookback_days, period * 3),
        adjusted=True,
        provider=provider,
    )
    df = frames.get(symbol) or pd.DataFrame()
    return compute_atr_from_df(df, period=period)


# ───────────────────────────────────────────────────────────────────────────────
# Position planning (ATR sizing)
# ───────────────────────────────────────────────────────────────────────────────


def atr_position_plan(
    entry: float,
    side: str,
    atr: float,
    atr_mult: float = 1.5,
    r_multiple: float = 2.0,
    risk_amount: float | None = None,
) -> dict[str, Any]:
    """
    Given entry/side and an ATR value, compute a suggested stop/target and (optional) qty.
    - stop is ATR * atr_mult away from entry (below for BUY, above for SELL)
    - target is entry +/- stopDistance * r_multiple (sign according to side)
    - qty = floor(risk_amount / stopDistance) if risk_amount provided

    Returns dict with: { stop, target, stopDistance, rMultiple, qty? }
    """
    if entry is None or not math.isfinite(entry):
        raise ValueError("entry must be a finite number")
    if atr is None or not math.isfinite(atr):
        raise ValueError("atr must be a finite number")
    if atr_mult <= 0:
        raise ValueError("atr_mult must be > 0")

    side_u = (side or "").upper()
    if side_u not in {"BUY", "SELL"}:
        raise ValueError("side must be BUY or SELL")

    stop = entry - atr * atr_mult if side_u == "BUY" else entry + atr * atr_mult
    stop_dist = abs(entry - stop)

    if r_multiple <= 0:
        r_multiple = 2.0

    target = (
        entry + stop_dist * r_multiple
        if side_u == "BUY"
        else entry - stop_dist * r_multiple
    )

    qty = None
    if risk_amount is not None and risk_amount > 0:
        qty = int(max(0, math.floor(risk_amount / max(stop_dist, 1e-12))))

    return {
        "stop": float(stop),
        "target": float(target),
        "stopDistance": float(stop_dist),
        "rMultiple": float(r_multiple),
        **({"qty": int(qty)} if qty is not None else {}),
    }


# ───────────────────────────────────────────────────────────────────────────────
# Simple strategies & backtest runner
# ───────────────────────────────────────────────────────────────────────────────


def sma_cross_backtest(close: pd.Series, window: int = 50) -> dict[str, Any]:
    """
    Long-only SMA(window) cross:
    - Enter when Close crosses above SMA
    - Exit when Close crosses below SMA
    - No shorting, fees, or slippage. Equity follows price only while invested.

    Returns:
      {
        "trades": [{"entry": iso_date, "exit": iso_date, "ret": float}, ...],
        "returns": [float, ...],  # per-trade returns
        "equity": [float, ...],   # equity curve from second bar onward
        "metrics": {
            "total_return", "cagr", "win_rate", "trades", "max_drawdown", "sharpe", "window"
        }
      }
    """
    if close is None or close.shape[0] < max(5, window + 2):
        return {
            "trades": [],
            "returns": [],
            "equity": [],
            "metrics": {"window": window},
        }

    close = close.astype(float)
    sma = close.rolling(window=window).mean()
    long_signal = (close > sma).astype(int)
    cross = long_signal.diff().fillna(0)

    entries = list(close.index[cross > 0])
    exits = list(close.index[cross < 0])

    if len(entries) > len(exits):
        exits.append(close.index[-1])

    # Build equity curve and daily returns
    equity = 1.0
    eq: list[float] = []
    daily_rets: list[float] = [0.0]
    last_price = float(close.iloc[0])

    # For each day after the first, update equity if invested
    for i in range(1, len(close)):
        p = float(close.iloc[i])
        r = (p / last_price) - 1.0
        last_price = p
        invested = any(
            e <= close.index[i] and close.index[i] < x for e, x in zip(entries, exits)
        )
        if invested:
            equity *= 1.0 + r
            daily_rets.append(r)
        else:
            daily_rets.append(0.0)
        eq.append(equity)

    trades: list[dict[str, Any]] = []
    pnl: list[float] = []
    for ent, ex in zip(entries, exits):
        try:
            pe = float(close.loc[ent])
            px = float(close.loc[ex])
        except Exception:
            continue
        ret = (px / pe) - 1.0
        trades.append(
            {
                "entry": str(getattr(ent, "date", ent)),
                "exit": str(getattr(ex, "date", ex)),
                "ret": ret,
            }
        )
        pnl.append(ret)

    total_ret = equity - 1.0 if eq else 0.0
    # Approximate elapsed days
    try:
        days = (close.index[-1] - close.index[0]).days  # type: ignore
        if not isinstance(days, (int, float)):
            raise Exception
        days = max(int(days), 1)
    except Exception:
        days = max(len(close), 1)

    yrs = max(days / 365.0, 1e-9)
    cagr = (equity ** (1.0 / yrs) - 1.0) if equity > 0 else None
    wins = sum(1 for x in pnl if x > 0)
    win_rate = (wins / len(pnl)) if pnl else None

    # Max drawdown
    if eq:
        arr = np.array(eq, dtype=float)
        peak = np.maximum.accumulate(arr)
        dd = (arr / np.maximum(peak, 1e-12)) - 1.0
        max_dd = float(dd.min())
    else:
        max_dd = None

    # Daily Sharpe (252 trading days)
    dr = np.array(daily_rets[1:], dtype=float)
    sharpe = (
        float(dr.mean() / dr.std() * math.sqrt(252))
        if (dr.size > 1 and dr.std() > 0)
        else None
    )

    return {
        "trades": trades,
        "returns": pnl,
        "equity": eq,
        "metrics": {
            "total_return": total_ret,
            "cagr": cagr,
            "win_rate": win_rate,
            "trades": len(trades),
            "max_drawdown": max_dd,
            "sharpe": sharpe,
            "window": window,
        },
    }


def run_backtest(
    symbol: str,
    strategy: str = "sma50_cross",
    period_days: int = 365,
    provider=None,
) -> dict[str, Any]:
    """
    High-level backtest entrypoint.

    Parameters
    ----------
    symbol : str
        Ticker symbol (provider dependent).
    strategy : str
        Strategy key: 'sma50_cross', 'sma20_cross' (aliases: 'sma50', 'dma50', 'sma20').
    period_days : int
        Lookback period for OHLC data.
    provider :
        Optional provider instance; if None, discovery will be attempted.

    Returns
    -------
    dict
        {
          "symbol": str,
          "strategy": str,
          "metrics": { ... },
          "trades": [...],
          "equity": [...],
          "meta": { "period_days": int, "provider_chain": [str,...] }
        }
    """
    sym = (symbol or "").strip().upper()
    if not sym:
        return {
            "symbol": "",
            "strategy": strategy,
            "metrics": {},
            "trades": [],
            "equity": [],
            "meta": {"period_days": period_days},
        }

    mp = provider or get_price_provider()
    frames = fetch_ohlc(
        [sym], period_days=max(5, int(period_days)), adjusted=True, provider=mp
    )
    df = frames.get(sym) or pd.DataFrame()
    close = series_from_df(df)

    strat_key = (strategy or "sma50_cross").strip().lower()
    if strat_key in ("sma50_cross", "sma50", "dma50"):
        result = sma_cross_backtest(close, window=50)
    elif strat_key in ("sma20_cross", "sma20"):
        result = sma_cross_backtest(close, window=20)
    else:
        # default fallback
        result = sma_cross_backtest(close, window=50)

    # provide minimal provider chain information, if available
    def _provider_names(p) -> list[str]:
        if p is None:
            return []
        chain = getattr(p, "providers", None)
        if isinstance(chain, (list, tuple)) and chain:
            return [
                str(
                    getattr(
                        pp, "name", getattr(pp, "__class__", type("x", (), {})).__name__
                    )
                ).lower()
                for pp in chain
            ]
        return [
            str(
                getattr(p, "name", getattr(p, "__class__", type("x", (), {})).__name__)
            ).lower()
        ]

    out = {
        "symbol": sym,
        "strategy": strat_key,
        "metrics": dict(result.get("metrics") or {}),
        "trades": list(result.get("trades") or []),
        "equity": list(result.get("equity") or []),
        "meta": {
            "period_days": int(period_days),
            "provider_chain": _provider_names(mp),
        },
    }
    return out
