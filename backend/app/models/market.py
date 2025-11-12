# app/models/market.py
from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Index, Integer, Numeric, String, Text

from .base import Base


class MarketData(Base):
    __tablename__ = "market_data"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), nullable=False, index=True)

    # OHLCV data
    open_price = Column(Numeric(12, 4), nullable=False)
    high_price = Column(Numeric(12, 4), nullable=False)
    low_price = Column(Numeric(12, 4), nullable=False)
    close_price = Column(Numeric(12, 4), nullable=False)
    volume = Column(Numeric(15, 0), nullable=True)

    # Adjusted prices
    adj_close = Column(Numeric(12, 4), nullable=True)

    # Metadata
    data_date = Column(DateTime, nullable=False, index=True)
    provider = Column(String(50), nullable=True)
    interval = Column(String(10), nullable=False)  # 1d, 1h, 5m, etc.

    created_at = Column(DateTime, default=datetime.utcnow)

    # Composite index for efficient queries
    __table_args__ = (
        Index("ix_market_data_ticker_date", "ticker", "data_date"),
        Index("ix_market_data_ticker_interval", "ticker", "interval"),
    )


class NewsItem(Base):
    __tablename__ = "news_items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=True)

    # Source information
    source = Column(String(100), nullable=True)
    author = Column(String(200), nullable=True)
    url = Column(String(1000), nullable=True, unique=True)

    # Classification
    category = Column(String(50), nullable=True)
    sentiment = Column(Numeric(3, 2), nullable=True)  # -1.00 to 1.00
    relevance_score = Column(Numeric(3, 2), nullable=True)

    # Related symbols
    mentioned_tickers = Column(JSON, default=list)

    # Timestamps
    published_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Search optimization
    __table_args__ = (
        Index("ix_news_published_category", "published_at", "category"),
        Index("ix_news_sentiment", "sentiment"),
    )
