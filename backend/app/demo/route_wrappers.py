"""
Demo-aware route wrappers.

Provides helpers to wrap routes with demo mode support.
"""
from functools import wraps
from typing import Any, Callable

from fastapi import Request

from app.demo.data_generators import (
    get_demo_backtest_result,
    get_demo_cognitive_response,
    get_demo_market_data,
    get_demo_news,
    get_demo_portfolio,
    get_demo_screener_results,
    get_demo_signals,
    is_demo_mode,
)


def demo_market_data(func: Callable) -> Callable:
    """Wrap market data endpoint with demo mode support."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if is_demo_mode():
            ticker = kwargs.get('symbol', kwargs.get('ticker', 'AAPL'))
            return get_demo_market_data(ticker)
        return await func(*args, **kwargs) if callable(func) else func(*args, **kwargs)
    return wrapper


def demo_portfolio(func: Callable) -> Callable:
    """Wrap portfolio endpoint with demo mode support."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if is_demo_mode():
            return get_demo_portfolio()
        return await func(*args, **kwargs) if callable(func) else func(*args, **kwargs)
    return wrapper


def demo_signals(func: Callable) -> Callable:
    """Wrap signals endpoint with demo mode support."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if is_demo_mode():
            ticker = kwargs.get('ticker', 'AAPL')
            return get_demo_signals(ticker)
        return await func(*args, **kwargs) if callable(func) else func(*args, **kwargs)
    return wrapper


def demo_news(func: Callable) -> Callable:
    """Wrap news endpoint with demo mode support."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if is_demo_mode():
            ticker = kwargs.get('ticker', None)
            return get_demo_news(ticker)
        return await func(*args, **kwargs) if callable(func) else func(*args, **kwargs)
    return wrapper


def demo_backtest(func: Callable) -> Callable:
    """Wrap backtest endpoint with demo mode support."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if is_demo_mode():
            symbol = kwargs.get('symbol', 'AAPL')
            strategy = kwargs.get('strategy', 'sma50_cross')
            return get_demo_backtest_result(symbol, strategy)
        return await func(*args, **kwargs) if callable(func) else func(*args, **kwargs)
    return wrapper


def demo_screener(func: Callable) -> Callable:
    """Wrap screener endpoint with demo mode support."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if is_demo_mode():
            preset = kwargs.get('preset', 'momentum')
            return get_demo_screener_results(preset)
        return await func(*args, **kwargs) if callable(func) else func(*args, **kwargs)
    return wrapper


def demo_cognitive(func: Callable) -> Callable:
    """Wrap cognitive/chat endpoint with demo mode support."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if is_demo_mode():
            question = kwargs.get('question', kwargs.get('message', 'What should I know about AAPL?'))
            return get_demo_cognitive_response(question)
        return await func(*args, **kwargs) if callable(func) else func(*args, **kwargs)
    return wrapper


def get_demo_status() -> dict[str, Any]:
    """Get current demo mode status."""
    return {
        "demo_mode": is_demo_mode(),
        "message": "Demo mode is active - using deterministic demo data" if is_demo_mode() else "Demo mode is disabled",
        "safe_actions_only": is_demo_mode(),
    }
