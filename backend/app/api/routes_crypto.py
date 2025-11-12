# backend/app/api/routes_crypto.py
from __future__ import annotations

import os
import time
from typing import Any

from fastapi import APIRouter, Query


# Market Brain Integration
try:
    from app.services.market_brain.simple_data_hub import DataSource, enhance_market_data

    BRAIN_AVAILABLE = True
    _enhance_market_data = enhance_market_data
    _DataSource = DataSource
except ImportError:
    BRAIN_AVAILABLE = False
    _enhance_market_data = None
    _DataSource = None

router = APIRouter()

# small in-mem TTL cache (scoped for crypto)
# Ensure quotes refresh ~10–15s even if global CACHE_TTL_SECONDS is large.
_GLOBAL_TTL = int(os.getenv("CACHE_TTL_SECONDS", "60"))
_TTL = min(_GLOBAL_TTL, 15)  # cap at 15s so frontend’s 10s poll isn't stale
_CACHE: dict[str, dict[str, Any]] = {}  # key -> {"ts": float, "data": any}


def _cache_get(key: str):
    e = _CACHE.get(key)
    if not e:
        return None
    if time.time() - e.get("ts", 0) > _TTL:
        _CACHE.pop(key, None)
        return None
    return e.get("data")


def _cache_put(key: str, data: Any):
    _CACHE[key] = {"ts": time.time(), "data": data}
    return data


def _split(s: str | None) -> list[str]:
    return [x.strip().upper() for x in str(s or "").split(",") if x.strip()]


def _get_crypto_provider():
    try:
        from app.services.provider_factory import get_crypto_provider  # type: ignore

        return get_crypto_provider()
    except Exception:
        return None


# ---- QUOTES -----------------------------------------------------------------


@router.get("/crypto/quotes")
async def crypto_quotes(
    symbols: str = Query(..., description="Comma-separated symbols like BTC-USD,ETH-USD,SOL-USD"),
):
    syms = _split(symbols)
    key = f"quotes:{','.join(syms)}"
    c = _cache_get(key)
    if c is not None:
        return c

    out: dict[str, dict[str, Any]] = {s: {} for s in syms}

    # Try primary provider chain
    prov = _get_crypto_provider()
    if prov:
        try:
            # Try a few likely method names
            if hasattr(prov, "fetch_quotes"):
                data = await prov.fetch_quotes(syms)  # type: ignore
            elif hasattr(prov, "fetch_crypto_quotes"):
                data = await prov.fetch_crypto_quotes(syms)  # type: ignore
            elif hasattr(prov, "quotes"):
                data = await prov.quotes(syms)  # type: ignore
            else:
                data = None
            if isinstance(data, dict):
                for s in syms:
                    d = data.get(s) or {}
                    # normalize
                    price = d.get("price") or d.get("last") or d.get("close")
                    try:
                        price = float(price) if price is not None else None
                    except Exception:
                        price = None
                    out[s] = {
                        "price": price,
                        "change_pct_24h": d.get("change_pct_24h")
                        or d.get("pct24h")
                        or d.get("chg24h"),
                        "source": d.get("source") or getattr(prov, "name", "provider"),
                    }
        except Exception:
            # fall back below
            pass

    # Fallback to yfinance for majors if provider failed/partial
    missing = [s for s in syms if not out.get(s) or out[s].get("price") is None]
    if missing:
        try:
            import yfinance as yf  # type: ignore

            for s in missing:
                try:
                    t = yf.Ticker(s)
                    # Try fast_info (newer yfinance), fallback to history
                    pr = getattr(getattr(t, "fast_info", {}), "last_price", None)
                    if pr is None:
                        hist = t.history(period="2d", interval="1h")
                        if hist is not None and not hist.empty:
                            pr = float(hist["Close"].iloc[-1])
                            # 24h pct (approx): compare with ~24h back if we have it (percent)
                            base = (
                                float(hist["Close"].iloc[-25])
                                if hist.shape[0] > 25
                                else float(hist["Close"].iloc[0])
                            )
                            pct24 = ((pr - base) / base * 100.0) if base else None
                        else:
                            pct24 = None
                    else:
                        # compute pct24 via 1d history
                        hist = t.history(period="2d", interval="1h")
                        if hist is not None and not hist.empty:
                            base = (
                                float(hist["Close"].iloc[-25])
                                if hist.shape[0] > 25
                                else float(hist["Close"].iloc[0])
                            )
                            pct24 = ((float(pr) - base) / base * 100.0) if base else None
                        else:
                            pct24 = None
                    out[s] = {
                        "price": float(pr) if pr is not None else None,
                        "change_pct_24h": pct24,
                        "source": "yfinance",
                    }
                except Exception:
                    out[s] = {"price": None, "change_pct_24h": None, "source": "fallback"}
        except Exception:
            # leave whatever we have
            pass

    # Enhance with market brain intelligence
    if BRAIN_AVAILABLE and _enhance_market_data and _DataSource:
        out = _enhance_market_data(out, _DataSource.CRYPTO, symbols=symbols)

    return _cache_put(key, out)


# ---- OHLC -------------------------------------------------------------------


@router.get("/crypto/ohlc")
async def crypto_ohlc(
    symbols: str = Query(..., description="Comma-separated symbols"),
    interval: str = Query("1m", pattern="^(1m|5m)$"),
    minutes: int = Query(240, ge=1, le=7 * 24 * 60),
):
    syms = _split(symbols)
    key = f"ohlc:{','.join(syms)}:{interval}:{minutes}"
    c = _cache_get(key)
    if c is not None:
        return c

    out: dict[str, list[dict[str, Any]]] = {s: [] for s in syms}

    prov = _get_crypto_provider()
    if prov:
        try:
            # Try likely method names
            if hasattr(prov, "fetch_ohlc_crypto"):
                data = await prov.fetch_ohlc_crypto(syms, interval=interval, minutes=minutes)  # type: ignore
            elif hasattr(prov, "fetch_ohlc"):
                data = await prov.fetch_ohlc(syms, interval=interval, minutes=minutes)  # type: ignore
            else:
                data = None
            if isinstance(data, dict):
                # Expect each symbol -> list of records (date/open/high/low/close/volume)
                for s, arr in data.items():
                    if isinstance(arr, list):
                        out[s] = [
                            {
                                "date": str(r.get("date") or r.get("time") or r.get("ts")),
                                "open": r.get("open"),
                                "high": r.get("high"),
                                "low": r.get("low"),
                                "close": r.get("close"),
                                "volume": r.get("volume"),
                            }
                            for r in arr
                        ]
        except Exception:
            pass

    # Fallback: yfinance intraday bars
    remain = [s for s in syms if not out.get(s) or not out[s]]
    if remain:
        try:
            import math

            import yfinance as yf  # type: ignore

            # yfinance intraday supports period up to 7d for 1m/5m
            days = max(1, min(7, math.ceil(minutes / (24 * 60))))
            yf_interval = interval  # "1m" or "5m"
            for s in remain:
                try:
                    df = yf.download(
                        s,
                        period=f"{days}d",
                        interval=yf_interval,
                        auto_adjust=False,
                        progress=False,
                        threads=False,
                    )
                    if df is None or df.empty:
                        continue
                    # Slice last N minutes
                    arr: list[dict[str, Any]] = []
                    tail = df.tail(minutes)
                    for idx, row in tail.iterrows():
                        # idx is a Timestamp
                        ts = getattr(idx, "to_pydatetime", lambda: idx)()
                        d = getattr(ts, "strftime", lambda *_: str(ts))("%Y-%m-%d %H:%M")
                        arr.append(
                            {
                                "date": d,
                                "open": (
                                    float(row.get("Open", float("nan")))
                                    if row.get("Open") is not None
                                    else None
                                ),
                                "high": (
                                    float(row.get("High", float("nan")))
                                    if row.get("High") is not None
                                    else None
                                ),
                                "low": (
                                    float(row.get("Low", float("nan")))
                                    if row.get("Low") is not None
                                    else None
                                ),
                                "close": (
                                    float(row.get("Close", float("nan")))
                                    if row.get("Close") is not None
                                    else None
                                ),
                                "volume": (
                                    float(row.get("Volume", float("nan")))
                                    if row.get("Volume") is not None
                                    else None
                                ),
                            }
                        )
                    out[s] = arr
                except Exception:
                    out[s] = []
        except Exception:
            pass

    # Enhance with market brain intelligence
    if BRAIN_AVAILABLE and _enhance_market_data and _DataSource:
        out = _enhance_market_data(out, _DataSource.CRYPTO, symbols=symbols)

    return _cache_put(key, out)
