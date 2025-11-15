# isort: skip_file
# =============================================================
# Ziggy — Provider Factory (priority + failover + TTL cache + health scoring + brain integration)
# - _TTLCache with default TTL from CACHE_TTL_SECONDS
# - MultiProvider: per-ticker failover across providers with health scoring
#   * fetch_ohlc(..., return_source=False) -> dict | (dict, sources)
#   * today_open_prices(tickers): uses first intraday-capable provider, with soft fallback
# - get_price_provider(): reads PROVIDERS_PRICES (fallback PRICE_PROVIDER or "yfinance")
# - Crypto: MultiCrypto + get_crypto_provider() reading PROVIDERS_CRYPTO (default "polygon,yfinance")
# - Health scoring: providers ordered by success rate, latency, and contract compliance
# - Vendor stamping: all data includes vendor, version, source_tz, ingest_ts_utc
# - Brain integration: all data flows through Ziggy's brain for learning and recall
# =============================================================
from __future__ import annotations

import asyncio
import logging
import os
import time
from contextlib import suppress
from datetime import UTC
from typing import Any, TYPE_CHECKING
from app.middleware.request_logging import json_log

from app.services.market_providers import (
    AlpacaProvider,
    MarketProvider,
    PolygonProvider,
    YFinanceProvider,
)

try:
    # Optional sandbox providers (fixtures)
    from app.services.sandbox import (
        SandboxNewsProvider,
        SandboxPriceProvider,
        SandboxSignalsProvider,
    )

    _SANDBOX_AVAILABLE = True
except Exception:
    # Make names exist for type-checkers even if import fails
    SandboxNewsProvider = None  # type: ignore[assignment]
    SandboxPriceProvider = None  # type: ignore[assignment]
    SandboxSignalsProvider = None  # type: ignore[assignment]
    _SANDBOX_AVAILABLE = False


# Brain integration (optional)
try:
    from app.services.brain_integration import write_market_data_to_brain
    from app.services.timezone_utils import normalize_event_ts

    BRAIN_INTEGRATION_AVAILABLE = True
except ImportError:
    BRAIN_INTEGRATION_AVAILABLE = False

    async def write_market_data_to_brain(*args, **kwargs) -> str:
        return "brain_unavailable"

    def normalize_event_ts(*args, **kwargs):
        return {"success": False, "error": "timezone_utils unavailable"}


# Environment configuration
PRIMARY_VENDOR = os.getenv("PRIMARY_VENDOR", "polygon")
SECONDARY_VENDOR = os.getenv("SECONDARY_VENDOR", "yfinance")
PROVIDER_QUORUM = os.getenv("PROVIDER_QUORUM", "PRIMARY_THEN_SECONDARY")
PROVIDER_TIMEOUT_MS = int(os.getenv("PROVIDER_TIMEOUT_MS", "1500"))
STAMP_VENDOR_VERSION = bool(int(os.getenv("STAMP_VENDOR_VERSION", "1")))
CACHE_STAMP_INCLUDE = os.getenv(
    "CACHE_STAMP_INCLUDE", "vendor,version,source_tz"
).split(",")

logger = logging.getLogger(__name__)

# Optional typing for pandas without requiring import at runtime in annotations
if TYPE_CHECKING:  # pragma: no cover - typing-only
    from pandas import DataFrame as _PDDataFrame
else:  # fallback for runtime
    _PDDataFrame = Any  # type: ignore


def _create_vendor_stamp(provider_name: str, source_tz: str = "UTC") -> dict[str, Any]:
    """Create vendor stamp for data traceability."""
    if not STAMP_VENDOR_VERSION:
        return {}

    from datetime import datetime

    # Get provider version (basic implementation)
    version_map = {
        "polygon": "1.0.0",
        "yfinance": "0.2.18",
        "alpaca": "1.0.0",
        "yahoo": "0.2.18",
    }

    stamp = {
        "vendor": provider_name,
        "version": version_map.get(provider_name, "1.0.0"),
        "source_tz": source_tz,
        "ingest_ts_utc": datetime.now(UTC).isoformat(),
    }

    # Filter by configured fields
    if CACHE_STAMP_INCLUDE:
        filtered_stamp = {}
        for field in CACHE_STAMP_INCLUDE:
            field = field.strip()
            if field in stamp:
                filtered_stamp[field] = stamp[field]
        return filtered_stamp

    return stamp


def _record_provider_success(
    provider_name: str, latency_ms: int, contract_ok: bool = True
) -> None:
    """Record successful provider event."""
    try:
        from app.services.provider_health import record_provider_event

        record_provider_event(
            provider_name, ok=True, latency_ms=latency_ms, contract_ok=contract_ok
        )
    except ImportError:
        # Health tracking not available
        pass


def _record_provider_failure(
    provider_name: str, latency_ms: int, error: Exception
) -> None:
    """Record failed provider event."""
    try:
        from app.services.provider_health import record_provider_event

        record_provider_event(
            provider_name, ok=False, latency_ms=latency_ms, contract_ok=False
        )
        logger.warning(f"Provider {provider_name} failed: {error}")
    except ImportError:
        # Health tracking not available
        pass


# ------------------------------- TTL Cache -------------------------------


class _TTLCache:
    def __init__(self, ttl_seconds: int | None = None, max_entries: int = 256):
        self.ttl: float = float(
            ttl_seconds
            if ttl_seconds is not None
            else int(os.getenv("CACHE_TTL_SECONDS", "60"))
        )
        self.max = max_entries
        self._store: dict[Any, tuple[float, Any]] = {}

    def _now(self) -> float:
        return time.time()

    def get(self, key: Any) -> Any:
        item = self._store.get(key)
        if not item:
            return None
        exp, val = item
        if exp < self._now():
            # expired
            self._store.pop(key, None)
            return None
        return val

    def set(self, key: Any, value: Any, ttl: float | None = None) -> None:
        # tiny LRU-ish trim
        if len(self._store) >= self.max:
            try:
                # drop oldest by expiry
                oldest_key = min(self._store.items(), key=lambda kv: kv[1][0])[0]
                self._store.pop(oldest_key, None)
            except Exception:
                self._store.clear()
        self._store[key] = (self._now() + (ttl if ttl is not None else self.ttl), value)


_CACHE = _TTLCache()

# Small in-memory map to track providers that recently failed so we don't hammer them.
_PROV_FAIL: dict[str, float] = {}

# Import centralized configuration
from app.core.config.time_tuning import BACKOFFS

# Retry/backoff config (now using centralized config)
_PROV_RETRIES = BACKOFFS["provider_retries"]
_PROV_BACKOFF_BASE = BACKOFFS["provider_base"]
_PROV_FAIL_PENALTY = BACKOFFS["provider_fail_penalty"]


def _key(*parts: Any) -> str:
    def _norm(x: Any) -> Any:
        if isinstance(x, (list, tuple)):
            return tuple(x)
        return x

    return repr(tuple(_norm(p) for p in parts))


# ---------------------------- Provider helpers ---------------------------

_VALID_PROVIDER_NAMES = {"yfinance", "polygon", "alpaca"}


def _provider_by_name(name: str) -> MarketProvider:
    n = (name or "").strip().lower()
    if n == "polygon":
        return PolygonProvider()
    if n == "alpaca":
        return AlpacaProvider()
    return YFinanceProvider()


def _parse_list(s: str | None) -> list[str]:
    if not s:
        return []
    return [x.strip().lower() for x in s.split(",") if x.strip()]


# ------------------------------ MultiProvider ----------------------------


class MultiProvider(MarketProvider):
    """Priority + failover wrapper around concrete providers.

    Use for *equities* price data. Per-ticker failover across providers in order.
    """

    name = "multi"
    supports_intraday = True  # because chain may include intraday-capable providers

    def __init__(self, priority: list[str] | list[MarketProvider]):
        # Build provider objects; ensure yfinance as last-resort
        self.providers: list[MarketProvider] = []
        for p in priority or ["yfinance"]:
            if isinstance(p, MarketProvider):
                self.providers.append(p)
            else:
                self.providers.append(_provider_by_name(p))
        if all(getattr(p, "name", "").lower() != "yfinance" for p in self.providers):
            self.providers.append(YFinanceProvider())

    async def fetch_ohlc(
        self,
        tickers: list[str],
        period_days: int = 60,
        adjusted: bool = True,
        return_source: bool = False,
    ) -> Any:
        """Fetch OHLC across providers with per-ticker failover.

        Returns dict[symbol, DataFrame]. When return_source=True, returns
        a tuple: (frames, sources).
        """
        tickers_norm = [t for t in tickers if t]
        prov_names = tuple(
            getattr(p, "name", p.__class__.__name__).lower() for p in self.providers
        )
        key = (
            "ohlc",
            tuple(sorted(tickers_norm)),
            int(period_days),
            bool(adjusted),
            prov_names,
        )
        cached = _CACHE.get(key)
        if cached is not None:
            return (cached, {}) if return_source else cached

        # Pre-fill with normalized empty frames
        result: dict[str, _PDDataFrame] = {
            t: MarketProvider._empty_frame() for t in tickers_norm
        }
        source: dict[str, str] = {}
        remaining = set(tickers_norm)

        for provider in self.providers:
            if not remaining:
                break
            batch = list(remaining)
            # If this provider recently failed, skip it for a short penalty window
            pname = getattr(provider, "name", provider.__class__.__name__).lower()
            now = time.time()
            skip_until = _PROV_FAIL.get(pname)
            if skip_until and skip_until > now:
                # Treat as empty fetch to continue to next provider
                logging.getLogger("ziggy").info(
                    "[provider] skipping %s until %s due to recent failures",
                    pname,
                    skip_until,
                )
                fetched = {t: MarketProvider._empty_frame() for t in batch}
            else:
                # Try with retries + exponential backoff
                attempt = 0
                fetched = None
                start_time = time.time()

                while attempt <= _PROV_RETRIES:
                    try:
                        # provider.fetch_ohlc may be sync or async; handle both
                        val = provider.fetch_ohlc(batch, period_days=period_days, adjusted=adjusted)  # type: ignore[arg-type]
                        if asyncio.iscoroutine(val):
                            # Enforce a timeout on async providers
                            fetched = await asyncio.wait_for(
                                val,
                                timeout=(
                                    (PROVIDER_TIMEOUT_MS / 1000)
                                    if PROVIDER_TIMEOUT_MS > 0
                                    else None
                                ),
                            )  # type: ignore[assignment]
                        else:
                            fetched = val  # type: ignore[assignment]

                        # Record successful provider event
                        latency_ms = int((time.time() - start_time) * 1000)
                        _record_provider_success(pname, latency_ms)
                        break

                    except Exception as e:
                        attempt += 1
                        latency_ms = int((time.time() - start_time) * 1000)

                        if attempt > _PROV_RETRIES:
                            # permanent-ish failure for now: record penalty and proceed
                            _PROV_FAIL[pname] = time.time() + _PROV_FAIL_PENALTY
                            logging.getLogger("ziggy").warning(
                                "[provider] %s fetch_ohlc failed after %d attempts: %s",
                                pname,
                                attempt,
                                e,
                            )

                            # Record final failure
                            _record_provider_failure(pname, latency_ms, e)
                            fetched = {t: MarketProvider._empty_frame() for t in batch}
                            break
                        else:
                            backoff = _PROV_BACKOFF_BASE * (2 ** (attempt - 1))
                            # Succinct timeout log, otherwise generic failure
                            if isinstance(e, asyncio.TimeoutError):
                                json_log(
                                    logging.WARNING,
                                    "provider_timeout",
                                    provider=pname,
                                    attempt=attempt,
                                    timeout_ms=PROVIDER_TIMEOUT_MS,
                                    tickers=len(batch),
                                )
                            else:
                                logging.getLogger("ziggy").info(
                                    "[provider] %s fetch_ohlc attempt %d failed: %s — retrying in %.2fs",
                                    pname,
                                    attempt,
                                    e,
                                    backoff,
                                )
                            with suppress(Exception):
                                await asyncio.sleep(backoff)

                if fetched is None:
                    # Fallback to empty frames if something unexpected happened
                    latency_ms = int((time.time() - start_time) * 1000)
                    _record_provider_failure(
                        pname, latency_ms, Exception("Unexpected failure")
                    )
                    fetched = {t: MarketProvider._empty_frame() for t in batch}

            # Accept per-ticker first non-empty
            still: list[str] = []
            for t in batch:
                df = fetched.get(t)
                if df is not None and hasattr(df, "empty") and not df.empty:
                    result[t] = df
                    source[t] = getattr(
                        provider, "name", provider.__class__.__name__
                    ).lower()
                else:
                    still.append(t)
            remaining = set(still)

        _CACHE.set(key, result)
        return (result, source) if return_source else result

    def today_open_prices(self, tickers: list[str]) -> dict[str, float | None]:
        # First intraday-capable provider; soft fallback if all None/missing
        intraday_chain = [
            p for p in self.providers if getattr(p, "supports_intraday", False)
        ]
        if not intraday_chain:
            return dict.fromkeys(tickers)

        def _try_with(p: MarketProvider) -> dict[str, float | None]:
            k = _key(
                "open", getattr(p, "name", p.__class__.__name__), tuple(sorted(tickers))
            )
            cached = _CACHE.get(k)
            if cached is None:
                try:
                    vals = p.today_open_prices(tickers)
                except Exception:
                    vals = dict.fromkeys(tickers)
                _CACHE.set(k, vals)
                return vals
            return cached

        first = _try_with(intraday_chain[0])
        if any(v is not None for v in first.values()):
            return first
        # fallback through the rest if first yielded nothing
        for p in intraday_chain[1:]:
            vals = _try_with(p)
            if any(v is not None for v in vals.values()):
                return vals
        # nothing useful
        return first


# ------------------------------ Crypto wrapper ---------------------------


class MultiCrypto(MultiProvider):
    """Crypto priority + failover. Uses same provider classes; note that
    some underlying equity providers may return empty for crypto tickers.
    """

    name = "multi-crypto"


# ------------------------------ Factory funcs ----------------------------


def _parse_chain(env_value: str | None, fallback: str) -> list[str]:
    raw = (env_value or fallback or "").strip()
    if "," in raw:
        items = [x.strip().lower() for x in raw.split(",") if x.strip()]
    else:
        items = [raw.lower()] if raw else []
    # keep only valid provider names; preserve order; default yfinance
    chain = [x for x in items if x in _VALID_PROVIDER_NAMES]
    if not chain:
        chain = ["yfinance"]
    return chain


def get_price_provider() -> MultiProvider:
    """Read provider chain from env and return a MultiProvider.

    Env precedence:
      1) PROVIDERS_PRICES (comma-separated, e.g., "polygon,alpaca,yfinance")
      2) PRICE_PROVIDER (single name)
      3) default "yfinance"
    """
    # Sandbox mode short-circuit to fixtures provider
    if (
        os.getenv("PROVIDER_MODE", "live").strip().lower() == "sandbox"
    ) and _SANDBOX_AVAILABLE:
        # Return a single sandbox provider (implements MarketProvider)
        try:
            return SandboxPriceProvider()  # type: ignore[return-value]
        except Exception:
            pass
    chain = _parse_chain(
        os.getenv("PROVIDERS_PRICES")
        or os.getenv("PRICES_PROVIDER"),  # accept a common typo variant
        os.getenv("PRICE_PROVIDER", "yfinance"),
    )
    return MultiProvider(chain)


def get_crypto_provider() -> MultiCrypto:
    """Return crypto provider chain (default: polygon,yfinance)."""
    chain = _parse_chain(
        os.getenv("PROVIDERS_CRYPTO"),
        "polygon,yfinance",
    )
    return MultiCrypto(chain)


# ------------------------------ News/Signals -----------------------------


def get_news_provider():
    """Return a news provider when in sandbox mode; else None.

    The news API routes can use this to serve local fixtures when offline.
    """
    if (
        os.getenv("PROVIDER_MODE", "live").strip().lower() == "sandbox"
        and _SANDBOX_AVAILABLE
        and SandboxNewsProvider is not None
    ):
        try:
            return SandboxNewsProvider()
        except Exception:
            return None
    return None


def get_signals_provider():
    """Return a signals provider when in sandbox mode; else None.

    The signals API routes can use this to serve local fixtures when offline.
    """
    if (
        os.getenv("PROVIDER_MODE", "live").strip().lower() == "sandbox"
        and _SANDBOX_AVAILABLE
        and SandboxSignalsProvider is not None
    ):
        try:
            return SandboxSignalsProvider()
        except Exception:
            return None
    return None


# ==================== Brain Integration Functions ====================


async def _write_data_to_brain(
    data: dict[str, Any], data_type: str, provider_name: str, source_tz: str = "UTC"
) -> str | None:
    """Write market data to brain with vendor stamping and timezone info."""
    if not BRAIN_INTEGRATION_AVAILABLE:
        return None

    try:
        # Create vendor stamp
        vendor_stamp = _create_vendor_stamp(provider_name, source_tz)

        # Normalize timezone information
        timezone_info = None
        if "timestamp" in data or "ts" in data:
            ts_field = "timestamp" if "timestamp" in data else "ts"
            timezone_info = normalize_event_ts(
                data[ts_field],
                source_tz,
                "NYSE",  # Default exchange for normalization
            )

        # Write to brain
        event_id = await write_market_data_to_brain(
            data=data,
            data_type=data_type,
            vendor_stamp=vendor_stamp,
            timezone_info=timezone_info,
        )

        return event_id

    except Exception as e:
        logger.error(f"Failed to write {data_type} to brain: {e}")
        return None


def get_brain_integration_stats() -> dict[str, Any]:
    """Get brain integration statistics."""
    # Check if health manager is available
    health_available = False
    try:
        from app.services.provider_health import health_manager

        health_available = health_manager is not None
    except ImportError:
        pass

    stats = {
        "available": BRAIN_INTEGRATION_AVAILABLE,
        "provider_health_available": health_available,
        "vendor_stamping": STAMP_VENDOR_VERSION,
        "timezone_normalization": BRAIN_INTEGRATION_AVAILABLE,
    }

    if BRAIN_INTEGRATION_AVAILABLE:
        try:
            from app.services.brain_integration import get_brain_stats

            stats.update(get_brain_stats())
        except ImportError:
            pass

    return stats
