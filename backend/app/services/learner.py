# backend/app/services/learner.py
"""
Strict rule-based learning system for Ziggy AI.
Focuses on interpretable parameter optimization with rigorous validation gates.
"""

from __future__ import annotations

import json
import time
from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .calibration import ProbabilityCalibrator
from .data_log import get_logger
from .evaluation import PerformanceMetrics, compare_runs, evaluate_trading_performance


@dataclass
class RuleParameter:
    """Definition of a rule parameter that can be optimized."""

    name: str
    current_value: Any
    param_type: str  # 'float', 'int', 'bool'
    min_value: float | None = None
    max_value: float | None = None
    step_size: float | None = None
    category: str = "general"  # 'signal', 'regime', 'risk', 'timing'


@dataclass
class RuleSet:
    """Complete set of trading rules with versioning."""

    version: str
    parameters: dict[str, RuleParameter]
    creation_timestamp: float
    description: str = ""
    parent_version: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "version": self.version,
            "parameters": {k: asdict(v) for k, v in self.parameters.items()},
            "creation_timestamp": self.creation_timestamp,
            "description": self.description,
            "parent_version": self.parent_version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RuleSet:
        """Create from dictionary."""
        parameters = {}
        for k, v in data["parameters"].items():
            parameters[k] = RuleParameter(**v)

        return cls(
            version=data["version"],
            parameters=parameters,
            creation_timestamp=data["creation_timestamp"],
            description=data.get("description", ""),
            parent_version=data.get("parent_version"),
        )


@dataclass
class StrictGates:
    """Strict validation gates that candidate rules must pass."""

    min_trades: int = 200
    min_sharpe_improvement_abs: float = 0.20
    min_sharpe_improvement_rel: float = 0.15
    max_brier_score_improvement: float = 0.02  # Lower is better
    calibration_slope_range: tuple[float, float] = (0.8, 1.2)
    max_drawdown_deterioration_rel: float = 0.10
    hit_rate_significance_p: float = 0.05
    max_psi_threshold: float = 0.25
    max_daily_turnover_cap: float = 50.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class LearningResult:
    """Results from a learning iteration."""

    baseline_version: str
    candidate_version: str
    passed_gates: bool
    gate_results: dict[str, bool]
    baseline_metrics: PerformanceMetrics
    candidate_metrics: PerformanceMetrics
    comparison: dict[str, Any]
    recommendation: str
    timestamp: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "baseline_version": self.baseline_version,
            "candidate_version": self.candidate_version,
            "passed_gates": self.passed_gates,
            "gate_results": self.gate_results,
            "baseline_metrics": self.baseline_metrics.to_dict(),
            "candidate_metrics": self.candidate_metrics.to_dict(),
            "comparison": self.comparison,
            "recommendation": self.recommendation,
            "timestamp": self.timestamp,
        }


class RuleParameterGenerator:
    """Generates candidate rule modifications."""

    def __init__(self, max_candidates: int = 50):
        self.max_candidates = max_candidates

    def generate_candidates(self, current_rules: RuleSet) -> list[RuleSet]:
        """
        Generate candidate rule sets by making small modifications.

        Args:
            current_rules: Current rule set to modify

        Returns:
            List of candidate rule sets
        """
        candidates = []

        for param_name, param in current_rules.parameters.items():
            # Generate variations for this parameter
            param_candidates = self._generate_parameter_variations(param)

            for new_value in param_candidates:
                # Create new rule set with modified parameter
                candidate_rules = deepcopy(current_rules)
                candidate_rules.parameters[param_name].current_value = new_value
                candidate_rules.version = (
                    f"{current_rules.version}_mod_{param_name}_{len(candidates)}"
                )
                candidate_rules.parent_version = current_rules.version
                candidate_rules.creation_timestamp = time.time()
                candidate_rules.description = (
                    f"Modified {param_name}: {param.current_value} → {new_value}"
                )

                candidates.append(candidate_rules)

                if len(candidates) >= self.max_candidates:
                    return candidates

        return candidates

    def _generate_parameter_variations(self, param: RuleParameter) -> list[Any]:
        """Generate variations for a single parameter."""
        variations = []
        current = param.current_value

        if param.param_type == "float":
            if (
                param.step_size
                and param.min_value is not None
                and param.max_value is not None
            ):
                # Grid search around current value
                steps = [-2, -1, 1, 2]  # Small steps around current
                for step in steps:
                    new_val = current + step * param.step_size
                    if param.min_value <= new_val <= param.max_value:
                        variations.append(new_val)
            else:
                # Default percentage variations
                for pct in [-0.20, -0.10, 0.10, 0.20]:
                    new_val = current * (1 + pct)
                    if param.min_value is None or new_val >= param.min_value:
                        if param.max_value is None or new_val <= param.max_value:
                            variations.append(new_val)

        elif param.param_type == "int":
            if param.min_value is not None and param.max_value is not None:
                for delta in [-2, -1, 1, 2]:
                    new_val = int(current + delta)
                    if param.min_value <= new_val <= param.max_value:
                        variations.append(new_val)

        elif param.param_type == "bool":
            variations.append(not current)

        return variations


class StrictLearner:
    """
    Strict learning system that optimizes rule parameters with rigorous validation.
    """

    def __init__(
        self,
        data_window_days: int = 180,
        train_split: float = 0.6,
        valid_split: float = 0.2,
        test_split: float = 0.2,
        gates: StrictGates | None = None,
    ):
        """
        Initialize strict learner.

        Args:
            data_window_days: Days of data to use for learning
            train_split: Fraction for training (calibration fitting)
            valid_split: Fraction for validation (hyperparameter selection)
            test_split: Fraction for testing (final evaluation)
            gates: Validation gates (uses defaults if None)
        """
        self.data_window_days = data_window_days
        self.train_split = train_split
        self.valid_split = valid_split
        self.test_split = test_split

        # Ensure splits sum to 1
        total = train_split + valid_split + test_split
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"Splits must sum to 1.0, got {total}")

        self.gates = gates or StrictGates()
        self.generator = RuleParameterGenerator()

        # Storage paths
        self.rules_dir = Path("./data/rules")
        self.learning_dir = Path("./data/learning")
        self.rules_dir.mkdir(parents=True, exist_ok=True)
        self.learning_dir.mkdir(parents=True, exist_ok=True)

    def load_recent_data(self) -> pd.DataFrame:
        """Load recent trading data for learning."""
        logger = get_logger()
        df = logger.load_window(self.data_window_days)

        # Filter to completed trades only
        completed_mask = df["realized_pnl"].notna()
        return df[completed_mask]

    def split_data_chronologically(
        self, df: pd.DataFrame
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Split data chronologically to avoid look-ahead bias.

        Returns:
            Tuple of (train_df, valid_df, test_df)
        """
        if len(df) == 0:
            return df, df, df

        # Sort by timestamp
        df_sorted = df.sort_values("timestamp")

        # Calculate split indices
        train_end = int(len(df_sorted) * self.train_split)
        valid_end = int(len(df_sorted) * (self.train_split + self.valid_split))

        train_df = df_sorted.iloc[:train_end]
        valid_df = df_sorted.iloc[train_end:valid_end]
        test_df = df_sorted.iloc[valid_end:]

        return train_df, valid_df, test_df

    def evaluate_candidate_on_split(
        self, candidate_rules: RuleSet, train_df: pd.DataFrame, valid_df: pd.DataFrame
    ) -> PerformanceMetrics | None:
        """
        Evaluate candidate rules on validation split.

        Args:
            candidate_rules: Rules to evaluate
            train_df: Training data (for calibration)
            valid_df: Validation data (for evaluation)

        Returns:
            Performance metrics if successful, None if failed
        """
        if len(valid_df) == 0:
            return None

        # Build calibrator on training data if we have probabilities
        calibrator = None
        if "predicted_prob" in train_df.columns and len(train_df) >= 50:
            train_probs = train_df["predicted_prob"].dropna().values
            train_outcomes = (train_df["realized_pnl"].dropna() > 0).astype(int).values

            if len(train_probs) >= 50:
                calibrator = ProbabilityCalibrator(method="isotonic")
                calibrator.fit(train_probs, train_outcomes)

        # Apply calibration to validation data if available
        eval_df = valid_df.copy()
        if calibrator and "predicted_prob" in eval_df.columns:
            valid_probs = eval_df["predicted_prob"].fillna(0.5).values
            calibrated_probs = calibrator.predict(valid_probs)
            eval_df["predicted_prob"] = calibrated_probs

        # Calculate metrics
        metrics = evaluate_trading_performance(eval_df, baseline_df=train_df)
        return metrics

    def check_strict_gates(
        self,
        baseline_metrics: PerformanceMetrics,
        candidate_metrics: PerformanceMetrics,
        comparison: dict[str, Any],
        test_df: pd.DataFrame,
    ) -> dict[str, bool]:
        """
        Check all strict gates against test results.

        Returns:
            Dict mapping gate names to pass/fail status
        """
        gates = {}

        # Gate 1: Minimum number of trades
        gates["min_trades"] = candidate_metrics.total_trades >= self.gates.min_trades

        # Gate 2: Sharpe improvement (absolute)
        sharpe_improvement = comparison["sharpe_improvement"]
        gates["sharpe_improvement_abs"] = (
            sharpe_improvement >= self.gates.min_sharpe_improvement_abs
        )

        # Gate 3: Sharpe improvement (relative)
        if baseline_metrics.sharpe_ratio > 0:
            rel_improvement = sharpe_improvement / baseline_metrics.sharpe_ratio
            gates["sharpe_improvement_rel"] = (
                rel_improvement >= self.gates.min_sharpe_improvement_rel
            )
        else:
            gates["sharpe_improvement_rel"] = sharpe_improvement > 0

        # Gate 4: Brier score improvement
        brier_improvement = comparison.get("brier_improvement", 0)
        gates["brier_score_improvement"] = (
            brier_improvement >= self.gates.max_brier_score_improvement
        )

        # Gate 5: Calibration slope in range
        slope = candidate_metrics.calibration_slope
        gates["calibration_slope"] = (
            self.gates.calibration_slope_range[0]
            <= slope
            <= self.gates.calibration_slope_range[1]
        )

        # Gate 6: Max drawdown not significantly worse
        dd_delta_rel = comparison.get("max_drawdown_delta_pct", 0) / 100.0
        gates["max_drawdown"] = (
            dd_delta_rel <= self.gates.max_drawdown_deterioration_rel
        )

        # Gate 7: Hit rate statistical significance
        gates["hit_rate_significance"] = comparison.get(
            "hit_rate_statistically_significant", False
        )

        # Gate 8: Feature stability (PSI)
        max_psi = 0.0
        for feature, psi_score in candidate_metrics.psi_scores.items():
            if not np.isinf(psi_score):
                max_psi = max(max_psi, psi_score)
        gates["feature_stability"] = max_psi <= self.gates.max_psi_threshold

        # Gate 9: Trading frequency cap
        gates["turnover_cap"] = (
            candidate_metrics.avg_daily_turnover <= self.gates.max_daily_turnover_cap
        )

        return gates

    def learn_iteration(self, current_rules: RuleSet) -> LearningResult:
        """
        Run one complete learning iteration.

        Args:
            current_rules: Current rule set to improve upon

        Returns:
            LearningResult with recommendations
        """
        # Load recent data
        df = self.load_recent_data()

        if len(df) < self.gates.min_trades:
            return LearningResult(
                baseline_version=current_rules.version,
                candidate_version="insufficient_data",
                passed_gates=False,
                gate_results={},
                baseline_metrics=PerformanceMetrics(
                    total_trades=len(df),
                    win_rate=0,
                    avg_pnl_per_trade=0,
                    total_pnl=0,
                    expectancy_after_costs=0,
                    sharpe_ratio=0,
                    sortino_ratio=0,
                    max_drawdown=0,
                    max_drawdown_duration=0,
                    calmar_ratio=0,
                    brier_score=1.0,
                    calibration_slope=1.0,
                    calibration_intercept=0.0,
                    reliability_diagram={},
                    avg_daily_turnover=0,
                    avg_holding_period=0,
                    hit_rate_confidence_interval=(0, 0),
                    expectancy_confidence_interval=(0, 0),
                    psi_scores={},
                ),
                candidate_metrics=PerformanceMetrics(
                    total_trades=0,
                    win_rate=0,
                    avg_pnl_per_trade=0,
                    total_pnl=0,
                    expectancy_after_costs=0,
                    sharpe_ratio=0,
                    sortino_ratio=0,
                    max_drawdown=0,
                    max_drawdown_duration=0,
                    calmar_ratio=0,
                    brier_score=1.0,
                    calibration_slope=1.0,
                    calibration_intercept=0.0,
                    reliability_diagram={},
                    avg_daily_turnover=0,
                    avg_holding_period=0,
                    hit_rate_confidence_interval=(0, 0),
                    expectancy_confidence_interval=(0, 0),
                    psi_scores={},
                ),
                comparison={},
                recommendation="Insufficient data for learning. Need at least {self.gates.min_trades} completed trades.",
                timestamp=time.time(),
            )

        # Split data chronologically
        train_df, valid_df, test_df = self.split_data_chronologically(df)

        # Evaluate baseline on test set
        baseline_metrics = evaluate_trading_performance(test_df, baseline_df=train_df)

        # Generate candidates
        candidates = self.generator.generate_candidates(current_rules)

        # Evaluate candidates on validation set
        best_candidate = None
        best_metrics = None
        best_objective = float("-inf")

        for candidate in candidates:
            metrics = self.evaluate_candidate_on_split(candidate, train_df, valid_df)
            if metrics is None:
                continue

            # Objective: expectancy with drawdown penalty
            objective = metrics.expectancy_after_costs - 0.1 * metrics.max_drawdown

            # Apply hard constraints
            if (
                metrics.total_trades >= 50  # Minimum trades in validation
                and metrics.avg_daily_turnover <= self.gates.max_daily_turnover_cap
            ):
                if objective > best_objective:
                    best_objective = objective
                    best_candidate = candidate
                    best_metrics = metrics

        # If no valid candidate found
        if best_candidate is None:
            return LearningResult(
                baseline_version=current_rules.version,
                candidate_version="no_valid_candidates",
                passed_gates=False,
                gate_results={},
                baseline_metrics=baseline_metrics,
                candidate_metrics=baseline_metrics,
                comparison={},
                recommendation="No candidates passed validation constraints.",
                timestamp=time.time(),
            )

        # Evaluate best candidate on test set
        candidate_test_metrics = evaluate_trading_performance(
            test_df, baseline_df=train_df
        )

        # Compare results
        comparison = compare_runs(baseline_metrics, candidate_test_metrics)

        # Check strict gates
        gate_results = self.check_strict_gates(
            baseline_metrics, candidate_test_metrics, comparison, test_df
        )

        passed_gates = all(gate_results.values())

        # Generate recommendation
        if passed_gates:
            recommendation = f"PROMOTE: Candidate {best_candidate.version} passed all gates. Ready for production."
        else:
            failed_gates = [gate for gate, passed in gate_results.items() if not passed]
            recommendation = f"REJECT: Failed gates: {', '.join(failed_gates)}"

        return LearningResult(
            baseline_version=current_rules.version,
            candidate_version=best_candidate.version,
            passed_gates=passed_gates,
            gate_results=gate_results,
            baseline_metrics=baseline_metrics,
            candidate_metrics=candidate_test_metrics,
            comparison=comparison,
            recommendation=recommendation,
            timestamp=time.time(),
        )

    def save_rule_set(self, rules: RuleSet) -> bool:
        """Save rule set to disk."""
        try:
            filepath = self.rules_dir / f"{rules.version}.json"
            with open(filepath, "w") as f:
                json.dump(rules.to_dict(), f, indent=2)
            return True
        except Exception as e:
            print(f"Failed to save rule set: {e}")
            return False

    def load_rule_set(self, version: str) -> RuleSet | None:
        """Load rule set from disk."""
        try:
            filepath = self.rules_dir / f"{version}.json"
            with open(filepath) as f:
                data = json.load(f)
            return RuleSet.from_dict(data)
        except Exception as e:
            print(f"Failed to load rule set: {e}")
            return None

    def save_learning_result(self, result: LearningResult) -> bool:
        """Save learning result to disk."""
        try:
            timestamp_str = datetime.fromtimestamp(result.timestamp).strftime(
                "%Y%m%d_%H%M%S"
            )
            filepath = (
                self.learning_dir
                / f"learning_{timestamp_str}_{result.candidate_version}.json"
            )

            with open(filepath, "w") as f:
                json.dump(result.to_dict(), f, indent=2)
            return True
        except Exception as e:
            print(f"Failed to save learning result: {e}")
            return False


def create_default_rule_set() -> RuleSet:
    """Create a default rule set for testing."""
    parameters = {
        "rsi_oversold": RuleParameter(
            name="rsi_oversold",
            current_value=30.0,
            param_type="float",
            min_value=15.0,
            max_value=45.0,
            step_size=2.0,
            category="signal",
        ),
        "rsi_overbought": RuleParameter(
            name="rsi_overbought",
            current_value=70.0,
            param_type="float",
            min_value=55.0,
            max_value=85.0,
            step_size=2.0,
            category="signal",
        ),
        "atr_stop_multiplier": RuleParameter(
            name="atr_stop_multiplier",
            current_value=2.0,
            param_type="float",
            min_value=1.0,
            max_value=4.0,
            step_size=0.2,
            category="risk",
        ),
        "regime_strength_threshold": RuleParameter(
            name="regime_strength_threshold",
            current_value=0.6,
            param_type="float",
            min_value=0.3,
            max_value=0.9,
            step_size=0.05,
            category="regime",
        ),
    }

    return RuleSet(
        version="v1.0_default",
        parameters=parameters,
        creation_timestamp=time.time(),
        description="Default rule set for Ziggy AI",
    )


if __name__ == "__main__":
    # Example usage

    # Create default rules
    default_rules = create_default_rule_set()

    # Initialize learner
    learner = StrictLearner(data_window_days=90)

    # Save default rules
    learner.save_rule_set(default_rules)

    # Run learning iteration
    result = learner.learn_iteration(default_rules)

    print(f"Learning Result: {result.recommendation}")
    print(f"Passed gates: {result.passed_gates}")
    print(f"Gate results: {result.gate_results}")

    # Save result
    learner.save_learning_result(result)
