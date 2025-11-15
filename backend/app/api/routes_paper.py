# app/api/routes_paper.py
# type: ignore
"""
Paper Trading Lab API Routes

Provides endpoints for managing the autonomous paper trading lab with
thousands of concurrent micro-trades, online learning, and theory testing.
All endpoints are dev-only with strict safety guards.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import db_state
from app.models.base import get_db
from app.models.paper import ModelSnapshot, PaperRun, TheoryPerf, TheoryStatus, Trade, TradeStatus
from app.utils.time import monotonic_now


logger = logging.getLogger("ziggy.api.paper")
settings = get_settings()

router = APIRouter()


# Module-level health state with backoff and caching to avoid DB hammering
@dataclass
class _HealthState:
    last_status: str = "INIT"  # "UP" | "DOWN" | "INIT"
    last_checked_at: float = 0.0
    next_retry_at: float = 0.0
    backoff_seconds: float = 1.0
    cached_payload: dict[str, Any] | None = None
    cache_expiry_at: float = 0.0

    def should_try_check(self) -> bool:
        now = monotonic_now()
        return now >= self.next_retry_at

    def record_failure(self, err: Exception):
        now = monotonic_now()
        prev = self.last_status
        self.last_status = "DOWN"
        # Exponential backoff capped at 30s
        self.backoff_seconds = min(30.0, max(1.0, self.backoff_seconds * 2.0))
        self.last_checked_at = now
        self.next_retry_at = now + self.backoff_seconds
        # Cache a minimal DOWN payload for quick responses
        self.cached_payload = {"status": "DOWN"}
        self.cache_expiry_at = self.next_retry_at  # reuse until next retry
        if prev != "DOWN":
            logger.warning(
                "Paper lab health transitioned DOWN",
                extra={"error": repr(err), "backoff_s": self.backoff_seconds},
            )

    def record_success(self, payload: dict[str, Any]):
        now = monotonic_now()
        prev = self.last_status
        self.last_status = "UP"
        self.backoff_seconds = 1.0
        self.last_checked_at = now
        self.next_retry_at = now + 10.0  # cache for 10s
        self.cached_payload = {**payload, "status": "healthy"}
        self.cache_expiry_at = self.next_retry_at
        if prev != "UP":
            logger.info("Paper lab health transitioned UP")


_HEALTH_STATE = _HealthState()


# Request/Response Models
class PaperRunRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    initial_balance: float = Field(default=100000.0, gt=0)
    max_trades_per_minute: int = Field(default=100, ge=1, le=1000)
    config: dict[str, Any] = Field(default_factory=dict)


class PaperRunResponse(BaseModel):
    id: int
    name: str
    status: str
    started_at: datetime
    total_trades: int
    total_pnl: float
    current_balance: float
    win_rate: float | None
    avg_fill_latency_ms: float | None


class TradeResponse(BaseModel):
    id: int
    trade_id: str
    ticker: str
    direction: str
    quantity: float
    theory_name: str
    status: str
    signal_time: datetime
    fill_price: float | None
    realized_pnl: float | None


class TheoryPerfResponse(BaseModel):
    theory_name: str
    status: str
    current_allocation: float
    total_trades_executed: int
    total_pnl: float
    win_rate: float | None
    sharpe_ratio: float | None
    avg_fill_latency_ms: float | None


def verify_dev_only():
    """Verify this is a development environment"""
    if settings.ENV not in ["development", "dev"] and not settings.DEBUG:
        raise HTTPException(
            status_code=404,
            detail="Paper trading lab is only available in development environments",
        )


def to_paper_run_response(run: PaperRun) -> PaperRunResponse:
    """Convert PaperRun model to response format"""
    return PaperRunResponse(
        id=run.id,  # type: ignore
        name=run.name,  # type: ignore
        status=run.status,  # type: ignore
        started_at=run.started_at,  # type: ignore
        total_trades=run.total_trades,  # type: ignore
        total_pnl=float(run.total_pnl),  # type: ignore
        current_balance=float(run.current_balance),  # type: ignore
        win_rate=float(run.win_rate) if run.win_rate is not None else None,  # type: ignore
        avg_fill_latency_ms=float(run.avg_fill_latency_ms)
        if run.avg_fill_latency_ms is not None
        else None,  # type: ignore
    )


def to_trade_response(trade: Trade) -> TradeResponse:
    """Convert Trade model to response format"""
    return TradeResponse(
        id=trade.id,  # type: ignore
        trade_id=trade.trade_id,  # type: ignore
        ticker=trade.ticker,  # type: ignore
        direction=trade.direction,  # type: ignore
        quantity=float(trade.quantity),  # type: ignore
        theory_name=trade.theory_name,  # type: ignore
        status=trade.status,  # type: ignore
        signal_time=trade.signal_time,  # type: ignore
        fill_price=float(trade.fill_price) if trade.fill_price is not None else None,  # type: ignore
        realized_pnl=float(trade.realized_pnl) if trade.realized_pnl is not None else None,  # type: ignore
    )


def to_theory_perf_response(theory: TheoryPerf) -> TheoryPerfResponse:
    """Convert TheoryPerf model to response format"""
    return TheoryPerfResponse(
        theory_name=theory.theory_name,  # type: ignore
        status=theory.theory_status,  # type: ignore
        current_allocation=float(theory.current_allocation),  # type: ignore
        total_trades_executed=theory.total_trades_executed,  # type: ignore
        total_pnl=float(theory.total_pnl),  # type: ignore
        win_rate=float(theory.win_rate) if theory.win_rate is not None else None,  # type: ignore
        sharpe_ratio=float(theory.sharpe_ratio) if theory.sharpe_ratio is not None else None,  # type: ignore
        avg_fill_latency_ms=float(theory.avg_fill_latency_ms)
        if theory.avg_fill_latency_ms is not None
        else None,  # type: ignore
    )


# Paper Run Management
@router.post("/runs", response_model=PaperRunResponse)
async def create_paper_run(request: PaperRunRequest, db: Session = Depends(get_db)):
    """
    Create a new paper trading run with specified configuration.
    Dev environments only.
    """
    verify_dev_only()

    try:
        # Create paper run record
        paper_run = PaperRun(
            name=request.name,
            description=request.description,
            config=request.config,
            initial_balance=request.initial_balance,
            current_balance=request.initial_balance,
            max_trades_per_minute=request.max_trades_per_minute,
            status="ACTIVE",
        )

        db.add(paper_run)
        db.commit()
        db.refresh(paper_run)

        logger.info(f"Created paper run {paper_run.id}: {paper_run.name}")

        return to_paper_run_response(paper_run)

    except Exception as e:
        logger.error(f"Failed to create paper run: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create paper run") from e


@router.get("/runs", response_model=list[PaperRunResponse])
async def list_paper_runs(
    status: str | None = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List paper trading runs with optional filtering"""
    verify_dev_only()

    try:
        query = db.query(PaperRun)

        if status:
            query = query.filter(PaperRun.status == status)

        runs = query.order_by(PaperRun.created_at.desc()).limit(limit).all()

        return [to_paper_run_response(run) for run in runs]

    except Exception as e:
        logger.error(f"Failed to list paper runs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve paper runs") from e


@router.get("/runs/{run_id}", response_model=PaperRunResponse)
async def get_paper_run(run_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a specific paper run"""
    verify_dev_only()

    try:
        run = db.query(PaperRun).filter(PaperRun.id == run_id).first()
        if not run:
            raise HTTPException(status_code=404, detail="Paper run not found")

        return to_paper_run_response(run)  # type: ignore

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get paper run {run_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve paper run") from e


@router.post("/runs/{run_id}/stop", response_model=None)
async def stop_paper_run(run_id: int, db: Session = Depends(get_db)):
    """Stop a running paper trading session"""
    verify_dev_only()

    try:
        run = db.query(PaperRun).filter(PaperRun.id == run_id).first()
        if not run:
            raise HTTPException(status_code=404, detail="Paper run not found")

        if run.status != "ACTIVE":
            raise HTTPException(status_code=400, detail="Paper run is not active")

        run.status = "STOPPED"
        run.ended_at = datetime.utcnow()

        db.commit()
        logger.info(f"Stopped paper run {run_id}")

        return {"status": "stopped", "ended_at": run.ended_at}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop paper run {run_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to stop paper run") from e


# Trade History and Monitoring
@router.get("/runs/{run_id}/trades", response_model=list[TradeResponse])
async def get_trades(
    run_id: int,
    status: str | None = Query(None, description="Filter by trade status"),
    theory_name: str | None = Query(None, description="Filter by theory"),
    ticker: str | None = Query(None, description="Filter by ticker"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Get trade history for a paper run with filtering options"""
    verify_dev_only()

    try:
        query = db.query(Trade).filter(Trade.paper_run_id == run_id)

        if status:
            query = query.filter(Trade.status == status)
        if theory_name:
            query = query.filter(Trade.theory_name == theory_name)
        if ticker:
            query = query.filter(Trade.ticker == ticker)

        trades = query.order_by(Trade.signal_time.desc()).offset(offset).limit(limit).all()

        return [
            TradeResponse(
                id=trade.id,
                trade_id=trade.trade_id,
                ticker=trade.ticker,
                direction=trade.direction,
                quantity=trade.quantity,
                theory_name=trade.theory_name,
                status=trade.status,
                signal_time=trade.signal_time,
                fill_price=trade.fill_price,
                realized_pnl=trade.realized_pnl,
            )
            for trade in trades
        ]

    except Exception as e:
        logger.error(f"Failed to get trades for run {run_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve trades") from e


# Theory Performance Monitoring
@router.get("/runs/{run_id}/theories", response_model=list[TheoryPerfResponse])
async def get_theory_performance(
    run_id: int,
    status: str | None = Query(None, description="Filter by theory status"),
    db: Session = Depends(get_db),
):
    """Get theory performance metrics for a paper run"""
    verify_dev_only()

    try:
        query = db.query(TheoryPerf).filter(TheoryPerf.paper_run_id == run_id)

        if status:
            query = query.filter(TheoryPerf.theory_status == status)

        theories = query.order_by(TheoryPerf.total_pnl.desc()).all()

        return [
            TheoryPerfResponse(
                theory_name=theory.theory_name,
                status=theory.theory_status,
                current_allocation=theory.current_allocation,
                total_trades_executed=theory.total_trades_executed,
                total_pnl=theory.total_pnl,
                win_rate=theory.win_rate,
                sharpe_ratio=theory.sharpe_ratio,
                avg_fill_latency_ms=theory.avg_fill_latency_ms,
            )
            for theory in theories
        ]

    except Exception as e:
        logger.error(f"Failed to get theory performance for run {run_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve theory performance") from e


@router.post("/runs/{run_id}/theories/{theory_name}/pause", response_model=None)
async def pause_theory(run_id: int, theory_name: str, db: Session = Depends(get_db)):
    """Pause a specific theory (stop receiving new allocations)"""
    verify_dev_only()

    try:
        theory = (
            db.query(TheoryPerf)
            .filter(TheoryPerf.paper_run_id == run_id)
            .filter(TheoryPerf.theory_name == theory_name)
            .first()
        )

        if not theory:
            raise HTTPException(status_code=404, detail="Theory not found")

        theory.theory_status = TheoryStatus.PAUSED.value
        theory.current_allocation = 0.0

        db.commit()
        logger.info(f"Paused theory {theory_name} for run {run_id}")

        return {"status": "paused", "theory_name": theory_name}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to pause theory {theory_name}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to pause theory") from e


# System Health and Diagnostics
@router.get("/runs/{run_id}/stats", response_model=None)
async def get_run_stats(run_id: int, db: Session = Depends(get_db)):
    """Get detailed statistics and health metrics for a paper run"""
    verify_dev_only()

    try:
        run = db.query(PaperRun).filter(PaperRun.id == run_id).first()
        if not run:
            raise HTTPException(status_code=404, detail="Paper run not found")

        # Get recent trade statistics
        recent_trades = (
            db.query(Trade)
            .filter(Trade.paper_run_id == run_id)
            .filter(Trade.signal_time >= datetime.utcnow() - timedelta(hours=1))
            .count()
        )

        # Get theory distribution
        theory_counts = (
            db.query(TheoryPerf.theory_name, TheoryPerf.total_trades_executed)
            .filter(TheoryPerf.paper_run_id == run_id)
            .all()
        )

        # Get error rate
        failed_trades = (
            db.query(Trade)
            .filter(Trade.paper_run_id == run_id)
            .filter(Trade.status.in_([TradeStatus.FAILED.value, TradeStatus.REJECTED.value]))
            .count()
        )

        error_rate = failed_trades / max(run.total_trades, 1)

        return {
            "run_id": run_id,
            "status": run.status,
            "uptime_minutes": (datetime.utcnow() - run.started_at).total_seconds() / 60,
            "total_trades": run.total_trades,
            "trades_last_hour": recent_trades,
            "current_balance": float(run.current_balance),
            "total_pnl": float(run.total_pnl),
            "win_rate": run.win_rate,
            "error_rate": error_rate,
            "avg_fill_latency_ms": run.avg_fill_latency_ms,
            "theory_distribution": {theory: int(count) for theory, count in theory_counts},
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get stats for run {run_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve run statistics") from e


# Model Snapshots and Learning Metrics
@router.get("/runs/{run_id}/models", response_model=None)
async def get_model_snapshots(
    run_id: int,
    model_name: str | None = Query(None, description="Filter by model name"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Get model snapshots and learning progress for a paper run"""
    verify_dev_only()

    try:
        query = db.query(ModelSnapshot).filter(ModelSnapshot.paper_run_id == run_id)

        if model_name:
            query = query.filter(ModelSnapshot.model_name == model_name)

        snapshots = query.order_by(ModelSnapshot.created_at.desc()).limit(limit).all()

        return [
            {
                "id": snapshot.id,
                "model_name": snapshot.model_name,
                "model_type": snapshot.model_type,
                "version": snapshot.version,
                "samples_seen": snapshot.samples_seen,
                "training_accuracy": snapshot.training_accuracy,
                "validation_accuracy": snapshot.validation_accuracy,
                "brier_score": snapshot.brier_score,
                "trades_since_last": snapshot.trades_since_last,
                "pnl_since_last": (
                    float(snapshot.pnl_since_last) if snapshot.pnl_since_last else None
                ),
                "created_at": snapshot.created_at,
            }
            for snapshot in snapshots
        ]

    except Exception as e:
        logger.error(f"Failed to get model snapshots for run {run_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve model snapshots") from e


# Emergency Controls
@router.post("/emergency/stop_all", response_model=None)
async def emergency_stop_all(db: Session = Depends(get_db)):
    """Emergency stop all active paper trading runs"""
    verify_dev_only()

    try:
        active_runs = db.query(PaperRun).filter(PaperRun.status == "ACTIVE").all()

        stopped_count = 0
        for run in active_runs:
            run.status = "STOPPED"
            run.ended_at = datetime.utcnow()
            stopped_count += 1

        db.commit()

        logger.warning(f"Emergency stop executed - stopped {stopped_count} paper runs")

        return {
            "status": "emergency_stop_complete",
            "runs_stopped": stopped_count,
            "timestamp": datetime.utcnow(),
        }

    except Exception as e:
        logger.error(f"Emergency stop failed: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Emergency stop failed") from e


@router.get("/health", response_model=None)
async def paper_lab_health():
    """Comprehensive paper trading system health check with backoff/caching.

    Acceptance checks (lightweight):
    - When Postgres is down, first call returns 503 and subsequent calls before next_retry_at
      return cached DOWN without hammering DB.
    - On success, result is cached for ~10s.
    """
    verify_dev_only()

    # If DB is not connected, return a clean 503 JSON without raising
    if not bool(db_state.get("connected")):
        return JSONResponse(status_code=503, content={"status": "down", "reason": "db_unavailable"})

    # Serve cached response if not time to retry yet
    now = monotonic_now()
    if (
        _HEALTH_STATE.cached_payload
        and now < _HEALTH_STATE.cache_expiry_at
        and not _HEALTH_STATE.should_try_check()
    ):
        if _HEALTH_STATE.last_status == "DOWN":
            return JSONResponse(status_code=503, content=_HEALTH_STATE.cached_payload)
        return _HEALTH_STATE.cached_payload

    try:
        from sqlalchemy import func, text

        from app.models.base import get_db
        from app.models.paper import Trade
        from app.paper.ingest import get_brain_queue_metrics, get_learner_metrics
        from app.paper.learner_gateway import get_learner_gateway
        from app.tasks.paper_worker import get_paper_worker

        # Get paper worker status
        paper_worker = get_paper_worker()
        paper_enabled = paper_worker is not None and paper_worker.is_running

        # Check strict isolation (no live broker env vars)
        from app.utils.isolation import check_strict_isolation

        strict_isolation, detected_vars = check_strict_isolation()

        # Database health check and trade verification
        db_ok = True
        recent_trades_5m = 0
        total_trades_today = 0
        last_trade_at = None
        last_error = None

        try:
            db: Session = next(get_db())

            # Count recent trades in last 5 minutes
            recent_result = (
                db.query(func.count(Trade.id))
                .filter(Trade.signal_time >= text("NOW() - INTERVAL '5 minutes'"))
                .scalar()
            )
            recent_trades_5m = recent_result or 0

            # Count today's trades
            today_result = (
                db.query(func.count(Trade.id))
                .filter(Trade.signal_time >= text("CURRENT_DATE"))
                .scalar()
            )
            total_trades_today = today_result or 0

            # Get last trade timestamp
            last_trade = db.query(func.max(Trade.signal_time)).scalar()
            if last_trade:
                last_trade_at = last_trade.isoformat() + "Z"

            db.close()

        except Exception as e:
            db_ok = False
            last_error = f"Database error: {e!s}"
            # Record failure with backoff and return cached DOWN immediately
            _HEALTH_STATE.record_failure(e)
            return JSONResponse(
                status_code=503, content=_HEALTH_STATE.cached_payload or {"status": "DOWN"}
            )

        # Get brain queue metrics (with fallbacks)
        try:
            brain_metrics = get_brain_queue_metrics()
        except Exception as e:
            brain_metrics = {"queue_depth": 0, "events_total": 0, "events_5m": 0}
            logger.warning(f"Could not get brain metrics: {e}")

        # Get learner metrics (with fallbacks)
        try:
            learner_metrics = get_learner_metrics()
        except Exception as e:
            learner_metrics = {"batches_total": 0, "batches_5m": 0, "learner_available": False}
            logger.warning(f"Could not get learner metrics: {e}")

        # Get learner gateway status
        try:
            gateway = get_learner_gateway()
            gateway_running = gateway is not None and gateway.is_running
        except Exception as e:
            gateway_running = False
            logger.warning(f"Could not get gateway status: {e}")

        # Worker metrics
        open_trades = 0
        signals_5m = recent_trades_5m  # Fallback estimate
        orders_5m = recent_trades_5m  # Fallback estimate
        fills_5m = recent_trades_5m  # Filled trades

        if paper_worker:
            try:
                worker_status = await paper_worker.get_status()
                engine_status = worker_status.get("engine_status", {})
                stats = engine_status.get("stats", {})
                open_trades = stats.get("open_trades", 0)
            except Exception as e:
                logger.warning(f"Worker status error: {e}")
                if not last_error:
                    last_error = f"Worker status error: {e!s}"

        # Build comprehensive health response
        health_data = {
            "paper_enabled": paper_enabled,
            "strict_isolation": strict_isolation,
            "broker": "paper" if paper_enabled else "unknown",
            "signals_5m": signals_5m,
            "orders_5m": orders_5m,
            "fills_5m": fills_5m,
            "recent_trades_5m": recent_trades_5m,
            "total_trades_today": total_trades_today,
            "last_trade_at": last_trade_at,
            "open_trades": open_trades,
            "queue_depth": brain_metrics.get("queue_depth", 0),
            "learner_batches_5m": learner_metrics.get("batches_5m", 0),
            "db_ok": db_ok,
            "gateway_running": gateway_running,
            "last_error": last_error,
            "brain_metrics": brain_metrics,
            "learner_metrics": learner_metrics,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        # Add detected live broker vars to error if isolation failed
        if not strict_isolation:
            health_data["detected_live_vars"] = detected_vars
            if not last_error:
                last_error = (
                    f"Live broker environment variables detected: {', '.join(detected_vars)}"
                )
                health_data["last_error"] = last_error

        # Return appropriate status codes; record success once we formed payload
        # If isolation failed critically or trade activity missing, still count as DOWN
        if paper_enabled and not strict_isolation:
            _HEALTH_STATE.record_failure(RuntimeError("strict_isolation_failed"))
            payload = {**health_data, "status": "unhealthy", "reason": "strict_isolation_failed"}
            return JSONResponse(status_code=503, content=payload)

        if paper_enabled and recent_trades_5m == 0 and paper_worker and paper_worker.is_running:
            _HEALTH_STATE.record_failure(RuntimeError("no_recent_trades"))
            payload = {**health_data, "status": "unhealthy", "reason": "no_recent_trades"}
            return JSONResponse(status_code=503, content=payload)

        # Success path: cache for 10s
        _HEALTH_STATE.record_success(health_data)
        return _HEALTH_STATE.cached_payload

    except Exception as e:
        # Any unexpected error: enter DOWN/backoff and return cached DOWN
        _HEALTH_STATE.record_failure(e)
        logger.error("Health check failed", extra={"error": repr(e)})
        return JSONResponse(
            status_code=503, content=_HEALTH_STATE.cached_payload or {"status": "DOWN"}
        )
