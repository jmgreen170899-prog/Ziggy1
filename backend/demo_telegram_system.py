#!/usr/bin/env python3
"""
Demo script to showcase the enhanced Telegram notification system
This demonstrates the full flow of ZiggyAI's intelligent trading signals
"""

import sys


sys.path.insert(0, ".")

from app.tasks.telegram_formatter import (
    format_alert_triggered_message,
    format_bulk_signals,
    format_regime_change_message,
    format_signal_message,
)


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def main():
    print("\n" + "🤖 " * 20)
    print(" " * 25 + "ZiggyAI Telegram Notification System Demo")
    print("🤖 " * 20 + "\n")

    # Demo 1: BUY Signal with Full Details
    print_section("1. BUY SIGNAL - Mean Reversion Strategy")

    buy_signal = {
        "ticker": "AAPL",
        "signal": "BUY",
        "confidence": 0.85,
        "reason": "Mean reversion: RSI 28.5 oversold (< 30); Z-score -1.80 below -1.5; Price bouncing off lower Bollinger Band",
        "signal_type": "MeanReversion",
        "regime_context": "Chop",
        "time_horizon": "3D",
        "entry_price": 150.00,
        "stop_loss": 145.00,
        "take_profit": 160.00,
        "expected_return": 6.67,
        "features_snapshot": {
            "rsi_14": 28.5,
            "z_score_20": -1.8,
            "slope_20d": 0.5,
        },
    }

    print(format_signal_message(buy_signal))

    # Demo 2: SELL Signal with Momentum
    print_section("2. SELL SIGNAL - Overbought Conditions")

    sell_signal = {
        "ticker": "TSLA",
        "signal": "SELL",
        "confidence": 0.72,
        "reason": "RSI overbought at 78.5; Bearish divergence on MACD; Volume declining on rally",
        "signal_type": "MeanReversion",
        "regime_context": "RiskOff",
        "time_horizon": "5D",
        "entry_price": 250.00,
        "stop_loss": 260.00,
        "take_profit": 230.00,
        "features_snapshot": {
            "rsi_14": 78.5,
            "z_score_20": 2.1,
        },
    }

    print(format_signal_message(sell_signal))

    # Demo 3: Momentum Breakout
    print_section("3. BUY SIGNAL - Momentum Breakout Strategy")

    momentum_signal = {
        "ticker": "NVDA",
        "signal": "BUY",
        "confidence": 0.88,
        "reason": "Momentum breakout: New 20-day high at 450.50; Price above 20D SMA (442.30); 20D SMA above 50D SMA (420.15); Strong uptrend: 2.5% slope",
        "brain_signal_type": "Momentum",
        "market_regime": "RiskOn",
        "time_horizon": "5D",
        "brain_entry": 450.50,
        "brain_stop_loss": 440.00,
        "brain_take_profit": 470.00,
        "price": 450.50,
        "features_snapshot": {
            "slope_20d": 2.5,
        },
    }

    print(format_signal_message(momentum_signal))

    # Demo 4: Bulk Summary
    print_section("4. MARKET SCAN - Multiple Signals Summary")

    signals = [
        {"ticker": "AAPL", "signal": "BUY", "confidence": 0.85},
        {"ticker": "GOOGL", "signal": "SELL", "confidence": 0.78},
        {"ticker": "MSFT", "signal": "BUY", "confidence": 0.70},
        {"ticker": "AMZN", "signal": "BUY", "confidence": 0.82},
        {"ticker": "META", "signal": "SELL", "confidence": 0.75},
    ]

    print(format_bulk_signals(signals, max_signals=5))

    # Demo 5: Market Regime Change
    print_section("5. MARKET REGIME UPDATE - Risk-Off Conditions")

    regime_change = {
        "regime": "RiskOff",
        "confidence": 0.82,
        "rules_fired": [
            "VIX > 25 (current: 27.5)",
            "SPX < MA200 (4,450 < 4,500)",
            "Credit spreads widening (BBB: +15bp)",
            "Put/Call ratio elevated (1.25)",
            "High yield bonds under pressure (-1.2%)",
        ],
    }

    print(format_regime_change_message(regime_change))

    # Demo 6: Price Alert Trigger
    print_section("6. PRICE ALERT TRIGGERED")

    alert_trigger = {
        "symbol": "BTC-USD",
        "condition_met": "price_above: 50000.0",
        "trigger_price": 50125.50,
        "message": "Bitcoin crossed above $50,000 resistance level - bullish breakout confirmed",
    }

    print(format_alert_triggered_message(alert_trigger))

    # Demo 7: Panic Regime Example
    print_section("7. MARKET REGIME - Panic Mode")

    panic_regime = {
        "regime": "Panic",
        "confidence": 0.92,
        "rules_fired": [
            "VIX > 35 (current: 38.2)",
            "SPX down -3.5% intraday",
            "Breadth ratio < 20% (only 15% advancing)",
            "Credit markets frozen",
            "Flight to quality - treasuries rallying",
        ],
    }

    print(format_regime_change_message(panic_regime))

    # Demo 8: Risk-On Bullish Environment
    print_section("8. MARKET REGIME - Risk-On (Bullish)")

    riskon_regime = {
        "regime": "RiskOn",
        "confidence": 0.88,
        "rules_fired": [
            "VIX < 15 (current: 12.5)",
            "SPX making new highs",
            "Breadth strong: 85% advancing",
            "High beta outperforming",
            "Cyclicals leading defensives",
        ],
    }

    print(format_regime_change_message(riskon_regime))

    # Summary
    print("\n" + "=" * 80)
    print("  DEMO COMPLETE - Enhanced Telegram System Features")
    print("=" * 80)
    print("\n✅ Rich formatting with emojis and visual indicators")
    print("✅ Detailed AI reasoning explaining buy/sell decisions")
    print("✅ Time horizons showing signal validity periods")
    print("✅ Price levels: entry, stop loss, and take profit targets")
    print("✅ Market regime context for environmental awareness")
    print("✅ Risk/reward ratios for position sizing")
    print("✅ Technical indicators backing the decisions")
    print("✅ Confidence scores with visual star ratings")
    print("✅ Bulk summaries for multiple signals")
    print("✅ Regime change notifications with impact analysis")
    print("✅ Price alert triggers with context")

    print("\n" + "🚀 " * 20)
    print(" " * 30 + "Ready for Production!")
    print("🚀 " * 20 + "\n")

    print("\nNext Steps:")
    print("1. Configure your Telegram bot (see docs/TELEGRAM_SETUP.md)")
    print("2. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env")
    print("3. Start the backend: cd backend && uvicorn app.main:app")
    print("4. Test connection: curl -X POST http://localhost:8000/alerts/ping/test")
    print("5. Enable scanner: curl -X POST http://localhost:8000/alerts/start")
    print("\n")


if __name__ == "__main__":
    main()
