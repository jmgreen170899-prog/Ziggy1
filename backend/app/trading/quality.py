"""
Execution Quality Monitor - Action & Execution Layer

Mission: Safety ↑, slippage ↓
Compare fills vs mid/VWAP; track slippage per venue & time bucket.
Industrial-grade execution analytics with detailed performance metrics.
"""

from __future__ import annotations

import json
import logging
import os
import statistics
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)

# Environment configuration
QUALITY_VWAP_WINDOW = int(os.getenv("QUALITY_VWAP_WINDOW", "300"))  # 5 minutes
QUALITY_BUCKET = int(os.getenv("QUALITY_BUCKET", "15"))  # 15 minutes
QUALITY_DATA_PATH = os.getenv("QUALITY_DATA_PATH", "data/trading/quality.json")
QUALITY_RETENTION_DAYS = int(os.getenv("QUALITY_RETENTION_DAYS", "30"))

# Slippage thresholds (basis points)
SLIPPAGE_GOOD_BPS = float(os.getenv("SLIPPAGE_GOOD_BPS", "5"))
SLIPPAGE_WARNING_BPS = float(os.getenv("SLIPPAGE_WARNING_BPS", "15"))
SLIPPAGE_POOR_BPS = float(os.getenv("SLIPPAGE_POOR_BPS", "30"))


@dataclass
class MarketDataPoint:
    """Market data point for VWAP calculation."""

    price: float
    volume: float
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return {"price": self.price, "volume": self.volume, "timestamp": self.timestamp}


@dataclass
class ExecutionRecord:
    """Record of an individual execution."""

    execution_id: str
    symbol: str
    side: str  # buy/sell
    quantity: float
    fill_price: float
    fill_time: str
    venue: str

    # Market context
    mid_at_submit: float | None = None
    mid_at_fill: float | None = None
    vwap_window: float | None = None
    submit_time: str | None = None

    # Calculated metrics
    slippage_vs_mid_submit_bps: float | None = None
    slippage_vs_mid_fill_bps: float | None = None
    slippage_vs_vwap_bps: float | None = None
    market_impact_bps: float | None = None

    # Additional context
    order_type: str = "market"
    time_to_fill_ms: int | None = None
    commission: float = 0.0

    def calculate_slippage(self) -> None:
        """Calculate all slippage metrics."""
        if self.mid_at_submit and self.fill_price:
            self.slippage_vs_mid_submit_bps = slippage_bps(
                self.fill_price, self.mid_at_submit, self.side
            )

        if self.mid_at_fill and self.fill_price:
            self.slippage_vs_mid_fill_bps = slippage_bps(
                self.fill_price, self.mid_at_fill, self.side
            )

        if self.vwap_window and self.fill_price:
            self.slippage_vs_vwap_bps = slippage_bps(
                self.fill_price, self.vwap_window, self.side
            )

        # Market impact (difference between submit and fill mid)
        if self.mid_at_submit and self.mid_at_fill:
            if self.side.lower() == "buy":
                self.market_impact_bps = (
                    10000.0
                    * (self.mid_at_fill - self.mid_at_submit)
                    / self.mid_at_submit
                )
            else:
                self.market_impact_bps = (
                    10000.0
                    * (self.mid_at_submit - self.mid_at_fill)
                    / self.mid_at_submit
                )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API/logging."""
        return {
            "execution_id": self.execution_id,
            "symbol": self.symbol,
            "side": self.side,
            "quantity": self.quantity,
            "fill_price": self.fill_price,
            "fill_time": self.fill_time,
            "venue": self.venue,
            "mid_at_submit": self.mid_at_submit,
            "mid_at_fill": self.mid_at_fill,
            "vwap_window": self.vwap_window,
            "submit_time": self.submit_time,
            "slippage_vs_mid_submit_bps": self.slippage_vs_mid_submit_bps,
            "slippage_vs_mid_fill_bps": self.slippage_vs_mid_fill_bps,
            "slippage_vs_vwap_bps": self.slippage_vs_vwap_bps,
            "market_impact_bps": self.market_impact_bps,
            "order_type": self.order_type,
            "time_to_fill_ms": self.time_to_fill_ms,
            "commission": self.commission,
        }


@dataclass
class QualityStats:
    """Aggregated quality statistics for a bucket."""

    bucket_start: str
    bucket_end: str
    venue: str
    symbol: str

    execution_count: int = 0
    total_volume: float = 0.0
    avg_slippage_vs_mid_bps: float = 0.0
    avg_slippage_vs_vwap_bps: float = 0.0
    avg_market_impact_bps: float = 0.0

    slippage_percentiles: dict[str, float] = field(default_factory=dict)
    worst_execution: str | None = None
    best_execution: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "bucket_start": self.bucket_start,
            "bucket_end": self.bucket_end,
            "venue": self.venue,
            "symbol": self.symbol,
            "execution_count": self.execution_count,
            "total_volume": self.total_volume,
            "avg_slippage_vs_mid_bps": self.avg_slippage_vs_mid_bps,
            "avg_slippage_vs_vwap_bps": self.avg_slippage_vs_vwap_bps,
            "avg_market_impact_bps": self.avg_market_impact_bps,
            "slippage_percentiles": self.slippage_percentiles,
            "worst_execution": self.worst_execution,
            "best_execution": self.best_execution,
        }


class QualityMonitor:
    """
    Execution quality monitor for tracking slippage and performance.

    Features:
    - Real-time VWAP calculation
    - Slippage tracking vs mid and VWAP
    - Venue performance comparison
    - Time-bucketed statistics
    - Market impact analysis
    """

    def __init__(self):
        self.executions: list[ExecutionRecord] = []
        self.market_data: dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.quality_stats: dict[tuple[str, str, str], QualityStats] = (
            {}
        )  # (venue, symbol, bucket)
        self._load_state()

    def record_market_data(
        self, symbol: str, price: float, volume: float, timestamp: str | None = None
    ) -> None:
        """Record market data point for VWAP calculation."""
        if timestamp is None:
            timestamp = datetime.now(UTC).isoformat()

        data_point = MarketDataPoint(price, volume, timestamp)
        self.market_data[symbol].append(data_point)

    def record_execution(
        self,
        execution_id: str,
        symbol: str,
        side: str,
        quantity: float,
        fill_price: float,
        venue: str,
        submit_time: str | None = None,
        fill_time: str | None = None,
        order_type: str = "market",
        commission: float = 0.0,
    ) -> ExecutionRecord:
        """
        Record an execution and calculate quality metrics.

        Args:
            execution_id: Unique execution identifier
            symbol: Trading symbol
            side: "buy" or "sell"
            quantity: Shares executed
            fill_price: Execution price
            venue: Execution venue
            submit_time: Order submission time (ISO format)
            fill_time: Execution time (ISO format)
            order_type: Order type
            commission: Commission paid

        Returns:
            ExecutionRecord with calculated metrics
        """
        if fill_time is None:
            fill_time = datetime.now(UTC).isoformat()

        if submit_time is None:
            submit_time = fill_time

        # Create execution record
        execution = ExecutionRecord(
            execution_id=execution_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            fill_price=fill_price,
            fill_time=fill_time,
            venue=venue,
            submit_time=submit_time,
            order_type=order_type,
            commission=commission,
        )

        # Calculate market context
        self._calculate_market_context(execution)

        # Calculate slippage metrics
        execution.calculate_slippage()

        # Calculate time to fill
        if submit_time and fill_time:
            try:
                submit_dt = datetime.fromisoformat(submit_time.replace("Z", "+00:00"))
                fill_dt = datetime.fromisoformat(fill_time.replace("Z", "+00:00"))
                execution.time_to_fill_ms = int(
                    (fill_dt - submit_dt).total_seconds() * 1000
                )
            except Exception as e:
                logger.warning(f"Failed to calculate time to fill: {e}")

        # Store execution
        self.executions.append(execution)

        # Update statistics
        self._update_quality_stats(execution)

        # Cleanup old data
        self._cleanup_old_data()

        logger.info(
            f"Recorded execution {execution_id}: {symbol} {side} {quantity} @ {fill_price}"
        )
        return execution

    def _calculate_market_context(self, execution: ExecutionRecord) -> None:
        """Calculate market context (mid prices, VWAP) for execution."""
        try:
            # Get current market data
            symbol_data = self.market_data.get(execution.symbol, deque())

            if not symbol_data:
                logger.warning(f"No market data available for {execution.symbol}")
                return

            # Find mid price at fill time (use most recent)
            fill_dt = datetime.fromisoformat(execution.fill_time.replace("Z", "+00:00"))

            # Use most recent market data point as mid at fill
            if symbol_data:
                execution.mid_at_fill = symbol_data[-1].price

            # For mid at submit, try to find data point closest to submit time
            if execution.submit_time:
                submit_dt = datetime.fromisoformat(
                    execution.submit_time.replace("Z", "+00:00")
                )

                closest_data = None
                min_time_diff = float("inf")

                for data_point in symbol_data:
                    data_dt = datetime.fromisoformat(
                        data_point.timestamp.replace("Z", "+00:00")
                    )
                    time_diff = abs((data_dt - submit_dt).total_seconds())

                    if time_diff < min_time_diff:
                        min_time_diff = time_diff
                        closest_data = data_point

                if closest_data:
                    execution.mid_at_submit = closest_data.price
            else:
                execution.mid_at_submit = execution.mid_at_fill

            # Calculate VWAP over window
            execution.vwap_window = self._calculate_vwap(
                symbol_data, fill_dt, QUALITY_VWAP_WINDOW
            )

        except Exception as e:
            logger.error(f"Failed to calculate market context: {e}")

    def _calculate_vwap(
        self, symbol_data: deque, reference_time: datetime, window_seconds: int
    ) -> float | None:
        """Calculate VWAP over specified window."""
        try:
            start_time = reference_time - timedelta(seconds=window_seconds)

            total_value = 0.0
            total_volume = 0.0

            for data_point in symbol_data:
                data_time = datetime.fromisoformat(
                    data_point.timestamp.replace("Z", "+00:00")
                )

                if start_time <= data_time <= reference_time:
                    total_value += data_point.price * data_point.volume
                    total_volume += data_point.volume

            if total_volume > 0:
                return total_value / total_volume
            else:
                return None

        except Exception as e:
            logger.error(f"VWAP calculation failed: {e}")
            return None

    def _update_quality_stats(self, execution: ExecutionRecord) -> None:
        """Update aggregated quality statistics."""
        try:
            # Determine bucket
            fill_dt = datetime.fromisoformat(execution.fill_time.replace("Z", "+00:00"))
            bucket_start = self._get_bucket_start(fill_dt, QUALITY_BUCKET)
            bucket_end = bucket_start + timedelta(minutes=QUALITY_BUCKET)

            bucket_key = (execution.venue, execution.symbol, bucket_start.isoformat())

            # Get or create stats
            if bucket_key not in self.quality_stats:
                self.quality_stats[bucket_key] = QualityStats(
                    bucket_start=bucket_start.isoformat(),
                    bucket_end=bucket_end.isoformat(),
                    venue=execution.venue,
                    symbol=execution.symbol,
                )

            stats = self.quality_stats[bucket_key]

            # Update aggregate metrics
            old_count = stats.execution_count
            new_count = old_count + 1

            stats.execution_count = new_count
            stats.total_volume += abs(execution.quantity)

            # Update averages
            if execution.slippage_vs_mid_submit_bps is not None:
                stats.avg_slippage_vs_mid_bps = (
                    stats.avg_slippage_vs_mid_bps * old_count
                    + execution.slippage_vs_mid_submit_bps
                ) / new_count

            if execution.slippage_vs_vwap_bps is not None:
                stats.avg_slippage_vs_vwap_bps = (
                    stats.avg_slippage_vs_vwap_bps * old_count
                    + execution.slippage_vs_vwap_bps
                ) / new_count

            if execution.market_impact_bps is not None:
                stats.avg_market_impact_bps = (
                    stats.avg_market_impact_bps * old_count
                    + execution.market_impact_bps
                ) / new_count

            # Track best/worst executions
            if execution.slippage_vs_mid_submit_bps is not None:
                if (
                    stats.worst_execution is None
                    or execution.slippage_vs_mid_submit_bps
                    > self._get_execution_slippage(stats.worst_execution)
                ):
                    stats.worst_execution = execution.execution_id

                if (
                    stats.best_execution is None
                    or execution.slippage_vs_mid_submit_bps
                    < self._get_execution_slippage(stats.best_execution)
                ):
                    stats.best_execution = execution.execution_id

        except Exception as e:
            logger.error(f"Failed to update quality stats: {e}")

    def _get_bucket_start(self, timestamp: datetime, bucket_minutes: int) -> datetime:
        """Get bucket start time for given timestamp."""
        # Round down to nearest bucket
        minutes = (timestamp.minute // bucket_minutes) * bucket_minutes
        return timestamp.replace(minute=minutes, second=0, microsecond=0)

    def _get_execution_slippage(self, execution_id: str) -> float:
        """Get slippage for execution ID."""
        for execution in self.executions:
            if execution.execution_id == execution_id:
                return execution.slippage_vs_mid_submit_bps or 0.0
        return 0.0

    def get_quality_stats(
        self, venue: str | None = None, symbol: str | None = None, hours: int = 24
    ) -> list[dict[str, Any]]:
        """
        Get quality statistics for specified filters.

        Args:
            venue: Filter by venue (optional)
            symbol: Filter by symbol (optional)
            hours: Hours of history to include

        Returns:
            List of quality statistics dictionaries
        """
        cutoff_time = datetime.now(UTC) - timedelta(hours=hours)
        results = []

        for (
            stat_venue,
            stat_symbol,
            bucket_start_str,
        ), stats in self.quality_stats.items():
            bucket_start = datetime.fromisoformat(
                bucket_start_str.replace("Z", "+00:00")
            )

            if bucket_start < cutoff_time:
                continue

            if venue and stat_venue != venue:
                continue

            if symbol and stat_symbol != symbol:
                continue

            # Calculate percentiles for this bucket
            bucket_executions = [
                exec
                for exec in self.executions
                if (
                    exec.venue == stat_venue
                    and exec.symbol == stat_symbol
                    and exec.slippage_vs_mid_submit_bps is not None
                    and bucket_start
                    <= datetime.fromisoformat(exec.fill_time.replace("Z", "+00:00"))
                    < bucket_start + timedelta(minutes=QUALITY_BUCKET)
                )
            ]

            if bucket_executions:
                slippages = [
                    exec.slippage_vs_mid_submit_bps for exec in bucket_executions
                ]
                stats.slippage_percentiles = {
                    "p50": statistics.median(slippages),
                    "p75": (
                        statistics.quantiles(slippages, n=4)[2]
                        if len(slippages) >= 4
                        else statistics.median(slippages)
                    ),
                    "p90": (
                        statistics.quantiles(slippages, n=10)[8]
                        if len(slippages) >= 10
                        else max(slippages)
                    ),
                    "p99": (
                        statistics.quantiles(slippages, n=100)[98]
                        if len(slippages) >= 100
                        else max(slippages)
                    ),
                }

            results.append(stats.to_dict())

        # Sort by bucket start time
        results.sort(key=lambda x: x["bucket_start"], reverse=True)
        return results

    def get_venue_performance(self, hours: int = 24) -> dict[str, dict[str, Any]]:
        """Get performance comparison across venues."""
        venue_stats = defaultdict(
            lambda: {
                "execution_count": 0,
                "total_volume": 0.0,
                "avg_slippage_bps": 0.0,
                "slippages": [],
            }
        )

        cutoff_time = datetime.now(UTC) - timedelta(hours=hours)

        for execution in self.executions:
            exec_time = datetime.fromisoformat(
                execution.fill_time.replace("Z", "+00:00")
            )

            if exec_time < cutoff_time:
                continue

            if execution.slippage_vs_mid_submit_bps is None:
                continue

            venue = execution.venue
            stats = venue_stats[venue]

            stats["execution_count"] += 1
            stats["total_volume"] += abs(execution.quantity)
            stats["slippages"].append(execution.slippage_vs_mid_submit_bps)

        # Calculate aggregates
        for venue, stats in venue_stats.items():
            if stats["slippages"]:
                stats["avg_slippage_bps"] = statistics.mean(stats["slippages"])
                stats["median_slippage_bps"] = statistics.median(stats["slippages"])
                stats["p90_slippage_bps"] = (
                    statistics.quantiles(stats["slippages"], n=10)[8]
                    if len(stats["slippages"]) >= 10
                    else max(stats["slippages"])
                )

                # Quality rating
                avg_slip = stats["avg_slippage_bps"]
                if avg_slip <= SLIPPAGE_GOOD_BPS:
                    stats["quality_rating"] = "excellent"
                elif avg_slip <= SLIPPAGE_WARNING_BPS:
                    stats["quality_rating"] = "good"
                elif avg_slip <= SLIPPAGE_POOR_BPS:
                    stats["quality_rating"] = "fair"
                else:
                    stats["quality_rating"] = "poor"

            # Remove raw slippage list for API response
            del stats["slippages"]

        return dict(venue_stats)

    def get_execution_details(self, execution_id: str) -> dict[str, Any] | None:
        """Get detailed information for specific execution."""
        for execution in self.executions:
            if execution.execution_id == execution_id:
                return execution.to_dict()
        return None

    def _cleanup_old_data(self) -> None:
        """Clean up old execution records and market data."""
        cutoff_time = datetime.now(UTC) - timedelta(days=QUALITY_RETENTION_DAYS)

        # Clean executions
        self.executions = [
            exec
            for exec in self.executions
            if datetime.fromisoformat(exec.fill_time.replace("Z", "+00:00"))
            > cutoff_time
        ]

        # Clean quality stats
        old_keys = []
        for key, stats in self.quality_stats.items():
            bucket_start = datetime.fromisoformat(
                stats.bucket_start.replace("Z", "+00:00")
            )
            if bucket_start < cutoff_time:
                old_keys.append(key)

        for key in old_keys:
            del self.quality_stats[key]

        # Clean market data (keep last 1000 points per symbol)
        # Already handled by deque maxlen

    def _save_state(self) -> None:
        """Save state to disk."""
        try:
            data = {
                "executions": [
                    exec.to_dict() for exec in self.executions[-1000:]
                ],  # Last 1000 executions
                "quality_stats": {
                    f"{venue}|{symbol}|{bucket}": stats.to_dict()
                    for (venue, symbol, bucket), stats in self.quality_stats.items()
                },
                "saved_at": datetime.now(UTC).isoformat(),
            }

            Path(QUALITY_DATA_PATH).parent.mkdir(parents=True, exist_ok=True)
            with open(QUALITY_DATA_PATH, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save quality state: {e}")

    def _load_state(self) -> None:
        """Load state from disk."""
        try:
            if Path(QUALITY_DATA_PATH).exists():
                with open(QUALITY_DATA_PATH) as f:
                    data = json.load(f)

                # Load executions
                for exec_data in data.get("executions", []):
                    exec = ExecutionRecord(**exec_data)
                    self.executions.append(exec)

                # Load quality stats
                for key_str, stats_data in data.get("quality_stats", {}).items():
                    venue, symbol, bucket = key_str.split("|", 2)
                    key = (venue, symbol, bucket)
                    stats = QualityStats(**stats_data)
                    self.quality_stats[key] = stats

                logger.info("Loaded quality monitor state from disk")

        except Exception as e:
            logger.warning(f"Failed to load quality state: {e}")


# Global quality monitor instance
quality_monitor = QualityMonitor()


# Convenience functions
def slippage_bps(fill_price: float, reference_price: float, side: str = "buy") -> float:
    """
    Calculate slippage in basis points.

    Args:
        fill_price: Actual execution price
        reference_price: Reference price (mid, VWAP, etc.)
        side: "buy" or "sell"

    Returns:
        Slippage in basis points (positive = adverse, negative = favorable)
    """
    if reference_price <= 0:
        return 0.0

    if side.lower() == "buy":
        # For buys, paying more than reference is adverse slippage
        return 10000.0 * (fill_price - reference_price) / reference_price
    else:
        # For sells, receiving less than reference is adverse slippage
        return 10000.0 * (reference_price - fill_price) / reference_price


def record_execution(
    execution_id: str,
    symbol: str,
    side: str,
    quantity: float,
    fill_price: float,
    venue: str,
    **kwargs,
) -> ExecutionRecord:
    """Record execution and calculate quality metrics."""
    return quality_monitor.record_execution(
        execution_id, symbol, side, quantity, fill_price, venue, **kwargs
    )


def record_market_data(symbol: str, price: float, volume: float) -> None:
    """Record market data for VWAP calculation."""
    quality_monitor.record_market_data(symbol, price, volume)


def get_quality_report(
    venue: str | None = None, symbol: str | None = None
) -> dict[str, Any]:
    """Get comprehensive quality report."""
    stats = quality_monitor.get_quality_stats(venue, symbol)
    venue_performance = quality_monitor.get_venue_performance()

    return {
        "bucket_stats": stats,
        "venue_performance": venue_performance,
        "generated_at": datetime.now(UTC).isoformat(),
    }
