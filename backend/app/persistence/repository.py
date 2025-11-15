from __future__ import annotations

import uuid
from collections.abc import Iterable
from datetime import datetime
from typing import Any, cast

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.persistence.models import (
    BanditSnapshot,
    LearnerCheckpoint,
    PaperRun,
    PnLPoint,
    Position,
    QueueSnapshot,
    Trade,
)


# Note: Idempotency is implemented by natural keys and catching IntegrityError on insert.


def open_or_resume_run(db: Session, meta: dict[str, Any]) -> str:
    """Open a new run or resume the latest open run.

    Returns run_id.
    """
    # Find latest open (ended_at is NULL)
    run = (
        db.execute(
            select(PaperRun)
            .where(PaperRun.ended_at.is_(None))
            .order_by(PaperRun.started_at.desc())
        )
        .scalars()
        .first()
    )
    if run:
        # SQLAlchemy attributes are dynamically instrumented; cast for type-checkers
        return cast(str, run.id)

    run_id = meta.get("run_id") or str(uuid.uuid4())
    run = PaperRun(id=run_id, started_at=datetime.utcnow(), meta=meta)
    db.add(run)
    db.commit()
    return run_id


def close_run(db: Session, run_id: str) -> None:
    run = db.get(PaperRun, run_id)
    if not run:
        return
    if run.ended_at is None:
        # Ignore SQLAlchemy typing noise for ORM attribute assignment
        run.ended_at = datetime.utcnow()  # type: ignore[assignment]
        db.add(run)
        db.commit()


def append_trade(db: Session, run_id: str, trade: dict[str, Any]) -> None:
    t = Trade(
        id=trade.get("id") or trade.get("trade_id"),
        symbol=trade["symbol"],
        side=trade["side"],
        qty=int(trade["qty"]),
        price=float(trade["price"]),
        ts=trade.get("ts") or datetime.utcnow(),
        fees=float(trade.get("fees", 0.0)),
        slippage_bps=float(trade.get("slippage_bps", 0.0)),
        run_id=run_id,
        raw=trade,
    )
    try:
        db.add(t)
        db.commit()
    except IntegrityError:
        db.rollback()
        # idempotent - already exists


def upsert_position(
    db: Session,
    run_id: str,
    symbol: str,
    qty: int,
    avg_price: float,
    ts: datetime | None = None,
    row_id: str | None = None,
) -> None:
    ts = ts or datetime.utcnow()
    # Try existing by (run_id, symbol)
    existing = (
        db.execute(
            select(Position).where(Position.run_id == run_id, Position.symbol == symbol)
        )
        .scalars()
        .first()
    )
    if existing:
        existing.qty = int(qty)  # type: ignore[assignment]
        existing.avg_price = float(avg_price)  # type: ignore[assignment]
        existing.ts = ts  # type: ignore[assignment]
        db.add(existing)
        db.commit()
        return
    # Insert new
    p = Position(
        id=row_id or str(uuid.uuid4()),
        run_id=run_id,
        symbol=symbol,
        qty=int(qty),
        avg_price=float(avg_price),
        ts=ts,
    )
    try:
        db.add(p)
        db.commit()
    except IntegrityError:
        db.rollback()


def append_pnl_points(
    db: Session, run_id: str, points: Iterable[dict[str, Any]]
) -> None:
    for pt in points:
        p = PnLPoint(
            run_id=run_id,
            ts=pt.get("ts") or datetime.utcnow(),
            equity=float(pt["equity"]),
            idx=int(pt.get("idx", 0)),
        )
        db.add(p)
    db.commit()


def save_bandit_snapshot(db: Session, run_id: str, payload: dict[str, Any]) -> None:
    db.add(BanditSnapshot(run_id=run_id, ts=datetime.utcnow(), payload=payload))
    db.commit()


def save_learner_checkpoint(
    db: Session,
    run_id: str,
    algo: str | None,
    model_bytes: bytes,
    meta: dict[str, Any] | None,
) -> None:
    db.add(
        LearnerCheckpoint(
            run_id=run_id,
            ts=datetime.utcnow(),
            algo=algo or "",
            bytes=model_bytes,
            meta=meta,
        )
    )
    db.commit()


def save_queue_snapshot(db: Session, run_id: str, payload: dict[str, Any]) -> None:
    db.add(QueueSnapshot(run_id=run_id, ts=datetime.utcnow(), payload=payload))
    db.commit()


def load_latest_run(db: Session) -> PaperRun | None:
    return (
        db.execute(select(PaperRun).order_by(PaperRun.started_at.desc()))
        .scalars()
        .first()
    )


def load_positions(db: Session, run_id: str) -> list[Position]:
    return cast(
        list[Position],
        db.execute(select(Position).where(Position.run_id == run_id)).scalars().all(),
    )


def load_trades(db: Session, run_id: str) -> list[Trade]:
    return cast(
        list[Trade],
        db.execute(select(Trade).where(Trade.run_id == run_id)).scalars().all(),
    )


def load_pnl_points(db: Session, run_id: str) -> list[PnLPoint]:
    return cast(
        list[PnLPoint],
        db.execute(
            select(PnLPoint)
            .where(PnLPoint.run_id == run_id)
            .order_by(PnLPoint.ts.asc())
        )
        .scalars()
        .all(),
    )


def load_bandit_latest(db: Session, run_id: str) -> BanditSnapshot | None:
    return (
        db.execute(
            select(BanditSnapshot)
            .where(BanditSnapshot.run_id == run_id)
            .order_by(BanditSnapshot.ts.desc())
        )
        .scalars()
        .first()
    )


def load_learner_latest(db: Session, run_id: str) -> LearnerCheckpoint | None:
    return (
        db.execute(
            select(LearnerCheckpoint)
            .where(LearnerCheckpoint.run_id == run_id)
            .order_by(LearnerCheckpoint.ts.desc())
        )
        .scalars()
        .first()
    )


def load_queue_latest(db: Session, run_id: str) -> QueueSnapshot | None:
    return (
        db.execute(
            select(QueueSnapshot)
            .where(QueueSnapshot.run_id == run_id)
            .order_by(QueueSnapshot.ts.desc())
        )
        .scalars()
        .first()
    )
