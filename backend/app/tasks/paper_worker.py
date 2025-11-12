"""
Async paper trading worker for ZiggyAI trading lab.

This module provides the main worker loop that coordinates data fetching,
signal generation, allocation, trade execution, labeling, and learning.
"""

from __future__ import annotations

import asyncio
import traceback
from datetime import datetime, timedelta
from typing import Any

from app.core.logging import get_logger
from app.paper import (
    BanditAllocator,
    FeatureComputer,
    LabelGenerator,
    OnlineLearner,
    PaperEngine,
    RunParams,
    Signal,
    theory_registry,
)
from app.paper.features import PriceData


logger = get_logger("ziggy.paper_worker")


class PaperWorker:
    """
    Async worker for paper trading operations.

    Coordinates the full pipeline:
    1. Fetch market data
    2. Compute features
    3. Generate signals from theories
    4. Allocate via bandit
    5. Execute trades
    6. Label outcomes
    7. Update learner
    8. Track metrics
    """

    def __init__(
        self,
        engine: PaperEngine | None = None,
        allocator: BanditAllocator | None = None,
        feature_computer: FeatureComputer | None = None,
        label_generator: LabelGenerator | None = None,
        learner: OnlineLearner | None = None,
        data_fetch_interval: float = 30.0,  # seconds
        learning_batch_size: int = 50,
        max_errors_per_hour: int = 100,
    ):
        self.engine = engine or PaperEngine()
        self.allocator = allocator or BanditAllocator()
        self.feature_computer = feature_computer or FeatureComputer()
        self.label_generator = label_generator or LabelGenerator()
        self.learner = learner or OnlineLearner()

        self.data_fetch_interval = data_fetch_interval
        self.learning_batch_size = learning_batch_size
        self.max_errors_per_hour = max_errors_per_hour

        # Worker state
        self.is_running = False
        self.last_data_fetch: datetime | None = None
        self.last_learning_update: datetime | None = None

        # Error tracking
        self.error_count = 0
        self.error_timestamps: list[datetime] = []

        # Performance tracking
        self.signals_generated = 0
        self.trades_executed = 0
        self.learning_updates = 0

        # Background tasks
        self.worker_tasks: list[asyncio.Task] = []

        logger.info(
            "PaperWorker initialized",
            extra={
                "data_fetch_interval": data_fetch_interval,
                "learning_batch_size": learning_batch_size,
            },
        )

    # --- Durability API ---
    def get_state(self) -> dict[str, Any]:
        """Return minimal worker state including queue snapshots (bounded)."""
        # Capture a small snapshot of pending signal IDs to avoid large payloads
        pending_signal_ids: list[str] = []
        try:
            # Non-destructive: peek by draining up to N then requeue
            tmp: list[Any] = []
            max_sample = 50
            while len(tmp) < max_sample:
                try:
                    item = self.signal_queue.get_nowait()
                    tmp.append(item)
                except asyncio.QueueEmpty:
                    break
            for it in tmp:
                sid = getattr(it, "signal_id", None)
                if isinstance(sid, str):
                    pending_signal_ids.append(sid)
                # put back
                try:
                    self.signal_queue.put_nowait(it)
                except asyncio.QueueFull:
                    break
        except Exception:
            pass
        return {
            "queues": {
                "signal_queue_size": self.signal_queue.qsize(),
                "trade_requests_size": self.trade_requests.qsize(),
                "sample_signal_ids": pending_signal_ids,
            }
        }

    def set_state(self, state: dict[str, Any]) -> None:
        """Restore queued items best-effort (sizes only are tracked; IDs ignored)."""
        # For safety, do not mutate queues here; restoration is handled at engine level.
        return

    async def start(self, run_params: dict[str, Any]) -> str:
        """
        Start the paper trading worker.

        Args:
            run_params: Parameters for the paper trading run

        Returns:
            Run ID
        """
        if self.is_running:
            raise RuntimeError("Worker is already running")

        logger.info("Starting paper trading worker", extra=run_params)

        try:
            # Convert dict to RunParams
            run_params_obj = RunParams(
                universe=run_params.get("universe", []),
                theories=run_params.get("theories", []),
                horizons_mins=run_params.get("horizons_mins", [5, 15, 60]),
                max_concurrency=run_params.get("max_concurrency", 64),
                max_trades_per_minute=run_params.get("max_trades_per_minute", 600),
                microtrade_notional=run_params.get("microtrade_notional", 25.0),
                max_exposure_notional=run_params.get("max_exposure_notional", 10000.0),
                max_open_trades=run_params.get("max_open_trades", 1000),
                max_trades_per_symbol=run_params.get("max_trades_per_symbol", 50),
                run_duration_hours=run_params.get("run_duration_hours"),
                enable_learning=run_params.get("enable_learning", True),
                random_seed=run_params.get("random_seed"),
            )

            # Start the paper trading engine
            run_id = await self.engine.start(run_params_obj)

            # Initialize allocator with theories
            for theory_id in run_params.get("theories", []):
                self.allocator.add_theory(theory_id)

            # Start background tasks
            self.is_running = True
            await self._start_background_tasks()

            logger.info("Paper trading worker started", extra={"run_id": run_id})
            return run_id

        except Exception as e:
            logger.error("Failed to start paper trading worker", extra={"error": str(e)})
            self.is_running = False
            raise

    async def stop(self) -> dict[str, Any]:
        """
        Stop the paper trading worker.

        Returns:
            Summary of the run
        """
        if not self.is_running:
            logger.warning("Worker is not running")
            return {}

        logger.info("Stopping paper trading worker")

        try:
            # Stop background tasks
            self.is_running = False

            # Cancel all tasks
            for task in self.worker_tasks:
                if not task.done():
                    task.cancel()

            # Wait for tasks to complete
            if self.worker_tasks:
                await asyncio.gather(*self.worker_tasks, return_exceptions=True)

            self.worker_tasks.clear()

            # Stop the engine
            engine_summary = await self.engine.stop()

            # Generate worker summary
            summary = {
                "engine_summary": engine_summary,
                "worker_stats": {
                    "signals_generated": self.signals_generated,
                    "trades_executed": self.trades_executed,
                    "learning_updates": self.learning_updates,
                    "error_count": self.error_count,
                },
                "allocator_performance": self.allocator.get_performance_summary(),
            }

            logger.info(
                "Paper trading worker stopped",
                extra={
                    "signals_generated": self.signals_generated,
                    "trades_executed": self.trades_executed,
                },
            )

            return summary

        except Exception as e:
            logger.error("Error stopping paper trading worker", extra={"error": str(e)})
            return {"error": str(e)}

    async def get_status(self) -> dict[str, Any]:
        """Get current worker status."""
        engine_status = await self.engine.get_status()

        return {
            "is_running": self.is_running,
            "engine_status": engine_status,
            "worker_stats": {
                "signals_generated": self.signals_generated,
                "trades_executed": self.trades_executed,
                "learning_updates": self.learning_updates,
                "error_count": self.error_count,
                "last_data_fetch": (
                    self.last_data_fetch.isoformat() if self.last_data_fetch else None
                ),
                "last_learning_update": (
                    self.last_learning_update.isoformat() if self.last_learning_update else None
                ),
            },
            "allocator_performance": self.allocator.get_performance_summary(),
            "active_tasks": len([t for t in self.worker_tasks if not t.done()]),
        }

    async def _start_background_tasks(self) -> None:
        """Start background worker tasks."""
        # Main data processing loop
        task = asyncio.create_task(self._data_processing_loop())
        self.worker_tasks.append(task)

        # Learning update loop
        task = asyncio.create_task(self._learning_loop())
        self.worker_tasks.append(task)

        # Health monitoring loop
        task = asyncio.create_task(self._health_monitoring_loop())
        self.worker_tasks.append(task)

        logger.info("Background tasks started", extra={"task_count": len(self.worker_tasks)})

    async def _data_processing_loop(self) -> None:
        """Main data processing loop."""
        logger.info("Starting data processing loop")

        try:
            while self.is_running:
                try:
                    await self._process_cycle()
                    await asyncio.sleep(self.data_fetch_interval)

                except Exception as e:
                    await self._handle_error("data_processing", e)
                    await asyncio.sleep(min(60, self.data_fetch_interval * 2))  # Backoff

        except asyncio.CancelledError:
            logger.info("Data processing loop cancelled")
            raise

    async def _process_cycle(self) -> None:
        """Single processing cycle."""
        # Step 1: Fetch market data (simulated for now)
        market_data = await self._fetch_market_data()
        self.last_data_fetch = datetime.utcnow()

        # Step 2: Update feature computer with new data
        for symbol_data in market_data:
            self.feature_computer.add_price_data(symbol_data)

        # Step 3: Generate signals from theories
        signals = await self._generate_signals(market_data)
        self.signals_generated += len(signals)

        # Step 4: Allocate signals via bandit
        if signals:
            allocated_signals = await self._allocate_signals(signals)

            # Step 5: Submit signals to engine
            for signal in allocated_signals:
                await self.engine.submit_signal(signal)

    async def _fetch_market_data(self) -> list[PriceData]:
        """
        Fetch current market data.

        In a real implementation, this would connect to market data providers.
        For simulation, we generate synthetic data.
        """
        current_time = datetime.utcnow()
        market_data = []

        # Get universe from engine parameters
        engine_status = await self.engine.get_status()
        universe = engine_status.get("params", {}).get("universe", ["AAPL", "MSFT", "NVDA"])

        # Generate synthetic price data
        for symbol in universe:
            # Simple random walk simulation
            base_price = 100.0 if not symbol.startswith("^") else 4000.0
            price_change = (hash(symbol + str(current_time.minute)) % 1000 - 500) / 10000.0

            price = base_price * (1 + price_change)
            volume = 1000000 + (hash(symbol + str(current_time.second)) % 500000)

            price_data = PriceData(
                timestamp=current_time,
                symbol=symbol,
                open_price=price * 0.999,
                high=price * 1.002,
                low=price * 0.998,
                close=price,
                volume=volume,
            )
            market_data.append(price_data)

        return market_data

    async def _generate_signals(self, market_data: list[PriceData]) -> list[Signal]:
        """Generate trading signals from theories."""
        signals = []

        for price_data in market_data:
            # Compute features for this symbol
            features = self.feature_computer.compute_features(price_data.symbol)
            if features is None:
                continue

            # Generate signals from enabled theories
            for theory in theory_registry.get_enabled():
                try:
                    theory_signals = theory.generate_signals(features)

                    # Apply risk model to adjust signal strength
                    risk_multiplier = theory.risk_model(features)

                    for signal in theory_signals:
                        signal.confidence *= risk_multiplier
                        signals.append(signal)

                except Exception as e:
                    logger.warning(
                        "Theory signal generation failed",
                        extra={
                            "theory_id": theory.theory_id,
                            "symbol": price_data.symbol,
                            "error": str(e),
                        },
                    )

        return signals

    async def _allocate_signals(self, signals: list[Signal]) -> list[Signal]:
        """Allocate signals based on bandit recommendations."""
        if not signals:
            return []

        # Group signals by theory
        theory_signals: dict[str, list[Signal]] = {}
        for signal in signals:
            if signal.theory_id not in theory_signals:
                theory_signals[signal.theory_id] = []
            theory_signals[signal.theory_id].append(signal)

        # Get allocation from bandit
        theory_ids = list(theory_signals.keys())
        allocation_result = self.allocator.allocate(theory_ids)

        # Select signals based on allocation
        allocated_signals = []

        for theory_id, allocation_weight in allocation_result.allocations.items():
            if theory_id in theory_signals:
                theory_signal_list = theory_signals[theory_id]

                # Select top signals based on allocation weight
                num_signals = max(1, int(len(theory_signal_list) * allocation_weight))

                # Sort by confidence and take top signals
                sorted_signals = sorted(
                    theory_signal_list, key=lambda s: s.confidence, reverse=True
                )
                allocated_signals.extend(sorted_signals[:num_signals])

        return allocated_signals

    async def _learning_loop(self) -> None:
        """Learning update loop."""
        logger.info("Starting learning loop")

        try:
            while self.is_running:
                try:
                    await self._update_learning()
                    await asyncio.sleep(60)  # Update every minute

                except Exception as e:
                    await self._handle_error("learning", e)
                    await asyncio.sleep(120)  # Longer backoff for learning errors

        except asyncio.CancelledError:
            logger.info("Learning loop cancelled")
            raise

    async def _update_learning(self) -> None:
        """Update learner with recent trade outcomes."""
        # In a full implementation, this would:
        # 1. Fetch recent completed trades
        # 2. Generate labels for those trades
        # 3. Create training batches
        # 4. Update the learner with partial_fit
        # 5. Update theory performance in the bandit allocator

        # For now, simulate some learning updates
        self.learning_updates += 1
        self.last_learning_update = datetime.utcnow()

        logger.debug("Learning update completed", extra={"update_count": self.learning_updates})

    async def _health_monitoring_loop(self) -> None:
        """Health monitoring and error recovery loop."""
        logger.info("Starting health monitoring loop")

        try:
            while self.is_running:
                try:
                    await self._check_health()
                    await asyncio.sleep(30)  # Check every 30 seconds

                except Exception as e:
                    logger.error("Health monitoring error", extra={"error": str(e)})
                    await asyncio.sleep(60)

        except asyncio.CancelledError:
            logger.info("Health monitoring loop cancelled")
            raise

    async def _check_health(self) -> None:
        """Check system health and perform recovery if needed."""
        current_time = datetime.utcnow()

        # Clean old error timestamps
        hour_ago = current_time - timedelta(hours=1)
        self.error_timestamps = [ts for ts in self.error_timestamps if ts > hour_ago]

        # Check error rate
        if len(self.error_timestamps) > self.max_errors_per_hour:
            logger.error(
                "Error rate exceeded threshold",
                extra={
                    "errors_last_hour": len(self.error_timestamps),
                    "threshold": self.max_errors_per_hour,
                },
            )
            # Could implement circuit breaker logic here

        # Check if data fetching is healthy
        if self.last_data_fetch:
            time_since_fetch = (current_time - self.last_data_fetch).total_seconds()
            if time_since_fetch > self.data_fetch_interval * 3:
                logger.warning(
                    "Data fetching appears stalled",
                    extra={
                        "time_since_fetch": time_since_fetch,
                        "expected_interval": self.data_fetch_interval,
                    },
                )

    async def _handle_error(self, context: str, error: Exception) -> None:
        """Handle and log errors with context."""
        self.error_count += 1
        self.error_timestamps.append(datetime.utcnow())

        error_msg = str(error)
        error_trace = traceback.format_exc()

        logger.error(
            "Worker error",
            extra={
                "context": context,
                "error": error_msg,
                "error_count": self.error_count,
                "traceback": error_trace,
            },
        )

        # Could implement error-specific recovery logic here
        if "connection" in error_msg.lower():
            # Network error - longer backoff
            await asyncio.sleep(30)
        elif "memory" in error_msg.lower():
            # Memory error - trigger cleanup
            logger.info("Memory error detected, triggering cleanup")
            # Could implement memory cleanup here


# Module-level startup function for integration with main.py
_paper_worker_instance: PaperWorker | None = None


async def start_paper_worker() -> None:
    """
    Start the paper trading worker in the background.

    This function is called by the main FastAPI app during startup
    in development environments only.
    """
    global _paper_worker_instance

    if _paper_worker_instance is not None:
        logger.info("Paper worker already running")
        return

    try:
        from app.core.config import get_settings

        settings = get_settings()

        # Verify we're in development mode
        if settings.ENV not in ["development", "dev"] and not settings.DEBUG:
            logger.warning("Paper worker disabled - not in development environment")
            return

        logger.info("Starting paper trading worker...")

        # Create worker instance
        _paper_worker_instance = PaperWorker(
            data_fetch_interval=30.0,  # 30 seconds between data fetches
            learning_batch_size=50,
            max_errors_per_hour=100,
        )

        # Default run parameters for autonomous operation
        run_params = {
            "universe": ["SPY", "QQQ", "IWM", "AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"],
            "theories": [
                "mean_revert",
                "breakout",
                "news_shock_guard",
                "vol_regime",
                "intraday_momentum",
            ],
            "max_trades_per_minute": 10,
            "max_trades_per_hour": 300,
            "max_position_size": 0.05,  # 5% of portfolio per position
            "max_daily_loss": 0.10,  # 10% max daily loss
            "enable_learning": True,
            "learning_frequency": 100,  # Learn every 100 trades
            "theory_allocation_method": "thompson_sampling",
            "horizons_mins": [5, 15, 60],
            "max_concurrency": 32,
            "microtrade_notional": 25.0,
            "max_exposure_notional": 5000.0,
            "max_open_trades": 500,
            "max_trades_per_symbol": 25,
            "run_duration_hours": None,  # Run indefinitely
        }

        # Start the worker
        run_id = await _paper_worker_instance.start(run_params)
        logger.info(
            "Paper trading worker started",
            extra={
                "run_id": run_id,
                "universe": run_params["universe"],
                "theories": run_params["theories"],
                "max_trades_per_hour": run_params["max_trades_per_hour"],
            },
        )

    except Exception as e:
        logger.error(
            "Failed to start paper trading worker",
            extra={"error": str(e), "traceback": traceback.format_exc()},
        )


async def stop_paper_worker() -> None:
    """Stop the paper trading worker."""
    global _paper_worker_instance

    if _paper_worker_instance is None:
        logger.info("Paper worker not running")
        return

    try:
        await _paper_worker_instance.stop()
        _paper_worker_instance = None
        logger.info("Paper trading worker stopped")
    except Exception as e:
        logger.error("Failed to stop paper trading worker", extra={"error": str(e)})


def get_paper_worker() -> PaperWorker | None:
    """Get the current paper worker instance."""
    return _paper_worker_instance
