#!/usr/bin/env python3
"""
Test script to verify decision logging functionality works correctly
"""

import os
import sys


# Add the backend directory to the Python path
backend_path = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, backend_path)

# Set up data directory
data_dir = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(data_dir, exist_ok=True)
os.makedirs(os.path.join(data_dir, "decisions"), exist_ok=True)

from app.services.decision_log import DecisionLogger, log_regime_event, log_signal_event


# Test decision logging
logger = DecisionLogger(data_dir)

print("Testing Decision Logging...")

# Test signal event
signal_event_id = log_signal_event(
    ticker="AAPL",
    signal_name="bullish_divergence",
    confidence=0.85,
    rules_fired=["rsi_divergence", "volume_confirmation"],
    decision={
        "action": "BUY",
        "reason": "RSI showing bullish divergence while price made new lows",
    },
    risk={"atr": 2.5, "stop_mult": 1.5, "qty": 100, "risk_pct": 1.0},
    parameters={"rsi_period": 14, "lookback": 5},
)

print(f"Created signal event: {signal_event_id}")

# Test regime event
regime_event_id = log_regime_event(
    regime="sideways_market",
    confidence=0.72,
    rules_fired=["vix_spike", "trend_break"],
    reasoning="Market volatility increasing, trend weakening",
    old_regime="bull_market",
    indicators_changed=["vix_spike", "trend_break"],
    parameters={"vix_threshold": 25, "trend_strength": 0.3},
)

print(f"Created regime event: {regime_event_id}")

# Query events
print("\nQuerying events...")
result = logger.query_events(limit=10)
events = result.get("items", result) if isinstance(result, dict) else result
print(f"Found {len(events)} events")

for event in events:
    if isinstance(event, dict):
        print(
            f"- {event.get('ts', 'N/A')}: {event.get('kind', 'N/A')} - {event.get('ticker', 'N/A')}"
        )
    else:
        print(f"- {event}")

print("\nDecision logging test completed successfully!")
