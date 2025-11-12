# backend/app/services/macro.py
from __future__ import annotations

import asyncio
import os
import time
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from app.core.config.time_tuning import TIMEOUTS


# ──────────────────────────────────────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────────────────────────────────────
FRED_API_BASE = "https://api.stlouisfed.org/fred"
FRED_API_KEY = os.getenv("FRED_API_KEY", "").strip()
# Reuse SEC_USER_AGENT/USER_AGENT if present to be descriptive; else fallback:
USER_AGENT = (
    os.getenv("SEC_USER_AGENT")
    or os.getenv("USER_AGENT")
    or "ZiggyMacro/1.0 (contact: devnull@example.com)"
)

# In-memory TTL caches
_TEXT_CACHE: dict[str, tuple[float, str]] = {}
_JSON_CACHE: dict[str, tuple[float, Any]] = {}

# Common series ids (stable FRED IDs)
SERIES = {
    "CPI": "CPIAUCSL",  # CPI (SA, 1982-84=100)
    "CORE_CPI": "CPILFESL",  # CPI less Food & Energy (SA)
    "PCE": "PCEPI",  # PCE Price Index
    "CORE_PCE": "PCEPILFE",  # Core PCE
    "UNRATE": "UNRATE",  # Unemployment rate (%)
    "FEDFUNDS": "FEDFUNDS",  # Effective Fed Funds Rate (%)
    "DGS10": "DGS10",  # 10Y Treasury (%)
    "DGS2": "DGS2",  # 2Y Treasury (%)
    "REAL_GDP": "GDPC1",  # Real GDP (chained 2017 $, SAAR)
}

__all__ = [
    "SERIES",
    "get_macro_dashboard",
    "get_macro_snapshot",
    "get_series",
    "get_series_latest",
]

# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────


def get_series(
    series_id: str,
    *,
    observation_start: str | None = None,
    observation_end: str | None = None,
    frequency: str | None = None,  # e.g., "m", "q"
    units: str | None = None,  # e.g., "pc1" (YoY), "pch" (MoM), "lin"
    aggregation_method: str | None = None,  # e.g., "avg", "eop"
    limit: int | None = None,  # local post-trim after fetch
    ttl: int = 300,
) -> dict[str, Any]:
    """
    Fetch a FRED series as normalized timeseries:
    {
      "id": "CPIAUCSL",
      "title": "Consumer Price Index ...",
      "units": "Percent Change from Year Ago" (resolved by FRED),
      "frequency": "Monthly",
      "last_updated": "2025-01-12T19:00:00Z",
      "points": [{"date":"YYYY-MM-DD","value": <float|null>}, ...]
    }
    """
    if not FRED_API_KEY:
        return _error("Missing FRED_API_KEY")

    # 1) series metadata (title, baseline units, freq)
    meta = _fred_json(
        "/series",
        {"series_id": series_id},
        ttl=max(600, ttl),
    )
    if not meta or "seriess" not in meta or not meta["seriess"]:
        return _error(f"Series not found: {series_id}")
    s_meta = meta["seriess"][0]
    title = s_meta.get("title")
    last_updated = _to_iso_utc(s_meta.get("last_updated"))
    freq_label = s_meta.get("frequency")
    units_label = s_meta.get("units")

    # 2) observations
    params = {
        "series_id": series_id,
        "file_type": "json",
        "sort_order": "asc",
    }
    if observation_start:
        params["observation_start"] = observation_start
    if observation_end:
        params["observation_end"] = observation_end
    if frequency:
        params["frequency"] = frequency
    if units:
        params["units"] = units
    if aggregation_method:
        params["aggregation_method"] = aggregation_method

    obs = _fred_json("/series/observations", params, ttl=ttl)
    rows = obs.get("observations", []) if obs else []

    points: list[dict[str, Any]] = []
    for r in rows:
        d = r.get("date")
        v = r.get("value", None)
        if v in (None, ".", ""):
            points.append({"date": d, "value": None})
        else:
            try:
                points.append({"date": d, "value": float(v)})
            except Exception:
                points.append({"date": d, "value": None})

    if limit and limit > 0 and len(points) > limit:
        points = points[-limit:]

    return {
        "id": series_id,
        "title": title,
        "units": obs.get("units_short") or obs.get("units") or units_label,
        "frequency": obs.get("frequency_short") or freq_label,
        "last_updated": last_updated,
        "points": points,
    }


def get_series_latest(
    series_id: str,
    *,
    frequency: str | None = None,
    units: str | None = None,
    aggregation_method: str | None = None,
    ttl: int = 300,
) -> dict[str, Any]:
    """
    Return latest non-null point:
    {
      "id": "...",
      "date": "YYYY-MM-DD",
      "value": float|null
    }
    """
    data = get_series(
        series_id,
        frequency=frequency,
        units=units,
        aggregation_method=aggregation_method,
        ttl=ttl,
    )
    pts = list(data.get("points") or [])
    for r in reversed(pts):
        if r["value"] is not None:
            return {"id": series_id, "date": r["date"], "value": r["value"]}
    return {"id": series_id, "date": None, "value": None}


def get_macro_snapshot(ttl: int = 600) -> dict[str, Any]:
    """
    Latest key macro datapoints:
    {
      "asof": <epoch>,
      "latest": {
        "inflation": {"cpi_yoy": 3.1, "core_cpi_yoy": 3.7, "pce_yoy": 2.6, "core_pce_yoy": 2.8},
        "labor": {"unemployment_rate": 3.7},
        "rates": {"fed_funds": 5.33, "ust2y": 4.20, "ust10y": 4.05, "slope_2s10s": -0.15},
        "growth": {"real_gdp_yoy": 2.4}
      }
    }
    """
    if not FRED_API_KEY:
        return _error("Missing FRED_API_KEY")

    # Inflation YoY using units=pc1 (Percent change from year ago)
    cpi_yoy = get_series_latest(SERIES["CPI"], units="pc1", frequency="m", ttl=ttl)
    core_cpi_yoy = get_series_latest(SERIES["CORE_CPI"], units="pc1", frequency="m", ttl=ttl)
    pce_yoy = get_series_latest(SERIES["PCE"], units="pc1", frequency="m", ttl=ttl)
    core_pce_yoy = get_series_latest(SERIES["CORE_PCE"], units="pc1", frequency="m", ttl=ttl)

    # Labor
    unrate = get_series_latest(SERIES["UNRATE"], frequency="m", ttl=ttl)

    # Rates (daily → monthly avg for consistency)
    fedfunds = get_series_latest(SERIES["FEDFUNDS"], frequency="m", ttl=ttl)
    dgs2 = get_series_latest(SERIES["DGS2"], frequency="m", aggregation_method="avg", ttl=ttl)
    dgs10 = get_series_latest(SERIES["DGS10"], frequency="m", aggregation_method="avg", ttl=ttl)

    slope = None
    if dgs2["value"] is not None and dgs10["value"] is not None:
        slope = dgs10["value"] - dgs2["value"]

    # Growth (Real GDP YoY)
    gdp_yoy = get_series_latest(SERIES["REAL_GDP"], frequency="q", units="pc1", ttl=ttl)

    return {
        "asof": time.time(),
        "latest": {
            "inflation": {
                "cpi_yoy": cpi_yoy["value"],
                "core_cpi_yoy": core_cpi_yoy["value"],
                "pce_yoy": pce_yoy["value"],
                "core_pce_yoy": core_pce_yoy["value"],
                "asof": cpi_yoy["date"]
                or core_cpi_yoy["date"]
                or pce_yoy["date"]
                or core_pce_yoy["date"],
            },
            "labor": {
                "unemployment_rate": unrate["value"],
                "asof": unrate["date"],
            },
            "rates": {
                "fed_funds": fedfunds["value"],
                "ust2y": dgs2["value"],
                "ust10y": dgs10["value"],
                "slope_2s10s": slope,
                "asof": dgs10["date"] or dgs2["date"] or fedfunds["date"],
            },
            "growth": {
                "real_gdp_yoy": gdp_yoy["value"],
                "asof": gdp_yoy["date"],
            },
        },
    }


def get_macro_dashboard(
    *,
    months: int = 120,
    months_rates: int = 120,
    quarters: int = 40,
    ttl: int = 600,
) -> dict[str, Any]:
    """
    Curated chart-ready macro panel:
    {
      "asof": <epoch>,
      "series": {
        "CPI_yoy": [{"date","value"}, ...],
        "CORE_CPI_yoy": [...],
        "UNRATE": [...],
        "FEDFUNDS": [...],
        "DGS2_m": [...],
        "DGS10_m": [...],
        "REAL_GDP_yoy": [...],
        "SPREAD_2s10s": [...],   # computed from DGS10_m - DGS2_m
      }
    }
    """
    if not FRED_API_KEY:
        return _error("Missing FRED_API_KEY")

    cpi = get_series(SERIES["CPI"], units="pc1", frequency="m", limit=months, ttl=ttl)
    core_cpi = get_series(SERIES["CORE_CPI"], units="pc1", frequency="m", limit=months, ttl=ttl)
    unrate = get_series(SERIES["UNRATE"], frequency="m", limit=months, ttl=ttl)
    fedf = get_series(SERIES["FEDFUNDS"], frequency="m", limit=months_rates, ttl=ttl)
    d2 = get_series(
        SERIES["DGS2"], frequency="m", aggregation_method="avg", limit=months_rates, ttl=ttl
    )
    d10 = get_series(
        SERIES["DGS10"], frequency="m", aggregation_method="avg", limit=months_rates, ttl=ttl
    )
    gdp = get_series(SERIES["REAL_GDP"], frequency="q", units="pc1", limit=quarters, ttl=ttl)

    # Compute 2s10s spread aligned by date
    spread = _diff_series(d10.get("points", []), d2.get("points", []))

    return {
        "asof": time.time(),
        "series": {
            "CPI_yoy": cpi.get("points", []),
            "CORE_CPI_yoy": core_cpi.get("points", []),
            "UNRATE": unrate.get("points", []),
            "FEDFUNDS": fedf.get("points", []),
            "DGS2_m": d2.get("points", []),
            "DGS10_m": d10.get("points", []),
            "REAL_GDP_yoy": gdp.get("points", []),
            "SPREAD_2s10s": spread,
        },
    }


# ──────────────────────────────────────────────────────────────────────────────
# Internals
# ──────────────────────────────────────────────────────────────────────────────


def _fred_json(path: str, params: dict[str, Any], *, ttl: int) -> dict[str, Any]:
    """
    GET FRED JSON with TTL cache.
    """
    params = {k: v for k, v in (params or {}).items() if v is not None and v != ""}
    params["api_key"] = FRED_API_KEY
    params["file_type"] = "json"

    url = f"{FRED_API_BASE}{path}"
    key = _cache_key(url, params)
    now = time.time()
    cached = _JSON_CACHE.get(key)
    if cached and (now - cached[0]) < max(10, ttl):
        return cached[1]

    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    with httpx.Client(timeout=TIMEOUTS["http_client_long"], headers=headers) as c:
        r = c.get(url, params=params)
        r.raise_for_status()
        data = r.json()

    _JSON_CACHE[key] = (now, data)
    return data


def _cache_key(url: str, params: dict[str, Any]) -> str:
    # deterministic ordering
    items = "&".join(f"{k}={params[k]}" for k in sorted(params.keys()))
    return f"{url}?{items}"


def _to_iso_utc(s: str | None) -> str | None:
    if not s:
        return None
    try:
        # FRED returns "YYYY-MM-DD HH:MM:SS-05"
        s = s.replace(" ", "T")
        if s.endswith("Z"):
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        elif "+" in s or "-" in s[10:]:
            dt = datetime.fromisoformat(s)
        else:
            dt = datetime.fromisoformat(s + "+00:00")
        dt = dt.astimezone(UTC)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return s


def _diff_series(a: list[dict[str, Any]], b: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Align by date and compute a.value - b.value (None if any missing).
    """
    by_b = {row["date"]: row.get("value") for row in b if "date" in row}
    out: list[dict[str, Any]] = []
    for row in a:
        d = row.get("date")
        va = row.get("value")
        vb = by_b.get(d)
        out.append({"date": d, "value": (va - vb) if (va is not None and vb is not None) else None})
    return out


def _error(msg: str) -> dict[str, Any]:
    return {"error": msg, "asof": time.time()}


# ──────────────────────────────────────────────────────────────────────────────
# Enhanced Market Calendar and Economic Data
# ──────────────────────────────────────────────────────────────────────────────


class MarketCalendar:
    """Real market calendar and economic events data."""

    def __init__(self):
        self.base_url = "https://financialmodelingprep.com/api/v3"
        self.api_key = os.getenv("FMP_API_KEY", "demo")  # Financial Modeling Prep API
        self.fred_api_key = os.getenv("FRED_API_KEY")  # Federal Reserve Economic Data
        self.cache_duration = timedelta(hours=1)
        self._cache = {}

    async def get_market_holidays(self, year: int | None = None) -> list[dict[str, Any]]:
        """Get market holidays for specified year."""
        if year is None:
            year = datetime.now().year

        cache_key = f"holidays_{year}"
        if self._is_cached(cache_key):
            return self._cache[cache_key]["data"]

        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/market-hours"
                params = {"apikey": self.api_key, "year": year}

                response = await client.get(
                    url, params=params, timeout=TIMEOUTS["http_client_medium"]
                )
                response.raise_for_status()
                data = response.json()

                # Process holidays
                holidays = []
                for item in data:
                    if item.get("isOpen") is False:
                        holidays.append(
                            {
                                "date": item.get("date"),
                                "name": item.get("name", "Market Holiday"),
                                "exchange": item.get("exchange", "NYSE"),
                                "type": "holiday",
                            }
                        )

                self._cache[cache_key] = {"data": holidays, "timestamp": datetime.now()}
                return holidays

        except Exception as e:
            import logging

            logging.error(f"Error fetching market holidays: {e}")
            # Return fallback holidays
            return self._get_fallback_holidays(year)

    async def get_earnings_calendar(
        self, start_date: str | None = None, end_date: str | None = None
    ) -> list[dict[str, Any]]:
        """Get earnings calendar for date range."""
        if start_date is None:
            start_date = datetime.now().strftime("%Y-%m-%d")
        if end_date is None:
            end_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

        cache_key = f"earnings_{start_date}_{end_date}"
        if self._is_cached(cache_key):
            return self._cache[cache_key]["data"]

        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/earning_calendar"
                params = {"apikey": self.api_key, "from": start_date, "to": end_date}

                response = await client.get(
                    url, params=params, timeout=TIMEOUTS["http_client_medium"]
                )
                response.raise_for_status()
                data = response.json()

                # Process earnings data
                earnings = []
                for item in data[:50]:  # Limit to 50 results
                    earnings.append(
                        {
                            "symbol": item.get("symbol"),
                            "company": item.get("name"),
                            "date": item.get("date"),
                            "time": item.get(
                                "time", "amc"
                            ),  # bmo = before market open, amc = after market close
                            "eps_estimate": item.get("epsEstimate"),
                            "eps_actual": item.get("eps"),
                            "revenue_estimate": item.get("revenueEstimate"),
                            "revenue_actual": item.get("revenue"),
                            "type": "earnings",
                        }
                    )

                self._cache[cache_key] = {"data": earnings, "timestamp": datetime.now()}
                return earnings

        except Exception as e:
            import logging

            logging.error(f"Error fetching earnings calendar: {e}")
            return []

    async def get_economic_calendar(
        self, start_date: str | None = None, end_date: str | None = None
    ) -> list[dict[str, Any]]:
        """Get economic events calendar."""
        if start_date is None:
            start_date = datetime.now().strftime("%Y-%m-%d")
        if end_date is None:
            end_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

        cache_key = f"economic_{start_date}_{end_date}"
        if self._is_cached(cache_key):
            return self._cache[cache_key]["data"]

        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/economic_calendar"
                params = {"apikey": self.api_key, "from": start_date, "to": end_date}

                response = await client.get(
                    url, params=params, timeout=TIMEOUTS["http_client_medium"]
                )
                response.raise_for_status()
                data = response.json()

                # Process economic events
                events = []
                for item in data[:30]:  # Limit to 30 results
                    events.append(
                        {
                            "date": item.get("date"),
                            "time": item.get("time"),
                            "country": item.get("country"),
                            "event": item.get("event"),
                            "currency": item.get("currency"),
                            "previous": item.get("previous"),
                            "estimate": item.get("estimate"),
                            "actual": item.get("actual"),
                            "impact": item.get("impact", "Medium"),  # High/Medium/Low
                            "type": "economic",
                        }
                    )

                self._cache[cache_key] = {"data": events, "timestamp": datetime.now()}
                return events

        except Exception as e:
            import logging

            logging.error(f"Error fetching economic calendar: {e}")
            return []

    async def get_market_schedule(self, date: str | None = None) -> dict[str, Any]:
        """Get market open/close times for specific date."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        cache_key = f"schedule_{date}"
        if self._is_cached(cache_key):
            return self._cache[cache_key]["data"]

        try:
            # For now, return standard market hours
            # This could be enhanced with API call for exact times including early close days
            schedule = {
                "date": date,
                "market_open": "09:30",
                "market_close": "16:00",
                "pre_market_open": "04:00",
                "after_hours_close": "20:00",
                "timezone": "US/Eastern",
                "is_open": self._is_market_day(date),
                "is_early_close": False,  # Could enhance with holiday API
            }

            self._cache[cache_key] = {"data": schedule, "timestamp": datetime.now()}
            return schedule

        except Exception as e:
            import logging

            logging.error(f"Error fetching market schedule: {e}")
            return {
                "date": date,
                "market_open": "09:30",
                "market_close": "16:00",
                "is_open": True,
                "error": str(e),
            }

    def _is_cached(self, key: str) -> bool:
        """Check if data is cached and still valid."""
        if key not in self._cache:
            return False

        cache_time = self._cache[key]["timestamp"]
        return datetime.now() - cache_time < self.cache_duration

    def _is_market_day(self, date_str: str) -> bool:
        """Simple check if date is a weekday (not weekend)."""
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            return date_obj.weekday() < 5  # Monday=0, Friday=4
        except Exception:
            return True

    def _get_fallback_holidays(self, year: int) -> list[dict[str, Any]]:
        """Fallback holidays when API fails."""
        holidays = [
            {"date": f"{year}-01-01", "name": "New Year's Day", "type": "holiday"},
            {"date": f"{year}-01-15", "name": "Martin Luther King Jr. Day", "type": "holiday"},
            {"date": f"{year}-02-19", "name": "Presidents Day", "type": "holiday"},
            {"date": f"{year}-04-07", "name": "Good Friday", "type": "holiday"},
            {"date": f"{year}-05-27", "name": "Memorial Day", "type": "holiday"},
            {"date": f"{year}-06-19", "name": "Juneteenth", "type": "holiday"},
            {"date": f"{year}-07-04", "name": "Independence Day", "type": "holiday"},
            {"date": f"{year}-09-02", "name": "Labor Day", "type": "holiday"},
            {"date": f"{year}-11-28", "name": "Thanksgiving", "type": "holiday"},
            {"date": f"{year}-12-25", "name": "Christmas Day", "type": "holiday"},
        ]
        return holidays


class FredEconomicData:
    """Federal Reserve Economic Data provider with enhanced functionality."""

    def __init__(self):
        self.api_key = FRED_API_KEY
        self.base_url = "https://api.stlouisfed.org/fred/series"
        self.cache_duration = timedelta(hours=2)
        self._cache = {}

    async def get_series_data(self, series_id: str, limit: int = 100) -> list[dict[str, Any]]:
        """Get economic data series from FRED."""
        if not self.api_key:
            import logging

            logging.warning("FRED API key not configured")
            return []

        cache_key = f"fred_{series_id}_{limit}"
        if self._is_cached(cache_key):
            return self._cache[cache_key]["data"]

        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/observations"
                params = {
                    "series_id": series_id,
                    "api_key": self.api_key,
                    "file_type": "json",
                    "limit": limit,
                    "sort_order": "desc",
                }

                response = await client.get(
                    url, params=params, timeout=TIMEOUTS["http_client_default"]
                )
                response.raise_for_status()
                data = response.json()

                observations = []
                for obs in data.get("observations", []):
                    if obs.get("value") not in [".", None]:
                        observations.append(
                            {
                                "date": obs.get("date"),
                                "value": float(obs.get("value")),
                                "series_id": series_id,
                            }
                        )

                self._cache[cache_key] = {"data": observations, "timestamp": datetime.now()}
                return observations

        except Exception as e:
            import logging

            logging.error(f"Error fetching FRED data for {series_id}: {e}")
            return []

    async def get_key_indicators(self) -> dict[str, list[dict[str, Any]]]:
        """Get key economic indicators."""
        indicators = {
            "unemployment": "UNRATE",  # Unemployment Rate
            "inflation": "CPIAUCSL",  # CPI
            "gdp": "GDP",  # Gross Domestic Product
            "fed_rate": "FEDFUNDS",  # Federal Funds Rate
            "10y_treasury": "GS10",  # 10-Year Treasury Rate
            "sp500": "SP500",  # S&P 500
        }

        results = {}
        for name, series_id in indicators.items():
            data = await self.get_series_data(series_id, 12)  # Last 12 observations
            results[name] = data

        return results

    def _is_cached(self, key: str) -> bool:
        """Check if data is cached and still valid."""
        if key not in self._cache:
            return False

        cache_time = self._cache[key]["timestamp"]
        return datetime.now() - cache_time < self.cache_duration


# Global instances
market_calendar = MarketCalendar()
fred_data = FredEconomicData()


async def get_market_calendar_data() -> dict[str, Any]:
    """Get comprehensive market calendar data."""
    try:
        # Get data in parallel
        tasks = [
            market_calendar.get_market_holidays(),
            market_calendar.get_earnings_calendar(),
            market_calendar.get_economic_calendar(),
            market_calendar.get_market_schedule(),
            fred_data.get_key_indicators(),
        ]

        holidays, earnings, economic, schedule, indicators = await asyncio.gather(*tasks)

        return {
            "holidays": holidays,
            "earnings": earnings,
            "economic_events": economic,
            "market_schedule": schedule,
            "economic_indicators": indicators,
            "status": "success",
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        import logging

        logging.error(f"Error getting market calendar data: {e}")
        return {"error": str(e), "status": "error", "timestamp": datetime.now().isoformat()}
