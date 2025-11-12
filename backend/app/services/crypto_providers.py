from __future__ import annotations

import datetime as dt
import os

import httpx
import pandas as pd

from app.core.config.time_tuning import TIMEOUTS


NORM_COLS = ["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]


def to_polygon_crypto(sym: str) -> str:
    # "BTC-USD" -> "X:BTCUSD"
    s = sym.upper().replace("/", "-")
    if "-" in s:
        base, quote = s.split("-", 1)
        return f"X:{base}{quote}"
    return f"X:{s.replace('USD', 'USD')}"


class CryptoProvider:
    name = "base"

    async def quotes(self, symbols: list[str]) -> dict[str, dict | None]:
        raise NotImplementedError

    async def bars(
        self, symbols: list[str], interval: str = "1m", minutes: int = 240
    ) -> dict[str, pd.DataFrame]:
        raise NotImplementedError


class CryptoPolygon(CryptoProvider):
    name = "polygon"

    def __init__(self):
        self.key = (os.getenv("POLYGON_API_KEY") or "").strip()
        self.base = (os.getenv("POLYGON_BASE_URL") or "https://api.polygon.io").rstrip("/")
        self.http = httpx.AsyncClient(timeout=TIMEOUTS["http_client_default"])

    async def quotes(self, symbols: list[str]) -> dict[str, dict | None]:
        out: dict[str, dict | None] = {}
        for s in symbols:
            ps = to_polygon_crypto(s)
            try:
                r = await self.http.get(
                    f"{self.base}/v2/snapshot/locale/global/markets/crypto/tickers/{ps}",
                    params={"apiKey": self.key},
                )
                if r.status_code == 404:
                    out[s] = None
                    continue
                r.raise_for_status()
                j = r.json().get("ticker", {})
                last = (j.get("lastTrade") or {}).get("p")
                day = j.get("day") or {}
                change = day.get("change")  # absolute
                openp = day.get("o")
                pct = None
                if last and openp:
                    try:
                        pct = (last / openp - 1) * 100
                    except:
                        pct = None
                out[s] = {"price": last, "change_pct_24h": pct, "source": "polygon"}
            except Exception:
                out[s] = None
        return out

    async def bars(self, symbols: list[str], interval: str = "1m", minutes: int = 240):
        gran = {"1m": ("1", "minute"), "5m": ("5", "minute")}.get(interval, ("1", "minute"))
        n = minutes
        end = dt.datetime.utcnow()
        start = end - dt.timedelta(minutes=n + 5)
        out: dict[str, pd.DataFrame] = {}
        for s in symbols:
            ps = to_polygon_crypto(s)
            try:
                r = await self.http.get(
                    f"{self.base}/v2/aggs/ticker/{ps}/range/{gran[0]}/{gran[1]}/{start.date()}/{end.date()}",
                    params={"adjusted": "true", "apiKey": self.key},
                )
                r.raise_for_status()
                rows = []
                for bar in r.json().get("results") or []:
                    ts = dt.datetime.utcfromtimestamp(bar["t"] / 1000)
                    if ts < start:
                        continue
                    rows.append(
                        {
                            "Date": ts,
                            "Open": bar["o"],
                            "High": bar["h"],
                            "Low": bar["l"],
                            "Close": bar["c"],
                            "Adj Close": bar["c"],
                            "Volume": bar["v"],
                        }
                    )
                df = (
                    pd.DataFrame(rows, columns=NORM_COLS).sort_values("Date").reset_index(drop=True)
                )
                out[s] = df
            except Exception:
                out[s] = pd.DataFrame(columns=NORM_COLS)
        return out


class CryptoYF(CryptoProvider):
    name = "yfinance"

    def __init__(self):
        import yfinance as yf

        self.yf = yf

    async def quotes(self, symbols: list[str]) -> dict[str, dict | None]:
        out = {}
        for s in symbols:
            try:
                t = self.yf.Ticker(s)
                info = t.fast_info
                price = float(info.get("last_price"))
                prev = float(info.get("previous_close") or price)
                pct = (price / prev - 1) * 100 if prev else None
                out[s] = {"price": price, "change_pct_24h": pct, "source": "yfinance"}
            except Exception:
                out[s] = None
        return out

    async def bars(self, symbols: list[str], interval: str = "1m", minutes: int = 240):
        out: dict[str, pd.DataFrame] = {}
        period = "1d" if minutes <= 1440 else "5d"
        for s in symbols:
            try:
                df = self.yf.download(
                    s,
                    period=period,
                    interval=interval,
                    auto_adjust=False,
                    progress=False,
                    threads=False,
                )
                if df.empty:
                    out[s] = pd.DataFrame(columns=NORM_COLS)
                    continue
                df = df.reset_index().rename(columns={"Datetime": "Date"})
                df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)
                df["Adj Close"] = df.get("Adj Close", df["Close"])
                df = df[["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]]
                cutoff = dt.datetime.utcnow() - dt.timedelta(minutes=minutes + 5)
                df = df[df["Date"] >= cutoff].sort_values("Date").reset_index(drop=True)
                out[s] = df
            except Exception:
                out[s] = pd.DataFrame(columns=NORM_COLS)
        return out
