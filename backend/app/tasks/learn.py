"""
Learning Tasks for ZiggyAI Memory & Knowledge System

Provides self-critique, Brier score computation, and drift detection.
Includes nightly learning jobs for model performance analysis.
"""

from __future__ import annotations

import json
import logging
import os
from collections import defaultdict
from collections.abc import Iterable
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from ..memory.events import iter_events


logger = logging.getLogger(__name__)

# Configuration from environment
LEARN_NIGHTLY_AT = os.getenv("LEARN_NIGHTLY_AT", "02:30Z")
LEARN_REPORT_PATH = os.getenv("LEARN_REPORT_PATH", "data/memory/learn_report.json")
DRIFT_THRESHOLD = float(os.getenv("DRIFT_THRESHOLD", "0.02"))


def brier_score(y_prob: Iterable[float], y_true: Iterable[int]) -> float:
    """
    Calculate Brier score for probability predictions.

    Brier Score = (1/N) * Σ(p_i - y_i)²
    Lower is better (perfect score = 0).

    Args:
        y_prob: Predicted probabilities
        y_true: True binary outcomes (0 or 1)

    Returns:
        Brier score (0 to 1, lower is better)
    """
    pairs = list(zip(y_prob, y_true))
    if not pairs:
        return 1.0  # Worst possible score if no data

    total_squared_error = sum((p - y) ** 2 for p, y in pairs)
    return total_squared_error / len(pairs)


def reliability_diagram(
    y_prob: Iterable[float], y_true: Iterable[int], n_bins: int = 10
) -> dict[str, list[float]]:
    """
    Calculate reliability diagram data for calibration analysis.

    Args:
        y_prob: Predicted probabilities
        y_true: True binary outcomes
        n_bins: Number of probability bins

    Returns:
        Dictionary with bin_centers, mean_predicted, mean_observed, counts
    """
    pairs = list(zip(y_prob, y_true))
    if not pairs:
        return {
            "bin_centers": [],
            "mean_predicted": [],
            "mean_observed": [],
            "counts": [],
        }

    # Create bins
    bins = [i / n_bins for i in range(n_bins + 1)]
    bin_data = [[] for _ in range(n_bins)]

    # Assign predictions to bins using rounding to nearest bin center
    for prob, true_val in pairs:
        # Round to nearest bin center for stable binning
        bin_idx = round(prob * n_bins)
        # Clamp to valid range [0, n_bins-1]
        bin_idx = max(0, min(bin_idx, n_bins - 1))
        bin_data[bin_idx].append((prob, true_val))

    # Calculate statistics for each bin
    bin_centers = []
    mean_predicted = []
    mean_observed = []
    counts = []

    for i, bin_pairs in enumerate(bin_data):
        if bin_pairs:
            probs = [p for p, _ in bin_pairs]
            trues = [t for _, t in bin_pairs]

            bin_centers.append((bins[i] + bins[i + 1]) / 2)
            mean_predicted.append(sum(probs) / len(probs))
            mean_observed.append(sum(trues) / len(trues))
            counts.append(len(bin_pairs))

    return {
        "bin_centers": bin_centers,
        "mean_predicted": mean_predicted,
        "mean_observed": mean_observed,
        "counts": counts,
    }


def compute_brier_by_family(events: Iterable[dict[str, Any]]) -> dict[str, float]:
    """
    Compute Brier scores grouped by feature family.

    Feature families are determined by analyzing SHAP feature names:
    - momentum: moving averages, RSI, momentum indicators
    - breadth: advance/decline, new highs/lows, breadth metrics
    - sentiment: VIX, put/call ratio, sentiment indicators
    - macro: interest rates, inflation, macro indicators
    - microstructure: volume, spread, microstructure features

    Args:
        events: Iterable of event dictionaries

    Returns:
        Dictionary mapping feature family to Brier score
    """
    FEATURE_FAMILIES = {
        "momentum": [
            "rsi",
            "macd",
            "stoch",
            "williams",
            "momentum",
            "ma",
            "ema",
            "sma",
            "moving",
            "trend",
            "adx",
            "cci",
            "roc",
        ],
        "breadth": [
            "breadth",
            "advance",
            "decline",
            "new_highs",
            "new_lows",
            "ad_line",
            "mcclellan",
            "arms",
            "trin",
            "tick",
        ],
        "sentiment": [
            "vix",
            "put_call",
            "sentiment",
            "fear",
            "greed",
            "volatility",
            "skew",
            "term_structure",
            "options",
        ],
        "macro": [
            "yield",
            "rates",
            "inflation",
            "gdp",
            "employment",
            "fed",
            "treasury",
            "bond",
            "curve",
            "dxy",
            "dollar",
        ],
        "microstructure": [
            "volume",
            "spread",
            "bid_ask",
            "flow",
            "liquidity",
            "depth",
            "imbalance",
            "tick_size",
            "market_impact",
        ],
    }

    family_predictions: dict[str, list[tuple[float, int]]] = defaultdict(list)

    for event in events:
        outcome = event.get("outcome", {})
        p_up = event.get("p_up")
        label = outcome.get("label")

        # Skip events without required data
        if p_up is None or label is None:
            continue

        # Analyze top features to determine dominant family
        explain = event.get("explain", {})
        shap_top = explain.get("shap_top", [])

        if not shap_top:
            family_predictions["unknown"].append((p_up, label))
            continue

        # Categorize features by family
        family_weights: dict[str, float] = defaultdict(float)
        total_weight = 0.0

        for feature_name, importance in shap_top:
            feature_lower = str(feature_name).lower()
            abs_importance = abs(float(importance))
            total_weight += abs_importance

            for family, keywords in FEATURE_FAMILIES.items():
                if any(keyword in feature_lower for keyword in keywords):
                    family_weights[family] += abs_importance
                    break
            else:
                family_weights["other"] += abs_importance

        # Assign to dominant family (or "mixed" if no clear winner)
        if total_weight > 0:
            dominant_family, dom_weight = max(
                family_weights.items(), key=lambda x: x[1]
            )
            if dom_weight / total_weight >= 0.4:  # At least 40% weight
                family_predictions[dominant_family].append((p_up, label))
            else:
                family_predictions["mixed"].append((p_up, label))
        else:
            family_predictions["unknown"].append((p_up, label))

    # Calculate Brier scores for each family
    brier_scores: dict[str, float] = {}
    for family, predictions in family_predictions.items():
        if predictions:
            probs = [p for p, _ in predictions]
            labels = [l for _, l in predictions]
            brier_scores[family] = brier_score(probs, labels)

    return brier_scores


def compute_drift_flags(
    current_scores: dict[str, float],
    previous_scores: dict[str, float],
    threshold: float = DRIFT_THRESHOLD,
) -> dict[str, bool]:
    """
    Detect performance drift by comparing current vs previous Brier scores.

    Args:
        current_scores: Current period Brier scores by family
        previous_scores: Previous period Brier scores by family
        threshold: Drift threshold (increase in Brier score)

    Returns:
        Dictionary mapping family to drift flag (True if drifted)
    """
    drift_flags: dict[str, bool] = {}

    for family in current_scores:
        if family in previous_scores:
            current = current_scores[family]
            previous = previous_scores[family]
            drift_flags[family] = (current - previous) > threshold
        else:
            drift_flags[family] = False  # New family, no drift by definition

    return drift_flags


def analyze_feature_importance_drift(
    recent_events: list[dict[str, Any]], window_days: int = 30
) -> dict[str, Any]:
    """
    Analyze changes in feature importance over time.

    Args:
        recent_events: List of recent events
        window_days: Window size for comparison

    Returns:
        Dictionary with feature importance analysis
    """
    if not recent_events:
        return {"status": "no_data"}

    # Split events into current and previous windows
    cutoff_date = datetime.utcnow() - timedelta(days=window_days)
    cutoff_str = cutoff_date.isoformat()

    current_features: dict[str, list[float]] = defaultdict(list)
    previous_features: dict[str, list[float]] = defaultdict(list)

    for event in recent_events:
        event_time = event.get("ts", "")
        explain = event.get("explain", {})
        shap_top = explain.get("shap_top", [])

        target_dict = (
            current_features if event_time >= cutoff_str else previous_features
        )

        for feature_name, importance in shap_top:
            target_dict[str(feature_name)].append(float(importance))

    # Calculate average importance for each feature
    current_avg = {
        feature: sum(values) / len(values)
        for feature, values in current_features.items()
        if values
    }
    previous_avg = {
        feature: sum(values) / len(values)
        for feature, values in previous_features.items()
        if values
    }

    # Find features with significant changes
    importance_changes: dict[str, dict[str, float]] = {}
    for feature in set(current_avg.keys()) | set(previous_avg.keys()):
        curr = current_avg.get(feature, 0.0)
        prev = previous_avg.get(feature, 0.0)
        if prev != 0:
            change_pct = (curr - prev) / abs(prev)
        else:
            change_pct = 1.0 if curr > 0 else 0.0
        importance_changes[feature] = {
            "current_avg": curr,
            "previous_avg": prev,
            "change_pct": change_pct,
        }

    # Sort by absolute change
    sorted_changes = sorted(
        importance_changes.items(), key=lambda x: abs(x[1]["change_pct"]), reverse=True
    )

    return {
        "status": "success",
        "window_days": window_days,
        "current_features": len(current_features),
        "previous_features": len(previous_features),
        "top_changes": sorted_changes[:10],
    }


def generate_learn_report(lookback_days: int = 30) -> dict[str, Any]:
    """
    Generate comprehensive learning report.

    Args:
        lookback_days: Number of days to analyze

    Returns:
        Learning report dictionary
    """
    # Get recent events with outcomes
    recent_events: list[dict[str, Any]] = []
    for event in iter_events():
        if "outcome" in event and event.get("outcome", {}).get("label") is not None:
            recent_events.append(event)

    # Filter to lookback period
    cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)
    cutoff_str = cutoff_date.isoformat()
    filtered_events = [
        event for event in recent_events if event.get("ts", "") >= cutoff_str
    ]

    if not filtered_events:
        return {
            "status": "no_data",
            "lookback_days": lookback_days,
            "generated_at": datetime.utcnow().isoformat(),
        }

    # Calculate current Brier scores
    current_brier = compute_brier_by_family(filtered_events)

    # Load previous report for comparison
    previous_brier: dict[str, float] = {}
    drift_flags: dict[str, bool] = {}

    try:
        path = LEARN_REPORT_PATH
        if os.path.exists(path):
            with open(path) as f:
                prev_report = json.load(f)
                previous_brier = prev_report.get("brier_scores", {}) or {}
    except Exception as e:
        logger.warning(f"Could not load previous report: {e}")

    # Compute drift flags
    if previous_brier:
        drift_flags = compute_drift_flags(current_brier, previous_brier)

    # Overall statistics
    all_probs = [e.get("p_up") for e in filtered_events if e.get("p_up") is not None]
    all_labels = [e.get("outcome", {}).get("label") for e in filtered_events]
    all_labels = [l for l in all_labels if l is not None]

    overall_brier = (
        brier_score(all_probs, all_labels) if all_probs and all_labels else None
    )

    # Feature importance analysis (use recent events to compare windows)
    importance_analysis = analyze_feature_importance_drift(recent_events)

    # Build report
    report: dict[str, Any] = {
        "status": "success",
        "generated_at": datetime.utcnow().isoformat(),
        "lookback_days": lookback_days,
        "total_events": len(filtered_events),
        "overall_brier": overall_brier,
        "brier_scores": current_brier,
        "previous_brier_scores": previous_brier,
        "drift_flags": drift_flags,
        "drift_threshold": DRIFT_THRESHOLD,
        "importance_analysis": importance_analysis,
        "recommendations": [],
    }

    # Generate recommendations
    recommendations: list[dict[str, Any]] = []
    for family, is_drifted in drift_flags.items():
        if is_drifted:
            current_score = current_brier.get(family, 0.0)
            previous_score = previous_brier.get(family, 0.0)
            increase = current_score - previous_score
            recommendations.append(
                {
                    "type": "drift_alert",
                    "family": family,
                    "message": f"Performance drift detected in {family} features",
                    "details": f"Brier score increased by {increase:.4f} (threshold: {DRIFT_THRESHOLD})",
                    "action": f"Consider reweighting or retraining {family} features",
                }
            )

    if overall_brier is not None and overall_brier > 0.3:
        recommendations.append(
            {
                "type": "performance_alert",
                "message": "Overall model performance is poor",
                "details": f"Overall Brier score: {overall_brier:.4f} (should be < 0.25)",
                "action": "Consider model retraining or feature engineering",
            }
        )

    report["recommendations"] = recommendations
    return report


def save_learn_report(report: dict[str, Any]) -> bool:
    """
    Save learning report to disk.

    Args:
        report: Learning report dictionary

    Returns:
        True if successful, False otherwise
    """
    try:
        path = LEARN_REPORT_PATH
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logger.info(f"Learning report saved to {path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save learning report: {e}")
        return False


def load_latest_report() -> dict[str, Any] | None:
    """
    Load the latest learning report.

    Returns:
        Latest report dictionary or None if not found
    """
    try:
        path = LEARN_REPORT_PATH
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load learning report: {e}")
    return None


def run_nightly_learning_job() -> dict[str, Any]:
    """
    Run the nightly learning job.

    This is the main entry point for the scheduled learning task.

    Returns:
        Job execution summary
    """
    logger.info("Starting nightly learning job")

    try:
        # Generate new report
        report = generate_learn_report()

        # Save report
        save_success = save_learn_report(report)

        # Log any drift alerts
        drift_count = sum(1 for flag in report.get("drift_flags", {}).values() if flag)

        # Log recommendations
        recommendations = report.get("recommendations", [])
        for rec in recommendations:
            rec_type = rec.get("type", "unknown")
            rec_message = rec.get("message", "")
            rec_details = rec.get("details", "")
            if rec_type == "drift_alert" and rec_message:
                logger.warning(f"Drift Alert: {rec_message} - {rec_details}")
            elif rec_type == "performance_alert" and rec_message:
                logger.warning(f"Performance Alert: {rec_message} - {rec_details}")

        return {
            "status": "success",
            "drift_detected": drift_count > 0,
            "completed_at": datetime.utcnow().isoformat(),
            "events_analyzed": report.get("total_events", 0),
            "drift_alerts": drift_count,
            "recommendations": len(recommendations),
            "report_saved": save_success,
        }

    except Exception as e:
        logger.error(f"Nightly learning job failed: {e}")
        return {
            "status": "error",
            "completed_at": datetime.utcnow().isoformat(),
            "error": str(e),
        }


# Utility functions for weight adjustment (placeholder)
def suggest_feature_weights(report: dict[str, Any]) -> dict[str, float]:
    """
    Suggest feature weight adjustments based on learning report.

    Args:
        report: Learning report

    Returns:
        Dictionary mapping feature families to suggested weights
    """
    weights: dict[str, float] = {}
    brier_scores: dict[str, float] = report.get("brier_scores", {})

    # Simple inverse relationship: lower Brier = higher weight
    if brier_scores:
        max_score = max(brier_scores.values())
        if max_score == 0:
            # Avoid divide-by-zero; give equal weights
            n = len(brier_scores)
            return dict.fromkeys(brier_scores, 1.0 / n)
        for family, score in brier_scores.items():
            weights[family] = (max_score - score) / max_score

    return weights
