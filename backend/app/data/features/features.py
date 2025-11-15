"""
Features Store Implementation

Handles versioned feature computation, caching, and retrieval for the ZiggyAI trading system.
Supports momentum, breadth, volatility regime, macro, news sentiment, and microstructure features.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import date, datetime
from typing import Any

import numpy as np


logger = logging.getLogger(__name__)

FEATURE_VERSION = "v1"
CACHE_SIZE = 1000  # LRU cache size for features


class FeatureStore:
    """
    Feature store with versioning and caching capabilities.

    Provides deterministic feature computation with cache keying by
    (ticker, dt_floor, interval, version) for efficient retrieval.
    """

    def __init__(self, cache_size: int = CACHE_SIZE):
        self.cache_size = cache_size
        self._cache: dict[str, dict[str, Any]] = {}
        self._setup_cache()

    def _setup_cache(self):
        """Initialize the feature cache."""
        # In production, this could be Redis or another distributed cache
        logger.info(f"Initialized feature store with cache size: {self.cache_size}")

    def get(
        self,
        ticker: str,
        dt: date | datetime,
        interval: str = "1D",
        version: str = FEATURE_VERSION,
    ) -> dict[str, Any]:
        """
        Get features for a ticker at a specific datetime and interval.

        Args:
            ticker: Stock symbol (e.g., 'AAPL')
            dt: Date or datetime for feature computation
            interval: Time interval ('1D', '4H', '1H', etc.)
            version: Feature version for backward compatibility

        Returns:
            Dictionary of computed features
        """
        cache_key = self._generate_key(ticker, dt, interval, version)

        # Check cache first
        if cache_key in self._cache:
            logger.debug(f"Cache hit for {ticker} {dt} {interval}")
            return self._cache[cache_key].copy()

        # Compute features
        features = self._compute_features(ticker, dt, interval, version)

        # Cache with LRU eviction
        if len(self._cache) >= self.cache_size:
            # Simple FIFO eviction (could implement proper LRU)
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]

        self._cache[cache_key] = features.copy()
        logger.debug(f"Computed and cached features for {ticker} {dt} {interval}")

        return features

    def _generate_key(
        self, ticker: str, dt: date | datetime, interval: str, version: str
    ) -> str:
        """Generate deterministic cache key."""
        dt_floor = dt.date() if isinstance(dt, datetime) else dt
        raw = f"{ticker.upper()}|{dt_floor.isoformat()}|{interval}|{version}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def _compute_features(
        self, ticker: str, dt: date | datetime, interval: str, version: str
    ) -> dict[str, Any]:
        """Compute all features for the given parameters."""

        # Base feature set - in production, these would pull from market data
        features = {
            # Momentum features
            "momentum_20d": self._compute_momentum(ticker, dt, 20),
            "momentum_5d": self._compute_momentum(ticker, dt, 5),
            "rsi_14": self._compute_rsi(ticker, dt, 14),
            # Breadth features
            "breadth_advdec": self._compute_breadth_advdec(dt),
            "breadth_hl": self._compute_breadth_high_low(dt),
            # Volatility regime
            "volatility_20d": self._compute_volatility(ticker, dt, 20),
            "volatility_5d": self._compute_volatility(ticker, dt, 5),
            "vol_regime": self._compute_vol_regime(ticker, dt),
            # Macro features
            "vix_level": self._compute_vix_level(dt),
            "yield_curve": self._compute_yield_curve(dt),
            "dollar_strength": self._compute_dollar_strength(dt),
            # News sentiment
            "news_sentiment": self._compute_news_sentiment(ticker, dt),
            "news_volume": self._compute_news_volume(ticker, dt),
            # Microstructure
            "liquidity_score": self._compute_liquidity_score(ticker, dt),
            "bid_ask_spread": self._compute_bid_ask_spread(ticker, dt),
            "order_flow": self._compute_order_flow(ticker, dt),
            # Meta features
            "trading_session": self._compute_trading_session(dt),
            "day_of_week": dt.weekday() if isinstance(dt, datetime) else dt.weekday(),
        }

        # Add version metadata
        features["_version"] = version
        features["_computed_at"] = datetime.now().isoformat()
        features["_ticker"] = ticker.upper()
        features["_interval"] = interval

        return features

    # Mock feature computation methods - replace with real implementations

    def _compute_momentum(self, ticker: str, dt: date | datetime, period: int) -> float:
        """Compute momentum over specified period."""
        # Mock: random walk with slight positive bias
        np.random.seed(hash(f"{ticker}{dt}{period}") % 2**32)
        return float(np.random.normal(0.02, 0.15))  # 2% average with 15% volatility

    def _compute_rsi(self, ticker: str, dt: date | datetime, period: int) -> float:
        """Compute RSI indicator."""
        np.random.seed(hash(f"{ticker}{dt}rsi{period}") % 2**32)
        return float(np.random.uniform(20, 80))  # RSI between 20-80

    def _compute_breadth_advdec(self, dt: date | datetime) -> float:
        """Compute advance/decline ratio."""
        np.random.seed(hash(f"advdec{dt}") % 2**32)
        return float(np.random.normal(1.0, 0.3))  # Around 1.0 with variation

    def _compute_breadth_high_low(self, dt: date | datetime) -> float:
        """Compute new highs vs new lows ratio."""
        np.random.seed(hash(f"highlow{dt}") % 2**32)
        return float(np.random.normal(0.5, 0.2))

    def _compute_volatility(
        self, ticker: str, dt: date | datetime, period: int
    ) -> float:
        """Compute realized volatility."""
        np.random.seed(hash(f"{ticker}{dt}vol{period}") % 2**32)
        return float(np.random.lognormal(np.log(0.2), 0.5))  # Log-normal around 20%

    def _compute_vol_regime(self, ticker: str, dt: date | datetime) -> str:
        """Determine volatility regime."""
        vol = self._compute_volatility(ticker, dt, 20)
        if vol > 0.4:
            return "high"
        elif vol < 0.15:
            return "low"
        else:
            return "medium"

    def _compute_vix_level(self, dt: date | datetime) -> float:
        """Get VIX level."""
        np.random.seed(hash(f"vix{dt}") % 2**32)
        return float(np.random.lognormal(np.log(20), 0.4))  # Around 20 with variation

    def _compute_yield_curve(self, dt: date | datetime) -> float:
        """Compute 10Y-2Y yield spread."""
        np.random.seed(hash(f"yield{dt}") % 2**32)
        return float(np.random.normal(1.5, 0.8))  # 150bps average spread

    def _compute_dollar_strength(self, dt: date | datetime) -> float:
        """Compute dollar strength index."""
        np.random.seed(hash(f"dxy{dt}") % 2**32)
        return float(np.random.normal(100, 5))  # Around 100 with variation

    def _compute_news_sentiment(self, ticker: str, dt: date | datetime) -> float:
        """Compute news sentiment score."""
        np.random.seed(hash(f"{ticker}{dt}news") % 2**32)
        return float(np.random.normal(0.1, 0.3))  # Slight positive bias

    def _compute_news_volume(self, ticker: str, dt: date | datetime) -> int:
        """Count news articles."""
        np.random.seed(hash(f"{ticker}{dt}newsvol") % 2**32)
        return int(np.random.poisson(5))  # Average 5 articles per day

    def _compute_liquidity_score(self, ticker: str, dt: date | datetime) -> float:
        """Compute liquidity score."""
        np.random.seed(hash(f"{ticker}{dt}liq") % 2**32)
        return float(np.random.beta(2, 2))  # Beta distribution between 0-1

    def _compute_bid_ask_spread(self, ticker: str, dt: date | datetime) -> float:
        """Compute bid-ask spread in basis points."""
        np.random.seed(hash(f"{ticker}{dt}spread") % 2**32)
        return float(np.random.lognormal(np.log(5), 0.5))  # Around 5bps

    def _compute_order_flow(self, ticker: str, dt: date | datetime) -> float:
        """Compute order flow imbalance."""
        np.random.seed(hash(f"{ticker}{dt}flow") % 2**32)
        return float(np.random.normal(0, 0.2))  # Centered around 0

    def _compute_trading_session(self, dt: date | datetime) -> str:
        """Determine trading session (pre, regular, post)."""
        if isinstance(dt, datetime):
            hour = dt.hour
            if hour < 9:
                return "pre"
            elif hour > 16:
                return "post"
            else:
                return "regular"
        return "regular"  # Default for date objects

    def clear_cache(self):
        """Clear the feature cache."""
        self._cache.clear()
        logger.info("Feature cache cleared")

    def cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return {
            "cache_size": len(self._cache),
            "max_size": self.cache_size,
            "hit_rate": "Not implemented",  # Would track hits/misses in production
        }


# Global feature store instance
_feature_store = FeatureStore()


def compute_features(
    ticker: str,
    dt: date | datetime,
    interval: str = "1D",
    version: str = FEATURE_VERSION,
) -> dict[str, Any]:
    """
    Convenience function to compute features using the global feature store.

    Args:
        ticker: Stock symbol
        dt: Date or datetime for feature computation
        interval: Time interval
        version: Feature version

    Returns:
        Dictionary of computed features
    """
    return _feature_store.get(ticker, dt, interval, version)


def key_for(
    ticker: str, dt: date | datetime, interval: str, version: str = FEATURE_VERSION
) -> str:
    """Generate cache key for given parameters."""
    return _feature_store._generate_key(ticker, dt, interval, version)


# Export the main interface
__all__ = ["FEATURE_VERSION", "FeatureStore", "compute_features", "key_for"]
