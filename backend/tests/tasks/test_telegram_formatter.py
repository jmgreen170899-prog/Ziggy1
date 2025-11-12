"""
Tests for enhanced Telegram message formatting
"""

import pytest

from app.tasks.telegram_formatter import (
    _calculate_expiry,
    _get_regime_description,
    _get_regime_emoji,
    format_alert_triggered_message,
    format_bulk_signals,
    format_regime_change_message,
    format_screener_alert,
    format_signal_message,
)


def test_format_signal_message_buy():
    """Test formatting a BUY signal with full details."""
    signal_data = {
        "ticker": "AAPL",
        "signal": "BUY",
        "confidence": 0.85,
        "reason": "RSI oversold, price below lower Bollinger Band",
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

    result = format_signal_message(signal_data)

    # Check key elements are present
    assert "🟢" in result
    assert "BUY SIGNAL" in result
    assert "AAPL" in result
    assert "85%" in result
    assert "RSI oversold" in result
    assert "MeanReversion" in result
    assert "Chop" in result
    assert "3D" in result
    assert "$150.00" in result
    assert "$145.00" in result
    assert "$160.00" in result
    assert "Risk/Reward: 1:2.0" in result
    assert "RSI(14): 28.5" in result
    assert "Z-Score: -1.80" in result


def test_format_signal_message_sell():
    """Test formatting a SELL signal."""
    signal_data = {
        "ticker": "TSLA",
        "signal": "SELL",
        "confidence": 0.72,
        "reason": "RSI overbought, bearish divergence",
        "signal_type": "MeanReversion",
        "regime_context": "RiskOff",
        "time_horizon": "5D",
        "entry_price": 250.00,
        "stop_loss": 260.00,
        "take_profit": 230.00,
    }

    result = format_signal_message(signal_data)

    assert "🔴" in result
    assert "SELL SIGNAL" in result
    assert "TSLA" in result
    assert "72%" in result
    assert "overbought" in result


def test_format_signal_message_minimal():
    """Test formatting with minimal data."""
    signal_data = {
        "ticker": "MSFT",
        "signal": "BUY",
        "confidence": 0.60,
        "reason": "Technical setup",
    }

    result = format_signal_message(signal_data)

    assert "MSFT" in result
    assert "BUY" in result
    assert "60%" in result
    assert "Technical setup" in result


def test_format_bulk_signals():
    """Test formatting multiple signals."""
    signals = [
        {"ticker": "AAPL", "signal": "BUY", "confidence": 0.85, "reason": "Oversold"},
        {"ticker": "GOOGL", "signal": "SELL", "confidence": 0.78, "reason": "Overbought"},
        {"ticker": "MSFT", "signal": "BUY", "confidence": 0.70, "reason": "Momentum"},
        {
            "ticker": "NVDA",
            "signal": "NEUTRAL",
            "confidence": 0.50,
            "reason": "No edge",
        },  # Should be filtered
    ]

    result = format_bulk_signals(signals, max_signals=2)

    assert "Market Scan Results" in result
    assert "3 actionable signal(s)" in result
    assert "AAPL" in result
    assert "GOOGL" in result
    assert "... and 1 more" in result
    assert "NVDA" not in result  # NEUTRAL should be filtered


def test_format_bulk_signals_empty():
    """Test formatting with no signals."""
    result = format_bulk_signals([])

    assert "No actionable signals" in result


def test_format_regime_change_message():
    """Test formatting a regime change notification."""
    regime_data = {
        "regime": "RiskOff",
        "confidence": 0.82,
        "rules_fired": [
            "VIX > 25",
            "SPX < MA200",
            "Credit spreads widening",
        ],
    }

    result = format_regime_change_message(regime_data)

    assert "MARKET REGIME UPDATE" in result
    assert "RiskOff" in result
    assert "82%" in result
    assert "VIX > 25" in result
    assert "⚠️" in result  # RiskOff emoji
    assert "Cautious market" in result


def test_format_alert_triggered_message():
    """Test formatting an alert trigger."""
    alert_data = {
        "symbol": "TSLA",
        "condition_met": "price_above: 250.0",
        "trigger_price": 251.50,
        "message": "TSLA crossed above $250 target",
    }

    result = format_alert_triggered_message(alert_data)

    assert "ALERT TRIGGERED" in result
    assert "TSLA" in result
    assert "$251.50" in result
    assert "price_above: 250.0" in result
    assert "crossed above" in result


def test_format_screener_alert():
    """Test backward-compatible screener alert formatting."""
    result = format_screener_alert("AAPL", "BUY", 0.75, "Oversold conditions")

    assert "AAPL" in result
    assert "BUY" in result
    assert "75%" in result
    assert "Oversold conditions" in result


def test_get_regime_emoji():
    """Test regime emoji selection."""
    assert _get_regime_emoji("Panic") == "😱"
    assert _get_regime_emoji("RiskOff") == "⚠️"
    assert _get_regime_emoji("RiskOn") == "🚀"
    assert _get_regime_emoji("Chop") == "🌊"
    assert _get_regime_emoji("Unknown") == "📊"


def test_get_regime_description():
    """Test regime descriptions."""
    desc = _get_regime_description("RiskOn")
    assert "Bullish" in desc
    assert "growth" in desc

    desc = _get_regime_description("Panic")
    assert "Extreme volatility" in desc
    assert "capital preservation" in desc


def test_calculate_expiry():
    """Test time horizon expiry calculation."""
    # Test days
    result = _calculate_expiry("3D")
    assert result != ""
    assert "UTC" in result

    # Test weeks
    result = _calculate_expiry("1W")
    assert result != ""
    assert "UTC" in result

    # Test hours
    result = _calculate_expiry("24H")
    assert result != ""
    assert "UTC" in result

    # Test invalid
    result = _calculate_expiry("invalid")
    assert result == ""

    result = _calculate_expiry("")
    assert result == ""


def test_format_signal_message_with_all_regimes():
    """Test formatting with different market regimes."""
    regimes = ["Panic", "RiskOff", "RiskOn", "Chop"]

    for regime in regimes:
        signal_data = {
            "ticker": "SPY",
            "signal": "BUY",
            "confidence": 0.70,
            "reason": "Test signal",
            "regime_context": regime,
        }

        result = format_signal_message(signal_data)
        assert regime in result
        # Each regime should have its emoji
        assert _get_regime_emoji(regime) in result


def test_format_signal_message_parse_mode_safe():
    """Test that message formatting is safe for Telegram parse modes."""
    # Test with special characters that might break Markdown/HTML
    signal_data = {
        "ticker": "TEST",
        "signal": "BUY",
        "confidence": 0.75,
        "reason": "Price > $100 & RSI < 30",  # Contains special chars
    }

    result = format_signal_message(signal_data)

    # Should contain the reason
    assert "Price > $100" in result or "Price &gt; $100" in result
    assert "RSI < 30" in result or "RSI &lt; 30" in result


def test_format_bulk_signals_limit():
    """Test that bulk signals respect the max_signals limit."""
    signals = [{"ticker": f"TICK{i}", "signal": "BUY", "confidence": 0.70} for i in range(10)]

    result = format_bulk_signals(signals, max_signals=3)

    # Should show first 3
    assert "TICK0" in result
    assert "TICK1" in result
    assert "TICK2" in result

    # Should indicate more exist
    assert "... and 7 more" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
