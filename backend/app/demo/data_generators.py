"""
Demo data generators for safe demonstrations.

Provides deterministic, realistic-looking data when DEMO_MODE is enabled.
"""

from datetime import datetime, timedelta
from typing import Any

from app.core.config.settings import get_settings


def is_demo_mode() -> bool:
    """Check if demo mode is enabled."""
    return get_settings().DEMO_MODE


def get_demo_market_data(ticker: str = "AAPL") -> dict[str, Any]:
    """Generate demo market data for a ticker."""
    base_prices = {
        "AAPL": 175.50,
        "MSFT": 380.25,
        "NVDA": 495.80,
        "TSLA": 245.30,
        "GOOGL": 140.60,
        "META": 485.20,
        "AMZN": 178.90,
    }

    base_price = base_prices.get(ticker, 150.00)

    return {
        "ticker": ticker,
        "price": round(base_price, 2),
        "change": round(base_price * 0.015, 2),
        "change_percent": 1.5,
        "volume": 45_000_000,
        "high": round(base_price * 1.025, 2),
        "low": round(base_price * 0.985, 2),
        "open": round(base_price * 0.995, 2),
        "prev_close": round(base_price / 1.015, 2),
        "market_cap": "2.8T" if ticker == "AAPL" else "1.5T",
        "pe_ratio": 28.5,
        "timestamp": datetime.now().isoformat(),
    }


def get_demo_portfolio() -> dict[str, Any]:
    """Generate demo portfolio data."""
    return {
        "total_value": 125_450.75,
        "cash": 25_450.75,
        "positions_value": 100_000.00,
        "total_return": 25_450.75,
        "total_return_percent": 25.45,
        "day_return": 1_234.50,
        "day_return_percent": 0.99,
        "positions": [
            {
                "ticker": "AAPL",
                "shares": 100,
                "avg_cost": 165.00,
                "current_price": 175.50,
                "market_value": 17_550.00,
                "unrealized_pl": 1_050.00,
                "unrealized_pl_percent": 6.36,
            },
            {
                "ticker": "MSFT",
                "shares": 50,
                "avg_cost": 350.00,
                "current_price": 380.25,
                "market_value": 19_012.50,
                "unrealized_pl": 1_512.50,
                "unrealized_pl_percent": 8.64,
            },
            {
                "ticker": "NVDA",
                "shares": 75,
                "avg_cost": 450.00,
                "current_price": 495.80,
                "market_value": 37_185.00,
                "unrealized_pl": 3_435.00,
                "unrealized_pl_percent": 10.18,
            },
        ],
        "recent_trades": [
            {
                "ticker": "NVDA",
                "action": "BUY",
                "shares": 25,
                "price": 495.80,
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
            },
            {
                "ticker": "AAPL",
                "action": "BUY",
                "shares": 50,
                "price": 175.20,
                "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
            },
        ],
    }


def get_demo_signals(ticker: str = "AAPL") -> dict[str, Any]:
    """Generate demo trading signals."""
    return {
        "ticker": ticker,
        "signal": "BUY",
        "confidence": 0.78,
        "strength": "STRONG",
        "indicators": {
            "rsi": 45.2,
            "macd": {"value": 2.35, "signal": 1.88, "histogram": 0.47},
            "moving_averages": {
                "sma_20": 172.50,
                "sma_50": 168.30,
                "sma_200": 165.80,
            },
            "bollinger_bands": {
                "upper": 178.50,
                "middle": 175.00,
                "lower": 171.50,
            },
        },
        "market_brain": {
            "regime": "TRENDING_UP",
            "volatility": "MODERATE",
            "sentiment": 0.65,
            "predicted_direction": "UP",
        },
        "timestamp": datetime.now().isoformat(),
    }


def get_demo_news(ticker: str | None = None) -> list[dict[str, Any]]:
    """Generate demo news articles."""
    articles = [
        {
            "title": "Tech Stocks Rally on Strong Earnings Reports",
            "summary": "Major technology companies exceeded analyst expectations, driving market gains.",
            "source": "Financial Times",
            "sentiment": 0.8,
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
            "url": "#",
        },
        {
            "title": "Fed Signals Steady Interest Rates Through Year End",
            "summary": "Federal Reserve indicates economic conditions support maintaining current policy.",
            "source": "Wall Street Journal",
            "sentiment": 0.6,
            "timestamp": (datetime.now() - timedelta(hours=3)).isoformat(),
            "url": "#",
        },
        {
            "title": "AI Innovation Drives Market Optimism",
            "summary": "Breakthroughs in artificial intelligence spark investor enthusiasm across sectors.",
            "source": "Bloomberg",
            "sentiment": 0.75,
            "timestamp": (datetime.now() - timedelta(hours=5)).isoformat(),
            "url": "#",
        },
    ]

    if ticker:
        articles[0]["title"] = f"{ticker} Reports Strong Quarterly Results"
        articles[0][
            "summary"
        ] = f"{ticker} exceeded expectations with robust revenue growth."

    return articles


def get_demo_backtest_result(
    symbol: str = "AAPL", strategy: str = "sma50_cross"
) -> dict[str, Any]:
    """Generate demo backtest results."""
    return {
        "symbol": symbol,
        "strategy": strategy,
        "period": "2023-01-01 to 2024-12-31",
        "initial_capital": 100_000.00,
        "final_value": 135_250.00,
        "total_return": 35_250.00,
        "total_return_percent": 35.25,
        "annualized_return": 17.12,
        "sharpe_ratio": 1.85,
        "max_drawdown": -8.5,
        "win_rate": 0.68,
        "total_trades": 45,
        "winning_trades": 31,
        "losing_trades": 14,
        "avg_win": 1_850.00,
        "avg_loss": -825.00,
        "profit_factor": 2.24,
        "trades": [
            {
                "entry_date": "2024-01-15",
                "exit_date": "2024-02-20",
                "entry_price": 165.00,
                "exit_price": 175.50,
                "shares": 100,
                "profit": 1_050.00,
                "profit_percent": 6.36,
            },
            {
                "entry_date": "2024-03-01",
                "exit_date": "2024-04-10",
                "entry_price": 170.00,
                "exit_price": 178.25,
                "shares": 100,
                "profit": 825.00,
                "profit_percent": 4.85,
            },
        ],
        "equity_curve": [
            {"date": "2024-01-01", "value": 100_000},
            {"date": "2024-02-01", "value": 105_200},
            {"date": "2024-03-01", "value": 112_500},
            {"date": "2024-04-01", "value": 118_750},
            {"date": "2024-05-01", "value": 122_100},
            {"date": "2024-06-01", "value": 127_800},
            {"date": "2024-07-01", "value": 125_300},
            {"date": "2024-08-01", "value": 129_600},
            {"date": "2024-09-01", "value": 131_200},
            {"date": "2024-10-01", "value": 133_800},
            {"date": "2024-11-01", "value": 134_500},
            {"date": "2024-12-01", "value": 135_250},
        ],
    }


def get_demo_screener_results(preset: str = "momentum") -> list[dict[str, Any]]:
    """Generate demo screener results."""
    base_results = [
        {"ticker": "NVDA", "score": 92, "price": 495.80, "change_percent": 2.8},
        {"ticker": "AMD", "score": 88, "price": 165.40, "change_percent": 1.9},
        {"ticker": "AVGO", "score": 85, "price": 1_345.60, "change_percent": 1.5},
        {"ticker": "AAPL", "score": 82, "price": 175.50, "change_percent": 1.5},
        {"ticker": "MSFT", "score": 79, "price": 380.25, "change_percent": 0.8},
    ]

    return base_results


def get_demo_cognitive_response(question: str) -> dict[str, Any]:
    """Generate demo cognitive/chat response."""
    return {
        "question": question,
        "answer": "Based on current market conditions and technical analysis, "
        "AAPL shows strong momentum with bullish indicators. The stock is trading "
        "above all major moving averages with increasing volume. Market brain analysis "
        "suggests a 78% confidence in continued upward movement over the next 5-10 days.",
        "confidence": 0.78,
        "sources": [
            {"type": "technical_analysis", "indicator": "RSI", "value": 45.2},
            {"type": "market_brain", "signal": "BUY", "strength": "STRONG"},
            {"type": "sentiment", "score": 0.65, "label": "POSITIVE"},
        ],
        "timestamp": datetime.now().isoformat(),
    }
