import logging
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


logger = logging.getLogger(__name__)


@dataclass
class FeatureSet:
    values: Mapping[str, Any]
    source: str | None = None

    # Common feature attributes for compatibility
    rsi_14: float | None = None
    z_score_20: float | None = None
    volatility_20d: float | None = None
    atr_14: float | None = None
    close: float | None = None
    sma_20: float | None = None
    sma_50: float | None = None
    vix_level: float | None = None
    price_change_1d: float | None = None
    breadth_50dma: float | None = None
    slope_20d: float | None = None


# ---- Minimal, import-safe feature computer & helpers (no network, no disk) ----
DEFAULT_FEATURES: dict[str, float] = {
    "volatility_20d": 0.20,
    "liquidity_score": 0.50,
    "vix_level": 20.0,
    "sma_fast": 1.0,
    "sma_slow": 1.0,
}


class FeatureComputer:
    """Tiny stub used by tests & routes. Deterministic, side-effect free."""

    def compute_for_ticker(self, ticker: str) -> dict[str, float]:
        """
        Compute features for a single ticker.

        Keep deterministic but slightly ticker-dependent to avoid identical outputs.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary of feature values
        """
        # Create a small deterministic variation based on ticker name
        salt = (sum(ord(c) for c in ticker) % 7) / 100.0
        return {
            **DEFAULT_FEATURES,
            "sma_fast": 1.0 + salt,
            "sma_slow": 1.0,
        }

    def compute_batch(self, tickers: list[str]) -> dict[str, dict[str, float]]:
        """
        Compute features for multiple tickers.

        Args:
            tickers: List of ticker symbols

        Returns:
            Dictionary mapping ticker to feature dict
        """
        return {t: self.compute_for_ticker(t) for t in tickers}

    def get_features(self, ticker: str, force_refresh: bool = False) -> FeatureSet | None:
        """
        Get features as a FeatureSet object (for compatibility with regime detector).

        Args:
            ticker: Stock ticker symbol
            force_refresh: Ignored in this stub implementation

        Returns:
            FeatureSet with computed features
        """
        features = self.compute_for_ticker(ticker)
        return FeatureSet(
            values=features,
            source="stub",
            volatility_20d=features.get("volatility_20d"),
            vix_level=features.get("vix_level"),
        )


def get_ticker_features(ticker: str) -> dict[str, float]:
    """
    Get features for a ticker.

    This is a lightweight stub implementation. In production, this would
    fetch and compute actual features from market data.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Dictionary of feature values
    """
    return FeatureComputer().compute_for_ticker(ticker)


def get_multiple_ticker_features(tickers: list[str]) -> dict[str, dict[str, float]]:
    """
    Get features for multiple tickers.

    Args:
        tickers: List of ticker symbols

    Returns:
        Dictionary mapping ticker to feature dict
    """
    return FeatureComputer().compute_batch(tickers)


def get_market_data(ticker: str) -> dict | None:
    """
    Get market data for a ticker.

    This is a placeholder implementation.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Market data dict or None if unavailable
    """
    logger.debug(f"get_market_data called for {ticker} (placeholder implementation)")
    return None


__all__ = [
    "FeatureComputer",
    "FeatureSet",
    "get_market_data",
    "get_multiple_ticker_features",
    "get_ticker_features",
]
