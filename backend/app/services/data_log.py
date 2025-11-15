# backend/app/services/data_log.py
"""
Conservative data logging system for Ziggy's learning pipeline.
Ensures every live decision is serialized with full context for later analysis.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass
class TradingDecisionRecord:
    """
    Complete record of a trading decision with all context needed for learning.
    """

    timestamp: float
    ticker: str
    regime: str  # bull/bear/neutral/transition
    features_used: dict[str, float]  # all features that went into decision
    signal_name: str
    params_used: dict[str, Any]  # exact parameters used in signal generation
    predicted_prob: float | None  # signal confidence/probability
    position_qty: float  # signed quantity (negative = short)
    stop_price: float | None
    take_profit: float | None
    entry_price: float

    # Outcomes (filled after trade completion)
    outcome_after_1h: float | None = None
    outcome_after_4h: float | None = None
    outcome_after_24h: float | None = None
    exit_price: float | None = None
    fees_paid: float | None = None
    slippage: float | None = None
    exit_reason: str | None = None  # stop/tp/timeout/manual
    realized_pnl: float | None = None

    # Metadata
    rule_version: str = "v1.0"
    signal_version: str = "v1.0"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TradingDecisionRecord:
        """Create from dictionary."""
        return cls(**data)


class TradingDataLogger:
    """
    Append-only logging system with monthly rotation.
    Stores all trading decisions for later analysis and learning.
    """

    def __init__(self, base_path: str = "./data/logs"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_monthly_path(self, timestamp: float | None = None) -> Path:
        """Get the monthly log file path."""
        if timestamp is None:
            timestamp = time.time()

        dt = datetime.fromtimestamp(timestamp)
        monthly_dir = self.base_path / f"{dt.year:04d}-{dt.month:02d}"
        monthly_dir.mkdir(exist_ok=True)

        return monthly_dir / "trading_decisions.parquet"

    def log_decision(self, record: TradingDecisionRecord) -> None:
        """
        Log a trading decision record.
        Uses append-only storage with monthly rotation.
        """
        try:
            monthly_path = self._get_monthly_path(record.timestamp)

            # Convert record to DataFrame row
            df_new = pd.DataFrame([record.to_dict()])

            # Append to existing file or create new one
            if monthly_path.exists():
                df_existing = pd.read_parquet(monthly_path)
                df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            else:
                df_combined = df_new

            # Save with proper compression
            df_combined.to_parquet(monthly_path, compression="snappy", index=False)

        except Exception as e:
            # Fallback to CSV if parquet fails
            csv_path = monthly_path.with_suffix(".csv")
            df_new.to_csv(csv_path, mode="a", header=not csv_path.exists(), index=False)
            print(f"Warning: Parquet save failed, used CSV fallback: {e}")

    def update_outcome(
        self, timestamp: float, ticker: str, outcome_data: dict[str, Any]
    ) -> bool:
        """
        Update the outcome data for a previously logged decision.

        Args:
            timestamp: Original decision timestamp
            ticker: Symbol
            outcome_data: Dict with outcome fields to update

        Returns:
            True if record was found and updated, False otherwise
        """
        try:
            monthly_path = self._get_monthly_path(timestamp)

            if not monthly_path.exists():
                return False

            df = pd.read_parquet(monthly_path)

            # Find the matching record
            mask = (df["timestamp"] == timestamp) & (df["ticker"] == ticker)

            if not mask.any():
                return False

            # Update the outcome fields
            for field, value in outcome_data.items():
                if field in df.columns:
                    df.loc[mask, field] = value

            # Save updated data
            df.to_parquet(monthly_path, compression="snappy", index=False)
            return True

        except Exception as e:
            print(f"Error updating outcome: {e}")
            return False

    def load_window(self, days: int = 90) -> pd.DataFrame:
        """
        Load trading decisions from the last N days.

        Args:
            days: Number of days to look back

        Returns:
            DataFrame with all decisions in the window
        """
        end_time = time.time()
        start_time = end_time - (days * 24 * 3600)

        start_dt = datetime.fromtimestamp(start_time)
        end_dt = datetime.fromtimestamp(end_time)

        all_dfs = []

        # Iterate through months in the window
        current_dt = start_dt.replace(day=1)

        while current_dt <= end_dt:
            monthly_path = (
                self.base_path
                / f"{current_dt.year:04d}-{current_dt.month:02d}"
                / "trading_decisions.parquet"
            )

            if monthly_path.exists():
                try:
                    df_month = pd.read_parquet(monthly_path)

                    # Filter by time window
                    mask = (df_month["timestamp"] >= start_time) & (
                        df_month["timestamp"] <= end_time
                    )
                    df_filtered = df_month[mask]

                    if not df_filtered.empty:
                        all_dfs.append(df_filtered)

                except Exception as e:
                    print(f"Error loading {monthly_path}: {e}")

            # Move to next month
            if current_dt.month == 12:
                current_dt = current_dt.replace(year=current_dt.year + 1, month=1)
            else:
                current_dt = current_dt.replace(month=current_dt.month + 1)

        if all_dfs:
            return pd.concat(all_dfs, ignore_index=True).sort_values("timestamp")
        else:
            return pd.DataFrame()

    def get_summary_stats(self, days: int = 30) -> dict[str, Any]:
        """Get summary statistics for recent trading activity."""
        df = self.load_window(days)

        if df.empty:
            return {
                "total_decisions": 0,
                "period_days": days,
                "avg_decisions_per_day": 0,
            }

        # Basic stats
        total_decisions = len(df)
        unique_tickers = df["ticker"].nunique()

        # Completed trades (have outcome data)
        completed_mask = df["realized_pnl"].notna()
        completed_trades = completed_mask.sum()

        stats = {
            "total_decisions": total_decisions,
            "completed_trades": completed_trades,
            "unique_tickers": unique_tickers,
            "period_days": days,
            "avg_decisions_per_day": total_decisions / max(days, 1),
            "completion_rate": completed_trades / max(total_decisions, 1),
        }

        if completed_trades > 0:
            completed_df = df[completed_mask]

            stats.update(
                {
                    "total_pnl": completed_df["realized_pnl"].sum(),
                    "avg_pnl_per_trade": completed_df["realized_pnl"].mean(),
                    "win_rate": (completed_df["realized_pnl"] > 0).mean(),
                    "avg_fees": (
                        completed_df["fees_paid"].mean()
                        if "fees_paid" in completed_df
                        else 0
                    ),
                    "avg_slippage": (
                        completed_df["slippage"].mean()
                        if "slippage" in completed_df
                        else 0
                    ),
                }
            )

        return stats


# Global logger instance
_global_logger: TradingDataLogger | None = None


def get_logger() -> TradingDataLogger:
    """Get the global trading data logger instance."""
    global _global_logger
    if _global_logger is None:
        _global_logger = TradingDataLogger()
    return _global_logger


def log_trading_decision(
    ticker: str,
    regime: str,
    features: dict[str, float],
    signal_name: str,
    params: dict[str, Any],
    position_qty: float,
    entry_price: float,
    stop_price: float | None = None,
    take_profit: float | None = None,
    predicted_prob: float | None = None,
    rule_version: str = "v1.0",
    signal_version: str = "v1.0",
) -> float:
    """
    Convenience function to log a trading decision.

    Returns:
        Timestamp of the logged decision (for later outcome updates)
    """
    logger = get_logger()

    timestamp = time.time()

    record = TradingDecisionRecord(
        timestamp=timestamp,
        ticker=ticker,
        regime=regime,
        features_used=features,
        signal_name=signal_name,
        params_used=params,
        predicted_prob=predicted_prob,
        position_qty=position_qty,
        entry_price=entry_price,
        stop_price=stop_price,
        take_profit=take_profit,
        rule_version=rule_version,
        signal_version=signal_version,
    )

    logger.log_decision(record)
    return timestamp


def update_trading_outcome(
    decision_timestamp: float,
    ticker: str,
    exit_price: float,
    realized_pnl: float,
    fees_paid: float = 0.0,
    slippage: float = 0.0,
    exit_reason: str = "unknown",
    outcome_1h: float | None = None,
    outcome_4h: float | None = None,
    outcome_24h: float | None = None,
) -> bool:
    """
    Convenience function to update trading outcome data.

    Returns:
        True if the record was found and updated
    """
    logger = get_logger()

    outcome_data = {
        "exit_price": exit_price,
        "realized_pnl": realized_pnl,
        "fees_paid": fees_paid,
        "slippage": slippage,
        "exit_reason": exit_reason,
    }

    if outcome_1h is not None:
        outcome_data["outcome_after_1h"] = outcome_1h
    if outcome_4h is not None:
        outcome_data["outcome_after_4h"] = outcome_4h
    if outcome_24h is not None:
        outcome_data["outcome_after_24h"] = outcome_24h

    return logger.update_outcome(decision_timestamp, ticker, outcome_data)


if __name__ == "__main__":
    # Example usage
    logger = TradingDataLogger()

    # Log a decision
    timestamp = log_trading_decision(
        ticker="AAPL",
        regime="bull",
        features={"rsi": 72.5, "atr": 2.1, "regime_strength": 0.8},
        signal_name="momentum_breakout",
        params={"rsi_threshold": 70, "atr_multiplier": 2.0},
        position_qty=100,
        entry_price=150.25,
        stop_price=148.0,
        take_profit=155.0,
        predicted_prob=0.65,
    )

    # Later, update with outcome
    update_trading_outcome(
        decision_timestamp=timestamp,
        ticker="AAPL",
        exit_price=154.80,
        realized_pnl=455.0,
        fees_paid=2.0,
        slippage=0.05,
        exit_reason="take_profit",
    )

    # Load recent data
    recent_data = logger.load_window(30)
    print(f"Loaded {len(recent_data)} decisions from last 30 days")

    # Get summary
    stats = logger.get_summary_stats(30)
    print("Summary stats:", stats)
