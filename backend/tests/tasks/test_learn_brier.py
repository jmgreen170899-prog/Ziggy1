"""
Tests for Learning System functionality in ZiggyAI Memory & Knowledge System

Tests Brier score computation, drift detection, feature family analysis,
and nightly learning job execution.
"""

import os
import shutil
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch


# Set test environment
os.environ["LEARN_REPORT_PATH"] = "test_learn_report.json"
os.environ["DRIFT_THRESHOLD"] = "0.02"

from app.tasks.learn import (
    analyze_feature_importance_drift,
    brier_score,
    compute_brier_by_family,
    compute_drift_flags,
    generate_learn_report,
    load_latest_report,
    reliability_diagram,
    run_nightly_learning_job,
    save_learn_report,
    suggest_feature_weights,
)


class TestBrierScore:
    """Test cases for Brier score computation."""

    def test_brier_score_perfect_predictions(self):
        """Test Brier score with perfect predictions."""
        y_prob = [1.0, 1.0, 0.0, 0.0]
        y_true = [1, 1, 0, 0]

        score = brier_score(y_prob, y_true)
        assert abs(score - 0.0) < 1e-6  # Perfect score = 0

    def test_brier_score_worst_predictions(self):
        """Test Brier score with worst possible predictions."""
        y_prob = [0.0, 0.0, 1.0, 1.0]
        y_true = [1, 1, 0, 0]

        score = brier_score(y_prob, y_true)
        assert abs(score - 1.0) < 1e-6  # Worst score = 1

    def test_brier_score_random_predictions(self):
        """Test Brier score with random predictions (0.5)."""
        y_prob = [0.5, 0.5, 0.5, 0.5]
        y_true = [1, 0, 1, 0]

        score = brier_score(y_prob, y_true)
        assert abs(score - 0.25) < 1e-6  # Random score = 0.25

    def test_brier_score_mixed_quality(self):
        """Test Brier score with mixed quality predictions."""
        y_prob = [0.8, 0.6, 0.3, 0.1]
        y_true = [1, 1, 0, 0]

        # (0.8-1)^2 + (0.6-1)^2 + (0.3-0)^2 + (0.1-0)^2 = 0.04 + 0.16 + 0.09 + 0.01 = 0.3
        expected = (0.04 + 0.16 + 0.09 + 0.01) / 4
        score = brier_score(y_prob, y_true)

        assert abs(score - expected) < 1e-6

    def test_brier_score_empty_data(self):
        """Test Brier score with empty data."""
        score = brier_score([], [])
        assert score == 1.0  # Returns worst possible score for empty data


class TestReliabilityDiagram:
    """Test cases for reliability diagram computation."""

    def test_reliability_diagram_basic(self):
        """Test basic reliability diagram computation."""
        y_prob = [0.1, 0.3, 0.5, 0.7, 0.9]
        y_true = [0, 0, 1, 1, 1]

        diagram = reliability_diagram(y_prob, y_true, n_bins=5)

        assert "bin_centers" in diagram
        assert "mean_predicted" in diagram
        assert "mean_observed" in diagram
        assert "counts" in diagram

        # Should have <= number of bins requested (empty bins omitted)
        assert len(diagram["bin_centers"]) <= 5

    def test_reliability_diagram_empty_data(self):
        """Test reliability diagram with empty data."""
        diagram = reliability_diagram([], [], n_bins=10)

        assert diagram["bin_centers"] == []
        assert diagram["mean_predicted"] == []
        assert diagram["mean_observed"] == []
        assert diagram["counts"] == []

    def test_reliability_diagram_single_bin(self):
        """Test reliability diagram when all predictions fall in one bin."""
        y_prob = [0.48, 0.49, 0.50, 0.51, 0.52]
        y_true = [0, 1, 0, 1, 1]

        diagram = reliability_diagram(y_prob, y_true, n_bins=10)

        # Should have exactly one non-empty bin
        assert len(diagram["bin_centers"]) == 1
        assert len(diagram["counts"]) == 1
        assert diagram["counts"][0] == 5


class TestFeatureFamilyAnalysis:
    """Test cases for feature family analysis."""

    def test_compute_brier_by_family_basic(self):
        """Test basic feature family Brier score computation."""
        events = [
            {
                "p_up": 0.8,
                "outcome": {"label": 1},
                "explain": {"shap_top": [["rsi", 0.3], ["momentum", 0.2]]},  # momentum family
            },
            {
                "p_up": 0.3,
                "outcome": {"label": 0},
                "explain": {"shap_top": [["vix", 0.4], ["put_call", 0.2]]},  # sentiment family
            },
            {
                "p_up": 0.7,
                "outcome": {"label": 1},
                "explain": {"shap_top": [["breadth", 0.5], ["advance", 0.3]]},  # breadth family
            },
        ]

        family_scores = compute_brier_by_family(events)

        # Should have entries for detected families
        assert len(family_scores) > 0

        # All scores should be between 0 and 1
        for score in family_scores.values():
            assert 0 <= score <= 1

    def test_compute_brier_by_family_mixed_features(self):
        """Test feature family computation with mixed features."""
        events = [
            {
                "p_up": 0.6,
                "outcome": {"label": 1},
                "explain": {"shap_top": [["rsi", 0.2], ["vix", 0.2], ["breadth", 0.2]]},  # Mixed
            }
        ]

        family_scores = compute_brier_by_family(events)

        # Should handle mixed features appropriately
        assert isinstance(family_scores, dict)

    def test_compute_brier_by_family_unknown_features(self):
        """Test feature family computation with unknown features."""
        events = [
            {
                "p_up": 0.6,
                "outcome": {"label": 1},
                "explain": {"shap_top": [["unknown_feature_xyz", 0.5]]},
            }
        ]

        family_scores = compute_brier_by_family(events)

        # Should categorize unknown features appropriately
        assert "other" in family_scores or "unknown" in family_scores or "mixed" in family_scores

    def test_compute_brier_by_family_no_explanation(self):
        """Test feature family computation with missing explanations."""
        events = [
            {
                "p_up": 0.6,
                "outcome": {"label": 1},
                # No explain field
            },
            {"p_up": 0.4, "outcome": {"label": 0}, "explain": {}},  # Empty explain
        ]

        family_scores = compute_brier_by_family(events)

        # Should handle missing explanations gracefully
        assert "unknown" in family_scores or len(family_scores) == 0

    def test_compute_brier_by_family_missing_data(self):
        """Test feature family computation with missing outcome data."""
        events = [
            {
                "p_up": 0.6,
                # No outcome
                "explain": {"shap_top": [["rsi", 0.3]]},
            },
            {
                # No p_up
                "outcome": {"label": 1},
                "explain": {"shap_top": [["vix", 0.4]]},
            },
            {
                "p_up": 0.7,
                "outcome": {},  # Empty outcome
                "explain": {"shap_top": [["momentum", 0.2]]},
            },
        ]

        family_scores = compute_brier_by_family(events)

        # Should skip events with missing data
        assert isinstance(family_scores, dict)


class TestDriftDetection:
    """Test cases for drift detection."""

    def test_compute_drift_flags_no_drift(self):
        """Test drift detection with no significant drift."""
        current_scores = {"momentum": 0.25, "sentiment": 0.30, "breadth": 0.22}
        previous_scores = {"momentum": 0.24, "sentiment": 0.31, "breadth": 0.21}

        drift_flags = compute_drift_flags(current_scores, previous_scores, threshold=0.02)

        # No family should be flagged for drift
        assert not any(drift_flags.values())

    def test_compute_drift_flags_with_drift(self):
        """Test drift detection with significant drift."""
        current_scores = {"momentum": 0.30, "sentiment": 0.25, "breadth": 0.35}
        previous_scores = {"momentum": 0.25, "sentiment": 0.24, "breadth": 0.30}

        drift_flags = compute_drift_flags(current_scores, previous_scores, threshold=0.02)

        # momentum and breadth should be flagged (increases > 0.02)
        assert drift_flags["momentum"] is True  # 0.30 - 0.25 = 0.05 > 0.02
        assert drift_flags["sentiment"] is False  # 0.25 - 0.24 = 0.01 < 0.02
        assert drift_flags["breadth"] is True  # 0.35 - 0.30 = 0.05 > 0.02

    def test_compute_drift_flags_new_families(self):
        """Test drift detection with new feature families."""
        current_scores = {"momentum": 0.25, "sentiment": 0.30, "new_family": 0.28}
        previous_scores = {"momentum": 0.24, "sentiment": 0.31}

        drift_flags = compute_drift_flags(current_scores, previous_scores, threshold=0.02)

        # New family should not be flagged as drift
        assert drift_flags["new_family"] is False

    def test_compute_drift_flags_missing_families(self):
        """Test drift detection when some families are missing from current."""
        current_scores = {"momentum": 0.25}
        previous_scores = {"momentum": 0.24, "sentiment": 0.31}

        drift_flags = compute_drift_flags(current_scores, previous_scores, threshold=0.02)

        # Only families in current_scores should be in drift_flags
        assert "momentum" in drift_flags
        assert "sentiment" not in drift_flags


class TestFeatureImportanceAnalysis:
    """Test cases for feature importance drift analysis."""

    def test_analyze_feature_importance_drift_basic(self):
        """Test basic feature importance drift analysis."""
        recent_events = [
            {
                "ts": (datetime.utcnow() - timedelta(days=10)).isoformat(),
                "explain": {"shap_top": [["momentum", 0.3], ["sentiment", 0.2]]},
            },
            {
                "ts": (datetime.utcnow() - timedelta(days=40)).isoformat(),
                "explain": {"shap_top": [["momentum", 0.1], ["sentiment", 0.4]]},
            },
        ]

        analysis = analyze_feature_importance_drift(recent_events, window_days=30)

        assert analysis["status"] == "success"
        assert "top_changes" in analysis
        assert analysis["window_days"] == 30

    def test_analyze_feature_importance_drift_no_data(self):
        """Test feature importance drift analysis with no data."""
        analysis = analyze_feature_importance_drift([], window_days=30)

        assert analysis["status"] == "no_data"

    def test_analyze_feature_importance_drift_significant_changes(self):
        """Test detection of significant feature importance changes."""
        recent_events = [
            # Current period: momentum high, sentiment low
            {
                "ts": (datetime.utcnow() - timedelta(days=10)).isoformat(),
                "explain": {"shap_top": [["momentum", 0.5], ["sentiment", 0.1]]},
            },
            {
                "ts": (datetime.utcnow() - timedelta(days=15)).isoformat(),
                "explain": {"shap_top": [["momentum", 0.4], ["sentiment", 0.1]]},
            },
            # Previous period: momentum low, sentiment high
            {
                "ts": (datetime.utcnow() - timedelta(days=40)).isoformat(),
                "explain": {"shap_top": [["momentum", 0.1], ["sentiment", 0.5]]},
            },
            {
                "ts": (datetime.utcnow() - timedelta(days=45)).isoformat(),
                "explain": {"shap_top": [["momentum", 0.1], ["sentiment", 0.4]]},
            },
        ]

        analysis = analyze_feature_importance_drift(recent_events, window_days=30)

        assert analysis["status"] == "success"
        assert len(analysis["top_changes"]) > 0

        # Should detect significant changes in momentum and sentiment
        changes_dict = {feature: data for feature, data in analysis["top_changes"]}

        if "momentum" in changes_dict:
            momentum_change = changes_dict["momentum"]["change_pct"]
            assert momentum_change > 0  # Should have increased

        if "sentiment" in changes_dict:
            sentiment_change = changes_dict["sentiment"]["change_pct"]
            assert sentiment_change < 0  # Should have decreased


class TestLearningReport:
    """Test cases for learning report generation."""

    def setup_method(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.test_report_path = os.path.join(self.test_dir, "test_learn_report.json")
        os.environ["LEARN_REPORT_PATH"] = self.test_report_path

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch("app.tasks.learn.iter_events")
    def test_generate_learn_report_basic(self, mock_iter_events):
        """Test basic learning report generation."""
        mock_events = [
            {
                "ts": (datetime.utcnow() - timedelta(days=5)).isoformat(),
                "ticker": "AAPL",
                "p_up": 0.8,
                "outcome": {"label": 1, "pnl": 0.05},
                "explain": {"shap_top": [["momentum", 0.3]]},
            },
            {
                "ts": (datetime.utcnow() - timedelta(days=10)).isoformat(),
                "ticker": "TSLA",
                "p_up": 0.3,
                "outcome": {"label": 0, "pnl": -0.02},
                "explain": {"shap_top": [["sentiment", 0.4]]},
            },
        ]

        mock_iter_events.return_value = mock_events

        report = generate_learn_report(lookback_days=30)

        assert report["status"] == "success"
        assert report["lookback_days"] == 30
        assert report["total_events"] == 2
        assert "overall_brier" in report
        assert "brier_scores" in report
        assert "recommendations" in report

    @patch("app.tasks.learn.iter_events")
    def test_generate_learn_report_no_data(self, mock_iter_events):
        """Test learning report generation with no data."""
        mock_iter_events.return_value = []

        report = generate_learn_report(lookback_days=30)

        assert report["status"] == "no_data"
        assert report["lookback_days"] == 30

    @patch("app.tasks.learn.iter_events")
    def test_generate_learn_report_with_drift(self, mock_iter_events):
        """Test learning report generation with detected drift."""
        mock_events = [
            {
                "ts": (datetime.utcnow() - timedelta(days=5)).isoformat(),
                "ticker": "AAPL",
                "p_up": 0.8,
                "outcome": {"label": 0},  # Wrong prediction
                "explain": {"shap_top": [["momentum", 0.5]]},
            }
        ]

        mock_iter_events.return_value = mock_events

        # Mock previous report with better scores
        previous_report = {"brier_scores": {"momentum": 0.20}}  # Was better before

        with patch("app.tasks.learn.load_latest_report", return_value=previous_report):
            report = generate_learn_report(lookback_days=30)

        # Should detect drift and generate recommendations
        assert "drift_flags" in report
        assert "recommendations" in report

    def test_save_and_load_report(self):
        """Test saving and loading of learning reports."""
        test_report = {
            "status": "success",
            "generated_at": datetime.utcnow().isoformat(),
            "total_events": 10,
            "overall_brier": 0.25,
            "brier_scores": {"momentum": 0.22, "sentiment": 0.28},
        }

        success = save_learn_report(test_report)
        assert success is True
        assert os.path.exists(self.test_report_path)

        loaded_report = load_latest_report()
        assert loaded_report is not None
        assert loaded_report["status"] == "success"
        assert loaded_report["total_events"] == 10
        assert loaded_report["overall_brier"] == 0.25

    def test_save_report_invalid_path(self):
        """Test saving report to invalid path."""
        os.environ["LEARN_REPORT_PATH"] = "/invalid/path/report.json"

        test_report = {"status": "test"}
        success = save_learn_report(test_report)

        # Should handle error gracefully
        assert success is False


class TestNightlyLearningJob:
    """Test cases for nightly learning job."""

    def setup_method(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.test_report_path = os.path.join(self.test_dir, "test_learn_report.json")
        os.environ["LEARN_REPORT_PATH"] = self.test_report_path

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch("app.tasks.learn.generate_learn_report")
    @patch("app.tasks.learn.save_learn_report")
    def test_run_nightly_learning_job_success(self, mock_save, mock_generate):
        """Test successful nightly learning job execution."""
        mock_report = {
            "status": "success",
            "total_events": 50,
            "drift_flags": {"momentum": True, "sentiment": False},
            "recommendations": [{"type": "drift_alert", "family": "momentum"}],
        }

        mock_generate.return_value = mock_report
        mock_save.return_value = True

        job_result = run_nightly_learning_job()

        assert job_result["status"] == "success"
        assert job_result["events_analyzed"] == 50
        assert job_result["drift_alerts"] == 1
        assert job_result["recommendations"] == 1
        assert job_result["report_saved"] is True

    @patch("app.tasks.learn.generate_learn_report")
    def test_run_nightly_learning_job_failure(self, mock_generate):
        """Test nightly learning job failure handling."""
        mock_generate.side_effect = Exception("Database connection failed")

        job_result = run_nightly_learning_job()

        assert job_result["status"] == "error"
        assert "error" in job_result
        assert "Database connection failed" in job_result["error"]


class TestFeatureWeightSuggestions:
    """Test cases for feature weight suggestions."""

    def test_suggest_feature_weights_basic(self):
        """Test basic feature weight suggestions."""
        report = {
            "brier_scores": {
                "momentum": 0.20,  # Good performance
                "sentiment": 0.35,  # Poor performance
                "breadth": 0.25,  # Average performance
            }
        }

        weights = suggest_feature_weights(report)

        # Lower Brier score should get higher weight
        assert weights["momentum"] > weights["sentiment"]
        assert weights["momentum"] > weights["breadth"]
        assert weights["breadth"] > weights["sentiment"]

        # All weights should be between 0 and 1
        for weight in weights.values():
            assert 0 <= weight <= 1

    def test_suggest_feature_weights_empty_scores(self):
        """Test feature weight suggestions with empty scores."""
        report = {"brier_scores": {}}

        weights = suggest_feature_weights(report)

        assert weights == {}

    def test_suggest_feature_weights_single_family(self):
        """Test feature weight suggestions with single family."""
        report = {"brier_scores": {"momentum": 0.25}}

        weights = suggest_feature_weights(report)

        assert len(weights) == 1
        assert "momentum" in weights
        assert weights["momentum"] == 0.0  # Single family gets relative weight 0


# Integration tests
class TestLearningIntegration:
    """Integration tests for learning system."""

    def test_end_to_end_learning_workflow(self):
        """Test complete learning workflow."""
        test_events = [
            {
                "ts": (datetime.utcnow() - timedelta(days=i)).isoformat(),
                "ticker": f"STOCK{i % 3}",
                "p_up": 0.5 + (i % 10) * 0.05,
                "outcome": {"label": i % 2},
                "explain": {"shap_top": [["momentum", 0.3], ["sentiment", 0.2]]},
            }
            for i in range(20)
        ]

        with patch("app.tasks.learn.iter_events", return_value=test_events):
            report = generate_learn_report()

            assert report["status"] == "success"
            assert report["total_events"] > 0

            assert "brier_scores" in report
            assert len(report["brier_scores"]) > 0

            weights = suggest_feature_weights(report)
            assert isinstance(weights, dict)

    def test_learning_system_performance(self):
        """Test learning system performance with large datasets."""
        import time

        large_events = []
        for i in range(1000):
            large_events.append(
                {
                    "ts": (datetime.utcnow() - timedelta(days=i % 365)).isoformat(),
                    "ticker": f"STOCK{i % 50}",
                    "p_up": 0.5 + (i % 100) * 0.005,
                    "outcome": {"label": i % 2},
                    "explain": {"shap_top": [[f"feature_{j}", 0.1 + j * 0.05] for j in range(5)]},
                }
            )

        with patch("app.tasks.learn.iter_events", return_value=large_events):
            start_time = time.time()

            report = generate_learn_report()

            end_time = time.time()
            processing_time = end_time - start_time

            # Should complete within reasonable time (< 5 seconds)
            assert processing_time < 5.0
            assert report["status"] == "success"
            assert report["total_events"] == 1000
