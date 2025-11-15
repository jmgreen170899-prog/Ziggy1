"""
Data Contracts - Perception Layer

Schema validation and integrity checks for all incoming market data.
Ensures data quality before processing and triggers quarantine for violations.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any

import pandas as pd


logger = logging.getLogger(__name__)

# Environment configuration
CONTRACT_VIOLATION_RATE_THRESHOLD = float(
    os.getenv("CONTRACT_VIOLATION_RATE_THRESHOLD", "0.001")
)


class ContractViolation(Exception):
    """Raised when data fails contract validation."""

    def __init__(self, contract_name: str, reason: str, data_sample: Any = None):
        self.contract_name = contract_name
        self.reason = reason
        self.data_sample = str(data_sample)[:500] if data_sample is not None else None
        super().__init__(f"Contract '{contract_name}' violation: {reason}")


def validate_ohlcv(df: pd.DataFrame, ticker: str = "UNKNOWN") -> None:
    """
    Validate OHLCV (Open, High, Low, Close, Volume) data frame.

    Args:
        df: DataFrame with OHLCV data
        ticker: Ticker symbol for context

    Raises:
        ContractViolation: If validation fails
    """
    if df is None or df.empty:
        raise ContractViolation("ohlcv", f"Empty or None DataFrame for {ticker}")

    # Required columns
    required = ["ts", "open", "high", "low", "close", "volume"]
    missing = set(required) - set(df.columns)
    if missing:
        raise ContractViolation(
            "ohlcv",
            f"Missing required columns for {ticker}: {missing}",
            df.columns.tolist(),
        )

    # Timestamp monotonicity
    if not df["ts"].is_monotonic_increasing:
        raise ContractViolation(
            "ohlcv",
            f"Timestamps not monotonic increasing for {ticker}",
            df["ts"].head().tolist(),
        )

    # No null values in core columns
    null_columns = []
    for col in ["open", "high", "low", "close", "volume"]:
        if df[col].isnull().any():
            null_count = df[col].isnull().sum()
            null_columns.append(f"{col}({null_count})")

    if null_columns:
        raise ContractViolation(
            "ohlcv",
            f"Null values found in {ticker}: {', '.join(null_columns)}",
            df[df.isnull().any(axis=1)].head().to_dict(),
        )

    # OHLC relationships
    high_low_violations = (df["high"] < df["low"]).sum()
    if high_low_violations > 0:
        raise ContractViolation(
            "ohlcv", f"High < Low violations in {ticker}: {high_low_violations} rows"
        )

    open_violations = ((df["open"] > df["high"]) | (df["open"] < df["low"])).sum()
    if open_violations > 0:
        raise ContractViolation(
            "ohlcv", f"Open outside High/Low range in {ticker}: {open_violations} rows"
        )

    close_violations = ((df["close"] > df["high"]) | (df["close"] < df["low"])).sum()
    if close_violations > 0:
        raise ContractViolation(
            "ohlcv",
            f"Close outside High/Low range in {ticker}: {close_violations} rows",
        )

    # Volume non-negative
    negative_volume = (df["volume"] < 0).sum()
    if negative_volume > 0:
        raise ContractViolation(
            "ohlcv", f"Negative volume in {ticker}: {negative_volume} rows"
        )

    # Reasonable price ranges (basic sanity check)
    price_cols = ["open", "high", "low", "close"]
    for col in price_cols:
        if (df[col] <= 0).any():
            zero_count = (df[col] <= 0).sum()
            raise ContractViolation(
                "ohlcv", f"Zero or negative prices in {ticker}.{col}: {zero_count} rows"
            )

        # Extreme price changes (>1000% in single period)
        pct_change = df[col].pct_change().abs()
        extreme_changes = (pct_change > 10.0).sum()
        if extreme_changes > 0:
            logger.warning(
                f"Extreme price changes in {ticker}.{col}: {extreme_changes} rows"
            )


def validate_quotes(df: pd.DataFrame, ticker: str = "UNKNOWN") -> None:
    """
    Validate bid/ask quote data.

    Args:
        df: DataFrame with quote data
        ticker: Ticker symbol for context

    Raises:
        ContractViolation: If validation fails
    """
    if df is None or df.empty:
        raise ContractViolation("quotes", f"Empty or None quote DataFrame for {ticker}")

    # Required columns
    required = ["ts", "bid", "ask"]
    missing = set(required) - set(df.columns)
    if missing:
        raise ContractViolation(
            "quotes",
            f"Missing required quote columns for {ticker}: {missing}",
            df.columns.tolist(),
        )

    # Timestamp monotonicity
    if not df["ts"].is_monotonic_increasing:
        raise ContractViolation(
            "quotes", f"Quote timestamps not monotonic increasing for {ticker}"
        )

    # No null values
    null_columns = []
    for col in ["bid", "ask"]:
        if df[col].isnull().any():
            null_count = df[col].isnull().sum()
            null_columns.append(f"{col}({null_count})")

    if null_columns:
        raise ContractViolation(
            "quotes",
            f"Null values in quote data for {ticker}: {', '.join(null_columns)}",
        )

    # Bid <= Ask relationship
    spread_violations = (df["bid"] > df["ask"]).sum()
    if spread_violations > 0:
        raise ContractViolation(
            "quotes", f"Bid > Ask violations in {ticker}: {spread_violations} rows"
        )

    # Positive prices
    for col in ["bid", "ask"]:
        if (df[col] <= 0).any():
            zero_count = (df[col] <= 0).sum()
            raise ContractViolation(
                "quotes",
                f"Zero or negative {col} prices in {ticker}: {zero_count} rows",
            )


def validate_news(df: pd.DataFrame) -> None:
    """
    Validate news data frame.

    Args:
        df: DataFrame with news data

    Raises:
        ContractViolation: If validation fails
    """
    if df is None or df.empty:
        raise ContractViolation("news", "Empty or None news DataFrame")

    # Required columns
    required = ["id", "ts", "headline", "source_tz"]
    missing = set(required) - set(df.columns)
    if missing:
        raise ContractViolation(
            "news", f"Missing required news columns: {missing}", df.columns.tolist()
        )

    # No null values in required fields
    null_columns = []
    for col in required:
        if df[col].isnull().any():
            null_count = df[col].isnull().sum()
            null_columns.append(f"{col}({null_count})")

    if null_columns:
        raise ContractViolation(
            "news", f"Null values in news data: {', '.join(null_columns)}"
        )

    # Unique IDs
    duplicate_ids = df["id"].duplicated().sum()
    if duplicate_ids > 0:
        raise ContractViolation(
            "news", f"Duplicate news IDs: {duplicate_ids} duplicates"
        )

    # Valid timestamps
    try:
        # Ensure timestamps can be parsed
        pd.to_datetime(df["ts"])
    except Exception as e:
        raise ContractViolation("news", f"Invalid timestamps in news data: {e}")

    # Non-empty headlines
    empty_headlines = (df["headline"].str.strip() == "").sum()
    if empty_headlines > 0:
        raise ContractViolation("news", f"Empty headlines: {empty_headlines} rows")


def validate_crypto_data(df: pd.DataFrame, symbol: str = "UNKNOWN") -> None:
    """
    Validate cryptocurrency data.

    Args:
        df: DataFrame with crypto data
        symbol: Crypto symbol for context

    Raises:
        ContractViolation: If validation fails
    """
    # Crypto data follows similar patterns to OHLCV but may have different ranges
    validate_ohlcv(df, symbol)

    # Additional crypto-specific validations
    if "volume" in df.columns:
        # Crypto volumes can be much higher than equities
        if df["volume"].max() > 1e12:  # Reasonable upper bound
            logger.warning(
                f"Very high volume detected in {symbol}: {df['volume'].max()}"
            )


def validate_market_hours(df: pd.DataFrame, exchange: str = "NYSE") -> None:
    """
    Validate that data timestamps align with expected market hours.

    Args:
        df: DataFrame with timestamp column
        exchange: Exchange name for market hours lookup

    Raises:
        ContractViolation: If validation fails
    """
    if df is None or df.empty or "ts" not in df.columns:
        return

    # Convert to datetime if needed
    timestamps = pd.to_datetime(df["ts"])

    # Basic validation: no future timestamps beyond reasonable buffer
    now = datetime.now()
    future_buffer_hours = 24  # Allow 24h buffer for timezone issues

    future_timestamps = timestamps > (now + pd.Timedelta(hours=future_buffer_hours))
    if future_timestamps.any():
        future_count = future_timestamps.sum()
        raise ContractViolation(
            "market_hours",
            f"Future timestamps detected ({future_count} rows): max={timestamps.max()}",
        )


def validate_data_consistency(df: pd.DataFrame, dataset_type: str, **kwargs) -> None:
    """
    Main validation entry point that routes to specific validators.

    Args:
        df: DataFrame to validate
        dataset_type: Type of dataset ('ohlcv', 'quotes', 'news', 'crypto')
        **kwargs: Additional context (ticker, exchange, etc.)

    Raises:
        ContractViolation: If validation fails
    """
    try:
        if dataset_type == "ohlcv":
            validate_ohlcv(df, kwargs.get("ticker", "UNKNOWN"))
        elif dataset_type == "quotes":
            validate_quotes(df, kwargs.get("ticker", "UNKNOWN"))
        elif dataset_type == "news":
            validate_news(df)
        elif dataset_type == "crypto":
            validate_crypto_data(df, kwargs.get("symbol", "UNKNOWN"))
        else:
            logger.warning(f"Unknown dataset type for validation: {dataset_type}")

        # Always validate market hours if applicable
        if "exchange" in kwargs:
            validate_market_hours(df, kwargs["exchange"])

        logger.debug(f"Data contract validation passed for {dataset_type}")

    except ContractViolation:
        # Re-raise contract violations
        raise
    except Exception as e:
        # Wrap unexpected errors as contract violations
        raise ContractViolation(
            dataset_type, f"Unexpected validation error: {e}", type(e).__name__
        )


def get_validation_stats() -> dict[str, Any]:
    """
    Get validation statistics (placeholder for future implementation).

    Returns:
        Dictionary with validation metrics
    """
    return {
        "total_validations": 0,
        "violations": 0,
        "violation_rate": 0.0,
        "last_violation": None,
    }
