from __future__ import annotations

import inspect
import math
import time
from typing import Any

from fastapi import APIRouter, Query

from app.services.provider_factory import get_price_provider


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

# ── helpers ────────────────────────────────────────────────────────────────────


def _finite(x: float | None) -> bool:
    try:
        return x is not None and math.isfinite(float(x))
    except Exception:
        return False


def _to_float(x) -> float | None:
    """Cast to float; return None on None/NaN/Inf or failure."""
    try:
        fx = float(x)
        return fx if math.isfinite(fx) else None
    except Exception:
        return None


def _pct(last: float | None, prev: float | None) -> float | None:
    """
    Percentage change helper.
    Returns None if either value is missing/non-finite or prev == 0.
    """
    try:
        if last is None or prev is None:
            return None
        la = float(last)
        pr = float(prev)
        if not math.isfinite(la) or not math.isfinite(pr) or pr == 0.0:
            return None
        return (la - pr) / pr * 100.0
    except Exception:
        return None


async def _maybe_await(x):
    """Await value if it's awaitable, else return directly."""
    if inspect.isawaitable(x):
        return await x
    return x


# Utility to check if another router already exposes a path (to avoid duplicates)
def _router_has_path(rtr: APIRouter, path: str, method: str = "GET") -> bool:
    try:
        for r in getattr(rtr, "routes", []):
            if getattr(r, "path", None) == path:
                methods = set(getattr(r, "methods", {"GET"}))
                if method.upper() in methods:
                    return True
    except Exception:
        pass
    return False


# ── route ─────────────────────────────────────────────────────────────────────


@router.get("/overview", response_model=None)
async def market_overview(
    symbols: str = Query("AAPL,MSFT", description="Comma-separated symbols."),
    period_days: int = Query(30, ge=2, le=3650),
    since_open: bool = Query(
        False,
        description="If true, 1D change is vs today's regular-session open; else vs previous close.",
    ),
    debug_source: bool = Query(
        False,
        description="If true, include provider source per symbol and provider_chain.",
    ),
) -> dict[str, Any]:
    """
    Compact overview using the provider factory (priority + failover + small cache).

    Per symbol:
      - last
      - chg1d   (vs today's open if since_open=true, else vs previous close)
      - chg5d   (vs close 5 bars ago)
      - chg20d  (vs close 20 bars ago)
      - ref     (baseline used for chg1d)
    """
    syms: list[str] = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    mp = get_price_provider()

    # No provider: return empty-but-valid shape
    if not mp:
        resp: dict[str, Any] = {
            "asof": time.time(),
            "since_open": bool(since_open),
            "symbols": dict.fromkeys(syms),
        }
        if debug_source:
            resp["source"] = dict.fromkeys(syms, "<none>")
            resp["provider_chain"] = []
        return resp

    # Fetch OHLC frames (normalized) and, optionally, the source provider per ticker
    try:
        if debug_source:
            frames, sources = await mp.fetch_ohlc(  # type: ignore
                syms, period_days=period_days, adjusted=True, return_source=True
            )
        else:
            frames = await mp.fetch_ohlc(  # type: ignore
                syms, period_days=period_days, adjusted=True
            )
            sources = {}
    except Exception:
        # Provider hiccup: keep UI resilient
        frames, sources = {}, {}

    # Normalize shapes: providers may return (frames, sources) or dict directly
    try:
        if isinstance(frames, tuple) or isinstance(frames, list):
            # e.g., (frames_dict, sources_dict)
            f0 = frames[0] if len(frames) > 0 else {}
            s0 = frames[1] if len(frames) > 1 else {}
            frames = f0 or {}
            sources = s0 or {}
        if frames is None:
            frames = {}
        if sources is None:
            sources = {}
    except Exception:
        frames = frames or {}
        sources = sources or {}

    # If requested, get today's regular-session opens (provider may be sync/async)
    opens_by_symbol: dict[str, float | None] = {}
    if since_open:
        try:
            opens_result = mp.today_open_prices(syms)  # may be sync or async
            opens_raw = await _maybe_await(opens_result) or {}
            # sanitize opens
            opens_by_symbol = {k: _to_float(v) for k, v in dict(opens_raw).items()}
        except Exception:
            opens_by_symbol = dict.fromkeys(syms)

    # Build response
    out: dict[str, Any] = {}

    for s in syms:
        df = frames.get(s)
        if df is None or getattr(df, "empty", True) or "Close" not in df.columns:
            out[s] = None
            continue

        last = _to_float(df["Close"].iloc[-1])
        if not _finite(last):
            out[s] = None
            continue

        def get_back(n: int) -> float | None:
            try:
                if len(df) > n:
                    return _to_float(df["Close"].iloc[-1 - n])
            except Exception:
                pass
            return None

        # Baseline for 1D change
        ref: float | None
        if since_open:
            # today's open (if available) else previous close
            ref = opens_by_symbol.get(s)
            if not _finite(ref):
                ref = get_back(1)
        else:
            ref = get_back(1)

        out[s] = {
            "last": last,
            "chg1d": _pct(last, ref),
            "chg5d": _pct(last, get_back(5)),
            "chg20d": _pct(last, get_back(20)),
            "ref": ref,
        }

    resp: dict[str, Any] = {
        "asof": time.time(),
        "since_open": bool(since_open),
        "symbols": out,
    }
    if debug_source:
        resp["source"] = {k: sources.get(k) for k in syms}
        resp["provider_chain"] = [
            getattr(p, "name", p.__class__.__name__).lower() for p in getattr(mp, "providers", [])
        ]

    # Enhance with Market Brain Intelligence
    if BRAIN_AVAILABLE and _enhance_market_data and _DataSource:
        try:
            resp = _enhance_market_data(
                resp,
                _DataSource.OVERVIEW,
                symbols=syms,
                period_days=period_days,
                since_open=since_open,
            )
        except Exception as e:
            # Log error but don't break the response
            print(f"Market brain enhancement failed: {e}")

    return resp


# ── Market breadth (no keys required; yfinance underneath via provider) ───────
@router.get("/breadth")
async def market_breadth(
    symbols: str | None = Query(
        None, description="Comma-separated tickers; default internal watchlist"
    ),
    period_days: int = Query(260, ge=30, le=2000),
) -> dict[str, Any]:
    """
    Market breadth over a watchlist:
      - Advance/Decline/Unch
      - % above 50/200DMA
      - New highs/lows (≈52w using 252 trading days)
      - TRIN (Arms Index) using end-of-day volume

    NOTE: To support multiple front-ends without breaking changes, we KEEP the
    existing response shape and *augment* it with a few mirrored top-level
    convenience fields (adv/dec/unch, n/count, above50/above200, pct50/pct200,
    ratio50/ratio200). No existing keys are removed or renamed.
    """
    import pandas as pd  # local import

    try:
        try:
            from app.services.screener import DEFAULT_TICKERS as _DEF  # type: ignore
        except Exception:
            _DEF = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA"]

        tickers: list[str] = (
            [t.strip().upper() for t in symbols.split(",") if t.strip()] if symbols else _DEF
        )

        # Use provider factory (which defaults to yfinance for no-key usage)
        mp = get_price_provider()
        frames = {}
        if mp:
            res = mp.fetch_ohlc(tickers, period_days=period_days, adjusted=True)  # type: ignore
            frames = await _maybe_await(res) or {}

        adv = dec = unch = 0
        vol_adv = vol_dec = 0.0
        above50 = above200 = 0
        nh = nl = 0
        total = 0

        for t, df in (frames or {}).items():
            if df is None or getattr(df, "empty", True) or "Close" not in df.columns:
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

        # Base (existing) payload
        payload: dict[str, Any] = {
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

        # ---- Augment with *additional* top-level mirrors (non-breaking) ----
        # Sample size
        payload["n"] = total
        payload["count"] = total

        # A/D mirrors
        payload["adv"] = adv
        payload["dec"] = dec
        payload["unch"] = unch

        # Above MA counts
        payload["above50"] = above50
        payload["above200"] = above200

        # Percent/ratio helpers expected by some UIs
        # ratios (0..1)
        payload["ratio50"] = (above50 / total) if total else None
        payload["ratio200"] = (above200 / total) if total else None
        # pct (0..100)
        payload["pct50"] = ((above50 / total) * 100.0) if total else None
        payload["pct200"] = ((above200 / total) * 100.0) if total else None

        # Enhance with Market Brain Intelligence
        if BRAIN_AVAILABLE and _enhance_market_data and _DataSource:
            try:
                payload = _enhance_market_data(payload, _DataSource.BREADTH)
            except Exception as e:
                # Log error but don't break the response
                print(f"Market brain breadth enhancement failed: {e}")

        return payload
    except Exception:
        # keep shape stable
        return {
            "asof": time.time(),
            "universe": {"count": 0, "symbols": []},
            "ad": {"adv": 0, "dec": 0, "unch": 0},
            "pct_above": {"dma50": None, "dma200": None},
            "nh_nl": {"highs": 0, "lows": 0},
            "trin": None,
            "period_days": period_days,
            # non-breaking mirrors present even on error
            "n": 0,
            "count": 0,
            "adv": 0,
            "dec": 0,
            "unch": 0,
            "above50": 0,
            "above200": 0,
            "ratio50": None,
            "ratio200": None,
            "pct50": None,
            "pct200": None,
        }


# ── Risk-lite (CPC/CPCE via yfinance with 5-min cache) — enhanced with backoff ──
# NOTE: We preserve existing keys and only *add* optional metadata to help the UI
#       display a retry countdown while serving the last good value.

_CPC_CACHE: dict[str, Any] = {"ts": 0.0, "data": None}
_CPC_TTL = 300  # seconds

# NEW: minimal backoff/last-good state (non-breaking)
_CPC_STATE: dict[str, Any] = {
    "last_ok": None,  # last successful payload (same shape as response)
    "fail": 0,  # consecutive failure count
    "retry_until": 0.0,  # epoch seconds until next allowed attempt
    "last_err": "",  # last error string
}


def _now() -> float:
    return time.time()


def _add_block_meta(
    payload: dict[str, Any], seconds: int, until_ts: float, err: str = ""
) -> dict[str, Any]:
    """Augment a payload with blocked/retry metadata (top-level and mirrored under cpc)."""
    out = dict(payload or {})
    out["blocked"] = True
    out["retry_in"] = max(0, int(seconds))
    out["retry_at"] = int(round(until_ts * 1000))  # ms epoch for UI convenience
    if err:
        out.setdefault("error", str(err))
    cpc = dict(out.get("cpc") or {})  # mirror under cpc if present
    cpc["blocked"] = True
    cpc["retry_in"] = out["retry_in"]
    cpc["retry_at"] = out["retry_at"]
    out["cpc"] = cpc or None
    return out


def _risk_lite_payload() -> dict[str, Any]:
    """Fetch ^CPC (fallback ^CPCE) and compute last, ma20, z20, date.
    Augments with std20 and default z-score bands for the thermometer UI.
    """
    import pandas as pd
    import yfinance as yf

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
        return {"cpc": None, "error": "No data for ^CPC/^CPCE"}

    last = float(series.iloc[-1])
    tail = series.tail(20)
    ma20 = float(tail.mean())
    std20 = float(tail.std()) or 1e-9
    z20 = (last - ma20) / std20
    date = str(series.index[-1].date())
    # Preserve existing keys; safely add extras for UI
    payload = {
        "cpc": {
            "ticker": used,
            "last": last,
            "ma20": ma20,
            "z20": z20,
            "date": date,
            # ---- new (non-breaking) fields for thermometer UI ----
            "std20": std20,
            "n": int(tail.shape[0]),
            "bands": [-2, -1, 0, 1, 2],
        }
    }

    # Enhance with Market Brain Intelligence
    if BRAIN_AVAILABLE and _enhance_market_data and _DataSource:
        try:
            payload = _enhance_market_data(payload, _DataSource.RISK_LITE)
        except Exception as e:
            # Log error but don't break the response
            print(f"Market brain risk enhancement failed: {e}")

    return payload


# Check if routes_trading already defines /market/risk-lite; if yes, skip here.
_risk_already_exposed = False
try:
    from app.api import routes_trading as _rt  # type: ignore

    if hasattr(_rt, "router") and _router_has_path(_rt.router, "/market/risk-lite", "GET"):
        _risk_already_exposed = True
except Exception:
    _risk_already_exposed = False

if not _risk_already_exposed:

    @router.get("/risk-lite")
    def market_risk_lite():
        now = _now()

        # Return within TTL if we have a fresh payload
        try:
            if _CPC_CACHE["data"] and (now - _CPC_CACHE["ts"] < _CPC_TTL):
                return _CPC_CACHE["data"]
        except Exception:
            pass

        # If we are in backoff window, serve last_ok with blocked metadata
        try:
            retry_until = float(_CPC_STATE.get("retry_until") or 0.0)
        except Exception:
            retry_until = 0.0

        if retry_until > now:
            remaining = int(math.ceil(retry_until - now))
            last_ok = _CPC_STATE.get("last_ok")
            if last_ok:
                payload = _add_block_meta(
                    dict(last_ok), remaining, retry_until, str(_CPC_STATE.get("last_err", ""))
                )
                # cache this blocked response briefly to avoid thrash
                _CPC_CACHE["ts"] = now
                _CPC_CACHE["data"] = payload
                return payload
            # no last_ok: return a minimal blocked shape (non-breaking keys intact)
            minimal = _add_block_meta(
                {"cpc": None}, remaining, retry_until, str(_CPC_STATE.get("last_err", ""))
            )
            _CPC_CACHE["ts"] = now
            _CPC_CACHE["data"] = minimal
            return minimal

        # Attempt fresh fetch
        try:
            payload = _risk_lite_payload()
            # Treat cpc: None as failure for backoff purposes
            if not payload.get("cpc"):
                raise RuntimeError(payload.get("error") or "cpc unavailable")

            # Success → reset backoff and cache
            _CPC_STATE["last_ok"] = payload
            _CPC_STATE["fail"] = 0
            _CPC_STATE["retry_until"] = 0.0
            _CPC_STATE["last_err"] = ""

            _CPC_CACHE["ts"] = now
            _CPC_CACHE["data"] = payload
            return payload

        except Exception as e:
            # Failure → exponential backoff, serve last_ok with countdown if present
            try:
                _CPC_STATE["fail"] = int(_CPC_STATE.get("fail", 0) or 0) + 1
            except Exception:
                _CPC_STATE["fail"] = 1
            # backoff: 60, 120, 240, ... capped at 900s
            backoff = min(60 * (2 ** max(0, int(_CPC_STATE["fail"]) - 1)), 900)
            retry_until = now + backoff
            _CPC_STATE["retry_until"] = retry_until
            _CPC_STATE["last_err"] = repr(e)

            last_ok = _CPC_STATE.get("last_ok")
            if last_ok:
                payload = _add_block_meta(dict(last_ok), int(backoff), retry_until, repr(e))
            else:
                payload = _add_block_meta(
                    {"cpc": None, "error": f"risk-lite error: {e!r}"}, int(backoff), retry_until
                )

            _CPC_CACHE["ts"] = now
            _CPC_CACHE["data"] = payload
            return payload


# ── OPTIONAL: Macro history endpoint for modal (non-breaking, soft dependencies) ──
# Returns recent macro prints for a given code with optional SPX reactions.
# Shape:
#   { code, label?, history: [ { date, actual?, consensus?, previous?, surprise?,
#                               spx1d?, spx5d?, notes? } ] }
_MACRO_CACHE: dict[str, Any] = {"ts": 0.0, "key": "", "data": None}
_MACRO_TTL = 120  # seconds


def _read_macro_file(code: str) -> list[dict[str, Any]]:
    """
    Optional local source: data/macro_history/{CODE}.json or app/data/...
    File format: array of objects with fields (date, actual, consensus, previous, surprise?, notes?)
    Dates: 'YYYY-MM-DD' preferred.
    """
    import json
    import os

    candidates = [
        os.path.join("data", "macro_history", f"{code}.json"),
        os.path.join("app", "data", "macro_history", f"{code}.json"),
    ]
    for path in candidates:
        try:
            if os.path.exists(path):
                with open(path, encoding="utf-8") as f:
                    arr = json.load(f)
                    if isinstance(arr, list):
                        return arr
        except Exception:
            continue
    return []


def _compute_surprise_pct(
    actual: float | None, consensus: float | None, fallback: float | None = None
) -> float | None:
    try:
        if fallback is not None and math.isfinite(float(fallback)):
            return float(fallback)
    except Exception:
        pass
    try:
        if actual is None or consensus is None:
            return None
        a = float(actual)
        c = float(consensus)
        if not math.isfinite(a) or not math.isfinite(c) or c == 0.0:
            return None
        return (a - c) / abs(c) * 100.0
    except Exception:
        return None


async def _spx_reactions(dates: list[str]) -> dict[str, dict[str, float | None]]:
    """
    For each date (YYYY-MM-DD), compute SPX 1d/5d % changes based on close-to-close.
    Returns map: { date: { spx1d: %, spx5d: % } }
    """
    out: dict[str, dict[str, float | None]] = {}
    if not dates:
        return out

    mp = get_price_provider()
    if not mp:
        return out

    # Fetch enough history around the earliest date
    try:
        # crude buffer: ~400 days to cover most cases
        frames = await _maybe_await(mp.fetch_ohlc(["^GSPC"], period_days=400, adjusted=True))  # type: ignore
        df = (frames or {}).get("^GSPC")
        if df is None or getattr(df, "empty", True) or "Close" not in df.columns:
            return out

        # Normalize index to str dates
        idx_to_close = {}
        try:
            # If df index is datetime-like
            for i, v in enumerate(df["Close"].tolist()):
                d = df.index[i]
                ds = str(getattr(d, "date", lambda: d)())
                # If d is Timestamp -> date(); else assume already date-like
                if " " in ds:
                    ds = ds.split(" ")[0]
                idx_to_close.setdefault("dates", []).append(ds)
                idx_to_close.setdefault("closes", []).append(float(v))
        except Exception:
            # Fallback: try to read a Date column if present
            dates_col = list(map(str, df.get("Date", [])))
            closes_col = [float(x) for x in df["Close"].tolist()]
            idx_to_close["dates"] = dates_col
            idx_to_close["closes"] = closes_col

        cal_dates: list[str] = idx_to_close.get("dates", [])  # type: ignore
        closes: list[float] = idx_to_close.get("closes", [])  # type: ignore
        pos = {d: i for i, d in enumerate(cal_dates)}

        for d in dates:
            i = pos.get(d)
            if i is None:
                # try nearest same-day match by slicing (handles e.g., timezone variants)
                if d in pos:
                    i = pos[d]
                else:
                    out[d] = {"spx1d": None, "spx5d": None}
                    continue
            c0 = closes[i]
            c1 = closes[i + 1] if i + 1 < len(closes) else None
            c5 = closes[i + 5] if i + 5 < len(closes) else None
            spx1 = ((c1 - c0) / c0 * 100.0) if (c1 is not None and c0) else None
            spx5 = ((c5 - c0) / c0 * 100.0) if (c5 is not None and c0) else None
            out[d] = {"spx1d": spx1, "spx5d": spx5}
    except Exception:
        # best-effort
        return out

    return out


@router.get("/macro/history")
async def market_macro_history(
    code: str = Query(..., description="Macro code (e.g., CPI, NFP, PCE, ISM)."),
    limit: int = Query(50, ge=1, le=200),
) -> dict[str, Any]:
    """
    Optional macro history for UI modal. Best-effort, zero external keys changed.
    Source order priority:
      1) Local file: data/macro_history/{CODE}.json (or app/data/...)
      2) ( extensibility point ) Other providers can be added behind the factory.
    Enriches rows with computed surprise% (if missing) and SPX reactions when possible.
    """
    code_uc = str(code or "").strip().upper()
    label = None

    now = time.time()
    cache_key = f"{code_uc}:{limit}"
    if (
        _MACRO_CACHE["data"]
        and _MACRO_CACHE["key"] == cache_key
        and (now - _MACRO_CACHE["ts"] < _MACRO_TTL)
    ):
        return _MACRO_CACHE["data"]  # type: ignore

    # 1) Local JSON (non-blocking if absent)
    rows = _read_macro_file(code_uc)

    # TODO: hook in upstream providers here if available in your stack.

    # Normalize rows → {date, actual?, consensus?, previous?, surprise?, notes?}
    norm: list[dict[str, Any]] = []
    for r in rows:
        try:
            date = str(r.get("date") or r.get("day") or r.get("dt") or "")
            if not date:
                continue
            actual = _to_float(r.get("actual", r.get("value")))
            consensus = _to_float(r.get("consensus", r.get("estimate")))
            previous = _to_float(r.get("previous", r.get("prior")))
            surprise = _compute_surprise_pct(actual, consensus, _to_float(r.get("surprise")))
            notes = r.get("notes") or ""
            norm.append(
                {
                    "date": date,
                    "actual": actual,
                    "consensus": consensus,
                    "previous": previous,
                    "surprise": surprise,
                    "notes": notes,
                }
            )
        except Exception:
            continue

    # Sort desc and cap
    norm.sort(key=lambda x: x.get("date", ""), reverse=True)
    if len(norm) > limit:
        norm = norm[:limit]

    # Enrich with SPX reactions (best-effort) — single outer guard for provider and computed enrichments
    try:
        # Provider-based next-day reaction enrichment (best-effort)
        mp = get_price_provider()
        if mp is not None:
            ticker_spx = "^GSPC"
            # local optional imports -> keep endpoint soft-dependency
            try:
                import pandas as pd  # type: ignore
            except Exception:
                pd = None  # type: ignore

            res = mp.fetch_ohlc([ticker_spx], period_days=365)  # type: ignore
            # In async endpoint: await if awaitable, else accept sync result
            if inspect.isawaitable(res):
                frames = await _maybe_await(res)
            else:
                frames = res

            spx_df = (frames or {}).get(ticker_spx)
            if (
                spx_df is not None
                and not getattr(spx_df, "empty", True)
                and "Close" in spx_df.columns
            ):
                # Normalize date -> YYYY-MM-DD strings and compute next-day pct change
                spx_df = spx_df.copy()
                # Ensure Date column exists and use pandas if available
                if pd is None:
                    # pandas unavailable -> skip per-row mapping
                    raise RuntimeError("pandas unavailable for SPX enrichment")
                if "Date" in spx_df.columns:
                    dates = pd.to_datetime(spx_df["Date"], errors="coerce")
                else:
                    dates = pd.to_datetime(spx_df.index, errors="coerce")
                spx_df["_dstr"] = dates.dt.date.astype(str)
                spx_df["_close"] = pd.to_numeric(
                    spx_df.get("Close") or spx_df.get("close"), errors="coerce"
                )
                spx_df = spx_df.dropna(subset=["_close"]).reset_index(drop=True)
                spx_df["_next_close"] = spx_df["_close"].shift(-1)
                spx_df["_next_pct"] = (
                    (spx_df["_next_close"] - spx_df["_close"]) / spx_df["_close"] * 100.0
                )
                spx_map = dict(zip(spx_df["_dstr"], spx_df["_next_pct"]))
                for r in norm:
                    try:
                        d = r.get("date")
                        v = spx_map.get(d)
                        if v is not None and not pd.isna(v):
                            r["spx_reaction_next_pct"] = float(v)
                    except Exception:
                        continue

        # Compute aggregated spx1d/spx5d using existing helper (best-effort)
        dates = [row["date"] for row in norm]
        spx_map2 = await _spx_reactions(dates)
        for row in norm:
            spx = spx_map2.get(row["date"], {})
            row["spx1d"] = spx.get("spx1d")
            row["spx5d"] = spx.get("spx5d")
            # Fallback: if provider-based next-day pct wasn't set, use computed spx1d
            try:
                if row.get("spx_reaction_next_pct") is None and row.get("spx1d") is not None:
                    row["spx_reaction_next_pct"] = float(row.get("spx1d"))
            except Exception:
                pass
    except Exception:
        # swallow any enrichment errors; return normalized macro rows unchanged
        pass

    payload: dict[str, Any] = {"code": code_uc, "label": label, "history": norm}
    _MACRO_CACHE["ts"] = now
    _MACRO_CACHE["key"] = cache_key
    _MACRO_CACHE["data"] = payload
    return payload
