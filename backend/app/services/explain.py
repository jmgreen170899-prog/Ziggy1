"""
ZiggyAI Explain Service - Feature Analysis and Mind-Flip Detection

Provides explanation services for signal decisions including:
- SHAP feature importance analysis
- Waterfall chart data generation
- Calibration curve sampling
- Mind-flip detection (feature changes vs last signal)
- Data staleness computation

Brain-first: All computations are designed for storage/retrieval from memory.
"""

import hashlib
import logging
import os
import time
from datetime import datetime
from typing import Any


logger = logging.getLogger(__name__)

# Environment configuration
EXPLAIN_TOPK = int(os.getenv("EXPLAIN_TOPK", "5"))
STALENESS_THRESHOLD = 0.15  # 15% change threshold for mind-flip detection


def get_top_features(ticker: str, limit: int = None) -> list[list[Any]]:
    """
    Get top contributing features for a ticker.

    In production, this would query the actual feature importance from
    the model. For now, returns mock SHAP-style feature contributions.

    Args:
        ticker: Stock symbol
        limit: Number of top features to return

    Returns:
        List of [feature_name, contribution] pairs
    """
    if limit is None:
        limit = EXPLAIN_TOPK

    # Mock feature importance based on ticker characteristics
    # In production, this would come from actual SHAP values

    ticker_features = {
        "AAPL": [
            ["momentum_20d", 0.24],
            ["sentiment_news", 0.18],
            ["earnings_surprise", 0.16],
            ["volume_ratio", 0.12],
            ["sector_rotation", 0.10],
            ["options_flow", 0.08],
            ["technical_confluence", 0.07],
            ["macro_correlation", 0.05],
        ],
        "TSLA": [
            ["volatility_regime", 0.28],
            ["elon_sentiment", 0.22],
            ["ev_sector_momentum", 0.18],
            ["options_gamma", 0.15],
            ["crypto_correlation", 0.10],
            ["delivery_expectations", 0.07],
        ],
        "SPY": [
            ["vix_term_structure", 0.26],
            ["yield_curve_slope", 0.20],
            ["breadth_advance_decline", 0.18],
            ["sector_rotation", 0.14],
            ["fed_policy_expectations", 0.12],
            ["international_flows", 0.10],
        ],
    }

    # Get features for specific ticker or use default
    features = ticker_features.get(
        ticker.upper(),
        [
            ["momentum", 0.25],
            ["sentiment", 0.20],
            ["volatility", 0.18],
            ["volume", 0.15],
            ["sector", 0.12],
            ["macro", 0.10],
        ],
    )

    # Add some noise to make it more realistic
    import random

    random.seed(hash(ticker) % 2**32)  # Deterministic but varied by ticker

    noisy_features = []
    for feature_name, base_contrib in features[:limit]:
        # Add ±5% noise
        noise = random.uniform(-0.05, 0.05)
        contrib = base_contrib + noise
        noisy_features.append([feature_name, round(contrib, 3)])

    # Normalize so they sum to ~1.0
    total = sum(contrib for _, contrib in noisy_features)
    if total > 0:
        noisy_features = [[name, round(contrib / total, 3)] for name, contrib in noisy_features]

    return noisy_features


def build_waterfall(top_features: list[list[Any]]) -> list[dict[str, Any]]:
    """
    Convert top features into waterfall chart data.

    Creates a sequential breakdown showing how each feature contributes
    to the final prediction, building up from a base probability.

    Args:
        top_features: List of [feature_name, contribution] pairs

    Returns:
        List of waterfall data points with cumulative deltas
    """
    waterfall = []
    cumulative = 0.0

    # Starting point (base probability)
    waterfall.append(
        {"name": "base", "delta": 0.0, "cumulative": 0.5, "type": "base"}  # Start at neutral
    )
    cumulative = 0.5

    # Add each feature contribution
    for feature_name, contribution in top_features:
        delta = float(contribution)
        cumulative += delta

        waterfall.append(
            {
                "name": feature_name,
                "delta": delta,
                "cumulative": round(cumulative, 3),
                "type": "positive" if delta > 0 else "negative",
            }
        )

    # Final result
    waterfall.append(
        {"name": "final", "delta": 0.0, "cumulative": round(cumulative, 3), "type": "result"}
    )

    return waterfall


def sample_calibration(curve_points: int = 12) -> dict[str, Any]:
    """
    Generate calibration curve sample for display.

    In production, this would sample from the actual calibration
    curve stored in the model. Returns Expected Calibration Error (ECE)
    and binned probability data.

    Args:
        curve_points: Number of calibration bins to return

    Returns:
        Dictionary with calibration bins and ECE
    """
    # Mock calibration data - in production this comes from model validation
    bins = []
    total_ece = 0.0

    for i in range(curve_points):
        # Create realistic calibration curve (slightly overconfident)
        bin_center = (i + 0.5) / curve_points

        # Add slight miscalibration (models tend to be overconfident)
        actual_freq = bin_center * 0.95 + 0.025  # Slight compression toward 50%

        # Calculate bin ECE contribution
        bin_width = 1.0 / curve_points
        bin_ece = abs(bin_center - actual_freq) * bin_width
        total_ece += bin_ece

        bins.append([round(bin_center, 3), round(actual_freq, 3)])

    return {
        "bins": bins,
        "ece": round(total_ece, 4),
        "num_bins": curve_points,
        "reliability": "good" if total_ece < 0.05 else "fair" if total_ece < 0.10 else "poor",
    }


def compute_staleness(ttl_seconds: int) -> dict[str, Any]:
    """
    Compute data staleness information.

    Args:
        ttl_seconds: Time-to-live threshold in seconds

    Returns:
        Staleness metadata with age and freshness status
    """
    # Mock staleness computation - in production this would check
    # actual data timestamps vs current time

    # Simulate some data age (random but deterministic)
    current_time = time.time()
    data_age_ms = int((current_time % 100) * 1000)  # 0-100 seconds in ms

    is_stale = data_age_ms > (ttl_seconds * 1000)

    return {
        "age_ms": data_age_ms,
        "ttl_s": ttl_seconds,
        "is_stale": is_stale,
        "freshness": "stale" if is_stale else "fresh",
        "computed_at": datetime.utcnow().isoformat() + "Z",
    }


def compute_mind_flip(
    current_features: list[list[Any]], last_event: dict[str, Any] | None
) -> dict[str, Any]:
    """
    Detect mind-flip by comparing current features to last signal.

    Analyzes feature importance changes to determine if the model's
    "mind has changed" significantly since the last signal.

    Args:
        current_features: Current top features [[name, contrib], ...]
        last_event: Previous event data from memory

    Returns:
        Mind-flip analysis with feature differences
    """
    if not last_event:
        return {"since_event": None, "flipped": False, "diff": [], "reason": "no_previous_event"}

    # Extract previous features
    last_explain = last_event.get("explain", {})
    last_features = last_explain.get("shap_top", [])

    if not last_features:
        return {
            "since_event": last_event.get("id"),
            "flipped": False,
            "diff": [],
            "reason": "no_previous_features",
        }

    # Convert to dictionaries for comparison
    current_dict = {name: contrib for name, contrib in current_features}
    last_dict = {name: contrib for name, contrib in last_features}

    # Calculate feature differences
    differences = []
    significant_changes = 0

    # Check changes in existing features
    for feature_name, current_contrib in current_dict.items():
        if feature_name in last_dict:
            last_contrib = last_dict[feature_name]
            delta = current_contrib - last_contrib

            if abs(delta) > STALENESS_THRESHOLD:
                significant_changes += 1

            differences.append(
                [
                    feature_name,
                    round(current_contrib, 3),
                    round(last_contrib, 3),
                    round(delta, 3),
                    "significant" if abs(delta) > STALENESS_THRESHOLD else "minor",
                ]
            )

    # Check for new features
    for feature_name, contrib in current_dict.items():
        if feature_name not in last_dict:
            differences.append(
                [feature_name, round(contrib, 3), 0.0, round(contrib, 3), "new_feature"]
            )
            significant_changes += 1

    # Check for removed features
    for feature_name, contrib in last_dict.items():
        if feature_name not in current_dict:
            differences.append(
                [feature_name, 0.0, round(contrib, 3), round(-contrib, 3), "removed_feature"]
            )
            significant_changes += 1

    # Determine if mind flipped
    flipped = significant_changes >= 2  # Need at least 2 significant changes

    return {
        "since_event": last_event.get("id"),
        "flipped": flipped,
        "diff": differences,
        "significant_changes": significant_changes,
        "threshold": STALENESS_THRESHOLD,
        "reason": "mind_flip" if flipped else "stable",
    }


def generate_explanation_hash(ticker: str, features: list[list[Any]], regime: str) -> str:
    """
    Generate a hash for explanation caching.

    Creates a deterministic hash based on the key explanation inputs
    to enable efficient caching and retrieval.

    Args:
        ticker: Stock symbol
        features: Feature contributions
        regime: Market regime

    Returns:
        Hex hash string for caching
    """
    # Create hash input from key parameters
    hash_input = f"{ticker}:{regime}:"

    # Add features in sorted order for consistency
    sorted_features = sorted(features, key=lambda x: x[0])  # Sort by feature name
    for name, contrib in sorted_features:
        hash_input += f"{name}:{contrib:.3f}:"

    # Generate SHA256 hash
    return hashlib.sha256(hash_input.encode()).hexdigest()[:16]


def validate_explanation_quality(explanation_data: dict[str, Any]) -> dict[str, Any]:
    """
    Validate the quality of an explanation.

    Checks for completeness, reasonableness, and potential issues
    with the explanation data.

    Args:
        explanation_data: Complete explanation data

    Returns:
        Validation results with quality score and issues
    """
    issues = []
    quality_score = 1.0

    # Check feature coverage
    features = explanation_data.get("top_features", [])
    if len(features) < 3:
        issues.append("insufficient_features")
        quality_score -= 0.2

    # Check feature contribution sum
    total_contrib = sum(abs(contrib) for _, contrib in features)
    if total_contrib < 0.5:
        issues.append("weak_feature_signal")
        quality_score -= 0.15

    # Check calibration quality
    calibration = explanation_data.get("calibration", {})
    ece = calibration.get("ece", 0.0)
    if ece > 0.10:
        issues.append("poor_calibration")
        quality_score -= 0.2

    # Check staleness
    staleness = explanation_data.get("staleness", {})
    if staleness.get("is_stale", False):
        issues.append("stale_data")
        quality_score -= 0.1

    # Check for neighbors
    neighbors = explanation_data.get("neighbors", [])
    if len(neighbors) == 0:
        issues.append("no_neighbors")
        quality_score -= 0.1

    quality_score = max(0.0, quality_score)

    return {
        "quality_score": round(quality_score, 2),
        "issues": issues,
        "is_high_quality": quality_score >= 0.8,
        "recommendation": (
            "use" if quality_score >= 0.7 else "caution" if quality_score >= 0.5 else "avoid"
        ),
    }
