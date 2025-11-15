# app/models/trading.py
from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .base import Base


class SignalType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    NEUTRAL = "NEUTRAL"


class SignalStatus(str, Enum):
    PENDING = "PENDING"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class TradingSignal(Base):
    __tablename__ = "trading_signals"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), nullable=False, index=True)
    signal_type = Column(String(20), nullable=False)  # BUY, SELL, NEUTRAL
    confidence = Column(Numeric(5, 4), nullable=False)  # 0.0000 to 1.0000
    price_target = Column(Numeric(12, 4), nullable=True)
    stop_loss = Column(Numeric(12, 4), nullable=True)

    # Status and execution
    status = Column(String(20), default=SignalStatus.PENDING.value)
    executed_price = Column(Numeric(12, 4), nullable=True)
    executed_quantity = Column(Numeric(12, 4), nullable=True)

    # Metadata
    reason = Column(Text, nullable=True)
    features = Column(JSON, nullable=True)  # Technical indicators used
    correlation_id = Column(String(36), nullable=True, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    executed_at = Column(DateTime, nullable=True)

    # Relationships
    backtest_results = relationship("BacktestResult", back_populates="signal")
    positions = relationship("Position", back_populates="signal")


class BacktestResult(Base):
    __tablename__ = "backtest_results"

    id = Column(Integer, primary_key=True, index=True)
    signal_id = Column(Integer, ForeignKey("trading_signals.id"), nullable=False)

    # Backtest parameters
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    initial_capital = Column(Numeric(12, 2), nullable=False)

    # Results
    total_return = Column(Numeric(8, 4), nullable=False)  # Percentage
    max_drawdown = Column(Numeric(8, 4), nullable=False)
    sharpe_ratio = Column(Numeric(6, 4), nullable=True)
    win_rate = Column(Numeric(5, 4), nullable=True)
    total_trades = Column(Integer, nullable=False)

    # Detailed metrics
    metrics = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    signal = relationship("TradingSignal", back_populates="backtest_results")


class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    # Portfolio settings
    initial_capital = Column(Numeric(12, 2), nullable=False)
    current_value = Column(Numeric(12, 2), nullable=False)
    cash_balance = Column(Numeric(12, 2), nullable=False)

    # Risk management
    max_position_size = Column(Numeric(5, 4), default=0.10)  # 10% max per position
    risk_tolerance = Column(
        String(20), default="MODERATE"
    )  # CONSERVATIVE, MODERATE, AGGRESSIVE

    # Status
    is_active = Column(Boolean, default=True)
    is_paper_trading = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    positions = relationship("Position", back_populates="portfolio")


class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    signal_id = Column(Integer, ForeignKey("trading_signals.id"), nullable=True)

    # Position details
    ticker = Column(String(20), nullable=False, index=True)
    quantity = Column(Numeric(12, 4), nullable=False)
    avg_entry_price = Column(Numeric(12, 4), nullable=False)
    current_price = Column(Numeric(12, 4), nullable=True)

    # P&L tracking
    unrealized_pnl = Column(Numeric(12, 2), nullable=True)
    realized_pnl = Column(Numeric(12, 2), default=0.0)

    # Position management
    stop_loss = Column(Numeric(12, 4), nullable=True)
    take_profit = Column(Numeric(12, 4), nullable=True)

    # Status
    is_open = Column(Boolean, default=True)

    # Timestamps
    opened_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    portfolio = relationship("Portfolio", back_populates="positions")
    signal = relationship("TradingSignal", back_populates="positions")
