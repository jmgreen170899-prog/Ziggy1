"""
Microstructure Features - Perception Layer

Advanced market microstructure indicators for enhanced signal generation.
Features cover order flow, volatility patterns, liquidity, and price dynamics.
"""

from __future__ import annotations

import logging
import warnings
from typing import Any

import numpy as np
import pandas as pd


logger = logging.getLogger(__name__)

# Suppress pandas warnings for cleaner output
warnings.filterwarnings("ignore", category=RuntimeWarning)


def opening_gap(df: pd.DataFrame) -> pd.Series:
    """
    Calculate opening gap as percentage change from previous close.

    Measures overnight price movement and potential gap-fill behavior.

    Args:
        df: DataFrame with 'open' and 'close' columns

    Returns:
        Series with opening gap percentages
    """
    if df.empty or "open" not in df.columns or "close" not in df.columns:
        return pd.Series(dtype=float, name="opening_gap")

    prev_close = df["close"].shift(1)
    gap = (df["open"] - prev_close) / prev_close.replace(0, np.nan)

    return gap.fillna(0.0)


def vwap_deviation(df: pd.DataFrame, window: int = 20) -> pd.Series:
    """
    Calculate deviation from Volume Weighted Average Price (VWAP).

    Measures how far current price is from volume-weighted average,
    indicating potential mean reversion opportunities.

    Args:
        df: DataFrame with 'close' and 'volume' columns
        window: Rolling window for VWAP calculation

    Returns:
        Series with VWAP deviation percentages
    """
    if df.empty or "close" not in df.columns or "volume" not in df.columns:
        return pd.Series(dtype=float, name="vwap_deviation")

    # Calculate VWAP using rolling window
    price_volume = (df["close"] * df["volume"]).rolling(window, min_periods=1)
    volume_sum = df["volume"].rolling(window, min_periods=1)

    vwap = price_volume.sum() / volume_sum.sum().replace(0, np.nan)
    deviation = (df["close"] - vwap) / vwap.replace(0, np.nan)

    return deviation.fillna(0.0)


def vol_of_vol(
    df: pd.DataFrame, window: int = 20, volatility_window: int = 10
) -> pd.Series:
    """
    Calculate volatility of volatility (vol-of-vol).

    Measures the uncertainty in volatility itself, indicating
    periods of changing market regime or uncertainty.

    Args:
        df: DataFrame with 'close' column
        window: Window for vol-of-vol calculation
        volatility_window: Window for underlying volatility calculation

    Returns:
        Series with vol-of-vol values
    """
    if df.empty or "close" not in df.columns:
        return pd.Series(dtype=float, name="vol_of_vol")

    # Calculate returns
    returns = df["close"].pct_change()

    # Calculate rolling volatility (standard deviation of returns)
    volatility = returns.rolling(volatility_window, min_periods=1).std()

    # Calculate volatility of volatility
    vol_of_vol_series = volatility.rolling(window, min_periods=1).std()

    return vol_of_vol_series.fillna(0.0)


def liquidity_proxy(df: pd.DataFrame, volume_power: float = 0.5) -> pd.Series:
    """
    Calculate liquidity proxy using volume and bid-ask spread approximation.

    Higher values indicate better liquidity. Uses high-low spread as
    proxy for bid-ask spread when actual spread unavailable.

    Args:
        df: DataFrame with 'high', 'low', 'volume' columns
        volume_power: Power to apply to volume (0.5 = square root)

    Returns:
        Series with liquidity proxy values
    """
    if df.empty or not all(col in df.columns for col in ["high", "low", "volume"]):
        return pd.Series(dtype=float, name="liquidity_proxy")

    # Use high-low spread as proxy for bid-ask spread
    spread = (df["high"] - df["low"]).replace(0, np.nan)

    # Apply power transform to volume (square root reduces impact of extreme values)
    volume_adjusted = np.power(df["volume"], volume_power)

    # Liquidity proxy: higher volume and lower spread = higher liquidity
    liquidity = volume_adjusted / spread

    return liquidity.fillna(0.0)


def imbalance_from_ohlc(df: pd.DataFrame) -> pd.Series:
    """
    Estimate order imbalance using OHLC data.

    Approximates buy vs sell volume using price movement within each period.
    Positive values indicate buy pressure, negative indicate sell pressure.

    Args:
        df: DataFrame with 'open', 'close', 'volume' columns

    Returns:
        Series with estimated order imbalance
    """
    if df.empty or not all(col in df.columns for col in ["open", "close", "volume"]):
        return pd.Series(dtype=float, name="order_imbalance")

    # Classify periods as up (close > open) or down (close <= open)
    is_up = df["close"] > df["open"]

    # Allocate volume based on price direction
    up_volume = is_up.astype(int) * df["volume"]
    down_volume = (~is_up).astype(int) * df["volume"]

    # Calculate imbalance: (buy_volume - sell_volume) / total_volume
    total_volume = df["volume"].replace(0, np.nan)
    imbalance = (up_volume - down_volume) / total_volume

    return imbalance.fillna(0.0)


def high_low_ratio(df: pd.DataFrame, window: int = 20) -> pd.Series:
    """
    Calculate rolling high-low ratio indicating volatility regime.

    Higher ratios indicate more volatile periods with wider trading ranges.

    Args:
        df: DataFrame with 'high' and 'low' columns
        window: Rolling window for calculation

    Returns:
        Series with high-low ratios
    """
    if df.empty or not all(col in df.columns for col in ["high", "low"]):
        return pd.Series(dtype=float, name="high_low_ratio")

    # Calculate rolling high and low
    rolling_high = df["high"].rolling(window, min_periods=1).max()
    rolling_low = df["low"].rolling(window, min_periods=1).min()

    # Ratio of range to current price level
    ratio = (rolling_high - rolling_low) / rolling_low.replace(0, np.nan)

    return ratio.fillna(0.0)


def price_momentum(df: pd.DataFrame, window: int = 10) -> pd.Series:
    """
    Calculate price momentum over specified window.

    Measures rate of change in price over time period.

    Args:
        df: DataFrame with 'close' column
        window: Window for momentum calculation

    Returns:
        Series with momentum values
    """
    if df.empty or "close" not in df.columns:
        return pd.Series(dtype=float, name="price_momentum")

    momentum = df["close"].pct_change(periods=window)

    return momentum.fillna(0.0)


def volume_momentum(df: pd.DataFrame, window: int = 10) -> pd.Series:
    """
    Calculate volume momentum indicating changing participation.

    Measures rate of change in volume over time period.

    Args:
        df: DataFrame with 'volume' column
        window: Window for momentum calculation

    Returns:
        Series with volume momentum values
    """
    if df.empty or "volume" not in df.columns:
        return pd.Series(dtype=float, name="volume_momentum")

    momentum = df["volume"].pct_change(periods=window)

    return momentum.fillna(0.0)


def volume_price_correlation(df: pd.DataFrame, window: int = 20) -> pd.Series:
    """
    Calculate rolling correlation between volume and price changes.

    Positive correlation suggests informed trading (volume follows price).
    Negative correlation may indicate contrarian activity.

    Args:
        df: DataFrame with 'close' and 'volume' columns
        window: Rolling window for correlation

    Returns:
        Series with volume-price correlations
    """
    if df.empty or not all(col in df.columns for col in ["close", "volume"]):
        return pd.Series(dtype=float, name="volume_price_correlation")

    price_change = df["close"].pct_change()
    volume_change = df["volume"].pct_change()

    correlation = price_change.rolling(window, min_periods=5).corr(volume_change)

    return correlation.fillna(0.0)


def intraday_intensity(df: pd.DataFrame) -> pd.Series:
    """
    Calculate Intraday Intensity Index (III).

    Measures the flow of volume in relation to price movement within the day.
    Helps identify accumulation vs distribution patterns.

    Args:
        df: DataFrame with 'high', 'low', 'close', 'volume' columns

    Returns:
        Series with intraday intensity values
    """
    if df.empty or not all(
        col in df.columns for col in ["high", "low", "close", "volume"]
    ):
        return pd.Series(dtype=float, name="intraday_intensity")

    # Calculate where close is within high-low range
    range_size = df["high"] - df["low"]
    close_position = (df["close"] - df["low"]) - (df["high"] - df["close"])

    # Avoid division by zero
    range_size = range_size.replace(0, np.nan)

    # Intensity = (close position / range) * volume
    intensity = (close_position / range_size) * df["volume"]

    return intensity.fillna(0.0)


def compute_all_features(
    df: pd.DataFrame, feature_config: dict[str, Any] = None
) -> dict[str, pd.Series]:
    """
    Compute all microstructure features for a given DataFrame.

    Args:
        df: DataFrame with OHLCV data
        feature_config: Configuration for feature parameters

    Returns:
        Dictionary of feature name -> Series mappings
    """
    config = feature_config or {}

    # Default parameters
    default_window = config.get("default_window", 20)
    vol_window = config.get("volatility_window", 10)
    momentum_window = config.get("momentum_window", 10)

    features = {}

    try:
        # Basic features
        features["opening_gap"] = opening_gap(df)
        features["vwap_deviation"] = vwap_deviation(df, window=default_window)
        features["vol_of_vol"] = vol_of_vol(
            df, window=default_window, volatility_window=vol_window
        )
        features["liquidity_proxy"] = liquidity_proxy(df)
        features["order_imbalance"] = imbalance_from_ohlc(df)

        # Extended features
        features["high_low_ratio"] = high_low_ratio(df, window=default_window)
        features["price_momentum"] = price_momentum(df, window=momentum_window)
        features["volume_momentum"] = volume_momentum(df, window=momentum_window)
        features["volume_price_correlation"] = volume_price_correlation(
            df, window=default_window
        )
        features["intraday_intensity"] = intraday_intensity(df)

        logger.debug(f"Computed {len(features)} microstructure features")

    except Exception as e:
        logger.error(f"Error computing microstructure features: {e}")
        # Return empty series for failed features
        for feature_name in [
            "opening_gap",
            "vwap_deviation",
            "vol_of_vol",
            "liquidity_proxy",
            "order_imbalance",
        ]:
            if feature_name not in features:
                features[feature_name] = pd.Series(dtype=float, name=feature_name)

    return features


def get_feature_summary(features: dict[str, pd.Series]) -> dict[str, dict[str, float]]:
    """
    Get summary statistics for computed features.

    Args:
        features: Dictionary of feature series

    Returns:
        Dictionary with summary stats for each feature
    """
    summary = {}

    for feature_name, series in features.items():
        if series.empty:
            summary[feature_name] = {
                "count": 0,
                "mean": 0.0,
                "std": 0.0,
                "min": 0.0,
                "max": 0.0,
            }
        else:
            # Remove infinite values for summary
            clean_series = series.replace([np.inf, -np.inf], np.nan).dropna()

            if clean_series.empty:
                summary[feature_name] = {
                    "count": 0,
                    "mean": 0.0,
                    "std": 0.0,
                    "min": 0.0,
                    "max": 0.0,
                }
            else:
                summary[feature_name] = {
                    "count": len(clean_series),
                    "mean": float(clean_series.mean()),
                    "std": float(clean_series.std()),
                    "min": float(clean_series.min()),
                    "max": float(clean_series.max()),
                }

    return summary


def validate_features(features: dict[str, pd.Series]) -> dict[str, bool]:
    """
    Validate computed features for quality checks.

    Args:
        features: Dictionary of feature series

    Returns:
        Dictionary of feature_name -> validation_passed
    """
    validation_results = {}

    for feature_name, series in features.items():
        try:
            # Check for basic issues
            has_data = not series.empty
            no_all_nan = not series.isna().all()
            no_all_inf = (
                not np.isinf(series.replace([np.inf, -np.inf], np.nan)).isna().all()
            )
            finite_values = np.isfinite(series.replace([np.inf, -np.inf], np.nan)).any()

            validation_results[feature_name] = has_data and no_all_nan and finite_values

        except Exception as e:
            logger.warning(f"Validation failed for feature {feature_name}: {e}")
            validation_results[feature_name] = False

    return validation_results
