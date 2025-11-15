# backend/app/services/evaluation.py
"""
Comprehensive evaluation metrics for Ziggy's learning system.
Focuses on risk-adjusted performance, calibration, and statistical significance.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss


@dataclass
class PerformanceMetrics:
    """Container for comprehensive trading performance metrics."""

    # Core performance
    total_trades: int
    win_rate: float
    avg_pnl_per_trade: float
    total_pnl: float
    expectancy_after_costs: float

    # Risk metrics
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    max_drawdown_duration: int
    calmar_ratio: float

    # Probability calibration
    brier_score: float
    calibration_slope: float
    calibration_intercept: float
    reliability_diagram: dict[str, list[float]]

    # Trading behavior
    avg_daily_turnover: float
    avg_holding_period: float

    # Statistical measures
    hit_rate_confidence_interval: tuple[float, float]
    expectancy_confidence_interval: tuple[float, float]

    # Feature stability
    psi_scores: dict[str, float]  # Population Stability Index per feature

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "total_trades": self.total_trades,
            "win_rate": self.win_rate,
            "avg_pnl_per_trade": self.avg_pnl_per_trade,
            "total_pnl": self.total_pnl,
            "expectancy_after_costs": self.expectancy_after_costs,
            "sharpe_ratio": self.sharpe_ratio,
            "sortino_ratio": self.sortino_ratio,
            "max_drawdown": self.max_drawdown,
            "max_drawdown_duration": self.max_drawdown_duration,
            "calmar_ratio": self.calmar_ratio,
            "brier_score": self.brier_score,
            "calibration_slope": self.calibration_slope,
            "calibration_intercept": self.calibration_intercept,
            "reliability_diagram": self.reliability_diagram,
            "avg_daily_turnover": self.avg_daily_turnover,
            "avg_holding_period": self.avg_holding_period,
            "hit_rate_confidence_interval": self.hit_rate_confidence_interval,
            "expectancy_confidence_interval": self.expectancy_confidence_interval,
            "psi_scores": self.psi_scores,
        }


def calculate_hit_rate(df: pd.DataFrame, horizon: str = "realized_pnl") -> float:
    """Calculate hit rate (percentage of profitable trades)."""
    if horizon not in df.columns or df[horizon].isna().all():
        return 0.0

    profitable = (df[horizon] > 0).sum()
    total = df[horizon].notna().sum()

    return profitable / max(total, 1)


def calculate_expectancy_after_costs(df: pd.DataFrame) -> float:
    """Calculate expectancy per trade after all costs."""
    if "realized_pnl" not in df.columns:
        return 0.0

    pnl = df["realized_pnl"].dropna()
    if len(pnl) == 0:
        return 0.0

    # Subtract fees and slippage if available
    if "fees_paid" in df.columns:
        fees = df["fees_paid"].fillna(0)
        pnl = pnl - fees[pnl.index]

    if "slippage" in df.columns:
        slippage = df["slippage"].fillna(0)
        pnl = pnl - slippage[pnl.index]

    return pnl.mean()


def calculate_sharpe_ratio(df: pd.DataFrame, risk_free_rate: float = 0.02) -> float:
    """Calculate annualized Sharpe ratio."""
    if "realized_pnl" not in df.columns:
        return 0.0

    pnl = df["realized_pnl"].dropna()
    if len(pnl) < 2:
        return 0.0

    # Annualize assuming 252 trading days
    mean_return = pnl.mean() * 252
    std_return = pnl.std() * np.sqrt(252)

    if std_return == 0:
        return 0.0

    return (mean_return - risk_free_rate) / std_return


def calculate_sortino_ratio(df: pd.DataFrame, risk_free_rate: float = 0.02) -> float:
    """Calculate Sortino ratio (downside deviation)."""
    if "realized_pnl" not in df.columns:
        return 0.0

    pnl = df["realized_pnl"].dropna()
    if len(pnl) < 2:
        return 0.0

    # Annualize
    mean_return = pnl.mean() * 252
    downside_returns = pnl[pnl < 0]

    if len(downside_returns) == 0:
        return float("inf")  # No downside

    downside_std = downside_returns.std() * np.sqrt(252)

    if downside_std == 0:
        return 0.0

    return (mean_return - risk_free_rate) / downside_std


def calculate_max_drawdown(df: pd.DataFrame) -> tuple[float, int]:
    """
    Calculate maximum drawdown and duration.

    Returns:
        Tuple of (max_drawdown_percent, duration_in_trades)
    """
    if "realized_pnl" not in df.columns or len(df) == 0:
        return 0.0, 0

    # Calculate cumulative PnL
    pnl = df["realized_pnl"].fillna(0)
    cumulative_pnl = pnl.cumsum()

    # Calculate running maximum
    running_max = cumulative_pnl.expanding().max()

    # Calculate drawdown
    drawdown = cumulative_pnl - running_max

    max_drawdown = abs(drawdown.min())

    # Calculate duration
    max_dd_duration = 0
    current_duration = 0

    for dd in drawdown:
        if dd < 0:
            current_duration += 1
            max_dd_duration = max(max_dd_duration, current_duration)
        else:
            current_duration = 0

    return max_drawdown, max_dd_duration


def calculate_brier_score(df: pd.DataFrame) -> float:
    """Calculate Brier score for probability calibration."""
    if "predicted_prob" not in df.columns or "realized_pnl" not in df.columns:
        return 1.0  # Worst possible score

    # Filter to rows with both probability and outcome
    valid_mask = df["predicted_prob"].notna() & df["realized_pnl"].notna()
    valid_df = df[valid_mask]

    if len(valid_df) < 10:
        return 1.0

    probabilities = valid_df["predicted_prob"].values
    outcomes = (valid_df["realized_pnl"] > 0).astype(int).values

    return brier_score_loss(outcomes, probabilities)


def calculate_calibration_metrics(
    df: pd.DataFrame, n_bins: int = 10
) -> tuple[float, float, dict[str, list[float]]]:
    """
    Calculate calibration slope, intercept, and reliability diagram data.

    Returns:
        Tuple of (slope, intercept, reliability_diagram)
    """
    if "predicted_prob" not in df.columns or "realized_pnl" not in df.columns:
        return (
            1.0,
            0.0,
            {
                "bin_centers": [],
                "observed_freq": [],
                "predicted_freq": [],
                "counts": [],
            },
        )

    valid_mask = df["predicted_prob"].notna() & df["realized_pnl"].notna()
    valid_df = df[valid_mask]

    if len(valid_df) < 20:
        return (
            1.0,
            0.0,
            {
                "bin_centers": [],
                "observed_freq": [],
                "predicted_freq": [],
                "counts": [],
            },
        )

    probabilities = valid_df["predicted_prob"].values
    outcomes = (valid_df["realized_pnl"] > 0).astype(int).values

    # Calculate calibration slope and intercept via logistic regression
    try:
        from sklearn.linear_model import LogisticRegression

        lr = LogisticRegression(fit_intercept=True)
        lr.fit(probabilities.reshape(-1, 1), outcomes)
        slope = lr.coef_[0][0]
        intercept = lr.intercept_[0]
    except:
        slope, intercept = 1.0, 0.0

    # Create reliability diagram
    bin_edges = np.linspace(0, 1, n_bins + 1)
    bin_centers = []
    observed_freq = []
    predicted_freq = []
    counts = []

    for i in range(n_bins):
        mask = (probabilities >= bin_edges[i]) & (probabilities < bin_edges[i + 1])
        if i == n_bins - 1:  # Include right edge in last bin
            mask = (probabilities >= bin_edges[i]) & (probabilities <= bin_edges[i + 1])

        if mask.sum() > 0:
            bin_center = (bin_edges[i] + bin_edges[i + 1]) / 2
            obs_freq = outcomes[mask].mean()
            pred_freq = probabilities[mask].mean()
            count = mask.sum()

            bin_centers.append(bin_center)
            observed_freq.append(obs_freq)
            predicted_freq.append(pred_freq)
            counts.append(int(count))

    reliability_diagram = {
        "bin_centers": bin_centers,
        "observed_freq": observed_freq,
        "predicted_freq": predicted_freq,
        "counts": counts,
    }

    return slope, intercept, reliability_diagram


def calculate_psi(
    baseline_df: pd.DataFrame, candidate_df: pd.DataFrame, features: list[str]
) -> dict[str, float]:
    """
    Calculate Population Stability Index (PSI) for feature drift detection.

    Args:
        baseline_df: Reference dataset
        candidate_df: New dataset to compare
        features: List of feature column names to check

    Returns:
        Dict mapping feature names to PSI scores
    """
    psi_scores = {}

    for feature in features:
        if feature not in baseline_df.columns or feature not in candidate_df.columns:
            psi_scores[feature] = float("inf")  # Missing feature
            continue

        try:
            baseline_values = baseline_df[feature].dropna()
            candidate_values = candidate_df[feature].dropna()

            if len(baseline_values) == 0 or len(candidate_values) == 0:
                psi_scores[feature] = float("inf")
                continue

            # Create bins based on baseline distribution
            n_bins = min(10, len(baseline_values.unique()))
            bin_edges = np.percentile(baseline_values, np.linspace(0, 100, n_bins + 1))

            # Calculate distributions
            baseline_counts, _ = np.histogram(baseline_values, bins=bin_edges)
            candidate_counts, _ = np.histogram(candidate_values, bins=bin_edges)

            # Add small constant to avoid division by zero
            baseline_pct = (baseline_counts + 1e-6) / (
                baseline_counts.sum() + n_bins * 1e-6
            )
            candidate_pct = (candidate_counts + 1e-6) / (
                candidate_counts.sum() + n_bins * 1e-6
            )

            # Calculate PSI
            psi = np.sum(
                (candidate_pct - baseline_pct) * np.log(candidate_pct / baseline_pct)
            )
            psi_scores[feature] = psi

        except Exception:
            psi_scores[feature] = float("inf")

    return psi_scores


def bootstrap_confidence_interval(
    data: np.ndarray, statistic_func, n_bootstrap: int = 1000, confidence: float = 0.95
) -> tuple[float, float]:
    """Calculate bootstrap confidence interval for a statistic."""
    if len(data) == 0:
        return 0.0, 0.0

    bootstrap_stats = []

    for _ in range(n_bootstrap):
        sample = np.random.choice(data, size=len(data), replace=True)
        bootstrap_stats.append(statistic_func(sample))

    alpha = 1 - confidence
    lower = np.percentile(bootstrap_stats, alpha / 2 * 100)
    upper = np.percentile(bootstrap_stats, (1 - alpha / 2) * 100)

    return lower, upper


def evaluate_trading_performance(
    df: pd.DataFrame, baseline_df: pd.DataFrame | None = None
) -> PerformanceMetrics:
    """
    Calculate comprehensive trading performance metrics.

    Args:
        df: DataFrame with trading data
        baseline_df: Optional baseline for feature drift comparison

    Returns:
        PerformanceMetrics object with all calculated metrics
    """
    # Filter to completed trades
    completed_mask = df["realized_pnl"].notna()
    completed_df = df[completed_mask]

    if len(completed_df) == 0:
        # Return zero metrics if no completed trades
        return PerformanceMetrics(
            total_trades=0,
            win_rate=0.0,
            avg_pnl_per_trade=0.0,
            total_pnl=0.0,
            expectancy_after_costs=0.0,
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            max_drawdown=0.0,
            max_drawdown_duration=0,
            calmar_ratio=0.0,
            brier_score=1.0,
            calibration_slope=1.0,
            calibration_intercept=0.0,
            reliability_diagram={
                "bin_centers": [],
                "observed_freq": [],
                "predicted_freq": [],
                "counts": [],
            },
            avg_daily_turnover=0.0,
            avg_holding_period=0.0,
            hit_rate_confidence_interval=(0.0, 0.0),
            expectancy_confidence_interval=(0.0, 0.0),
            psi_scores={},
        )

    # Core metrics
    total_trades = len(completed_df)
    win_rate = calculate_hit_rate(completed_df)
    avg_pnl_per_trade = completed_df["realized_pnl"].mean()
    total_pnl = completed_df["realized_pnl"].sum()
    expectancy_after_costs = calculate_expectancy_after_costs(completed_df)

    # Risk metrics
    sharpe_ratio = calculate_sharpe_ratio(completed_df)
    sortino_ratio = calculate_sortino_ratio(completed_df)
    max_drawdown, max_dd_duration = calculate_max_drawdown(completed_df)

    calmar_ratio = 0.0
    if max_drawdown > 0:
        annual_return = avg_pnl_per_trade * 252  # Assuming daily trading
        calmar_ratio = annual_return / max_drawdown

    # Probability calibration
    brier_score = calculate_brier_score(completed_df)
    calibration_slope, calibration_intercept, reliability_diagram = (
        calculate_calibration_metrics(completed_df)
    )

    # Trading behavior metrics
    avg_daily_turnover = 0.0
    avg_holding_period = 0.0

    if "timestamp" in completed_df.columns:
        # Calculate daily turnover
        completed_df["date"] = pd.to_datetime(
            completed_df["timestamp"], unit="s"
        ).dt.date
        daily_trades = completed_df.groupby("date").size()
        avg_daily_turnover = daily_trades.mean()

        # Estimate holding period (if we have entry/exit times)
        if "exit_timestamp" in completed_df.columns:
            holding_periods = completed_df["exit_timestamp"] - completed_df["timestamp"]
            avg_holding_period = holding_periods.mean() / 3600  # Convert to hours

    # Statistical confidence intervals
    outcomes = (completed_df["realized_pnl"] > 0).astype(int).values
    pnl_values = completed_df["realized_pnl"].values

    hit_rate_ci = bootstrap_confidence_interval(outcomes, lambda x: x.mean())
    expectancy_ci = bootstrap_confidence_interval(pnl_values, lambda x: x.mean())

    # Feature stability (PSI)
    psi_scores = {}
    if baseline_df is not None:
        feature_cols = [
            col
            for col in df.columns
            if col.startswith("feature_") or col in ["rsi", "atr", "regime_strength"]
        ]
        if len(feature_cols) > 0:
            psi_scores = calculate_psi(baseline_df, df, feature_cols)

    return PerformanceMetrics(
        total_trades=total_trades,
        win_rate=win_rate,
        avg_pnl_per_trade=avg_pnl_per_trade,
        total_pnl=total_pnl,
        expectancy_after_costs=expectancy_after_costs,
        sharpe_ratio=sharpe_ratio,
        sortino_ratio=sortino_ratio,
        max_drawdown=max_drawdown,
        max_drawdown_duration=max_dd_duration,
        calmar_ratio=calmar_ratio,
        brier_score=brier_score,
        calibration_slope=calibration_slope,
        calibration_intercept=calibration_intercept,
        reliability_diagram=reliability_diagram,
        avg_daily_turnover=avg_daily_turnover,
        avg_holding_period=avg_holding_period,
        hit_rate_confidence_interval=hit_rate_ci,
        expectancy_confidence_interval=expectancy_ci,
        psi_scores=psi_scores,
    )


def compare_runs(
    baseline_metrics: PerformanceMetrics, candidate_metrics: PerformanceMetrics
) -> dict[str, Any]:
    """
    Compare two metric sets and return deltas with statistical significance.

    Returns:
        Dict with comparison results and significance tests
    """
    comparison = {
        "sharpe_improvement": candidate_metrics.sharpe_ratio
        - baseline_metrics.sharpe_ratio,
        "sharpe_improvement_pct": (
            (candidate_metrics.sharpe_ratio / max(baseline_metrics.sharpe_ratio, 0.001))
            - 1
        )
        * 100,
        "brier_improvement": baseline_metrics.brier_score
        - candidate_metrics.brier_score,  # Lower is better
        "brier_improvement_pct": (
            (baseline_metrics.brier_score / max(candidate_metrics.brier_score, 0.001))
            - 1
        )
        * 100,
        "win_rate_delta": candidate_metrics.win_rate - baseline_metrics.win_rate,
        "win_rate_delta_pct": (
            (candidate_metrics.win_rate / max(baseline_metrics.win_rate, 0.001)) - 1
        )
        * 100,
        "expectancy_delta": candidate_metrics.expectancy_after_costs
        - baseline_metrics.expectancy_after_costs,
        "expectancy_delta_pct": (
            (
                candidate_metrics.expectancy_after_costs
                / max(abs(baseline_metrics.expectancy_after_costs), 0.001)
            )
            - 1
        )
        * 100,
        "max_drawdown_delta": candidate_metrics.max_drawdown
        - baseline_metrics.max_drawdown,
        "max_drawdown_delta_pct": (
            (candidate_metrics.max_drawdown / max(baseline_metrics.max_drawdown, 0.001))
            - 1
        )
        * 100,
        "calibration_slope_delta": candidate_metrics.calibration_slope
        - baseline_metrics.calibration_slope,
        "total_trades": {
            "baseline": baseline_metrics.total_trades,
            "candidate": candidate_metrics.total_trades,
            "delta": candidate_metrics.total_trades - baseline_metrics.total_trades,
        },
    }

    # Statistical significance tests
    baseline_ci = baseline_metrics.hit_rate_confidence_interval
    candidate_ci = candidate_metrics.hit_rate_confidence_interval

    # Check if confidence intervals overlap
    hit_rate_significant = (candidate_ci[0] > baseline_ci[1]) or (
        candidate_ci[1] < baseline_ci[0]
    )

    comparison["hit_rate_statistically_significant"] = hit_rate_significant
    comparison["baseline_hit_rate_ci"] = baseline_ci
    comparison["candidate_hit_rate_ci"] = candidate_ci

    return comparison


if __name__ == "__main__":
    # Example usage
    import numpy as np
    import pandas as pd

    # Create sample data
    np.random.seed(42)
    n_trades = 500

    sample_data = pd.DataFrame(
        {
            "realized_pnl": np.random.normal(10, 50, n_trades),
            "predicted_prob": np.random.beta(2, 2, n_trades),
            "fees_paid": np.random.uniform(1, 5, n_trades),
            "slippage": np.random.uniform(0, 2, n_trades),
            "timestamp": np.linspace(1634567890, 1634567890 + 86400 * 30, n_trades),
        }
    )

    # Calculate metrics
    metrics = evaluate_trading_performance(sample_data)
    print("Sample metrics:")
    print(f"Sharpe ratio: {metrics.sharpe_ratio:.3f}")
    print(f"Win rate: {metrics.win_rate:.3f}")
    print(f"Brier score: {metrics.brier_score:.3f}")
    print(f"Max drawdown: {metrics.max_drawdown:.2f}")
