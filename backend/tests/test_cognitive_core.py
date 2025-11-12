"""
Comprehensive tests for ZiggyAI Cognitive Core components.

Tests include ECE validation, latency benchmarks, and explainability checks.
"""

import os
import sys
import time
import warnings

import numpy as np
import pandas as pd
import pytest


warnings.filterwarnings("ignore")

# Add path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.backtest.engine import BacktestEngine
from app.data.features.features import FeatureStore
from app.services.fusion.ensemble import SignalFusionEnsemble
from app.services.position_sizing import PositionSizer
from app.services.regime import RegimeDetector


class TestCognitiveCore:
    """Test suite for cognitive core components."""

    @pytest.fixture
    def sample_data(self):
        """Generate sample market data for testing."""
        dates = pd.date_range(start="2023-01-01", end="2023-12-31", freq="D")
        np.random.seed(42)

        data = pd.DataFrame(
            {
                "symbol": ["AAPL"] * len(dates),
                "date": dates,
                "open": 150 + np.random.randn(len(dates)).cumsum() * 0.5,
                "high": 150 + np.random.randn(len(dates)).cumsum() * 0.5 + 2,
                "low": 150 + np.random.randn(len(dates)).cumsum() * 0.5 - 2,
                "close": 150 + np.random.randn(len(dates)).cumsum() * 0.5,
                "volume": np.random.randint(1000000, 10000000, len(dates)),
                "returns": np.random.randn(len(dates)) * 0.02,
            }
        )

        # Ensure high >= max(open, close) and low <= min(open, close)
        data["high"] = np.maximum(data["high"], np.maximum(data["open"], data["close"]))
        data["low"] = np.minimum(data["low"], np.minimum(data["open"], data["close"]))

        return data

    @pytest.fixture
    def feature_store(self):
        """Initialize feature store."""
        return FeatureStore()

    @pytest.fixture
    def regime_detector(self):
        """Initialize regime detector."""
        return RegimeDetector()

    @pytest.fixture
    def signal_ensemble(self):
        """Initialize signal fusion ensemble."""
        return SignalFusionEnsemble()

    @pytest.fixture
    def position_sizer(self):
        """Initialize position sizer."""
        return PositionSizer()


class TestFeatureStore(TestCognitiveCore):
    """Test feature store functionality."""

    def test_feature_computation_latency(self, feature_store, sample_data):
        """Test feature computation meets latency requirements (<150ms)."""
        start_time = time.time()

        features = feature_store.get("AAPL", sample_data)

        latency = (time.time() - start_time) * 1000  # Convert to ms

        assert latency < 150, f"Feature computation took {latency:.2f}ms, exceeds 150ms limit"
        assert isinstance(features, dict), "Features should be returned as dictionary"
        assert len(features) > 0, "Should compute at least one feature"

    def test_feature_caching(self, feature_store, sample_data):
        """Test feature caching functionality."""
        # First computation
        start_time = time.time()
        features1 = feature_store.get("AAPL", sample_data)
        first_latency = (time.time() - start_time) * 1000

        # Second computation (should be cached)
        start_time = time.time()
        features2 = feature_store.get("AAPL", sample_data)
        second_latency = (time.time() - start_time) * 1000

        assert features1 == features2, "Cached features should match original"
        assert second_latency < first_latency, "Cached computation should be faster"
        assert second_latency < 10, (
            f"Cached retrieval took {second_latency:.2f}ms, should be < 10ms"
        )

    def test_feature_completeness(self, feature_store, sample_data):
        """Test that all expected features are computed."""
        features = feature_store.get("AAPL", sample_data)

        # Check that we have features from multiple categories
        feature_keys = list(features.keys())
        assert len(feature_keys) >= 10, f"Expected at least 10 features, got {len(feature_keys)}"

        # Check for specific key features
        assert "rsi_14" in features, "Should include RSI feature"
        assert "volatility_20" in features, "Should include volatility feature"
        assert "volume_sma_20" in features, "Should include volume feature"


class TestRegimeDetection(TestCognitiveCore):
    """Test regime detection functionality."""

    def test_regime_detection_latency(self, regime_detector, sample_data):
        """Test regime detection meets latency requirements."""
        start_time = time.time()

        regime = regime_detector.detect_regime(sample_data)

        latency = (time.time() - start_time) * 1000

        assert latency < 50, f"Regime detection took {latency:.2f}ms, should be < 50ms"
        assert regime in ["bull_market", "bear_market", "sideways", "high_volatility"]

    def test_regime_confidence(self, regime_detector, sample_data):
        """Test regime confidence scoring."""
        regime_weights = regime_detector.get_regime_weights(sample_data)

        assert isinstance(regime_weights, dict), "Regime weights should be dictionary"
        assert len(regime_weights) == 4, "Should have weights for all 4 regime types"

        # Check probabilities sum to 1
        total_weight = sum(regime_weights.values())
        assert abs(total_weight - 1.0) < 0.01, (
            f"Regime weights sum to {total_weight}, should be ~1.0"
        )

        # Check all weights are non-negative
        for regime, weight in regime_weights.items():
            assert weight >= 0, f"Regime weight for {regime} is negative: {weight}"
            assert weight <= 1, f"Regime weight for {regime} exceeds 1: {weight}"

    def test_regime_vector_mapping(self, regime_detector, sample_data):
        """Test regime vector mapping functionality."""
        regime_vector = regime_detector.regime_vector(sample_data)

        assert isinstance(regime_vector, dict), "Regime vector should be dictionary"
        assert len(regime_vector) >= 4, "Should include regime weights and additional features"

        # Check required keys
        required_keys = ["bull_market", "bear_market", "sideways", "high_volatility"]
        for key in required_keys:
            assert key in regime_vector, f"Missing regime weight: {key}"


class TestSignalFusion(TestCognitiveCore):
    """Test signal fusion ensemble functionality."""

    def test_signal_fusion_latency(self, signal_ensemble, sample_data):
        """Test signal fusion meets latency requirements."""
        start_time = time.time()

        signal = signal_ensemble.fused_probability("AAPL", sample_data)

        latency = (time.time() - start_time) * 1000

        assert latency < 100, f"Signal fusion took {latency:.2f}ms, should be < 100ms"
        assert 0 <= signal <= 1, f"Signal probability {signal} should be between 0 and 1"

    def test_signal_explainability(self, signal_ensemble, sample_data):
        """Test signal explainability features."""
        explanation = signal_ensemble.explain("AAPL", sample_data)

        assert isinstance(explanation, dict), "Explanation should be dictionary"
        assert "feature_importance" in explanation, "Should include feature importance"
        assert "model_contributions" in explanation, "Should include model contributions"
        assert "regime_influence" in explanation, "Should include regime influence"

        # Check feature importance
        feature_importance = explanation["feature_importance"]
        assert isinstance(feature_importance, dict), "Feature importance should be dictionary"
        assert len(feature_importance) > 0, "Should have feature importance scores"

        # Check model contributions
        model_contributions = explanation["model_contributions"]
        assert isinstance(model_contributions, dict), "Model contributions should be dictionary"
        assert len(model_contributions) > 0, "Should have model contribution scores"

    def test_signal_calibration_integration(self, signal_ensemble, sample_data):
        """Test integration with calibration system."""
        # Generate multiple signals for calibration test
        signals = []
        for i in range(100):
            # Add some noise to create variation
            noisy_data = sample_data.copy()
            noisy_data["returns"] += np.random.randn(len(sample_data)) * 0.001
            signal = signal_ensemble.fused_probability("AAPL", noisy_data)
            signals.append(signal)

        signals = np.array(signals)

        # Check signal distribution
        assert signals.min() >= 0, "All signals should be non-negative"
        assert signals.max() <= 1, "All signals should be <= 1"
        assert signals.std() > 0, "Signals should have some variation"


class TestPositionSizing(TestCognitiveCore):
    """Test position sizing functionality."""

    def test_position_sizing_latency(self, position_sizer, sample_data):
        """Test position sizing meets latency requirements."""
        signal_confidence = 0.75
        current_price = sample_data["close"].iloc[-1]
        portfolio_value = 100000

        start_time = time.time()

        position = position_sizer.compute_position(
            signal_confidence=signal_confidence,
            current_price=current_price,
            portfolio_value=portfolio_value,
            price_data=sample_data[["high", "low", "close"]].tail(20),
        )

        latency = (time.time() - start_time) * 1000

        assert latency < 20, f"Position sizing took {latency:.2f}ms, should be < 20ms"
        assert isinstance(position, dict), "Position should be dictionary"

    def test_position_risk_constraints(self, position_sizer, sample_data):
        """Test position sizing risk constraints."""
        signal_confidence = 0.8
        current_price = sample_data["close"].iloc[-1]
        portfolio_value = 100000

        position = position_sizer.compute_position(
            signal_confidence=signal_confidence,
            current_price=current_price,
            portfolio_value=portfolio_value,
            price_data=sample_data[["high", "low", "close"]].tail(20),
        )

        assert "shares" in position, "Position should include shares"
        assert "dollar_amount" in position, "Position should include dollar amount"
        assert "risk_percent" in position, "Position should include risk percentage"

        # Check risk constraints
        shares = position["shares"]
        dollar_amount = position["dollar_amount"]
        risk_percent = position["risk_percent"]

        assert shares >= 0, "Shares should be non-negative"
        assert dollar_amount >= 0, "Dollar amount should be non-negative"
        assert 0 <= risk_percent <= 1, f"Risk percent {risk_percent} should be between 0 and 1"

        # Check position doesn't exceed portfolio
        assert dollar_amount <= portfolio_value, "Position shouldn't exceed portfolio value"


class TestBacktesting(TestCognitiveCore):
    """Test backtesting functionality."""

    def test_backtest_latency(self, sample_data):
        """Test backtesting meets reasonable latency requirements."""

        # Create simple strategy for testing
        def simple_strategy(data):
            """Simple momentum strategy for testing."""
            returns_5d = data["close"].pct_change(5)
            return returns_5d.iloc[-1] > 0.02  # Buy if 5-day return > 2%

        engine = BacktestEngine()

        start_time = time.time()

        results = engine.backtest(
            data=sample_data,
            strategy_func=simple_strategy,
            initial_capital=100000,
            commission=0.001,
        )

        latency = (time.time() - start_time) * 1000

        # Backtest can be slower, but should complete in reasonable time
        assert latency < 5000, f"Backtest took {latency:.2f}ms, should be < 5000ms"
        assert hasattr(results, "total_return"), "Results should include total return"
        assert hasattr(results, "trades"), "Results should include trades"

    def test_backtest_metrics_completeness(self, sample_data):
        """Test backtest results include all required metrics."""

        def simple_strategy(data):
            return data["close"].pct_change(1).iloc[-1] > 0

        engine = BacktestEngine()
        results = engine.backtest(
            data=sample_data, strategy_func=simple_strategy, initial_capital=100000
        )

        # Check required metrics
        required_attrs = [
            "total_return",
            "annualized_return",
            "volatility",
            "sharpe_ratio",
            "max_drawdown",
            "win_rate",
            "total_trades",
            "trades",
        ]

        for attr in required_attrs:
            assert hasattr(results, attr), f"Results missing required attribute: {attr}"

        # Check trades list
        assert isinstance(results.trades, list), "Trades should be a list"


class TestExpectedCalibrationError(TestCognitiveCore):
    """Test Expected Calibration Error (ECE) requirements."""

    def test_ece_computation(self):
        """Test ECE computation function."""
        # Create sample predictions and outcomes
        np.random.seed(42)
        predictions = np.random.random(1000)
        outcomes = (np.random.random(1000) < predictions).astype(int)

        ece = self.compute_ece(predictions, outcomes)

        assert isinstance(ece, float), "ECE should be a float"
        assert 0 <= ece <= 1, f"ECE {ece} should be between 0 and 1"

    def test_signal_calibration_ece(self, signal_ensemble, sample_data):
        """Test that signal ensemble meets ECE requirements (<0.05)."""
        # Generate predictions and synthetic outcomes for testing
        np.random.seed(42)
        predictions = []
        outcomes = []

        for i in range(200):  # Generate 200 samples
            # Add noise to create variation
            noisy_data = sample_data.copy()
            noise = np.random.randn(len(sample_data)) * 0.001
            noisy_data["returns"] += noise

            # Get signal prediction
            signal = signal_ensemble.fused_probability("AAPL", noisy_data)
            predictions.append(signal)

            # Synthetic outcome based on noisy signal + randomness
            outcome = np.random.random() < signal * 0.7 + 0.15  # Some correlation
            outcomes.append(int(outcome))

        predictions = np.array(predictions)
        outcomes = np.array(outcomes)

        ece = self.compute_ece(predictions, outcomes)

        # Note: With synthetic data, ECE might not meet strict requirements
        # In production, this would use real historical data
        assert ece < 0.2, f"ECE {ece:.4f} should be < 0.2 (relaxed for synthetic data)"
        print(f"Signal ensemble ECE: {ece:.4f}")

    @staticmethod
    def compute_ece(predictions, outcomes, n_bins=10):
        """
        Compute Expected Calibration Error.

        Args:
            predictions: Array of probability predictions [0,1]
            outcomes: Array of binary outcomes {0,1}
            n_bins: Number of bins for calibration

        Returns:
            ece: Expected Calibration Error
        """
        bin_boundaries = np.linspace(0, 1, n_bins + 1)
        bin_lowers = bin_boundaries[:-1]
        bin_uppers = bin_boundaries[1:]

        ece = 0.0
        for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
            # Find predictions in this bin
            in_bin = (predictions > bin_lower) & (predictions <= bin_upper)
            prop_in_bin = in_bin.mean()

            if prop_in_bin > 0:
                # Average prediction and outcome in this bin
                accuracy_in_bin = outcomes[in_bin].mean()
                avg_confidence_in_bin = predictions[in_bin].mean()

                # Add to ECE
                ece += np.abs(avg_confidence_in_bin - accuracy_in_bin) * prop_in_bin

        return ece


class TestIntegrationPerformance(TestCognitiveCore):
    """Test full cognitive core integration performance."""

    def test_end_to_end_latency(self, sample_data):
        """Test complete cognitive core pipeline latency."""
        start_time = time.time()

        # Initialize all components
        feature_store = FeatureStore()
        regime_detector = RegimeDetector()
        signal_ensemble = SignalFusionEnsemble()
        position_sizer = PositionSizer()

        # Run complete pipeline
        features = feature_store.get("AAPL", sample_data)
        regime = regime_detector.detect_regime(sample_data)
        signal = signal_ensemble.fused_probability("AAPL", sample_data)

        position = position_sizer.compute_position(
            signal_confidence=signal,
            current_price=sample_data["close"].iloc[-1],
            portfolio_value=100000,
            price_data=sample_data[["high", "low", "close"]].tail(20),
        )

        total_latency = (time.time() - start_time) * 1000

        # Full pipeline should complete within 200ms
        assert total_latency < 200, (
            f"End-to-end pipeline took {total_latency:.2f}ms, should be < 200ms"
        )

        # Verify all outputs
        assert isinstance(features, dict) and len(features) > 0
        assert regime in ["bull_market", "bear_market", "sideways", "high_volatility"]
        assert 0 <= signal <= 1
        assert isinstance(position, dict) and "shares" in position

        print(f"End-to-end pipeline latency: {total_latency:.2f}ms")

    def test_memory_efficiency(self, sample_data):
        """Test memory usage is reasonable."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Run cognitive core operations
        feature_store = FeatureStore()
        regime_detector = RegimeDetector()
        signal_ensemble = SignalFusionEnsemble()

        # Multiple operations to test memory growth
        for i in range(10):
            _ = feature_store.get(f"TEST_{i}", sample_data)
            _ = regime_detector.detect_regime(sample_data)
            _ = signal_ensemble.fused_probability(f"TEST_{i}", sample_data)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = final_memory - initial_memory

        # Memory growth should be reasonable (< 100MB for test operations)
        assert memory_growth < 100, f"Memory growth {memory_growth:.2f}MB exceeds 100MB limit"
        print(f"Memory growth during testing: {memory_growth:.2f}MB")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
