# backend/app/services/calibration.py
"""
Probability calibration system for Ziggy's trading signals.
Ensures predicted probabilities match actual outcomes for better decision-making.
"""

from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss


@dataclass
class CalibrationReport:
    """Results from calibration analysis."""

    method: str  # 'isotonic' or 'platt'
    n_train_samples: int
    n_test_samples: int

    # Before calibration
    raw_brier_score: float
    raw_log_loss: float

    # After calibration
    calibrated_brier_score: float
    calibrated_log_loss: float

    # Reliability diagram data
    bin_centers: list[float]
    bin_frequencies: list[float]
    bin_counts: list[int]

    # Calibration curve
    calibration_curve_x: list[float]
    calibration_curve_y: list[float]

    # Quality metrics
    calibration_slope: float
    calibration_intercept: float
    perfect_calibration_mse: float  # Mean squared error from perfect calibration line


class ProbabilityCalibrator:
    """
    Probability calibration using isotonic regression or Platt scaling.
    """

    def __init__(self, method: str = "isotonic", min_samples: int = 100):
        """
        Initialize calibrator.

        Args:
            method: 'isotonic' or 'platt'
            min_samples: Minimum samples required for calibration
        """
        if method not in ["isotonic", "platt"]:
            raise ValueError("Method must be 'isotonic' or 'platt'")

        self.method = method
        self.min_samples = min_samples
        self.calibrator = None
        self.is_fitted = False

    def fit(self, probabilities: np.ndarray, outcomes: np.ndarray) -> bool:
        """
        Fit calibration model on training data.

        Args:
            probabilities: Raw predicted probabilities [0,1]
            outcomes: Binary outcomes (0 or 1)

        Returns:
            True if calibration was successful, False otherwise
        """
        if len(probabilities) < self.min_samples:
            return False

        probabilities = np.clip(probabilities, 1e-6, 1 - 1e-6)  # Avoid extremes
        outcomes = outcomes.astype(int)

        try:
            if self.method == "isotonic":
                self.calibrator = IsotonicRegression(out_of_bounds="clip")
                self.calibrator.fit(probabilities, outcomes)
            else:  # platt
                self.calibrator = LogisticRegression(fit_intercept=True, max_iter=1000)
                self.calibrator.fit(probabilities.reshape(-1, 1), outcomes)

            self.is_fitted = True
            return True

        except Exception as e:
            print(f"Calibration fitting failed: {e}")
            return False

    def predict(self, probabilities: np.ndarray) -> np.ndarray:
        """
        Apply calibration to raw probabilities.

        Args:
            probabilities: Raw probabilities to calibrate

        Returns:
            Calibrated probabilities
        """
        if not self.is_fitted:
            return probabilities  # Return uncalibrated if not fitted

        probabilities = np.clip(probabilities, 1e-6, 1 - 1e-6)

        try:
            if self.method == "isotonic":
                return self.calibrator.predict(probabilities)
            else:  # platt
                return self.calibrator.predict_proba(probabilities.reshape(-1, 1))[:, 1]
        except Exception:
            return probabilities  # Fallback to uncalibrated

    def save(self, filepath: str) -> bool:
        """Save calibrator to disk."""
        try:
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, "wb") as f:
                pickle.dump(
                    {
                        "method": self.method,
                        "min_samples": self.min_samples,
                        "calibrator": self.calibrator,
                        "is_fitted": self.is_fitted,
                    },
                    f,
                )
            return True
        except Exception as e:
            print(f"Failed to save calibrator: {e}")
            return False

    def load(self, filepath: str) -> bool:
        """Load calibrator from disk."""
        try:
            with open(filepath, "rb") as f:
                data = pickle.load(f)

            self.method = data["method"]
            self.min_samples = data["min_samples"]
            self.calibrator = data["calibrator"]
            self.is_fitted = data["is_fitted"]
            return True
        except Exception as e:
            print(f"Failed to load calibrator: {e}")
            return False


def generate_reliability_diagram_data(
    probabilities: np.ndarray, outcomes: np.ndarray, n_bins: int = 10
) -> tuple[list[float], list[float], list[int]]:
    """
    Generate data for reliability diagram.

    Returns:
        Tuple of (bin_centers, bin_frequencies, bin_counts)
    """
    bin_edges = np.linspace(0, 1, n_bins + 1)
    bin_centers = []
    bin_frequencies = []
    bin_counts = []

    for i in range(n_bins):
        mask = (probabilities >= bin_edges[i]) & (probabilities < bin_edges[i + 1])
        if i == n_bins - 1:  # Include right edge in last bin
            mask = (probabilities >= bin_edges[i]) & (probabilities <= bin_edges[i + 1])

        if mask.sum() > 0:
            bin_center = (bin_edges[i] + bin_edges[i + 1]) / 2
            bin_freq = outcomes[mask].mean()
            bin_count = mask.sum()

            bin_centers.append(bin_center)
            bin_frequencies.append(bin_freq)
            bin_counts.append(int(bin_count))

    return bin_centers, bin_frequencies, bin_counts


def generate_calibration_curve(
    probabilities: np.ndarray, outcomes: np.ndarray, n_points: int = 20
) -> tuple[list[float], list[float]]:
    """
    Generate calibration curve by binning probabilities and calculating empirical frequencies.

    Returns:
        Tuple of (prob_points, frequency_points)
    """
    # Sort by probability
    sorted_indices = np.argsort(probabilities)
    sorted_probs = probabilities[sorted_indices]
    sorted_outcomes = outcomes[sorted_indices]

    # Create bins with roughly equal number of samples
    bin_size = len(probabilities) // n_points

    prob_points = []
    freq_points = []

    for i in range(0, len(probabilities), bin_size):
        end_idx = min(i + bin_size, len(probabilities))

        if end_idx - i >= 5:  # Minimum samples per bin
            bin_probs = sorted_probs[i:end_idx]
            bin_outcomes = sorted_outcomes[i:end_idx]

            avg_prob = bin_probs.mean()
            empirical_freq = bin_outcomes.mean()

            prob_points.append(avg_prob)
            freq_points.append(empirical_freq)

    return prob_points, freq_points


def calculate_calibration_quality(
    probabilities: np.ndarray, outcomes: np.ndarray
) -> dict[str, float]:
    """
    Calculate calibration quality metrics.

    Returns:
        Dict with calibration slope, intercept, and MSE from perfect calibration
    """
    try:
        # Fit linear regression: outcomes ~ probabilities
        from sklearn.linear_model import LinearRegression

        lr = LinearRegression()
        lr.fit(probabilities.reshape(-1, 1), outcomes)

        slope = lr.coef_[0]
        intercept = lr.intercept_

        # Calculate MSE from perfect calibration (y = x line)
        perfect_line = probabilities
        actual_outcomes = outcomes
        mse = np.mean((actual_outcomes - perfect_line) ** 2)

        return {
            "calibration_slope": slope,
            "calibration_intercept": intercept,
            "perfect_calibration_mse": mse,
        }
    except Exception:
        return {
            "calibration_slope": 1.0,
            "calibration_intercept": 0.0,
            "perfect_calibration_mse": float("inf"),
        }


def validate_calibration(
    train_probs: np.ndarray,
    train_outcomes: np.ndarray,
    test_probs: np.ndarray,
    test_outcomes: np.ndarray,
    method: str = "isotonic",
) -> CalibrationReport:
    """
    Validate calibration on train/test split.

    Args:
        train_probs: Training probabilities
        train_outcomes: Training outcomes
        test_probs: Test probabilities
        test_outcomes: Test outcomes
        method: Calibration method

    Returns:
        CalibrationReport with all metrics
    """
    # Initialize calibrator
    calibrator = ProbabilityCalibrator(method=method)

    # Fit on training data
    calibrator.fit(train_probs, train_outcomes)

    # Calculate raw (uncalibrated) metrics on test set
    test_probs_clipped = np.clip(test_probs, 1e-6, 1 - 1e-6)
    raw_brier = brier_score_loss(test_outcomes, test_probs_clipped)
    raw_log_loss_val = log_loss(test_outcomes, test_probs_clipped)

    # Apply calibration to test set
    calibrated_test_probs = calibrator.predict(test_probs)
    calibrated_test_probs = np.clip(calibrated_test_probs, 1e-6, 1 - 1e-6)

    # Calculate calibrated metrics
    calibrated_brier = brier_score_loss(test_outcomes, calibrated_test_probs)
    calibrated_log_loss_val = log_loss(test_outcomes, calibrated_test_probs)

    # Generate reliability diagram data
    bin_centers, bin_frequencies, bin_counts = generate_reliability_diagram_data(
        calibrated_test_probs, test_outcomes
    )

    # Generate calibration curve
    cal_curve_x, cal_curve_y = generate_calibration_curve(calibrated_test_probs, test_outcomes)

    # Calculate calibration quality
    quality_metrics = calculate_calibration_quality(calibrated_test_probs, test_outcomes)

    return CalibrationReport(
        method=method,
        n_train_samples=len(train_probs),
        n_test_samples=len(test_probs),
        raw_brier_score=raw_brier,
        raw_log_loss=raw_log_loss_val,
        calibrated_brier_score=calibrated_brier,
        calibrated_log_loss=calibrated_log_loss_val,
        bin_centers=bin_centers,
        bin_frequencies=bin_frequencies,
        bin_counts=bin_counts,
        calibration_curve_x=cal_curve_x,
        calibration_curve_y=cal_curve_y,
        calibration_slope=quality_metrics["calibration_slope"],
        calibration_intercept=quality_metrics["calibration_intercept"],
        perfect_calibration_mse=quality_metrics["perfect_calibration_mse"],
    )


def build_and_save_calibrator(
    df: pd.DataFrame,
    output_path: str = "./data/models/calibrator.pkl",
    method: str = "isotonic",
    test_size: float = 0.2,
) -> CalibrationReport | None:
    """
    Build calibration model from trading data and save to disk.

    Args:
        df: DataFrame with 'predicted_prob' and 'realized_pnl' columns
        output_path: Where to save the calibrator
        method: Calibration method
        test_size: Fraction of data to use for testing

    Returns:
        CalibrationReport if successful, None otherwise
    """
    # Filter to valid data
    valid_mask = df["predicted_prob"].notna() & df["realized_pnl"].notna()
    valid_df = df[valid_mask]

    if len(valid_df) < 100:
        print("Insufficient data for calibration")
        return None

    # Prepare data
    probabilities = valid_df["predicted_prob"].values
    outcomes = (valid_df["realized_pnl"] > 0).astype(int).values

    # Train/test split (chronological)
    split_idx = int(len(valid_df) * (1 - test_size))

    train_probs = probabilities[:split_idx]
    train_outcomes = outcomes[:split_idx]
    test_probs = probabilities[split_idx:]
    test_outcomes = outcomes[split_idx:]

    # Validate calibration
    report = validate_calibration(train_probs, train_outcomes, test_probs, test_outcomes, method)

    # Build final calibrator on all data
    calibrator = ProbabilityCalibrator(method=method)
    if calibrator.fit(probabilities, outcomes):
        # Save calibrator
        if calibrator.save(output_path):
            print(f"Calibrator saved to {output_path}")
        else:
            print("Failed to save calibrator")

    return report


def load_and_apply_calibrator(
    probabilities: np.ndarray, calibrator_path: str = "./data/models/calibrator.pkl"
) -> np.ndarray:
    """
    Load calibrator and apply to probabilities.

    Args:
        probabilities: Raw probabilities to calibrate
        calibrator_path: Path to saved calibrator

    Returns:
        Calibrated probabilities (or original if loading fails)
    """
    calibrator = ProbabilityCalibrator()

    if calibrator.load(calibrator_path):
        return calibrator.predict(probabilities)
    else:
        print("Failed to load calibrator, returning uncalibrated probabilities")
        return probabilities


def report_calibration_metrics(report: CalibrationReport) -> str:
    """
    Generate human-readable calibration report.
    """
    lines = [
        f"Calibration Report ({report.method})",
        "=" * 40,
        f"Training samples: {report.n_train_samples}",
        f"Test samples: {report.n_test_samples}",
        "",
        "Performance Improvement:",
        f"  Brier Score: {report.raw_brier_score:.4f} → {report.calibrated_brier_score:.4f} "
        f"(Δ {report.calibrated_brier_score - report.raw_brier_score:+.4f})",
        f"  Log Loss: {report.raw_log_loss:.4f} → {report.calibrated_log_loss:.4f} "
        f"(Δ {report.calibrated_log_loss - report.raw_log_loss:+.4f})",
        "",
        "Calibration Quality:",
        f"  Slope: {report.calibration_slope:.3f} (ideal: 1.0)",
        f"  Intercept: {report.calibration_intercept:.3f} (ideal: 0.0)",
        f"  Perfect Calibration MSE: {report.perfect_calibration_mse:.4f}",
        "",
        f"Reliability bins with data: {len(report.bin_centers)}",
    ]

    return "\n".join(lines)


if __name__ == "__main__":
    # Example usage
    import numpy as np
    import pandas as pd

    # Generate synthetic trading data
    np.random.seed(42)
    n_samples = 1000

    # Simulate miscalibrated probabilities
    true_probs = np.random.beta(2, 2, n_samples)
    # Add calibration error
    raw_probs = true_probs * 0.8 + 0.1  # Shift and scale
    outcomes = np.random.binomial(1, true_probs, n_samples)

    df = pd.DataFrame(
        {
            "predicted_prob": raw_probs,
            "realized_pnl": outcomes * 100 - 50,  # Profitable if outcome=1
        }
    )

    # Build and validate calibrator
    report = build_and_save_calibrator(df, method="isotonic")

    if report:
        print(report_calibration_metrics(report))

        # Test loading and applying
        test_probs = np.array([0.2, 0.5, 0.8])
        calibrated = load_and_apply_calibrator(test_probs)
        print(f"\nTest calibration: {test_probs} → {calibrated}")
