from __future__ import annotations

import asyncio
import datetime as dt

# =============================================================
# Ziggy — Market Providers (normalized OHLC, fail-safe)
# - Uniform interface across YFinance, Polygon, Alpaca
# - Async fetch_ohlc() returning {ticker: pd.DataFrame}
# - Columns: ["Date","Open","High","Low","Close","Adj Close","Volume"]
# - UTC-naive datetimes, ascending sorted, equities only
# - today_open_prices() returns regular-session open where available
# - Graceful timeouts/errors -> empty frames / None
# - Indices/unsupported symbols (e.g., ^GSPC) -> empty frames to trigger fallback
# =============================================================
import os
from typing import Any

import pandas as pd

from app.core.config.time_tuning import TIMEOUTS


# Use env or default
DATA_PROVIDER = (
    (os.getenv("DATA_PROVIDER", os.getenv("DATA_SOURCE", "yfinance")) or "yfinance").lower().strip()
)


class MarketProvider:
    """Interface all providers must implement."""

    name: str = "base"
    supports_intraday: bool = False

    async def fetch_ohlc(
        self, tickers: list[str], period_days: int = 60, adjusted: bool = True
    ) -> dict[str, pd.DataFrame]:
        raise NotImplementedError

    def today_open_prices(self, tickers: list[str]) -> dict[str, float | None]:
        raise NotImplementedError

    # --------------------- common helpers ---------------------
    @staticmethod
    def _is_equity_symbol(t: str) -> bool:
        """Return True for basic US equity-like symbols. Exclude indices & fx/crypto."""
        if not t or not isinstance(t, str):
            return False
        t = t.strip().upper()
        if t.startswith("^"):  # indices like ^GSPC
            return False
        if "/" in t or "=" in t:  # pairs like EURUSD=X, BTC/USD, etc.
            return False
        if t.endswith("-USD") or t.endswith("USD"):  # crypto/forex heuristic
            return False
        return True

    @staticmethod
    def _normalize_df(df: pd.DataFrame) -> pd.DataFrame:
        import pandas as pd

        if df is None or not hasattr(df, "empty") or df.empty:
            return pd.DataFrame(
                columns=["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]
            )  # empty normalized

        # Coerce index to datetime (UTC-naive)
        try:
            idx = pd.to_datetime(df.index, utc=True, errors="coerce").tz_convert(None)
        except Exception:
            # If tz_convert fails (not tz-aware), do to_datetime without utc and drop tz info if any
            idx = pd.to_datetime(df.index, errors="coerce")
            # if it's tz-aware after parse, remove tz
            try:
                idx = idx.tz_localize(None)
            except Exception:
                pass

        df = df.copy()
        df.index = idx

        # Standardize column names
        df.columns = [str(c).strip().title() for c in df.columns]

        # Map possible alternative names
        rename_map = {
            "Adj Close": "Adj Close",
            "Adjclose": "Adj Close",
            "Adjusted Close": "Adj Close",
            "Open": "Open",
            "High": "High",
            "Low": "Low",
            "Close": "Close",
            "Volume": "Volume",
        }
        for c in list(df.columns):
            if c not in rename_map and c.title() in rename_map:
                df.rename(columns={c: rename_map[c.title()]}, inplace=True)
        # Ensure required columns exist, filling where possible
        for col in ["Open", "High", "Low", "Close", "Volume"]:
            if col not in df.columns:
                df[col] = None
        if "Adj Close" not in df.columns:
            df["Adj Close"] = df.get("Close")

        # Keep only required columns
        df = df[["Open", "High", "Low", "Close", "Adj Close", "Volume"]]

        # Drop rows with missing Close
        df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
        df = df.dropna(subset=["Close"]).copy()

        # Build the explicit Date column (UTC-naive)
        df.insert(0, "Date", df.index)

        # Sort ascending
        df = df.sort_values("Date").reset_index(drop=True)
        return df

    @staticmethod
    def _empty_frame() -> pd.DataFrame:
        return pd.DataFrame(
            columns=["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]
        )  # normalized empty


# ---------- YFINANCE (default, no key required) ----------
class YFinanceProvider(MarketProvider):
    """
    Robust yfinance provider:
      - Uses yf.download(..., auto_adjust=False) to keep both Close & Adj Close
      - Cleans/normalizes frames (flatten & standardize)
      - Returns empty for unsupported symbols (e.g., ^GSPC) to allow fallback
    """

    name = "yfinance"
    supports_intraday = False

    def __init__(self):
        import yfinance as yf  # lazy import to keep import-time light

        self.yf = yf
        self._last_status: Any = "ok"  # for manager diagnostics

    async def fetch_ohlc(
        self, tickers: list[str], period_days: int = 60, adjusted: bool = True
    ) -> dict[str, pd.DataFrame]:
        period_days = max(30, int(period_days or 60))
        start = (dt.date.today() - dt.timedelta(days=period_days)).isoformat()

        async def _fetch_one(t: str) -> pd.DataFrame:
            if not self._is_equity_symbol(t):
                return self._empty_frame()

            # Wrap the sync calls in a thread + timeout
            async def _run() -> pd.DataFrame:
                try:
                    df = await asyncio.to_thread(
                        self.yf.download,
                        t,
                        start=start,
                        auto_adjust=False,  # keep Adj Close column
                        progress=False,
                        threads=False,
                    )
                except Exception:
                    df = None
                if df is None or getattr(df, "empty", True):
                    try:
                        hist = await asyncio.to_thread(
                            self.yf.Ticker(t).history,
                            period=f"{period_days}d",
                            interval="1d",
                            auto_adjust=False,
                            actions=False,
                        )
                        df = hist
                    except Exception:
                        df = None
                return self._normalize_df(df) if df is not None else self._empty_frame()

            try:
                df_norm = await asyncio.wait_for(_run(), timeout=TIMEOUTS["provider_market_data"])
                # Mark status for the manager (ok/nodata)
                self._last_status = (
                    "ok" if (df_norm is not None and not df_norm.empty) else "nodata"
                )
                return df_norm
            except Exception:
                self._last_status = "error"
                return self._empty_frame()

        out: dict[str, pd.DataFrame] = {}
        for t in tickers:
            out[t] = await _fetch_one(t)
        return out

    def today_open_prices(self, tickers: list[str]) -> dict[str, float | None]:
        out: dict[str, float | None] = {}
        for t in tickers:
            if not self._is_equity_symbol(t):
                out[t] = None
                continue
            try:
                hist = self.yf.Ticker(t).history(
                    period="5d", interval="1d", auto_adjust=False, actions=False
                )
                df = self._normalize_df(hist)
                if df.empty:
                    out[t] = None
                else:
                    # Try to find today's row by date (UTC-naive)
                    today = dt.date.today()
                    # df['Date'] is datetime; compare by date() value
                    row = df.loc[df["Date"].dt.date == today]
                    if row.empty:
                        row = df.tail(1)
                    out[t] = (
                        float(row.iloc[-1]["Open"])
                        if not row.empty and row.iloc[-1]["Open"] is not None
                        else None
                    )
            except Exception:
                out[t] = None
        return out


# ---------- POLYGON (optional) ----------
class PolygonProvider(MarketProvider):
    """Polygon.io daily aggregates provider (equities only)."""

    name = "polygon"
    supports_intraday = True

    def __init__(self):
        # Accept multiple env names for the API key
        self.api_key = (
            os.getenv("POLYGON_API_KEY") or os.getenv("POLYGON_KEY") or os.getenv("POLY_API_KEY")
        )
        # Base URL with default
        self.base = (
            os.getenv("POLYGON_BASE_URL") or os.getenv("POLYGON_BASE") or "https://api.polygon.io"
        ).rstrip("/")

        # Create a shared AsyncClient; never raise if httpx missing
        try:
            import httpx  # type: ignore

            headers = {"Accept": "application/json"}
            # Prefer Authorization header if key is present; Polygon supports this
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self.http = httpx.AsyncClient(
                base_url=self.base, timeout=TIMEOUTS["http_client_default"], headers=headers
            )
        except Exception:
            self.http = None  # soft-fail; provider stays usable but yields empties
        self._last_status: Any = None  # record last HTTP code or label

    async def fetch_ohlc(
        self, tickers: list[str], period_days: int = 60, adjusted: bool = True
    ) -> dict[str, pd.DataFrame]:
        import pandas as pd

        async def _fetch_one(t: str) -> pd.DataFrame:
            # Missing key or unsupported symbol => empty
            if not self._is_equity_symbol(t) or not self.http or not self.api_key:
                self._last_status = "missing_key" if not self.api_key else "no_client"
                return self._empty_frame()

            # Dates
            d = max(30, int(period_days or 60))
            end = dt.date.today()
            start = end - dt.timedelta(days=d)

            path = f"/v2/aggs/ticker/{t.upper()}/range/1/day/{start}/{end}"
            params = {"adjusted": str(adjusted).lower(), "limit": 50000}

            try:
                resp = await self.http.get(path, params=params)
                if resp is None:
                    self._last_status = "no_response"
                    return self._empty_frame()
                if resp.status_code != 200:
                    self._last_status = resp.status_code  # e.g., 429, 403, 5xx
                    return self._empty_frame()
                data = resp.json()
            except Exception:
                self._last_status = "error"
                return self._empty_frame()

            if not data or not data.get("results"):
                self._last_status = "nodata"
                return self._empty_frame()

            rows = data["results"]
            try:
                df = pd.DataFrame(
                    {
                        "Date": [
                            dt.datetime.utcfromtimestamp(r.get("t", 0) / 1000.0) for r in rows
                        ],
                        "Open": [r.get("o") for r in rows],
                        "High": [r.get("h") for r in rows],
                        "Low": [r.get("l") for r in rows],
                        "Close": [r.get("c") for r in rows],
                        "Adj Close": [r.get("c") for r in rows],  # already adjusted if requested
                        "Volume": [r.get("v") for r in rows],
                    }
                )
                df = df.sort_values("Date").reset_index(drop=True)
                self._last_status = "ok" if not df.empty else "nodata"
                return df
            except Exception:
                self._last_status = "error"
                return self._empty_frame()

        out: dict[str, pd.DataFrame] = {}
        for t in tickers:
            out[t] = await _fetch_one(t)
        return out

    def today_open_prices(self, tickers: list[str]) -> dict[str, float | None]:
        out: dict[str, float | None] = {}
        if not self.http or not self.api_key:
            return dict.fromkeys(tickers)

        async def _one(t: str) -> float | None:
            if not self._is_equity_symbol(t):
                return None
            try:
                resp = await self.http.get(
                    f"/v2/aggs/ticker/{t.upper()}/prev", params={"adjusted": "true"}
                )
                if resp.status_code != 200:
                    return None
                js = resp.json() or {}
                results = js.get("results") or []
                return (
                    float(results[0].get("o"))
                    if results and results[0].get("o") is not None
                    else None
                )
            except Exception:
                return None

        # Run sequentially; small batch
        for t in tickers:
            try:
                # run small Awaitable immediately inside sync method via loop
                out[t] = (
                    asyncio.get_event_loop().run_until_complete(_one(t))
                    if asyncio.get_event_loop().is_running() is False
                    else None
                )
            except RuntimeError:
                # If already in an event loop, fallback to None for sync call
                out[t] = None
        return out


# ---------- ALPACA (optional) ----------
class AlpacaProvider(MarketProvider):
    """Alpaca Market Data (v2) daily bars (equities only)."""

    name = "alpaca"
    supports_intraday = True

    def __init__(self):
        # Accept multiple env names for keys
        self.key = os.getenv("ALPACA_KEY_ID") or os.getenv("ALPACA_API_KEY")
        self.secret = os.getenv("ALPACA_SECRET_KEY") or os.getenv("ALPACA_API_SECRET")
        self.base = (
            os.getenv("ALPACA_DATA_BASE_URL")
            or os.getenv("ALPACA_DATA_BASE")
            or "https://data.alpaca.markets"
        ).rstrip("/")

        # Shared AsyncClient with auth headers; soft-fail if httpx not present
        try:
            import httpx  # type: ignore

            headers = {
                "Accept": "application/json",
            }
            if self.key and self.secret:
                headers.update(
                    {
                        "APCA-API-KEY-ID": self.key,
                        "APCA-API-SECRET-KEY": self.secret,
                    }
                )
            self.http = httpx.AsyncClient(
                base_url=self.base, timeout=TIMEOUTS["http_client_default"], headers=headers
            )
        except Exception:
            self.http = None
        self._last_status: Any = None

    async def fetch_ohlc(
        self, tickers: list[str], period_days: int = 60, adjusted: bool = True
    ) -> dict[str, pd.DataFrame]:
        import pandas as pd

        async def _fetch_one(t: str) -> pd.DataFrame:
            if not self._is_equity_symbol(t) or not self.http or not (self.key and self.secret):
                self._last_status = "missing_key" if not (self.key and self.secret) else "no_client"
                return self._empty_frame()

            # date range
            d = max(30, int(period_days or 60))
            end = dt.date.today().isoformat()
            start = (dt.date.today() - dt.timedelta(days=d)).isoformat()
            path = "/v2/stocks/bars"
            params = {
                "symbols": t.upper(),
                "timeframe": "1Day",
                "start": f"{start}T00:00:00Z",
                "end": f"{end}T23:59:59Z",
                "adjustment": "all" if adjusted else "raw",
                "limit": 10000,
            }

            try:
                resp = await self.http.get(path, params=params)
                if resp is None:
                    self._last_status = "no_response"
                    return self._empty_frame()
                if resp.status_code != 200:
                    self._last_status = resp.status_code  # 401/403/429/etc.
                    return self._empty_frame()
                data = resp.json()
            except Exception:
                self._last_status = "error"
                return self._empty_frame()

            # Response can be {"bars": {"AAPL": [{o,h,l,c,v,t}, ...]}}
            rows = (data.get("bars") or {}).get(t.upper()) or []
            if not rows:
                self._last_status = "nodata"
                return self._empty_frame()

            try:
                df = pd.DataFrame(
                    {
                        "Date": [
                            pd.to_datetime(r.get("t"), utc=True).tz_convert(None) for r in rows
                        ],
                        "Open": [r.get("o") for r in rows],
                        "High": [r.get("h") for r in rows],
                        "Low": [r.get("l") for r in rows],
                        "Close": [r.get("c") for r in rows],
                        "Adj Close": [r.get("c") for r in rows],  # adjusted per 'adjustment'
                        "Volume": [r.get("v") for r in rows],
                    }
                )
                df = df.sort_values("Date").reset_index(drop=True)
                self._last_status = "ok" if not df.empty else "nodata"
                return df
            except Exception:
                self._last_status = "error"
                return self._empty_frame()

        out: dict[str, pd.DataFrame] = {}
        for t in tickers:
            out[t] = await _fetch_one(t)
        return out

    def today_open_prices(self, tickers: list[str]) -> dict[str, float | None]:
        out: dict[str, float | None] = {}
        # If missing auth or client, do not crash; return None values
        if not self.http or not (self.key and self.secret):
            return dict.fromkeys(tickers)

        async def _one(sym: str) -> float | None:
            if not self._is_equity_symbol(sym):
                return None
            try:
                # Use snapshots batch endpoint for efficiency
                path = "/v2/stocks/snapshots"
                params = {"symbols": sym.upper()}
                resp = await self.http.get(path, params=params)
                if resp.status_code != 200:
                    return None
                js = resp.json() or {}
                snaps = js.get("snapshots") or {}
                sb = (snaps.get(sym.upper()) or {}).get("dailyBar") or {}
                return float(sb.get("o")) if sb.get("o") is not None else None
            except Exception:
                return None

        for t in tickers:
            try:
                out[t] = (
                    asyncio.get_event_loop().run_until_complete(_one(t))
                    if asyncio.get_event_loop().is_running() is False
                    else None
                )
            except RuntimeError:
                out[t] = None
        return out


# ---------------- Provider factory (legacy single) ----------------


def get_provider() -> MarketProvider:
    """Compatibility: return a single provider by DATA_PROVIDER (legacy)."""
    selected = DATA_PROVIDER
    try:
        if selected == "alpaca":
            return AlpacaProvider()
        if selected == "polygon":
            return PolygonProvider()
        return YFinanceProvider()
    except Exception as e:
        import logging

        logging.getLogger("ziggy").warning(
            "[provider] get_provider fallback to yfinance due to: %r", e
        )
        try:
            return YFinanceProvider()
        except Exception:
            # Last resort: a do-nothing provider
            class _Null(MarketProvider):
                name = "null"
                supports_intraday = False

                async def fetch_ohlc(
                    self, tickers: list[str], period_days: int = 60, adjusted: bool = True
                ):
                    return {t: self._empty_frame() for t in tickers}

                def today_open_prices(self, tickers: list[str]):
                    return dict.fromkeys(tickers)

            return _Null()


# ============================================================================
# Note: Save path — backend/app/services/market_providers.py
# ============================================================================
