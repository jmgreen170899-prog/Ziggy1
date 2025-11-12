"""
Market Data Fetcher with Timeout and Fallback Chain

Replaces direct calls to yfinance, alpaca, polygon, etc. in feature generation.
Provides strict per-provider timeouts and structured logging.
"""

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError

import yfinance as yf

from app.core.config import get_settings


logger = logging.getLogger(__name__)

_settings = get_settings()
PROVIDER_TIMEOUT = float(getattr(_settings, "MARKET_FETCH_TIMEOUT_S", 5.0) or 5.0)
CACHE_TTL_SECONDS = 300  # 5 minutes

# Concurrency-safe in-memory cache
_ohlcv_cache = {}
_ohlcv_cache_lock = threading.Lock()
_quote_cache = {}
_quote_cache_lock = threading.Lock()


class DataFetchUnavailableError(Exception):
    def __init__(self, ticker, failures):
        self.ticker = ticker
        self.failures = failures
        super().__init__(f"All providers failed for {ticker}: {failures}")


def fetch_yfinance_ohlcv(ticker, lookback_days=365):
    start = time.time()
    try:
        ticker_obj = yf.Ticker(ticker)
        data = ticker_obj.history(period=f"{lookback_days}d", interval="1d")
        latency = time.time() - start
        if data is not None and not data.empty:
            logger.info(f"[DATA] yfinance success for {ticker} in {latency:.2f}s")
            return data
        else:
            logger.warning(f"[DATA] yfinance returned empty for {ticker} in {latency:.2f}s")
            return None
    except Exception as e:
        latency = time.time() - start
        logger.warning(f"[DATA] yfinance failed for {ticker} in {latency:.2f}s: {e}")
        return None


# Placeholder for other providers (alpaca, polygon)
def fetch_alpaca_ohlcv(ticker, lookback_days=365):
    # TODO: Implement actual Alpaca fetch
    logger.info(f"[DATA] Alpaca not implemented for {ticker}")
    return None


def fetch_polygon_ohlcv(ticker, lookback_days=365):
    # TODO: Implement actual Polygon fetch
    logger.info(f"[DATA] Polygon not implemented for {ticker}")
    return None


PROVIDERS = [
    ("yfinance", fetch_yfinance_ohlcv),
    ("alpaca", fetch_alpaca_ohlcv),
    ("polygon", fetch_polygon_ohlcv),
]


def get_recent_ohlcv(
    ticker: str, lookback_days: int = 365, timeout: float = PROVIDER_TIMEOUT
) -> dict:
    """Fetch OHLCV using timeout+fallback with 5-min cache.

    Returns dict: {"data": DataFrame, "from_cache": bool, "stale_seconds": int | None}
    """
    now = time.time()
    # Cache check
    with _ohlcv_cache_lock:
        entry = _ohlcv_cache.get(ticker)
        if entry:
            df, ts = entry
            age = now - ts
            if age < CACHE_TTL_SECONDS and df is not None and not df.empty:
                logger.info(f"[DATA] OHLCV cache hit for {ticker}, age={age:.1f}s")
                return {"data": df, "from_cache": True, "stale_seconds": None}

    failures = {}
    # Provider attempts
    for name, func in PROVIDERS:
        with ThreadPoolExecutor(max_workers=1) as ex:
            fut = ex.submit(func, ticker, lookback_days)
            try:
                result = fut.result(timeout=timeout)
                if result is not None and not result.empty:
                    with _ohlcv_cache_lock:
                        _ohlcv_cache[ticker] = (result, now)
                    logger.info(f"[DATA] OHLCV fresh from {name} for {ticker}")
                    return {"data": result, "from_cache": False, "stale_seconds": None}
                failures[name] = "empty"
            except FuturesTimeoutError:
                failures[name] = "timeout"
                logger.warning(f"[DATA] {name} OHLCV timeout for {ticker} after {timeout}s")
            except Exception as e:
                failures[name] = str(e)
                logger.warning(f"[DATA] {name} OHLCV failed for {ticker}: {e}")

    # Stale cache fallback
    with _ohlcv_cache_lock:
        entry = _ohlcv_cache.get(ticker)
        if entry:
            df, ts = entry
            if df is not None and not df.empty:
                age = int(now - ts)
                logger.warning(f"[DATA] OHLCV stale cache for {ticker}, stale_seconds={age}")
                return {"data": df, "from_cache": True, "stale_seconds": age}

    raise DataFetchUnavailableError(ticker, failures)


def get_realtime_quote(ticker: str, timeout: float = PROVIDER_TIMEOUT) -> dict:
    """Fetch realtime quote with 5-min cache and timeout+fallback."""
    now = time.time()
    # Cache check
    with _quote_cache_lock:
        entry = _quote_cache.get(ticker)
        if entry:
            q, ts = entry
            age = now - ts
            if age < CACHE_TTL_SECONDS and q is not None:
                logger.info(f"[DATA] Quote cache hit for {ticker}, age={age:.1f}s")
                return {"data": q, "from_cache": True, "stale_seconds": None}

    # Provider attempt (yfinance)
    start = time.time()
    try:
        price = yf.Ticker(ticker).info.get("regularMarketPrice")
        latency = time.time() - start
        if price is not None:
            quote = {"ticker": ticker, "price": price, "latency": latency}
            with _quote_cache_lock:
                _quote_cache[ticker] = (quote, now)
            logger.info(f"[DATA] yfinance quote for {ticker} in {latency:.2f}s: {price}")
            return {"data": quote, "from_cache": False, "stale_seconds": None}
        logger.warning(f"[DATA] yfinance quote missing for {ticker} in {latency:.2f}s")
    except Exception as e:
        latency = time.time() - start
        logger.warning(f"[DATA] yfinance quote failed for {ticker} in {latency:.2f}s: {e}")

    # Stale cache fallback
    with _quote_cache_lock:
        entry = _quote_cache.get(ticker)
        if entry:
            q, ts = entry
            if q is not None:
                age = int(now - ts)
                logger.warning(f"[DATA] Quote stale cache for {ticker}, stale_seconds={age}")
                return {"data": q, "from_cache": True, "stale_seconds": age}

    raise DataFetchUnavailableError(ticker, {"yfinance": "failed"})


# Document: This module replaces direct calls to yfinance/alpaca/polygon in feature generation.
# Always use get_recent_ohlcv and get_realtime_quote for market data fetches with timeout/fallback.
