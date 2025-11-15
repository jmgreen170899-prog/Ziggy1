"""
Labels generation for ZiggyAI paper trading lab.

This module generates forward-looking labels for trades including
future returns at various horizons and trade outcome classification.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from app.core.logging import get_logger
from app.paper.features import PriceData


logger = get_logger("ziggy.labels")


@dataclass
class TradeLabel:
    """Label for a trade at various time horizons."""

    symbol: str
    entry_time: datetime
    entry_price: float
    side: str  # "BUY" or "SELL"

    # Forward returns at different horizons
    return_5m: float | None = None  # 5-minute forward return
    return_15m: float | None = None  # 15-minute forward return
    return_60m: float | None = None  # 60-minute forward return

    # Direction classification
    direction_5m: str | None = None  # "up", "down", "flat"
    direction_15m: str | None = None
    direction_60m: str | None = None

    # Trade outcome metrics
    max_favorable_excursion: float | None = None  # Best price achieved
    max_adverse_excursion: float | None = None  # Worst price achieved

    # Realized outcome (when trade is closed)
    exit_time: datetime | None = None
    exit_price: float | None = None
    realized_return: float | None = None
    hold_duration_mins: int | None = None


@dataclass
class CalibrationMetrics:
    """Calibration metrics for model predictions."""

    predicted_probability: float
    actual_outcome: bool  # True if prediction was correct
    confidence_bucket: str  # e.g., "0.7-0.8"
    horizon_mins: int


class LabelGenerator:
    """Generates labels for trades and predictions."""

    def __init__(
        self, horizons_mins: list[int] | None = None, direction_threshold: float = 0.001
    ):  # 0.1% threshold for direction
        self.horizons_mins = horizons_mins or [5, 15, 60]
        self.direction_threshold = direction_threshold
        self.price_history: dict[str, list[PriceData]] = {}

        logger.info(
            "LabelGenerator initialized",
            extra={
                "horizons_mins": self.horizons_mins,
                "direction_threshold": direction_threshold,
            },
        )

    def add_price_data(self, price_data: PriceData) -> None:
        """Add price data for label generation."""
        if price_data.symbol not in self.price_history:
            self.price_history[price_data.symbol] = []

        self.price_history[price_data.symbol].append(price_data)

        # Keep only recent data (e.g., last 500 points)
        if len(self.price_history[price_data.symbol]) > 500:
            self.price_history[price_data.symbol] = self.price_history[
                price_data.symbol
            ][-500:]

    def generate_trade_label(
        self, symbol: str, entry_time: datetime, entry_price: float, side: str
    ) -> TradeLabel:
        """
        Generate labels for a trade.

        Args:
            symbol: Trading symbol
            entry_time: Trade entry timestamp
            entry_price: Entry price
            side: Trade side ("BUY" or "SELL")

        Returns:
            TradeLabel with forward returns and metrics
        """
        label = TradeLabel(
            symbol=symbol, entry_time=entry_time, entry_price=entry_price, side=side
        )

        if symbol not in self.price_history:
            return label

        price_data = self.price_history[symbol]

        # Find the price data point closest to entry time
        entry_idx = self._find_closest_price_index(price_data, entry_time)
        if entry_idx is None:
            return label

        # Calculate forward returns at each horizon
        for horizon_mins in self.horizons_mins:
            future_time = entry_time + timedelta(minutes=horizon_mins)
            future_idx = self._find_closest_price_index(price_data, future_time)

            if future_idx is not None and future_idx > entry_idx:
                future_price = price_data[future_idx].close

                # Calculate return based on trade side
                if side == "BUY":
                    forward_return = (future_price - entry_price) / entry_price
                else:  # SELL
                    forward_return = (entry_price - future_price) / entry_price

                # Store return
                if horizon_mins == 5:
                    label.return_5m = forward_return
                    label.direction_5m = self._classify_direction(forward_return)
                elif horizon_mins == 15:
                    label.return_15m = forward_return
                    label.direction_15m = self._classify_direction(forward_return)
                elif horizon_mins == 60:
                    label.return_60m = forward_return
                    label.direction_60m = self._classify_direction(forward_return)

        # Calculate max favorable/adverse excursions
        label.max_favorable_excursion, label.max_adverse_excursion = (
            self._calculate_excursions(price_data, entry_idx, entry_price, side)
        )

        return label

    def update_trade_outcome(
        self, label: TradeLabel, exit_time: datetime, exit_price: float
    ) -> TradeLabel:
        """
        Update trade label with actual exit information.

        Args:
            label: Existing trade label
            exit_time: Actual exit timestamp
            exit_price: Actual exit price

        Returns:
            Updated TradeLabel
        """
        label.exit_time = exit_time
        label.exit_price = exit_price

        # Calculate realized return
        if label.side == "BUY":
            label.realized_return = (exit_price - label.entry_price) / label.entry_price
        else:  # SELL
            label.realized_return = (label.entry_price - exit_price) / label.entry_price

        # Calculate hold duration
        duration = exit_time - label.entry_time
        label.hold_duration_mins = int(duration.total_seconds() / 60)

        return label

    def generate_calibration_metrics(
        self, predictions: list[dict[str, Any]], actuals: list[dict[str, Any]]
    ) -> list[CalibrationMetrics]:
        """
        Generate calibration metrics for model predictions.

        Args:
            predictions: List of prediction dicts with 'probability', 'confidence', 'horizon'
            actuals: List of actual outcome dicts with 'outcome', 'horizon'

        Returns:
            List of CalibrationMetrics
        """
        calibration_metrics = []

        for pred, actual in zip(predictions, actuals):
            if pred.get("horizon") != actual.get("horizon"):
                continue

            probability = pred.get("probability", 0.5)
            confidence = pred.get("confidence", 0.5)
            outcome = actual.get("outcome", False)
            horizon = pred.get("horizon", 5)

            # Determine confidence bucket
            confidence_bucket = self._get_confidence_bucket(confidence)

            calibration_metrics.append(
                CalibrationMetrics(
                    predicted_probability=probability,
                    actual_outcome=outcome,
                    confidence_bucket=confidence_bucket,
                    horizon_mins=horizon,
                )
            )

        return calibration_metrics

    def compute_calibration_curve(
        self, metrics: list[CalibrationMetrics], horizon_mins: int | None = None
    ) -> dict[str, dict[str, float]]:
        """
        Compute calibration curve (reliability diagram).

        Args:
            metrics: List of calibration metrics
            horizon_mins: Optional horizon filter

        Returns:
            Dict mapping confidence buckets to calibration stats
        """
        # Filter by horizon if specified
        if horizon_mins is not None:
            metrics = [m for m in metrics if m.horizon_mins == horizon_mins]

        # Group by confidence bucket
        buckets: dict[str, list[CalibrationMetrics]] = {}
        for metric in metrics:
            bucket = metric.confidence_bucket
            if bucket not in buckets:
                buckets[bucket] = []
            buckets[bucket].append(metric)

        # Compute calibration stats for each bucket
        calibration_curve = {}
        for bucket, bucket_metrics in buckets.items():
            if not bucket_metrics:
                continue

            # Average predicted probability
            avg_predicted = sum(m.predicted_probability for m in bucket_metrics) / len(
                bucket_metrics
            )

            # Actual frequency of positive outcomes
            actual_frequency = sum(1 for m in bucket_metrics if m.actual_outcome) / len(
                bucket_metrics
            )

            # Calibration error (difference between predicted and actual)
            calibration_error = abs(avg_predicted - actual_frequency)

            calibration_curve[bucket] = {
                "avg_predicted": avg_predicted,
                "actual_frequency": actual_frequency,
                "calibration_error": calibration_error,
                "count": len(bucket_metrics),
            }

        return calibration_curve

    def compute_ece(self, calibration_curve: dict[str, dict[str, float]]) -> float:
        """
        Compute Expected Calibration Error (ECE).

        Args:
            calibration_curve: Calibration curve from compute_calibration_curve

        Returns:
            ECE value
        """
        total_samples = sum(bucket["count"] for bucket in calibration_curve.values())
        if total_samples == 0:
            return 0.0

        weighted_error = 0.0
        for bucket_stats in calibration_curve.values():
            weight = bucket_stats["count"] / total_samples
            error = bucket_stats["calibration_error"]
            weighted_error += weight * error

        return weighted_error

    def _find_closest_price_index(
        self, price_data: list[PriceData], target_time: datetime
    ) -> int | None:
        """Find index of price data closest to target time."""
        if not price_data:
            return None

        min_diff = float("inf")
        closest_idx = None

        for i, data in enumerate(price_data):
            diff = abs((data.timestamp - target_time).total_seconds())
            if diff < min_diff:
                min_diff = diff
                closest_idx = i

        return closest_idx

    def _classify_direction(self, return_value: float) -> str:
        """Classify return direction based on threshold."""
        if return_value > self.direction_threshold:
            return "up"
        elif return_value < -self.direction_threshold:
            return "down"
        else:
            return "flat"

    def _calculate_excursions(
        self, price_data: list[PriceData], entry_idx: int, entry_price: float, side: str
    ) -> tuple[float | None, float | None]:
        """Calculate max favorable and adverse excursions."""
        if entry_idx >= len(price_data) - 1:
            return None, None

        max_favorable = 0.0
        max_adverse = 0.0

        # Look at prices after entry
        for i in range(entry_idx + 1, len(price_data)):
            price = price_data[i].close

            if side == "BUY":
                # For long trades: favorable = higher prices, adverse = lower prices
                excursion = (price - entry_price) / entry_price
            else:  # SELL
                # For short trades: favorable = lower prices, adverse = higher prices
                excursion = (entry_price - price) / entry_price

            max_favorable = max(max_favorable, excursion)
            max_adverse = min(max_adverse, excursion)

        return max_favorable, abs(max_adverse)

    def _get_confidence_bucket(self, confidence: float) -> str:
        """Get confidence bucket for calibration analysis."""
        if confidence < 0.1:
            return "0.0-0.1"
        elif confidence < 0.2:
            return "0.1-0.2"
        elif confidence < 0.3:
            return "0.2-0.3"
        elif confidence < 0.4:
            return "0.3-0.4"
        elif confidence < 0.5:
            return "0.4-0.5"
        elif confidence < 0.6:
            return "0.5-0.6"
        elif confidence < 0.7:
            return "0.6-0.7"
        elif confidence < 0.8:
            return "0.7-0.8"
        elif confidence < 0.9:
            return "0.8-0.9"
        else:
            return "0.9-1.0"


# Global label generator instance
label_generator = LabelGenerator()
