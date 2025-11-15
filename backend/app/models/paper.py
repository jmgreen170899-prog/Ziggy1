# app/models/paper.py
"""
Paper Trading Lab Database Models

These models support the autonomous paper trading lab with thousands of
concurrent micro-trades, online learning, and theory performance tracking.
All operations are dev-only with strict isolation from live brokers.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .base import Base


class TradeStatus(str, Enum):
    """Status of a paper trade"""

    PENDING = "PENDING"  # Trade signal generated, not yet executed
    FILLED = "FILLED"  # Trade executed successfully
    PARTIAL = "PARTIAL"  # Partially filled
    CANCELLED = "CANCELLED"  # Trade cancelled before execution
    REJECTED = "REJECTED"  # Trade rejected by paper broker
    FAILED = "FAILED"  # Trade failed due to error


class TradeDirection(str, Enum):
    """Direction of trade"""

    LONG = "LONG"  # Buy to open
    SHORT = "SHORT"  # Sell to open
    CLOSE = "CLOSE"  # Close existing position


class TheoryStatus(str, Enum):
    """Status of trading theory"""

    ACTIVE = "ACTIVE"  # Theory is active and receiving allocations
    PAUSED = "PAUSED"  # Theory temporarily paused
    DISABLED = "DISABLED"  # Theory disabled due to poor performance
    TESTING = "TESTING"  # Theory in testing phase


class PaperRun(Base):
    """
    A paper trading run represents a continuous session of the paper trading lab.
    Each run has its own configuration, performance tracking, and isolated state.
    """

    __tablename__ = "paper_runs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    # Configuration
    config = Column(JSON, nullable=False)  # Full config snapshot
    initial_balance = Column(Numeric(12, 2), nullable=False, default=100000.00)
    max_trades_per_minute = Column(Integer, nullable=False, default=100)

    # Status and timing
    status = Column(
        String(20), nullable=False, default="ACTIVE"
    )  # ACTIVE, PAUSED, STOPPED
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    # Performance summary (updated periodically)
    total_trades = Column(Integer, nullable=False, default=0)
    total_pnl = Column(Numeric(12, 2), nullable=False, default=0.0)
    current_balance = Column(Numeric(12, 2), nullable=False, default=100000.00)
    max_drawdown = Column(Numeric(8, 4), nullable=True)  # Percentage
    win_rate = Column(Numeric(5, 4), nullable=True)  # 0.0 to 1.0

    # System metrics
    avg_fill_latency_ms = Column(Numeric(8, 2), nullable=True)
    error_rate = Column(Numeric(5, 4), nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    trades = relationship(
        "Trade", back_populates="paper_run", cascade="all, delete-orphan"
    )
    theory_perfs = relationship(
        "TheoryPerf", back_populates="paper_run", cascade="all, delete-orphan"
    )
    model_snapshots = relationship(
        "ModelSnapshot", back_populates="paper_run", cascade="all, delete-orphan"
    )


class Trade(Base):
    """
    Individual paper trade with full execution details, theory attribution,
    and performance tracking. Supports thousands of concurrent micro-trades.
    """

    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    paper_run_id = Column(
        Integer, ForeignKey("paper_runs.id"), nullable=False, index=True
    )

    # Trade identification
    trade_id = Column(String(36), nullable=False, unique=True, index=True)  # UUID
    correlation_id = Column(
        String(36), nullable=True, index=True
    )  # For grouping related trades

    # Market data
    ticker = Column(String(20), nullable=False, index=True)
    direction = Column(String(10), nullable=False)  # LONG, SHORT, CLOSE
    quantity = Column(Numeric(12, 4), nullable=False)

    # Pricing and execution
    signal_price = Column(Numeric(12, 4), nullable=False)  # Price when signal generated
    limit_price = Column(Numeric(12, 4), nullable=True)  # Limit price if applicable
    fill_price = Column(Numeric(12, 4), nullable=True)  # Actual execution price
    slippage = Column(Numeric(8, 4), nullable=True)  # Actual slippage applied
    commission = Column(Numeric(8, 2), nullable=True)  # Commission charged

    # Theory attribution
    theory_name = Column(String(50), nullable=False, index=True)
    theory_confidence = Column(Numeric(5, 4), nullable=False)  # 0.0 to 1.0
    theory_features = Column(JSON, nullable=True)  # Features used by theory

    # Execution details
    status = Column(String(20), nullable=False, default=TradeStatus.PENDING.value)
    execution_latency_ms = Column(Numeric(8, 2), nullable=True)
    error_message = Column(Text, nullable=True)

    # P&L tracking
    realized_pnl = Column(Numeric(12, 2), nullable=True)
    unrealized_pnl = Column(Numeric(12, 2), nullable=True)
    holding_period_minutes = Column(Integer, nullable=True)

    # Labels and learning
    labels = Column(JSON, nullable=True)  # Forward-looking labels for learning
    prediction_scores = Column(JSON, nullable=True)  # Model predictions

    # Timestamps
    signal_time = Column(DateTime, nullable=False, index=True)
    submitted_at = Column(DateTime, nullable=True)
    filled_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    paper_run = relationship("PaperRun", back_populates="trades")

    # Indexes for performance
    __table_args__ = (
        Index(
            "ix_trades_paper_run_ticker_time", "paper_run_id", "ticker", "signal_time"
        ),
        Index("ix_trades_theory_status_time", "theory_name", "status", "signal_time"),
        Index("ix_trades_status_filled_at", "status", "filled_at"),
    )


class TheoryPerf(Base):
    """
    Theory performance tracking for bandit allocation and performance analysis.
    Maintains rolling statistics and historical performance metrics.
    """

    __tablename__ = "theory_perfs"

    id = Column(Integer, primary_key=True, index=True)
    paper_run_id = Column(
        Integer, ForeignKey("paper_runs.id"), nullable=False, index=True
    )

    # Theory identification
    theory_name = Column(String(50), nullable=False, index=True)
    theory_status = Column(
        String(20), nullable=False, default=TheoryStatus.ACTIVE.value
    )

    # Allocation and usage
    current_allocation = Column(
        Numeric(5, 4), nullable=False, default=0.0
    )  # 0.0 to 1.0
    total_signals_generated = Column(Integer, nullable=False, default=0)
    total_trades_executed = Column(Integer, nullable=False, default=0)

    # Performance metrics
    total_pnl = Column(Numeric(12, 2), nullable=False, default=0.0)
    win_rate = Column(Numeric(5, 4), nullable=True)  # 0.0 to 1.0
    avg_trade_pnl = Column(Numeric(8, 2), nullable=True)
    sharpe_ratio = Column(Numeric(6, 4), nullable=True)
    max_drawdown = Column(Numeric(8, 4), nullable=True)

    # Bandit algorithm state
    bandit_stats = Column(JSON, nullable=True)  # Algorithm-specific statistics
    confidence_interval = Column(JSON, nullable=True)  # Upper/lower bounds

    # Rolling window metrics (configurable periods)
    rolling_1h_pnl = Column(Numeric(12, 2), nullable=True)
    rolling_24h_pnl = Column(Numeric(12, 2), nullable=True)
    rolling_7d_pnl = Column(Numeric(12, 2), nullable=True)

    # Execution quality
    avg_fill_latency_ms = Column(Numeric(8, 2), nullable=True)
    fill_rate = Column(Numeric(5, 4), nullable=True)  # Successful fills / attempts
    error_rate = Column(Numeric(5, 4), nullable=True)

    # Metadata
    last_signal_time = Column(DateTime, nullable=True)
    last_trade_time = Column(DateTime, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    paper_run = relationship("PaperRun", back_populates="theory_perfs")

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint(
            "paper_run_id", "theory_name", name="uq_theory_perf_run_theory"
        ),
        Index(
            "ix_theory_perf_status_allocation", "theory_status", "current_allocation"
        ),
        Index("ix_theory_perf_updated_at", "updated_at"),
    )


class ModelSnapshot(Base):
    """
    Snapshots of online learning models for reproducibility and analysis.
    Stores model state, hyperparameters, and performance metrics.
    """

    __tablename__ = "model_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    paper_run_id = Column(
        Integer, ForeignKey("paper_runs.id"), nullable=False, index=True
    )

    # Model identification
    model_name = Column(String(50), nullable=False, index=True)
    model_type = Column(String(30), nullable=False)  # sklearn, pytorch, fallback
    version = Column(String(20), nullable=False)
    snapshot_reason = Column(
        String(50), nullable=False
    )  # periodic, performance_change, manual

    # Model state
    model_params = Column(JSON, nullable=False)  # Hyperparameters
    model_state = Column(JSON, nullable=True)  # Serialized model weights/state
    model_metadata = Column(JSON, nullable=True)  # Additional model info

    # Training metrics
    samples_seen = Column(Integer, nullable=False, default=0)
    training_accuracy = Column(Numeric(5, 4), nullable=True)
    validation_accuracy = Column(Numeric(5, 4), nullable=True)
    loss_value = Column(Numeric(10, 6), nullable=True)

    # Calibration metrics
    calibration_slope = Column(Numeric(6, 4), nullable=True)
    calibration_intercept = Column(Numeric(6, 4), nullable=True)
    brier_score = Column(Numeric(6, 4), nullable=True)

    # Feature importance (top 10)
    feature_importance = Column(JSON, nullable=True)

    # Performance since last snapshot
    trades_since_last = Column(Integer, nullable=False, default=0)
    pnl_since_last = Column(Numeric(12, 2), nullable=False, default=0.0)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    paper_run = relationship("PaperRun", back_populates="model_snapshots")

    # Indexes
    __table_args__ = (
        Index("ix_model_snapshot_name_created", "model_name", "created_at"),
        Index("ix_model_snapshot_type_reason", "model_type", "snapshot_reason"),
    )


class TradingSession(Base):
    """
    Real-time trading session state for maintaining continuity across restarts.
    Tracks active positions, pending orders, and system state.
    """

    __tablename__ = "trading_sessions"

    id = Column(Integer, primary_key=True, index=True)
    paper_run_id = Column(
        Integer, ForeignKey("paper_runs.id"), nullable=False, index=True
    )

    # Session identification
    session_id = Column(String(36), nullable=False, unique=True, index=True)  # UUID
    hostname = Column(String(100), nullable=False)
    process_id = Column(Integer, nullable=False)

    # System state
    last_heartbeat = Column(DateTime, nullable=False, default=datetime.utcnow)
    active_positions = Column(JSON, nullable=True)  # Current position state
    pending_orders = Column(JSON, nullable=True)  # Unfinished orders
    bandit_state = Column(JSON, nullable=True)  # Bandit algorithm state
    feature_cache = Column(JSON, nullable=True)  # Recent feature computations

    # Counters and metrics
    trades_this_session = Column(Integer, nullable=False, default=0)
    signals_generated = Column(Integer, nullable=False, default=0)
    errors_encountered = Column(Integer, nullable=False, default=0)

    # Status
    is_active = Column(Boolean, nullable=False, default=True)

    # Timestamps
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    # Relationships
    paper_run = relationship("PaperRun")

    # Indexes
    __table_args__ = (
        Index("ix_trading_session_active_heartbeat", "is_active", "last_heartbeat"),
    )
