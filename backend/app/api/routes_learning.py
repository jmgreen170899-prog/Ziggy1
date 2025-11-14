# backend/app/api/routes_learning.py
"""
API endpoints for Ziggy's strict learning and adaptation system.
Provides full transparency and control over rule optimization.
"""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.data_log import get_logger
from app.services.evaluation import evaluate_trading_performance
from app.services.learner import (
    StrictLearner,
    create_default_rule_set,
)


router = APIRouter()

# Global learner instance
_learner: StrictLearner | None = None


def get_learner() -> StrictLearner:
    """Get global learner instance."""
    global _learner
    if _learner is None:
        _learner = StrictLearner()
    return _learner


# Pydantic models for API
class RuleParameterModel(BaseModel):
    name: str
    current_value: Any
    param_type: str
    min_value: float | None = None
    max_value: float | None = None
    step_size: float | None = None
    category: str = "general"


class RuleSetModel(BaseModel):
    version: str
    parameters: dict[str, RuleParameterModel]
    creation_timestamp: float
    description: str = ""
    parent_version: str | None = None


class StrictGatesModel(BaseModel):
    min_trades: int = 200
    min_sharpe_improvement_abs: float = 0.20
    min_sharpe_improvement_rel: float = 0.15
    max_brier_score_improvement: float = 0.02
    calibration_slope_range: tuple[float, float] = (0.8, 1.2)
    max_drawdown_deterioration_rel: float = 0.10
    hit_rate_significance_p: float = 0.05
    max_psi_threshold: float = 0.25
    max_daily_turnover_cap: float = 50.0


class LearningConfigModel(BaseModel):
    data_window_days: int = 180
    train_split: float = 0.6
    valid_split: float = 0.2
    test_split: float = 0.2
    gates: StrictGatesModel = Field(default_factory=StrictGatesModel)


# API Endpoints


@router.get("/status", response_model=None)
def get_learning_status():
    """Get current learning system status."""
    logger = get_logger()
    learner = get_learner()

    # Get recent data stats
    recent_data = logger.load_window(30)
    data_stats = logger.get_summary_stats(30)

    # Check if we have enough data for learning
    completed_trades = (recent_data["realized_pnl"].notna()).sum() if not recent_data.empty else 0

    return {
        "system_ready": completed_trades >= learner.gates.min_trades,
        "recent_data": {
            "total_decisions": len(recent_data),
            "completed_trades": completed_trades,
            "data_window_days": 30,
            "last_decision": recent_data["timestamp"].max() if not recent_data.empty else None,
        },
        "learning_config": {
            "data_window_days": learner.data_window_days,
            "train_split": learner.train_split,
            "valid_split": learner.valid_split,
            "test_split": learner.test_split,
        },
        "gates": learner.gates.to_dict(),
        "asof": time.time(),
    }


@router.get("/data/summary", response_model=None)
def get_learning_data_summary(days: int = Query(90, ge=7, le=365)):
    """Get summary of available learning data."""
    logger = get_logger()
    df = logger.load_window(days)

    if df.empty:
        return {
            "total_records": 0,
            "completed_trades": 0,
            "date_range": None,
            "symbols": [],
            "regimes": [],
            "signal_types": [],
            "message": "No data available",
        }

    completed_mask = df["realized_pnl"].notna()
    completed_df = df[completed_mask]

    summary = {
        "total_records": len(df),
        "completed_trades": len(completed_df),
        "date_range": {
            "start": df["timestamp"].min(),
            "end": df["timestamp"].max(),
            "days": (df["timestamp"].max() - df["timestamp"].min()) / 86400,
        },
        "symbols": df["ticker"].unique().tolist() if "ticker" in df.columns else [],
        "regimes": df["regime"].unique().tolist() if "regime" in df.columns else [],
        "signal_types": df["signal_name"].unique().tolist() if "signal_name" in df.columns else [],
    }

    if len(completed_df) > 0:
        summary["performance"] = {
            "total_pnl": completed_df["realized_pnl"].sum(),
            "avg_pnl_per_trade": completed_df["realized_pnl"].mean(),
            "win_rate": (completed_df["realized_pnl"] > 0).mean(),
            "trades_per_day": len(completed_df) / max(summary["date_range"]["days"], 1),
        }

    return summary


@router.get("/rules/current", response_model=None)
def get_current_rules():
    """Get the currently active rule set."""
    learner = get_learner()

    # Try to load the latest rule set
    # For now, return default rules
    default_rules = create_default_rule_set()

    return {
        "version": default_rules.version,
        "parameters": {
            name: {
                "name": param.name,
                "current_value": param.current_value,
                "param_type": param.param_type,
                "min_value": param.min_value,
                "max_value": param.max_value,
                "step_size": param.step_size,
                "category": param.category,
            }
            for name, param in default_rules.parameters.items()
        },
        "creation_timestamp": default_rules.creation_timestamp,
        "description": default_rules.description,
        "parent_version": default_rules.parent_version,
    }


@router.get("/rules/history", response_model=None)
def get_rules_history():
    """Get history of all rule versions."""
    learner = get_learner()

    # List all rule files
    rule_files = list(learner.rules_dir.glob("*.json"))

    history = []
    for rule_file in sorted(rule_files, key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            rule_set = learner.load_rule_set(rule_file.stem)
            if rule_set:
                history.append(
                    {
                        "version": rule_set.version,
                        "creation_timestamp": rule_set.creation_timestamp,
                        "description": rule_set.description,
                        "parent_version": rule_set.parent_version,
                        "num_parameters": len(rule_set.parameters),
                    }
                )
        except Exception:
            continue

    return {"rules": history, "total_versions": len(history)}


@router.post("/run", response_model=None)
def run_learning_iteration(background_tasks: BackgroundTasks):
    """Run a single learning iteration."""
    learner = get_learner()

    # Get current rules
    current_rules = create_default_rule_set()  # TODO: Load actual current rules

    def run_learning():
        """Background task to run learning."""
        try:
            result = learner.learn_iteration(current_rules)
            learner.save_learning_result(result)
        except Exception as e:
            print(f"Learning iteration failed: {e}")

    background_tasks.add_task(run_learning)

    return {
        "message": "Learning iteration started",
        "baseline_version": current_rules.version,
        "timestamp": time.time(),
    }


@router.get("/results/latest", response_model=None)
def get_latest_learning_result():
    """Get the most recent learning result."""
    learner = get_learner()

    # Find latest learning result file
    result_files = list(learner.learning_dir.glob("learning_*.json"))

    if not result_files:
        raise HTTPException(status_code=404, detail="No learning results found")

    latest_file = max(result_files, key=lambda x: x.stat().st_mtime)

    try:
        import json

        with open(latest_file) as f:
            result_data = json.load(f)

        return result_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load learning result: {e}")


@router.get("/results/history", response_model=None)
def get_learning_history(limit: int = Query(20, ge=1, le=100)):
    """Get history of learning results."""
    learner = get_learner()

    result_files = list(learner.learning_dir.glob("learning_*.json"))
    result_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    results = []
    for result_file in result_files[:limit]:
        try:
            import json

            with open(result_file) as f:
                result_data = json.load(f)

            # Return summary info only
            results.append(
                {
                    "timestamp": result_data.get("timestamp"),
                    "baseline_version": result_data.get("baseline_version"),
                    "candidate_version": result_data.get("candidate_version"),
                    "passed_gates": result_data.get("passed_gates"),
                    "recommendation": result_data.get("recommendation"),
                    "gate_results": result_data.get("gate_results", {}),
                    "filename": result_file.name,
                }
            )
        except Exception:
            continue

    return {"results": results, "total_found": len(result_files)}


@router.get("/evaluate/current", response_model=None)
def evaluate_current_performance(days: int = Query(30, ge=7, le=180)):
    """Evaluate current rule performance."""
    logger = get_logger()
    df = logger.load_window(days)

    if df.empty:
        raise HTTPException(status_code=404, detail="No data available for evaluation")

    # Evaluate performance
    metrics = evaluate_trading_performance(df)

    return {
        "evaluation_period_days": days,
        "data_points": len(df),
        "metrics": metrics.to_dict(),
        "timestamp": time.time(),
    }


@router.get("/gates", response_model=None)
def get_learning_gates():
    """Get current validation gates configuration."""
    learner = get_learner()
    return learner.gates.to_dict()


@router.put("/gates", response_model=None)
def update_learning_gates(gates: StrictGatesModel):
    """Update validation gates configuration."""
    learner = get_learner()

    # Update gates
    learner.gates.min_trades = gates.min_trades
    learner.gates.min_sharpe_improvement_abs = gates.min_sharpe_improvement_abs
    learner.gates.min_sharpe_improvement_rel = gates.min_sharpe_improvement_rel
    learner.gates.max_brier_score_improvement = gates.max_brier_score_improvement
    learner.gates.calibration_slope_range = gates.calibration_slope_range
    learner.gates.max_drawdown_deterioration_rel = gates.max_drawdown_deterioration_rel
    learner.gates.hit_rate_significance_p = gates.hit_rate_significance_p
    learner.gates.max_psi_threshold = gates.max_psi_threshold
    learner.gates.max_daily_turnover_cap = gates.max_daily_turnover_cap

    return {"message": "Gates updated successfully", "gates": learner.gates.to_dict()}


@router.get("/calibration/status", response_model=None)
def get_calibration_status():
    """Get probability calibration status."""
    from pathlib import Path

    calibrator_path = Path("./data/models/calibrator.pkl")

    return {
        "calibrator_exists": calibrator_path.exists(),
        "calibrator_path": str(calibrator_path),
        "last_modified": calibrator_path.stat().st_mtime if calibrator_path.exists() else None,
        "recommendation": (
            "Build calibrator" if not calibrator_path.exists() else "Calibrator ready"
        ),
    }


@router.post("/calibration/build", response_model=None)
def build_calibration_model(
    background_tasks: BackgroundTasks, days: int = Query(90, ge=30, le=365)
):
    """Build probability calibration model from recent data."""

    def build_calibrator():
        """Background task to build calibrator."""
        try:
            from app.services.calibration import build_and_save_calibrator

            logger = get_logger()
            df = logger.load_window(days)

            if len(df) < 100:
                print("Insufficient data for calibration")
                return

            report = build_and_save_calibrator(df, method="isotonic")
            if report:
                print("Calibrator built successfully")
            else:
                print("Failed to build calibrator")

        except Exception as e:
            print(f"Calibrator building failed: {e}")

    background_tasks.add_task(build_calibrator)

    return {
        "message": "Calibrator building started",
        "data_window_days": days,
        "timestamp": time.time(),
    }


@router.get("/health", response_model=None)
def get_learning_health():
    """Get overall health status of the learning system."""
    logger = get_logger()
    learner = get_learner()

    # Check data availability
    recent_data = logger.load_window(7)  # Last week
    completed_trades = (recent_data["realized_pnl"].notna()).sum() if not recent_data.empty else 0

    # Check calibrator
    from pathlib import Path

    calibrator_exists = Path("./data/models/calibrator.pkl").exists()

    # Check recent learning activity
    result_files = list(learner.learning_dir.glob("learning_*.json"))
    latest_learning = max([f.stat().st_mtime for f in result_files]) if result_files else 0

    health_score = 0
    issues = []

    # Data health (40 points)
    if completed_trades >= 50:
        health_score += 40
    elif completed_trades >= 20:
        health_score += 20
        issues.append("Low recent trading activity")
    else:
        issues.append("Insufficient recent trading data")

    # Calibration health (30 points)
    if calibrator_exists:
        health_score += 30
    else:
        issues.append("No calibration model available")

    # Learning activity health (30 points)
    if latest_learning > time.time() - 7 * 86400:  # Within last week
        health_score += 30
    elif latest_learning > time.time() - 30 * 86400:  # Within last month
        health_score += 15
        issues.append("No recent learning iterations")
    else:
        issues.append("No learning activity detected")

    status = "healthy" if health_score >= 80 else "warning" if health_score >= 50 else "critical"

    return {
        "status": status,
        "health_score": health_score,
        "issues": issues,
        "recent_trading_activity": {
            "completed_trades_7d": completed_trades,
            "data_points_7d": len(recent_data),
        },
        "calibrator_available": calibrator_exists,
        "latest_learning_activity": latest_learning,
        "timestamp": time.time(),
    }
