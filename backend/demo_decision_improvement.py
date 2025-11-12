#!/usr/bin/env python3
"""
Demonstration of Decision-Making Improvements

This script demonstrates how the enhanced decision context system improves
Ziggy's decision-making through confidence calibration and historical insights.
"""

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent))


from app.services.decision_context import enrich_decision
from app.services.decision_log import get_decision_logger, log_signal_event


def demo_basic_calibration():
    """Demonstrate basic confidence calibration."""
    print("\n" + "=" * 70)
    print("DEMONSTRATION: Confidence Calibration")
    print("=" * 70)

    print("\nScenario: Mean reversion signal in a choppy (CHOP) market regime")
    print("-" * 70)

    # Without enrichment (traditional approach)
    print("\n1. TRADITIONAL APPROACH (Static Confidence):")
    print("   - Signal type: MeanReversion")
    print("   - Market regime: CHOP")
    print("   - Raw confidence: 65% (based on static lookup table)")
    print("   - Decision: BUY with 65% confidence")
    print("   ⚠️  No adjustment based on actual performance")

    # With enrichment
    print("\n2. ENHANCED APPROACH (Calibrated Confidence):")
    context = enrich_decision(
        ticker="AAPL",
        signal_type="MeanReversion",
        regime="CHOP",
        raw_confidence=0.65,
        features={"rsi_14": 28.5, "z_score_20": -1.8},
    )

    print("   - Signal type: MeanReversion")
    print("   - Market regime: CHOP")
    print(f"   - Raw confidence: {context.raw_confidence:.1%}")
    print(f"   - Calibrated confidence: {context.calibrated_confidence:.1%}")
    print(f"   - Adjustment: {context.confidence_adjustment:+.1%}")
    print(f"   - Expected accuracy: {context.expected_accuracy:.1%}")
    print(f"   - Reliability score: {context.reliability_score:.2f}/1.00")

    if context.historical_performance:
        perf = context.historical_performance
        print("\n   Historical Performance:")
        print(f"   - {perf.total_signals} past signals analyzed")
        print(f"   - {perf.win_rate:.1%} actual win rate")
        print(f"   - Brier score: {perf.brier_score:.3f} (lower is better)")

    if context.similar_decisions:
        print("\n   Similar Past Decisions:")
        print(f"   - {len(context.similar_decisions)} similar trades found")
        summary = context.similar_decisions_summary
        if summary:
            print(f"   - Win rate: {summary.get('win_rate', 0):.1%}")
            if summary.get("avg_pnl"):
                print(f"   - Average P&L: ${summary.get('avg_pnl'):.2f}")

    if context.lessons_learned:
        print("\n   💡 Lessons Learned:")
        for i, lesson in enumerate(context.lessons_learned, 1):
            print(f"   {i}. {lesson}")

    print("\n   ✓ Decision uses calibrated confidence based on real outcomes")


def demo_regime_specific_calibration():
    """Demonstrate regime-specific calibration differences."""
    print("\n" + "=" * 70)
    print("DEMONSTRATION: Regime-Specific Calibration")
    print("=" * 70)

    print("\nShowing how the same signal type performs differently across regimes:")
    print("-" * 70)

    regimes = ["CHOP", "RISK_ON", "RISK_OFF", "PANIC"]
    base_confidence = 0.70

    for regime in regimes:
        context = enrich_decision(
            ticker="SPY",
            signal_type="Momentum",
            regime=regime,
            raw_confidence=base_confidence,
        )

        print(f"\n{regime}:")
        print(f"  Raw: {context.raw_confidence:.1%}")
        print(f"  Calibrated: {context.calibrated_confidence:.1%}")
        print(f"  Adjustment: {context.confidence_adjustment:+.1%}")
        print(f"  Reliability: {context.reliability_score:.2f}")


def demo_decision_quality_indicators():
    """Demonstrate decision quality indicators."""
    print("\n" + "=" * 70)
    print("DEMONSTRATION: Decision Quality Indicators")
    print("=" * 70)

    print("\nQuality metrics help assess how much to trust each signal:")
    print("-" * 70)

    # High quality decision (large sample size, good calibration)
    print("\n1. HIGH QUALITY DECISION:")
    print("   - Large historical sample (100+ signals)")
    print("   - Good Brier score (< 0.20)")
    print("   - High reliability score")
    print("   → More confidence in the calibrated prediction")

    # Medium quality decision
    print("\n2. MEDIUM QUALITY DECISION:")
    print("   - Moderate sample (30-100 signals)")
    print("   - Average Brier score (0.20-0.30)")
    print("   - Medium reliability score")
    print("   → Some confidence, but more uncertainty")

    # Low quality decision
    print("\n3. LOW QUALITY DECISION:")
    print("   - Small sample (< 30 signals)")
    print("   - Unknown Brier score")
    print("   - Low reliability score")
    print("   → Fallback to simple adjustment or no calibration")


def demo_feedback_loop():
    """Demonstrate the feedback loop."""
    print("\n" + "=" * 70)
    print("DEMONSTRATION: Continuous Learning Feedback Loop")
    print("=" * 70)

    print("\nHow the system improves over time:")
    print("-" * 70)

    print("\n1. SIGNAL GENERATION:")
    print("   - Generate trading signal with confidence")
    print("   - Enrich with historical context")
    print("   - Apply calibration")

    print("\n2. EXECUTION & OUTCOME TRACKING:")
    print("   - Trade executed")
    print("   - Outcome recorded (win/loss, P&L)")
    print("   - Linked to original decision")

    print("\n3. CALIBRATION UPDATE:")
    print("   - New outcome added to historical data")
    print("   - Calibration model retrained periodically")
    print("   - Performance metrics updated")

    print("\n4. IMPROVED FUTURE DECISIONS:")
    print("   - Next signal uses updated calibration")
    print("   - More accurate confidence scores")
    print("   - Better position sizing")

    print("\n   ♻️  This creates a continuous improvement cycle")


def create_sample_history():
    """Create some sample historical decisions for demonstration."""
    logger = get_decision_logger()

    sample_decisions = [
        {
            "ticker": "AAPL",
            "signal_name": "MeanReversion",
            "regime": "CHOP",
            "confidence": 0.68,
            "hit": True,
            "pnl": 145.0,
        },
        {
            "ticker": "MSFT",
            "signal_name": "MeanReversion",
            "regime": "CHOP",
            "confidence": 0.72,
            "hit": True,
            "pnl": 210.0,
        },
        {
            "ticker": "GOOGL",
            "signal_name": "MeanReversion",
            "regime": "CHOP",
            "confidence": 0.62,
            "hit": False,
            "pnl": -95.0,
        },
        {
            "ticker": "TSLA",
            "signal_name": "Momentum",
            "regime": "RISK_ON",
            "confidence": 0.75,
            "hit": True,
            "pnl": 285.0,
        },
        {
            "ticker": "NVDA",
            "signal_name": "Momentum",
            "regime": "RISK_ON",
            "confidence": 0.80,
            "hit": True,
            "pnl": 320.0,
        },
    ]

    for decision in sample_decisions:
        event_id = log_signal_event(
            ticker=decision["ticker"],
            signal_name=decision["signal_name"],
            confidence=decision["confidence"],
            rules_fired=["demo_rule"],
            decision={"action": "BUY", "reason": "Demo decision"},
            regime=decision["regime"],
        )

        outcome = {
            "h": "3d",
            "hit": decision["hit"],
            "pnl": decision["pnl"],
        }
        logger.update_event_outcome(event_id, outcome)


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print(" " * 10 + "ZIGGY DECISION-MAKING IMPROVEMENTS DEMO")
    print("=" * 70)
    print("\nThis demonstration shows how Ziggy's brain makes better decisions")
    print("through confidence calibration and historical context enrichment.")

    # Create sample history
    print("\n[Setting up sample historical data...]")
    create_sample_history()

    # Run demonstrations
    demo_basic_calibration()
    demo_regime_specific_calibration()
    demo_decision_quality_indicators()
    demo_feedback_loop()

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY: Key Benefits")
    print("=" * 70)
    print("\n✓ More Accurate Predictions:")
    print("  Confidence scores reflect actual historical performance")
    print("\n✓ Context-Aware Decisions:")
    print("  Similar past decisions inform current choices")
    print("\n✓ Regime-Specific Learning:")
    print("  Separate calibration for each market regime")
    print("\n✓ Continuous Improvement:")
    print("  System learns from every outcome")
    print("\n✓ Transparent Reasoning:")
    print("  Explainable adjustments and lessons learned")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
