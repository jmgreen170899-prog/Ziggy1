#!/usr/bin/env python3
"""
Test suite for decision context enrichment system.

Tests confidence calibration, historical performance tracking,
and decision context enrichment functionality.
"""

import sys
from pathlib import Path


# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime

import numpy as np

from app.services.calibration import ProbabilityCalibrator
from app.services.decision_context import (
    DecisionContextEnricher,
    HistoricalPerformance,
    enrich_decision,
)
from app.services.decision_log import get_decision_logger, log_signal_event


def setup_test_data():
    """Create test decision history for calibration."""
    logger = get_decision_logger()

    print("Setting up test data...")

    # Create some historical decisions with outcomes
    test_decisions = [
        # Mean reversion signals in CHOP regime
        {
            "signal_name": "MeanReversion",
            "regime": "CHOP",
            "confidence": 0.65,
            "hit": True,
            "pnl": 150.0,
        },
        {
            "signal_name": "MeanReversion",
            "regime": "CHOP",
            "confidence": 0.70,
            "hit": True,
            "pnl": 200.0,
        },
        {
            "signal_name": "MeanReversion",
            "regime": "CHOP",
            "confidence": 0.60,
            "hit": False,
            "pnl": -100.0,
        },
        {
            "signal_name": "MeanReversion",
            "regime": "CHOP",
            "confidence": 0.75,
            "hit": True,
            "pnl": 180.0,
        },
        # Momentum signals in RISK_ON regime
        {
            "signal_name": "Momentum",
            "regime": "RISK_ON",
            "confidence": 0.80,
            "hit": True,
            "pnl": 250.0,
        },
        {
            "signal_name": "Momentum",
            "regime": "RISK_ON",
            "confidence": 0.75,
            "hit": True,
            "pnl": 220.0,
        },
        {
            "signal_name": "Momentum",
            "regime": "RISK_ON",
            "confidence": 0.70,
            "hit": False,
            "pnl": -120.0,
        },
    ]

    event_ids = []
    for _i, decision in enumerate(test_decisions):
        # Create decision event
        event_id = log_signal_event(
            ticker="TEST",
            signal_name=decision["signal_name"],
            confidence=decision["confidence"],
            rules_fired=["test_rule"],
            decision={"action": "BUY", "reason": "Test decision"},
            risk={"atr": 2.0, "qty": 100},
            regime=decision["regime"],
        )

        # Add outcome
        outcome = {
            "h": "3d",
            "hit": decision["hit"],
            "pnl": decision["pnl"],
        }
        logger.update_event_outcome(event_id, outcome)
        event_ids.append(event_id)

    print(f"Created {len(event_ids)} test decisions")
    return event_ids


def test_historical_performance():
    """Test historical performance tracking."""
    print("\n=== Testing Historical Performance Tracking ===")

    enricher = DecisionContextEnricher()

    # Get performance for MeanReversion in CHOP
    perf = enricher._get_historical_performance("MeanReversion", "CHOP")

    if perf:
        print("MeanReversion/CHOP Performance:")
        print(f"  Total signals: {perf.total_signals}")
        print(f"  Win rate: {perf.win_rate:.2%}")
        print(f"  Avg confidence: {perf.avg_confidence:.2f}")
        print(f"  Brier score: {perf.brier_score:.4f}")

        assert perf.total_signals >= 3, "Should have at least 3 signals"
        assert 0.0 <= perf.win_rate <= 1.0, "Win rate should be between 0 and 1"
        assert perf.brier_score >= 0.0, "Brier score should be non-negative"
        print("✓ Historical performance tracking works")
    else:
        print("⚠ Not enough data for historical performance")

    return perf


def test_calibration():
    """Test confidence calibration."""
    print("\n=== Testing Confidence Calibration ===")

    # Test basic calibration with synthetic data
    np.random.seed(42)
    n = 100

    # Create miscalibrated probabilities (overconfident)
    true_probs = np.random.beta(2, 2, n)
    raw_probs = true_probs * 1.2  # Overconfident
    raw_probs = np.clip(raw_probs, 0.01, 0.99)
    outcomes = np.random.binomial(1, true_probs, n)

    # Fit calibrator
    calibrator = ProbabilityCalibrator(method="isotonic", min_samples=30)
    success = calibrator.fit(raw_probs, outcomes)

    assert success, "Calibrator should fit successfully"
    print(f"✓ Calibrator fitted with {n} samples")

    # Test calibration
    test_probs = np.array([0.3, 0.5, 0.7, 0.9])
    calibrated = calibrator.predict(test_probs)

    print(f"Raw probabilities: {test_probs}")
    print(f"Calibrated: {calibrated}")

    # Calibrated should differ from raw (unless perfectly calibrated)
    assert not np.allclose(test_probs, calibrated), "Calibration should adjust probabilities"
    print("✓ Calibration adjusts probabilities")

    return calibrator


def test_decision_enrichment():
    """Test full decision enrichment."""
    print("\n=== Testing Decision Enrichment ===")

    # Enrich a decision
    context = enrich_decision(
        ticker="TEST",
        signal_type="MeanReversion",
        regime="CHOP",
        raw_confidence=0.65,
        features={"rsi_14": 28.0, "z_score_20": -1.8},
    )

    print("Decision Enrichment for TEST/MeanReversion/CHOP:")
    print(f"  Raw confidence: {context.raw_confidence:.2%}")
    print(f"  Calibrated confidence: {context.calibrated_confidence:.2%}")
    print(f"  Adjustment: {context.confidence_adjustment:+.2%}")
    print(f"  Expected accuracy: {context.expected_accuracy:.2%}")
    print(f"  Reliability score: {context.reliability_score:.2f}")
    print(f"  Similar decisions: {len(context.similar_decisions)}")

    if context.lessons_learned:
        print("  Lessons learned:")
        for lesson in context.lessons_learned:
            print(f"    - {lesson}")

    # Verify enrichment worked
    assert context.calibrated_confidence > 0.0, "Should have calibrated confidence"
    assert context.reliability_score >= 0.0, "Should have reliability score"
    print("✓ Decision enrichment works")

    return context


def test_similar_decisions():
    """Test finding similar past decisions."""
    print("\n=== Testing Similar Decision Recall ===")

    enricher = DecisionContextEnricher()

    similar = enricher._find_similar_decisions(
        ticker="TEST",
        signal_type="MeanReversion",
        regime="CHOP",
        features=None,
        limit=5,
    )

    print(f"Found {len(similar)} similar decisions")

    if similar:
        summary = enricher._summarize_similar_decisions(similar)
        print("Similar decisions summary:")
        print(f"  Total: {summary.get('total_similar', 0)}")
        print(f"  Win rate: {summary.get('win_rate', 0):.2%}")
        if summary.get("avg_pnl"):
            print(f"  Avg P&L: ${summary.get('avg_pnl'):.2f}")

        print("✓ Similar decision recall works")
    else:
        print("⚠ No similar decisions found")

    return similar


def test_performance_summary():
    """Test performance summary generation."""
    print("\n=== Testing Performance Summary ===")

    enricher = DecisionContextEnricher()

    # Force cache refresh
    enricher._refresh_cache_if_needed()

    summary = enricher.get_performance_summary()

    print("Performance Summary:")
    print(f"  Tracked combinations: {summary['total_tracked_combinations']}")
    print(f"  Last updated: {summary['cache_last_updated']}")

    if summary["performance_by_signal"]:
        print("  Performance by signal:")
        for signal_type, regimes in summary["performance_by_signal"].items():
            print(f"    {signal_type}:")
            for regime, metrics in regimes.items():
                print(
                    f"      {regime}: {metrics['win_rate']:.2%} "
                    f"({metrics['total_signals']} signals, "
                    f"Brier: {metrics['brier_score']:.3f})"
                )

    print("✓ Performance summary works")
    return summary


def test_reliability_score():
    """Test reliability score calculation."""
    print("\n=== Testing Reliability Score ===")

    enricher = DecisionContextEnricher()

    # Test with different sample sizes
    test_cases = [
        (
            HistoricalPerformance("Test", "Test", 10, 7, 0.70, 0.65, 0.15, datetime.now()),
            "small sample",
        ),
        (
            HistoricalPerformance("Test", "Test", 100, 65, 0.65, 0.62, 0.18, datetime.now()),
            "good sample",
        ),
        (
            HistoricalPerformance("Test", "Test", 500, 325, 0.65, 0.64, 0.12, datetime.now()),
            "large sample",
        ),
        (None, "no data"),
    ]

    for perf, desc in test_cases:
        score = enricher._calculate_reliability_score(perf)
        print(f"  {desc}: reliability = {score:.2f}")
        assert 0.0 <= score <= 1.0, "Reliability should be between 0 and 1"

    print("✓ Reliability score calculation works")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Decision Context Enrichment Test Suite")
    print("=" * 60)

    try:
        # Setup test data
        setup_test_data()

        # Run tests
        test_historical_performance()
        test_calibration()
        test_decision_enrichment()
        test_similar_decisions()
        test_performance_summary()
        test_reliability_score()

        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
