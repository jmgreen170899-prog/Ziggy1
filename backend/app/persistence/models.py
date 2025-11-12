from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    UniqueConstraint,
)

from app.models.base import Base


class PaperRun(Base):
    __tablename__ = "durable_paper_runs"

    id = Column(String(64), primary_key=True)  # uuid string
    started_at = Column(DateTime(timezone=False), nullable=False, default=datetime.utcnow)
    ended_at = Column(DateTime(timezone=False), nullable=True)
    meta = Column(JSON, nullable=True)  # universe, theories, params_json


class Trade(Base):
    __tablename__ = "durable_paper_trades"

    id = Column(String(64), primary_key=True)  # trade_id / signal_id
    symbol = Column(String(32), nullable=False)
    side = Column(String(8), nullable=False)
    qty = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    ts = Column(DateTime(timezone=False), nullable=False, default=datetime.utcnow)
    fees = Column(Float, nullable=True)
    slippage_bps = Column(Float, nullable=True)
    run_id = Column(String(64), ForeignKey("durable_paper_runs.id"), nullable=False)
    raw = Column(JSON, nullable=True)


class Position(Base):
    __tablename__ = "durable_paper_positions"

    id = Column(String(64), primary_key=True)  # uuid for position row
    run_id = Column(String(64), ForeignKey("durable_paper_runs.id"), nullable=False)
    symbol = Column(String(32), nullable=False)
    qty = Column(Integer, nullable=False)
    avg_price = Column(Float, nullable=False)
    ts = Column(DateTime(timezone=False), nullable=False, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("run_id", "symbol", name="uq_positions_run_symbol"),)


class PnLPoint(Base):
    __tablename__ = "durable_paper_pnl_points"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    run_id = Column(String(64), ForeignKey("durable_paper_runs.id"), nullable=False)
    idx = Column(Integer, nullable=True)
    ts = Column(DateTime(timezone=False), nullable=False, default=datetime.utcnow)
    equity = Column(Float, nullable=False)


class BanditSnapshot(Base):
    __tablename__ = "durable_bandit_snapshots"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    run_id = Column(String(64), ForeignKey("durable_paper_runs.id"), nullable=False)
    ts = Column(DateTime(timezone=False), nullable=False, default=datetime.utcnow)
    payload = Column(JSON, nullable=False)


class LearnerCheckpoint(Base):
    __tablename__ = "durable_learner_checkpoints"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    run_id = Column(String(64), ForeignKey("durable_paper_runs.id"), nullable=False)
    ts = Column(DateTime(timezone=False), nullable=False, default=datetime.utcnow)
    algo = Column(String(64), nullable=True)
    bytes = Column(LargeBinary, nullable=False)  # model bytes or serialized payload
    meta = Column(JSON, nullable=True)


class QueueSnapshot(Base):
    __tablename__ = "durable_queue_snapshots"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    run_id = Column(String(64), ForeignKey("durable_paper_runs.id"), nullable=False)
    ts = Column(DateTime(timezone=False), nullable=False, default=datetime.utcnow)
    payload = Column(JSON, nullable=False)
