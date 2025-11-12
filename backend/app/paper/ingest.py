"""
Paper Trading Brain Integration - Trade Ingest System

This module handles the flow of trade data from paper trading execution
into Ziggy's brain learning system for future prediction enhancement.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.core.logging import get_logger
from app.models.paper import Trade
from app.paper.features import FeatureComputer


logger = get_logger("ziggy.paper.ingest")


@dataclass
class BrainTradeEvent:
    """Trade event prepared for brain ingestion."""

    trade_id: str
    symbol: str
    features: list[float]
    label: float | None
    timestamp: datetime
    theory_name: str
    metadata: dict[str, Any]


class BrainIngestQueue:
    """In-memory queue for trade events awaiting brain processing."""

    def __init__(self, max_size: int = 10000):
        self.queue: deque[BrainTradeEvent] = deque(maxlen=max_size)
        self.events_total = 0
        self.events_5m = 0
        self.last_5m_timestamp = datetime.utcnow()

    def enqueue(self, event: BrainTradeEvent) -> None:
        """Add trade event to brain queue."""
        self.queue.append(event)
        self.events_total += 1
        self._update_5m_counter()

        logger.debug(
            "Trade event enqueued for brain",
            extra={
                "trade_id": event.trade_id,
                "symbol": event.symbol,
                "features_count": len(event.features),
                "label": event.label,
                "theory": event.theory_name,
                "queue_depth": len(self.queue),
            },
        )

    def drain_batch(self, batch_size: int = 256) -> list[BrainTradeEvent]:
        """Drain a batch of events from the queue."""
        batch = []
        for _ in range(min(batch_size, len(self.queue))):
            if self.queue:
                batch.append(self.queue.popleft())
        return batch

    def get_depth(self) -> int:
        """Get current queue depth."""
        return len(self.queue)

    def get_5m_count(self) -> int:
        """Get count of events in last 5 minutes."""
        self._update_5m_counter()
        return self.events_5m

    def _update_5m_counter(self) -> None:
        """Update 5-minute event counter."""
        now = datetime.utcnow()
        if (now - self.last_5m_timestamp).total_seconds() >= 300:  # 5 minutes
            self.events_5m = 0
            self.last_5m_timestamp = now
        self.events_5m += 1


# Global queue instance
_brain_queue = BrainIngestQueue()


class LearnerMetrics:
    """Metrics for learner processing."""

    def __init__(self):
        self.batches_total = 0
        self.batches_5m = 0
        self.last_5m_timestamp = datetime.utcnow()
        self.last_batch_timestamp: datetime | None = None
        self.learner_available = False
        self.last_error: str | None = None

    def record_batch(self, batch_size: int) -> None:
        """Record a processed batch."""
        self.batches_total += 1
        self._update_5m_counter()
        self.last_batch_timestamp = datetime.utcnow()

        logger.info(
            "Learner batch processed",
            extra={
                "batch_size": batch_size,
                "batches_total": self.batches_total,
                "batches_5m": self.batches_5m,
            },
        )

    def record_error(self, error: str) -> None:
        """Record learner error."""
        self.last_error = error
        logger.error("Learner processing error", extra={"error": error})

    def get_5m_count(self) -> int:
        """Get batches processed in last 5 minutes."""
        self._update_5m_counter()
        return self.batches_5m

    def _update_5m_counter(self) -> None:
        """Update 5-minute batch counter."""
        now = datetime.utcnow()
        if (now - self.last_5m_timestamp).total_seconds() >= 300:  # 5 minutes
            self.batches_5m = 0
            self.last_5m_timestamp = now


# Global metrics instance
_learner_metrics = LearnerMetrics()


async def enqueue_for_brain(trade: Trade) -> None:
    """
    Enqueue trade for brain learning ingestion.

    This is called after each trade is persisted to the database.
    """
    try:
        # Extract features using existing feature computer
        feature_computer = FeatureComputer()

        # Simplified feature extraction for now
        features = [
            float(trade.quantity) if trade.quantity else 0.0,
            float(trade.fill_price) if trade.fill_price else 0.0,
            # Add more features based on existing feature pipeline
        ]

        # Compute label (simplified - should use existing labeling logic)
        label = None
        if trade.realized_pnl is not None:
            label = float(trade.realized_pnl)

        # Create brain event
        event = BrainTradeEvent(
            trade_id=trade.trade_id,
            symbol=trade.ticker,
            features=features,
            label=label,
            timestamp=trade.signal_time,
            theory_name=trade.theory_name,
            metadata={
                "direction": trade.direction,
                "status": trade.status,
                "fill_latency_ms": getattr(trade, "fill_latency_ms", None),
            },
        )

        # Enqueue for brain processing
        _brain_queue.enqueue(event)

        logger.info(
            "Trade enqueued for brain learning",
            extra={
                "evt": "brain_enqueue",
                "trade_id": trade.trade_id,
                "symbol": trade.ticker,
                "features": len(features),
                "label": label,
            },
        )

    except Exception as e:
        logger.error(
            "Failed to enqueue trade for brain",
            extra={"trade_id": getattr(trade, "trade_id", "unknown"), "error": str(e)},
        )


def get_brain_queue_metrics() -> dict[str, Any]:
    """Get current brain queue metrics."""
    return {
        "queue_depth": _brain_queue.get_depth(),
        "events_total": _brain_queue.events_total,
        "events_5m": _brain_queue.get_5m_count(),
    }


def get_learner_metrics() -> dict[str, Any]:
    """Get current learner processing metrics."""
    return {
        "batches_total": _learner_metrics.batches_total,
        "batches_5m": _learner_metrics.get_5m_count(),
        "last_batch_at": (
            _learner_metrics.last_batch_timestamp.isoformat()
            if _learner_metrics.last_batch_timestamp
            else None
        ),
        "learner_available": _learner_metrics.learner_available,
        "last_error": _learner_metrics.last_error,
    }
