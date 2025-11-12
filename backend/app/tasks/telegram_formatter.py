"""
Enhanced Telegram Message Formatter for ZiggyAI
Formats trading signals with detailed reasoning, price targets, and time horizons.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any


def format_signal_message(signal_data: dict[str, Any]) -> str:
    """
    Format a trading signal into a rich Telegram message with detailed reasoning.

    Args:
        signal_data: Dictionary containing signal information with keys:
            - ticker: Stock symbol
            - signal: "BUY", "SELL", or "NEUTRAL"
            - confidence: Float 0-1
            - reason: Human-readable explanation
            - signal_type: Type of signal (MeanReversion, Momentum, etc.)
            - regime_context: Market regime
            - time_horizon: Expected holding period
            - entry_price: Suggested entry price
            - stop_loss: Stop loss level
            - take_profit: Take profit level
            - expected_return: Expected % return (optional)
            - features_snapshot: Key technical indicators (optional)

    Returns:
        Formatted message string with emoji indicators and structured info
    """
    ticker = signal_data.get("ticker", "UNKNOWN")
    signal = signal_data.get("signal", "NEUTRAL")
    confidence = signal_data.get("confidence", 0.0)
    reason = signal_data.get("reason", "No reason provided")

    # Get signal emoji
    if signal == "BUY":
        signal_emoji = "🟢"
        action_text = "📈 BUY SIGNAL"
    elif signal == "SELL":
        signal_emoji = "🔴"
        action_text = "📉 SELL SIGNAL"
    else:
        signal_emoji = "⚪"
        action_text = "➖ NEUTRAL"

    # Build message header
    conf_pct = int(confidence * 100)
    confidence_stars = "⭐" * min(5, int(confidence * 5))

    lines = [
        f"{signal_emoji} *{action_text}* {signal_emoji}",
        "",
        f"🎯 *{ticker}*",
        f"📊 Confidence: {conf_pct}% {confidence_stars}",
    ]

    # Add signal type and regime if available
    # Support both brain signal format and direct format
    signal_type = signal_data.get(
        "signal_type", signal_data.get("type", signal_data.get("brain_signal_type", ""))
    )
    regime = signal_data.get(
        "regime_context", signal_data.get("regime", signal_data.get("market_regime", ""))
    )

    if signal_type:
        lines.append(f"🔬 Strategy: {signal_type}")
    if regime:
        regime_emoji = _get_regime_emoji(regime)
        lines.append(f"{regime_emoji} Market Regime: {regime}")

    lines.append("")

    # Add reasoning
    lines.append("💡 *Why this recommendation:*")
    lines.append(f"_{reason}_")
    lines.append("")

    # Add price levels if available (support both brain and direct formats)
    entry_price = signal_data.get(
        "entry_price", signal_data.get("brain_entry", signal_data.get("price"))
    )
    stop_loss = signal_data.get("stop_loss", signal_data.get("brain_stop_loss"))
    take_profit = signal_data.get("take_profit", signal_data.get("brain_take_profit"))

    if entry_price or stop_loss or take_profit:
        lines.append("💰 *Price Levels:*")
        if entry_price:
            lines.append(f"  • Entry: ${entry_price:.2f}")
        if stop_loss:
            lines.append(f"  • Stop Loss: ${stop_loss:.2f}")
        if take_profit:
            lines.append(f"  • Take Profit: ${take_profit:.2f}")

        # Calculate risk/reward if both available
        if entry_price and stop_loss and take_profit:
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit - entry_price)
            if risk > 0:
                rr_ratio = reward / risk
                lines.append(f"  • Risk/Reward: 1:{rr_ratio:.1f}")

        lines.append("")

    # Add expected return if available
    expected_return = signal_data.get("expected_return")
    if expected_return:
        lines.append(f"📈 Expected Return: {expected_return:.1f}%")
        lines.append("")

    # Add time horizon
    time_horizon = signal_data.get("time_horizon", signal_data.get("horizon", ""))
    if time_horizon:
        lines.append("⏱️ *Time Frame:*")
        lines.append(f"_{time_horizon} holding period_")

        # Calculate expiry time
        expiry_text = _calculate_expiry(time_horizon)
        if expiry_text:
            lines.append(f"⏰ Valid until: {expiry_text}")
        lines.append("")

    # Add technical indicators snapshot if available
    features = signal_data.get("features_snapshot", {})
    if features and isinstance(features, dict):
        indicator_lines = []
        if "rsi_14" in features:
            rsi = features["rsi_14"]
            if rsi is not None:
                indicator_lines.append(f"RSI(14): {rsi:.1f}")
        if "z_score_20" in features:
            z_score = features["z_score_20"]
            if z_score is not None:
                indicator_lines.append(f"Z-Score: {z_score:.2f}")
        if "slope_20d" in features:
            slope = features["slope_20d"]
            if slope is not None:
                indicator_lines.append(f"Trend: {slope:.1f}%")

        if indicator_lines:
            lines.append("📊 *Key Indicators:*")
            for ind in indicator_lines:
                lines.append(f"  • {ind}")
            lines.append("")

    # Add footer with timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    lines.append(f"🤖 _Generated by ZiggyAI at {timestamp}_")

    return "\n".join(lines)


def format_bulk_signals(signals: list[dict[str, Any]], max_signals: int = 5) -> str:
    """
    Format multiple trading signals into a summary message.

    Args:
        signals: List of signal dictionaries
        max_signals: Maximum number of signals to include in detail

    Returns:
        Formatted summary message
    """
    if not signals:
        return "📊 *ZiggyAI Market Scan*\n\nNo actionable signals at this time."

    # Filter to BUY/SELL only
    actionable = [s for s in signals if s.get("signal") in ("BUY", "SELL")]

    if not actionable:
        return "📊 *ZiggyAI Market Scan*\n\nNo actionable signals at this time."

    lines = [
        "📊 *ZiggyAI Market Scan Results*",
        "",
        f"Found {len(actionable)} actionable signal(s):",
        "",
    ]

    # Show summary of all signals
    for sig in actionable[:max_signals]:
        ticker = sig.get("ticker", "UNKNOWN")
        signal = sig.get("signal", "NEUTRAL")
        confidence = sig.get("confidence", 0.0)
        conf_pct = int(confidence * 100)

        emoji = "🟢" if signal == "BUY" else "🔴"
        lines.append(f"{emoji} *{ticker}*: {signal} ({conf_pct}% confidence)")

    if len(actionable) > max_signals:
        lines.append(f"... and {len(actionable) - max_signals} more")

    lines.append("")
    lines.append("💬 _Individual signal details will follow..._")

    return "\n".join(lines)


def format_regime_change_message(regime_data: dict[str, Any]) -> str:
    """
    Format a market regime change notification.

    Args:
        regime_data: Dictionary with regime, confidence, and rules_fired

    Returns:
        Formatted regime change message
    """
    regime = regime_data.get("regime", "Unknown")
    confidence = regime_data.get("confidence", 0.0)
    rules = regime_data.get("rules_fired", [])

    emoji = _get_regime_emoji(regime)
    conf_pct = int(confidence * 100)

    lines = [
        f"{emoji} *MARKET REGIME UPDATE* {emoji}",
        "",
        f"🌐 New Regime: *{regime}*",
        f"📊 Confidence: {conf_pct}%",
        "",
    ]

    if rules:
        lines.append("📋 *Key Indicators:*")
        for rule in rules[:5]:  # Limit to 5 rules
            lines.append(f"  • {rule}")
        lines.append("")

    # Add regime description
    regime_desc = _get_regime_description(regime)
    if regime_desc:
        lines.append("ℹ️ *What this means:*")
        lines.append(f"_{regime_desc}_")
        lines.append("")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    lines.append(f"🤖 _ZiggyAI Market Analysis - {timestamp}_")

    return "\n".join(lines)


def format_alert_triggered_message(alert_data: dict[str, Any]) -> str:
    """
    Format an alert trigger notification.

    Args:
        alert_data: Alert trigger data with symbol, condition, price, etc.

    Returns:
        Formatted alert message
    """
    symbol = alert_data.get("symbol", "UNKNOWN")
    condition = alert_data.get("condition_met", "condition met")
    price = alert_data.get("trigger_price", 0.0)
    message = alert_data.get("message", "Alert triggered")

    lines = [
        "🔔 *ALERT TRIGGERED* 🔔",
        "",
        f"🎯 {symbol}",
        f"💰 Price: ${price:.2f}",
        f"📋 Condition: {condition}",
        "",
        f"💬 _{message}_",
        "",
        f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}",
    ]

    return "\n".join(lines)


def _get_regime_emoji(regime: str) -> str:
    """Get emoji for market regime."""
    regime_lower = regime.lower()
    if "panic" in regime_lower:
        return "😱"
    elif "risk" in regime_lower and "off" in regime_lower:
        return "⚠️"
    elif "risk" in regime_lower and "on" in regime_lower:
        return "🚀"
    elif "chop" in regime_lower:
        return "🌊"
    else:
        return "📊"


def _get_regime_description(regime: str) -> str:
    """Get description for market regime."""
    regime_lower = regime.lower()
    if "panic" in regime_lower:
        return "Extreme volatility and fear - focus on capital preservation"
    elif "risk" in regime_lower and "off" in regime_lower:
        return "Cautious market - defensive positioning recommended"
    elif "risk" in regime_lower and "on" in regime_lower:
        return "Bullish environment - growth opportunities available"
    elif "chop" in regime_lower:
        return "Range-bound market - mean reversion strategies favored"
    else:
        return ""


def _calculate_expiry(time_horizon: str) -> str:
    """Calculate expiry time from horizon string like '3D', '1W', etc."""
    try:
        if not time_horizon:
            return ""

        horizon_str = str(time_horizon).upper().strip()

        # Parse the time horizon
        if horizon_str.endswith("D"):
            days = int(horizon_str[:-1])
            expiry = datetime.now() + timedelta(days=days)
        elif horizon_str.endswith("W"):
            weeks = int(horizon_str[:-1])
            expiry = datetime.now() + timedelta(weeks=weeks)
        elif horizon_str.endswith("H"):
            hours = int(horizon_str[:-1])
            expiry = datetime.now() + timedelta(hours=hours)
        else:
            return ""

        return expiry.strftime("%Y-%m-%d %H:%M UTC")
    except (ValueError, IndexError):
        return ""


# Convenience function for backward compatibility
def format_screener_alert(ticker: str, signal: str, confidence: float, reason: str = "") -> str:
    """
    Format a basic screener alert (backward compatible).

    Args:
        ticker: Stock symbol
        signal: "BUY", "SELL", or "NEUTRAL"
        confidence: Confidence 0-1
        reason: Optional reason text

    Returns:
        Formatted message
    """
    signal_data = {
        "ticker": ticker,
        "signal": signal,
        "confidence": confidence,
        "reason": reason or f"{signal} signal detected",
    }
    return format_signal_message(signal_data)
