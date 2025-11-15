"""
Micro-trade engine for ZiggyAI autonomous paper trading lab.

This module orchestrates thousands of micro-trades across instruments and theories,
providing rate limiting, replay buffer, walk-forward windows, and multi-order type support.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from app.brokers.paper_broker import OrderFill, PaperBroker
from app.core.logging import get_logger
from app.trading.models import Order, Side


logger = get_logger("ziggy.paper_engine")


class RunStatus(Enum):
    """Paper trading run status."""

    INITIALIZING = "initializing"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class RunParams:
    """Parameters for a paper trading run."""

    universe: list[str]
    theories: list[str]
    horizons_mins: list[int] = field(default_factory=lambda: [5, 15, 60])
    max_concurrency: int = 64
    max_trades_per_minute: int = 600
    microtrade_notional: float = 25.0
    max_exposure_notional: float = 10000.0
    max_open_trades: int = 1000
    max_trades_per_symbol: int = 50
    run_duration_hours: int | None = None
    enable_learning: bool = True
    random_seed: int | None = None


@dataclass
class Signal:
    """Trading signal from a theory."""

    theory_id: str
    symbol: str
    side: Side
    confidence: float  # 0.0 to 1.0
    horizon_mins: int
    features: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    signal_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class TradeRequest:
    """Request to execute a trade."""

    signal: Signal
    notional: float
    qty: int
    order_type: str = "MARKET"


@dataclass
class RunStats:
    """Real-time statistics for a paper trading run."""

    trades_executed: int = 0
    trades_per_minute: float = 0.0
    open_trades: int = 0
    total_pnl: float = 0.0
    win_rate: float = 0.0
    avg_bps: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    last_error: str | None = None
    queue_depth: int = 0


class PaperEngine:
    """
    Micro-trade engine for autonomous paper trading.

    Features:
    - Rate limiting and concurrency control
    - Signal queue and batch processing
    - Theory allocation and routing
    - Performance tracking and metrics
    - Graceful shutdown and recovery
    """

    def __init__(self, broker: PaperBroker | None = None, max_queue_size: int = 10000):
        self.broker = broker or PaperBroker()
        self.max_queue_size = max_queue_size

        # Run state
        self.status = RunStatus.STOPPED
        self.params: RunParams | None = None
        self.run_id: str | None = None
        self.start_time: datetime | None = None
        self.stop_time: datetime | None = None

        # Processing state
        self.signal_queue: asyncio.Queue[Signal] = asyncio.Queue(maxsize=max_queue_size)
        self.trade_requests: asyncio.Queue[TradeRequest] = asyncio.Queue()
        self.active_tasks: set[asyncio.Task] = set()
        self.semaphore: asyncio.Semaphore | None = None

        # Rate limiting
        self.trade_timestamps: list[datetime] = []
        self.last_minute_trades = 0

        # Statistics
        self.stats = RunStats()
        self.theory_stats: dict[str, dict[str, Any]] = {}

        # Data caches
        self.market_data_cache: dict[str, dict[str, Any]] = {}
        self.position_cache: dict[str, float] = {}  # symbol -> notional exposure

        logger.info("PaperEngine initialized", extra={"max_queue_size": max_queue_size})

    async def start(self, params: RunParams) -> str:
        """
        Start a paper trading run.

        Args:
            params: Run parameters

        Returns:
            Run ID

        Raises:
            RuntimeError: If already running or invalid params
        """
        if self.status == RunStatus.RUNNING:
            raise RuntimeError("Paper trading run already in progress")

        # Validate parameters
        self._validate_params(params)

        # Initialize run
        self.run_id = str(uuid.uuid4())
        self.params = params
        self.start_time = datetime.utcnow()
        self.stop_time = None
        self.status = RunStatus.INITIALIZING

        # Initialize rate limiting
        self.semaphore = asyncio.Semaphore(params.max_concurrency)
        self.trade_timestamps.clear()

        # Reset statistics
        self.stats = RunStats()
        self.theory_stats = {
            theory: self._init_theory_stats() for theory in params.theories
        }

        logger.info(
            "Starting paper trading run",
            extra={
                "run_id": self.run_id,
                "universe": params.universe,
                "theories": params.theories,
                "max_concurrency": params.max_concurrency,
                "max_trades_per_minute": params.max_trades_per_minute,
            },
        )

        try:
            # Start background tasks
            self.status = RunStatus.RUNNING
            await self._start_background_tasks()

            logger.info(
                "Paper trading run started successfully", extra={"run_id": self.run_id}
            )

            return self.run_id

        except Exception as e:
            self.status = RunStatus.ERROR
            self.stats.last_error = str(e)
            logger.error(
                "Failed to start paper trading run",
                extra={"run_id": self.run_id, "error": str(e)},
            )
            raise

    async def stop(self) -> dict[str, Any]:
        """
        Stop the current paper trading run.

        Returns:
            Run summary
        """
        if self.status not in [RunStatus.RUNNING, RunStatus.ERROR]:
            logger.warning("No active run to stop", extra={"status": self.status.value})
            return {}

        logger.info("Stopping paper trading run", extra={"run_id": self.run_id})

        self.status = RunStatus.STOPPING
        self.stop_time = datetime.utcnow()

        # Cancel all active tasks
        for task in self.active_tasks:
            if not task.done():
                task.cancel()

        # Wait for tasks to complete
        if self.active_tasks:
            await asyncio.gather(*self.active_tasks, return_exceptions=True)

        self.active_tasks.clear()

        # Generate final summary
        summary = await self._generate_run_summary()

        self.status = RunStatus.STOPPED

        logger.info(
            "Paper trading run stopped",
            extra={
                "run_id": self.run_id,
                "duration_mins": summary.get("duration_mins", 0),
                "total_trades": summary.get("total_trades", 0),
            },
        )

        return summary

    async def submit_signal(self, signal: Signal) -> bool:
        """
        Submit a trading signal for processing.

        Args:
            signal: Trading signal

        Returns:
            True if queued successfully, False if queue full
        """
        if self.status != RunStatus.RUNNING:
            return False

        try:
            self.signal_queue.put_nowait(signal)
            return True
        except asyncio.QueueFull:
            logger.warning(
                "Signal queue full, dropping signal",
                extra={"signal_id": signal.signal_id, "theory_id": signal.theory_id},
            )
            return False

    async def get_status(self) -> dict[str, Any]:
        """Get current engine status."""
        if self.params is None:
            return {
                "status": self.status.value,
                "run_id": None,
                "uptime_mins": 0,
                "stats": {},
            }

        uptime_mins = 0
        if self.start_time:
            uptime = datetime.utcnow() - self.start_time
            uptime_mins = uptime.total_seconds() / 60

        # Update stats
        await self._update_stats()

        return {
            "status": self.status.value,
            "run_id": self.run_id,
            "uptime_mins": uptime_mins,
            "params": {
                "universe": self.params.universe,
                "theories": self.params.theories,
                "max_concurrency": self.params.max_concurrency,
                "max_trades_per_minute": self.params.max_trades_per_minute,
            },
            "stats": {
                "trades_executed": self.stats.trades_executed,
                "trades_per_minute": self.stats.trades_per_minute,
                "open_trades": self.stats.open_trades,
                "queue_depth": self.signal_queue.qsize(),
                "total_pnl": self.stats.total_pnl,
                "win_rate": self.stats.win_rate,
                "last_error": self.stats.last_error,
            },
            "theory_stats": self.theory_stats,
        }

    def _validate_params(self, params: RunParams) -> None:
        """Validate run parameters."""
        if not params.universe:
            raise ValueError("Universe cannot be empty")

        if not params.theories:
            raise ValueError("Theories list cannot be empty")

        if params.max_concurrency <= 0:
            raise ValueError("max_concurrency must be positive")

        if params.max_trades_per_minute <= 0:
            raise ValueError("max_trades_per_minute must be positive")

        if params.microtrade_notional <= 0:
            raise ValueError("microtrade_notional must be positive")

    async def _start_background_tasks(self) -> None:
        """Start background processing tasks."""
        # Signal processor
        task = asyncio.create_task(self._process_signals())
        self.active_tasks.add(task)

        # Trade executor
        task = asyncio.create_task(self._execute_trades())
        self.active_tasks.add(task)

        # Stats updater
        task = asyncio.create_task(self._update_stats_loop())
        self.active_tasks.add(task)

        # Cleanup task for completed tasks
        task = asyncio.create_task(self._cleanup_tasks())
        self.active_tasks.add(task)

    async def _process_signals(self) -> None:
        """Process signals from the queue."""
        logger.info("Starting signal processor")

        try:
            while self.status == RunStatus.RUNNING:
                try:
                    # Wait for signal with timeout
                    signal = await asyncio.wait_for(
                        self.signal_queue.get(), timeout=1.0
                    )

                    # Process signal
                    await self._handle_signal(signal)

                except TimeoutError:
                    continue
                except Exception as e:
                    logger.error("Error processing signal", extra={"error": str(e)})
                    self.stats.last_error = f"Signal processing: {e!s}"

        except asyncio.CancelledError:
            logger.info("Signal processor cancelled")
            raise

    async def _handle_signal(self, signal: Signal) -> None:
        """Handle a single signal."""
        # Safety check
        if self.params is None:
            return

        # Check theory is enabled
        if signal.theory_id not in self.params.theories:
            return

        # Check exposure limits
        current_exposure = self.position_cache.get(signal.symbol, 0.0)
        if abs(current_exposure) >= self.params.max_exposure_notional:
            logger.debug(
                "Exposure limit reached",
                extra={"symbol": signal.symbol, "current_exposure": current_exposure},
            )
            return

        # Calculate position size
        notional = min(
            self.params.microtrade_notional,
            self.params.max_exposure_notional - abs(current_exposure),
        )

        if notional <= 0:
            return

        # Get market price for qty calculation (simplified)
        market_price = self._get_market_price(signal.symbol)
        qty = max(1, int(notional / market_price))

        # Create trade request
        trade_request = TradeRequest(signal=signal, notional=notional, qty=qty)

        try:
            self.trade_requests.put_nowait(trade_request)
        except asyncio.QueueFull:
            logger.warning("Trade request queue full")

    async def _execute_trades(self) -> None:
        """Execute trades from the request queue."""
        logger.info("Starting trade executor")

        try:
            while self.status == RunStatus.RUNNING:
                try:
                    # Wait for trade request
                    request = await asyncio.wait_for(
                        self.trade_requests.get(), timeout=1.0
                    )

                    # Check rate limit
                    if not await self._check_rate_limit():
                        # Re-queue the request for later
                        await asyncio.sleep(0.1)
                        import contextlib

                        with contextlib.suppress(asyncio.QueueFull):
                            self.trade_requests.put_nowait(request)
                        continue

                    # Execute trade
                    task = asyncio.create_task(self._execute_trade(request))
                    self.active_tasks.add(task)

                except TimeoutError:
                    continue

        except asyncio.CancelledError:
            logger.info("Trade executor cancelled")
            raise

    async def _execute_trade(self, request: TradeRequest) -> None:
        """Execute a single trade."""
        if self.semaphore is None:
            return

        async with self.semaphore:
            try:
                # Create order
                order = Order(
                    symbol=request.signal.symbol,
                    side=request.signal.side,
                    qty=request.qty,
                    order_type="MARKET",  # Force to MARKET for now
                    client_order_id=request.signal.signal_id,
                )

                # Submit to broker
                fill = await self.broker.submit(order)

                # Update statistics
                self._record_trade(request.signal, fill)

                # Update position cache
                notional_change = fill.avg_price * fill.qty
                if fill.side == "SELL":
                    notional_change = -notional_change

                self.position_cache[fill.symbol] = (
                    self.position_cache.get(fill.symbol, 0.0) + notional_change
                )

                logger.debug(
                    "Trade executed",
                    extra={
                        "symbol": fill.symbol,
                        "side": fill.side,
                        "qty": fill.qty,
                        "price": fill.avg_price,
                        "theory": request.signal.theory_id,
                    },
                )

            except Exception as e:
                logger.error(
                    "Failed to execute trade",
                    extra={
                        "symbol": request.signal.symbol,
                        "theory": request.signal.theory_id,
                        "error": str(e),
                    },
                )
                self.stats.last_error = f"Trade execution: {e!s}"

    async def _check_rate_limit(self) -> bool:
        """Check if we can execute another trade without exceeding rate limit."""
        if self.params is None:
            return False

        now = datetime.utcnow()

        # Clean old timestamps
        cutoff = now - timedelta(minutes=1)
        self.trade_timestamps = [ts for ts in self.trade_timestamps if ts > cutoff]

        # Check limit
        if len(self.trade_timestamps) >= self.params.max_trades_per_minute:
            return False

        # Record timestamp
        self.trade_timestamps.append(now)
        return True

    def _get_market_price(self, symbol: str) -> float:
        """Get market price for a symbol (simplified for now)."""
        # In a real implementation, this would fetch from market data provider
        # For now, use a simple synthetic price
        if symbol.startswith("^"):
            return 4000.0  # Index
        else:
            return 100.0  # Stock

    def _record_trade(self, signal: Signal, fill: OrderFill) -> None:
        """Record trade execution in statistics."""
        self.stats.trades_executed += 1

        # Update theory stats
        if signal.theory_id not in self.theory_stats:
            self.theory_stats[signal.theory_id] = self._init_theory_stats()

        theory_stats = self.theory_stats[signal.theory_id]
        theory_stats["trades"] += 1
        theory_stats["notional"] += fill.avg_price * fill.qty
        theory_stats["fees"] += fill.fees

        # Hook for brain ingest (if available)
        try:
            self._enqueue_for_brain(signal, fill)
        except Exception as e:
            logger.warning(
                "Failed to enqueue trade for brain",
                extra={"signal_id": signal.signal_id, "error": str(e)},
            )

    def _enqueue_for_brain(self, signal: Signal, fill: OrderFill) -> None:
        """Enqueue trade for brain learning (after persistence)."""
        try:
            # Import here to avoid circular dependencies
            from app.models.paper import Trade, TradeStatus
            from app.paper.ingest import enqueue_for_brain

            # Create a minimal Trade object for brain ingestion
            # Note: In a full implementation, this would be the actual persisted trade
            trade = Trade(
                trade_id=signal.signal_id,
                ticker=signal.symbol,
                direction="BUY" if signal.side == "BUY" else "SELL",
                quantity=fill.qty,
                theory_name=signal.theory_id,
                status=TradeStatus.FILLED.value,
                signal_time=fill.timestamp,
                fill_price=fill.avg_price,
                realized_pnl=0.0,  # Would be calculated later
            )

            # Enqueue asynchronously (fire and forget)
            import asyncio

            t = asyncio.create_task(enqueue_for_brain(trade))
            try:
                self.active_tasks.add(t)
                t.add_done_callback(self.active_tasks.discard)
            except Exception:
                pass

            logger.debug(
                "Trade enqueued for brain learning",
                extra={
                    "trade_id": signal.signal_id,
                    "symbol": signal.symbol,
                    "theory": signal.theory_id,
                },
            )

        except ImportError:
            # Brain ingest not available
            pass
        except Exception as e:
            logger.warning(
                "Failed to enqueue trade for brain",
                extra={"signal_id": signal.signal_id, "error": str(e)},
            )

    def _init_theory_stats(self) -> dict[str, Any]:
        """Initialize statistics for a theory."""
        return {
            "trades": 0,
            "notional": 0.0,
            "fees": 0.0,
            "pnl": 0.0,
            "win_rate": 0.0,
            "sharpe": 0.0,
            "allocation_weight": 0.0,
        }

    async def _update_stats(self) -> None:
        """Update real-time statistics."""
        # Calculate trades per minute
        if self.start_time:
            elapsed_mins = (datetime.utcnow() - self.start_time).total_seconds() / 60
            if elapsed_mins > 0:
                self.stats.trades_per_minute = self.stats.trades_executed / elapsed_mins

        # Get broker performance
        broker_summary = self.broker.get_performance_summary()
        self.stats.total_pnl = broker_summary["net_pnl"]
        self.stats.open_trades = int(broker_summary["num_positions"])

        # Update queue depth
        self.stats.queue_depth = self.signal_queue.qsize()

    async def _update_stats_loop(self) -> None:
        """Periodic stats update loop."""
        try:
            while self.status == RunStatus.RUNNING:
                await self._update_stats()
                await asyncio.sleep(10)  # Update every 10 seconds
        except asyncio.CancelledError:
            pass

    async def _cleanup_tasks(self) -> None:
        """Clean up completed tasks."""
        try:
            while self.status == RunStatus.RUNNING:
                # Remove completed tasks
                completed = {task for task in self.active_tasks if task.done()}
                for task in completed:
                    try:
                        await task  # Retrieve any exceptions
                    except Exception as e:
                        logger.error("Background task failed", extra={"error": str(e)})

                self.active_tasks -= completed

                await asyncio.sleep(5)  # Cleanup every 5 seconds
        except asyncio.CancelledError:
            pass

    async def _generate_run_summary(self) -> dict[str, Any]:
        """Generate summary of the trading run."""
        broker_summary = self.broker.get_performance_summary()

        duration = timedelta(0)
        if self.start_time and self.stop_time:
            duration = self.stop_time - self.start_time

        return {
            "run_id": self.run_id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "stop_time": self.stop_time.isoformat() if self.stop_time else None,
            "duration_mins": duration.total_seconds() / 60,
            "total_trades": self.stats.trades_executed,
            "avg_trades_per_minute": self.stats.trades_per_minute,
            "total_pnl": broker_summary["net_pnl"],
            "total_fees": broker_summary["total_fees"],
            "theory_stats": self.theory_stats,
            "broker_summary": broker_summary,
        }

    # --- Durability API ---
    async def get_state(self) -> dict[str, Any]:
        """Collect minimal durable state for snapshots.

        Returns:
            Dict with run_id, params, positions, equity_curve (tail), and config flags.
        """
        # Positions from broker
        positions: list[dict[str, Any]] = []
        try:
            pos_map = await self.broker.positions()
            for sym, pos in pos_map.items():
                positions.append(
                    {
                        "symbol": sym,
                        "qty": int(pos.qty),
                        "avg_price": float(pos.avg_price),
                    }
                )
        except Exception:
            pass

        # Equity curve points: use simple proxy from stats
        equity_curve: list[dict[str, Any]] = []
        import contextlib

        with contextlib.suppress(Exception):
            equity_curve.append(
                {
                    "ts": datetime.utcnow().isoformat(),
                    "equity": float(
                        self.broker.get_performance_summary().get("net_pnl", 0.0)
                    ),
                    "idx": 0,
                }
            )

        return {
            "run_id": self.run_id or "",
            "params": vars(self.params) if self.params else {},
            "positions": positions,
            "equity_curve": equity_curve[-500:],
        }

    async def set_state(self, state: dict[str, Any]) -> None:
        """Apply durable state at boot/resume.

        Args:
            state: Dict with positions, equity_curve, params, run_id
        """
        try:
            # restore run id and params
            self.run_id = state.get("run_id") or self.run_id
            params = state.get("params") or {}
            import contextlib

            with contextlib.suppress(Exception):
                # Attempt to coerce to RunParams if structure matches
                self.params = RunParams(
                    universe=params.get(
                        "universe", self.params.universe if self.params else []
                    ),
                    theories=params.get(
                        "theories", self.params.theories if self.params else []
                    ),
                    horizons_mins=params.get("horizons_mins", [5, 15, 60]),
                    max_concurrency=params.get("max_concurrency", 64),
                    max_trades_per_minute=params.get("max_trades_per_minute", 600),
                    microtrade_notional=params.get("microtrade_notional", 25.0),
                    max_exposure_notional=params.get("max_exposure_notional", 10000.0),
                    max_open_trades=params.get("max_open_trades", 1000),
                    max_trades_per_symbol=params.get("max_trades_per_symbol", 50),
                    run_duration_hours=params.get("run_duration_hours"),
                    enable_learning=params.get("enable_learning", True),
                    random_seed=params.get("random_seed"),
                )

            # Restore positions directly into broker (best-effort)
            from app.brokers.paper_broker import PaperPosition

            for p in state.get("positions", []) or []:
                try:
                    sym = p["symbol"]
                    qty = int(p.get("qty", 0))
                    avg = float(p.get("avg_price", 0.0))
                    self.broker._positions[sym] = PaperPosition(symbol=sym, qty=qty, avg_price=avg)  # type: ignore[attr-defined]
                except Exception:
                    continue
        except Exception:
            # Non-fatal
            pass
