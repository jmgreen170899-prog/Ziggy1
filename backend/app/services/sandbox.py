from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from app.services.market_providers import MarketProvider


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "data" / "fixtures"


def _load_json(name: str) -> Any:
    try:
        p = FIXTURES_DIR / name
        if not p.exists():
            return None
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


class SandboxPriceProvider(MarketProvider):
    """Price/OHLC provider that reads from fixtures to enable fully offline dev."""

    name = "sandbox"
    supports_intraday = False

    def __init__(self) -> None:
        self._ohlc = _load_json("ohlc.json") or {}

    async def fetch_ohlc(
        self, tickers: list[str], period_days: int = 60, adjusted: bool = True
    ) -> dict[str, pd.DataFrame]:
        out: dict[str, pd.DataFrame] = {}
        for t in tickers:
            key = (t or "").strip().upper()
            rows = []
            try:
                rows = list(self._ohlc.get(key) or [])
            except Exception:
                rows = []

            if not rows:
                out[key] = self._empty_frame()
                continue

            # Ensure normalized columns
            try:
                df = pd.DataFrame(rows)
                # Allow either 'Adj Close' or 'AdjClose' in fixtures
                if "AdjClose" in df.columns and "Adj Close" not in df.columns:
                    df = df.rename(columns={"AdjClose": "Adj Close"})
                # Coerce Date to datetime
                if "Date" in df.columns:
                    df["Date"] = pd.to_datetime(
                        df["Date"], utc=True, errors="coerce"
                    ).dt.tz_convert(None)
                    df = df.sort_values("Date").reset_index(drop=True)
                else:
                    # Allow index-based dates if not provided
                    df.insert(
                        0,
                        "Date",
                        pd.to_datetime(df.index, utc=True, errors="coerce").tz_convert(
                            None
                        ),
                    )
                # Ensure all required columns exist
                for col in ["Open", "High", "Low", "Close", "Volume"]:
                    if col not in df.columns:
                        df[col] = None
                if "Adj Close" not in df.columns:
                    df["Adj Close"] = df.get("Close")
                # Keep only required columns in normalized order
                df = df[["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]]
                out[key] = df
            except Exception:
                out[key] = self._empty_frame()
        return out

    def today_open_prices(self, tickers: list[str]) -> dict[str, float | None]:
        out: dict[str, float | None] = {}
        today = datetime.now(UTC).date()
        for t in tickers:
            key = (t or "").strip().upper()
            rows = list(self._ohlc.get(key) or [])
            if not rows:
                out[key] = None
                continue
            try:
                df = pd.DataFrame(rows)
                if "Date" in df.columns:
                    df["Date"] = pd.to_datetime(
                        df["Date"], utc=True, errors="coerce"
                    ).dt.tz_convert(None)
                    # Pick today's date if present; else last row
                    match = df.loc[df["Date"].dt.date == today]
                    row = match.iloc[-1] if not match.empty else df.iloc[-1]
                    val = row.get("Open") if isinstance(row, pd.Series) else None
                else:
                    val = None
                out[key] = float(val) if val is not None else None
            except Exception:
                out[key] = None
        return out


class SandboxNewsProvider:
    """News provider from fixtures."""

    name = "sandbox-news"

    def __init__(self) -> None:
        self._items: list[dict[str, Any]] = list(_load_json("news.json") or [])
        self._sources: list[dict[str, str]] = list(
            _load_json("news_sources.json") or []
        )

    def list_sources(self) -> list[dict[str, str]]:
        if self._sources:
            return self._sources
        # Derive from news items
        seen = {}
        out: list[dict[str, str]] = []
        for it in self._items:
            src = (it.get("source") or "Fixture News").strip()
            if src not in seen:
                seen[src] = True
                out.append(
                    {
                        "id": src.lower().replace(" ", "-"),
                        "label": src,
                        "url": it.get("url") or "#",
                    }
                )
        return out

    def get_headlines(
        self,
        symbols: list[str] | None = None,
        q: str | None = None,
        sources: list[str] | None = None,
        lookback_days: int = 3,
        limit: int = 30,
    ) -> dict[str, Any]:
        from urllib.parse import urlparse

        symset = {s.strip().upper() for s in (symbols or []) if s and s.strip()}
        srcset = {s.strip().lower() for s in (sources or []) if s and s.strip()}
        qnorm = (q or "").strip().lower()
        cutoff = datetime.now(UTC) - pd.Timedelta(days=max(1, int(lookback_days or 3)))

        def _match(it: dict[str, Any]) -> bool:
            if symset:
                ticks = {
                    s.strip().upper()
                    for s in (it.get("tickers") or it.get("symbols") or [])
                }
                if not (ticks & symset):
                    return False
            if srcset:
                src = str(it.get("source") or "").strip().lower()
                if src not in srcset:
                    return False
            if qnorm:
                blob = f"{it.get('title', '')} {it.get('summary', '')}".lower()
                if qnorm not in blob:
                    return False
            # lookback
            try:
                pub = it.get("published") or it.get("date")
                if pub:
                    dtv = datetime.fromisoformat(str(pub).replace("Z", "+00:00"))
                    if dtv.tzinfo is None:
                        dtv = dtv.replace(tzinfo=UTC)
                    if dtv < cutoff:
                        return False
            except Exception:
                pass
            return True

        items = [it for it in self._items if _match(it)]

        # sort newest first
        def _parse_dt(it: dict[str, Any]):
            try:
                pub = it.get("published") or it.get("date")
                return datetime.fromisoformat(str(pub).replace("Z", "+00:00"))
            except Exception:
                return datetime.now(UTC)

        items.sort(key=_parse_dt, reverse=True)
        items = items[: max(1, int(limit or 30))]

        out = []
        for it in items:
            url = str(it.get("url") or "")
            site = ""
            try:
                u = urlparse(url)
                site = (u.netloc or "").replace("www.", "")
            except Exception:
                pass
            published = it.get("published") or it.get("date")
            if isinstance(published, datetime):
                published = published.astimezone(UTC).isoformat().replace("+00:00", "Z")
            out.append(
                {
                    "id": it.get("id") or f"fx-{abs(hash(url))}",
                    "source": it.get("source") or "Fixture News",
                    "site": site,
                    "title": it.get("title") or "",
                    "url": url,
                    "published": published,
                    "date": published,
                    "summary": it.get("summary") or "",
                    "tickers": it.get("tickers") or it.get("symbols") or [],
                    "symbols": it.get("tickers") or it.get("symbols") or [],
                    "favicon": f"https://{site}/favicon.ico" if site else None,
                }
            )

        return {"asof": datetime.now(UTC).timestamp(), "count": len(out), "items": out}


class SandboxSignalsProvider:
    """Signals provider from fixtures."""

    name = "sandbox-signals"

    def __init__(self) -> None:
        self._signals: dict[str, Any] = _load_json("signals.json") or {}

    def get_ticker_signal(self, ticker: str) -> dict[str, Any] | None:
        key = (ticker or "").strip().upper()
        s = self._signals.get(key)
        if not s:
            return None
        return {
            "ticker": key,
            "signal": s.get("signal") or "NEUTRAL",
            "confidence": float(s.get("confidence", 0.5)),
            "reason": s.get("reason") or "",
            "indicators": s.get("indicators") or {},
        }

    def generate_watchlist_signals(self, tickers: list[str]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for t in tickers:
            sig = self.get_ticker_signal(t)
            if sig:
                out.append(sig)
        return out
