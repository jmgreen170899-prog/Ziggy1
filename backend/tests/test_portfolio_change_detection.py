import asyncio
from types import SimpleNamespace
from typing import cast

from app.core.websocket import ConnectionManager
from app.services.portfolio_streaming import PortfolioStreamer


def test_positions_order_independent_no_change():
    streamer = PortfolioStreamer(connection_manager=cast(ConnectionManager, SimpleNamespace()))
    # Seed last data
    streamer.last_portfolio_data = {"total_value": 1000.0, "daily_pnl": 0.0}
    streamer.last_positions_data = [
        {"symbol": "AAPL", "quantity": 10, "current_price": 100.0, "market_value": 1000.0},
        {"symbol": "MSFT", "quantity": 5, "current_price": 200.0, "market_value": 1000.0},
    ]

    # Same positions, different order
    current_portfolio = {"total_value": 1000.0, "daily_pnl": 0.0}
    current_positions = [
        {"symbol": "MSFT", "quantity": 5, "current_price": 200.0, "market_value": 1000.0},
        {"symbol": "AAPL", "quantity": 10, "current_price": 100.0, "market_value": 1000.0},
    ]

    changed = asyncio.run(streamer._has_portfolio_changed(current_portfolio, current_positions))
    assert changed is False


def test_positions_small_noise_no_change():
    streamer = PortfolioStreamer(connection_manager=cast(ConnectionManager, SimpleNamespace()))
    streamer.last_portfolio_data = {"total_value": 1000.0, "daily_pnl": 0.0}
    streamer.last_positions_data = [
        {"symbol": "AAPL", "quantity": 10, "current_price": 100.00, "market_value": 1000.00},
    ]
    # Minor noise below thresholds
    current_portfolio = {"total_value": 1000.0, "daily_pnl": 0.0}
    current_positions = [
        {"symbol": "AAPL", "quantity": 10, "current_price": 100.009, "market_value": 1000.005},
    ]

    changed = asyncio.run(streamer._has_portfolio_changed(current_portfolio, current_positions))
    assert changed is False


def test_positions_add_symbol_detected():
    streamer = PortfolioStreamer(connection_manager=cast(ConnectionManager, SimpleNamespace()))
    streamer.last_portfolio_data = {"total_value": 2000.0, "daily_pnl": 0.0}
    streamer.last_positions_data = [
        {"symbol": "AAPL", "quantity": 10, "current_price": 100.0, "market_value": 1000.0},
    ]

    current_portfolio = {"total_value": 2000.0, "daily_pnl": 0.0}
    current_positions = [
        {"symbol": "AAPL", "quantity": 10, "current_price": 100.0, "market_value": 1000.0},
        {"symbol": "MSFT", "quantity": 5, "current_price": 200.0, "market_value": 1000.0},
    ]

    changed = asyncio.run(streamer._has_portfolio_changed(current_portfolio, current_positions))
    assert changed is True


def test_positions_price_change_detected():
    streamer = PortfolioStreamer(connection_manager=cast(ConnectionManager, SimpleNamespace()))
    streamer.last_portfolio_data = {"total_value": 1000.0, "daily_pnl": 0.0}
    streamer.last_positions_data = [
        {"symbol": "AAPL", "quantity": 10, "current_price": 100.0, "market_value": 1000.0},
    ]

    current_portfolio = {"total_value": 1000.0, "daily_pnl": 0.0}
    current_positions = [
        {"symbol": "AAPL", "quantity": 10, "current_price": 100.05, "market_value": 1000.6},
    ]

    changed = asyncio.run(streamer._has_portfolio_changed(current_portfolio, current_positions))
    assert changed is True
