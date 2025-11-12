"""
Paper Trading Learner Gateway

Background task that drains the brain queue and feeds trade data
to Ziggy's online learning system for improved future predictions.
"""

from __future__ import annotations

import asyncio
import contextlib
import time
import traceback
from typing import Any, cast

from app.core.logging import get_logger
from app.paper.ingest import (
    BrainTradeEvent,
    _brain_queue,
    _learner_metrics,
    get_brain_queue_metrics,
    get_learner_metrics,
)


logger = get_logger("ziggy.paper.learner_gateway")


class LearnerGateway:
    """Gateway between paper trading and brain learning system."""

    def __init__(self, batch_size: int = 256, drain_interval: float = 5.0):
        self.batch_size = batch_size
        self.drain_interval = drain_interval
        self.is_running = False
        self.task: asyncio.Task | None = None
        self._learner: Any | None = None
        self._last_checkpoint_ts: float = 0.0
        self._checkpoint_interval_s: float = 600.0  # 10 minutes

    async def start(self) -> None:
        """Start the learner gateway background task."""
        if self.is_running:
            logger.warning("Learner gateway already running")
            return

        self.is_running = True
        self.task = asyncio.create_task(self._drain_loop())

        logger.info(
            "Learner gateway started",
            extra={"batch_size": self.batch_size, "drain_interval": self.drain_interval},
        )

    async def stop(self) -> None:
        """Stop the learner gateway."""
        if not self.is_running:
            return

        self.is_running = False

        if self.task and not self.task.done():
            self.task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.task

        logger.info("Learner gateway stopped")

    async def _drain_loop(self) -> None:
        """Main drain loop that processes brain queue."""
        logger.info("Starting learner gateway drain loop")

        try:
            while self.is_running:
                try:
                    # Drain a batch from the queue
                    batch = _brain_queue.drain_batch(self.batch_size)

                    if batch:
                        await self._process_batch(batch)

                    # Wait before next drain cycle
                    await asyncio.sleep(self.drain_interval)

                except Exception as e:
                    error_msg = f"Error in learner drain loop: {e!s}"
                    logger.error(
                        error_msg, extra={"error": str(e), "traceback": traceback.format_exc()}
                    )
                    _learner_metrics.record_error(error_msg)

                    # Brief pause before retrying
                    await asyncio.sleep(1.0)

        except asyncio.CancelledError:
            logger.info("Learner gateway drain loop cancelled")
            raise

    async def _process_batch(self, batch: list[BrainTradeEvent]) -> None:
        """Process a batch of trade events."""
        if not batch:
            return

        logger.info(
            "Processing learner batch",
            extra={
                "evt": "learner_partial_fit",
                "batch": len(batch),
                "queue_left": _brain_queue.get_depth(),
            },
        )

        try:
            # Try to get or create the online learner (auto-selects backend, falls back to simple)
            learner = self._get_online_learner()

            # Filter events that have labels to build aligned X/y
            labeled = [evt for evt in batch if evt.label is not None]
            if not labeled:
                logger.debug("No labeled events in batch; skipping learner update")
                _learner_metrics.record_batch(0)
                return

            # Prepare numpy arrays
            import numpy as np

            X = np.array([evt.features for evt in labeled], dtype=float)
            y = np.array([float(cast(float, evt.label)) for evt in labeled], dtype=float)

            features_dim = int(X.shape[1]) if X.ndim == 2 and X.size else 0

            if learner is not None and X.size and y.size and len(X) == len(y):
                # Run partial_fit off the event loop to avoid blocking
                await asyncio.to_thread(learner.partial_fit, X, y)
                _learner_metrics.learner_available = True

                logger.info(
                    "Batch processed by online learner",
                    extra={
                        "batch_size": len(labeled),
                        "features_dim": features_dim,
                        "labels_count": len(labeled),
                        "backend": getattr(learner, "backend", "unknown"),
                    },
                )
                # Best-effort periodic checkpoint stub
                self._maybe_checkpoint(learner)
            else:
                # No learner available - count the events but don't process
                _learner_metrics.learner_available = False
                logger.debug(
                    "Learner not present or empty batch—ingest counted only",
                    extra={"batch_size": len(batch)},
                )

            # Record the batch processing
            _learner_metrics.record_batch(len(labeled))

        except Exception as e:
            error_msg = f"Failed to process learner batch: {e!s}"
            logger.error(error_msg, extra={"batch_size": len(batch), "error": str(e)})
            _learner_metrics.record_error(error_msg)

    def _get_online_learner(self) -> Any | None:
        """Get the online learner instance if available."""
        try:
            # Lazy import to avoid heavy deps at module import time
            from app.paper.learner import OnlineLearner

            if self._learner is None:
                # Auto-select backend; will fall back to simple if sklearn/torch not available
                self._learner = OnlineLearner(backend="auto")
            return self._learner
        except ImportError:
            return None

    def _maybe_checkpoint(self, learner: Any) -> None:
        """Periodically checkpoint the learner (stub: log-only).

        Intentionally minimal to avoid IO churn; replace with real persistence if needed.
        """
        now = time.time()
        if (now - self._last_checkpoint_ts) >= self._checkpoint_interval_s:
            self._last_checkpoint_ts = now
            with contextlib.suppress(Exception):
                logger.info(
                    "Learner checkpoint (stub)",
                    extra={"backend": getattr(learner, "backend", "unknown")},
                )

    def get_status(self) -> dict[str, Any]:
        """Get gateway status."""
        return {
            "is_running": self.is_running,
            "batch_size": self.batch_size,
            "drain_interval": self.drain_interval,
            "queue_metrics": get_brain_queue_metrics(),
            "learner_metrics": get_learner_metrics(),
        }


# Global gateway instance
_learner_gateway: LearnerGateway | None = None


async def start_learner_gateway(batch_size: int = 256, drain_interval: float = 5.0) -> None:
    """Start the global learner gateway."""
    global _learner_gateway

    if _learner_gateway is None:
        _learner_gateway = LearnerGateway(batch_size, drain_interval)

    await _learner_gateway.start()


async def stop_learner_gateway() -> None:
    """Stop the global learner gateway."""
    global _learner_gateway

    if _learner_gateway is not None:
        await _learner_gateway.stop()


def get_learner_gateway() -> LearnerGateway | None:
    """Get the global learner gateway instance."""
    return _learner_gateway
