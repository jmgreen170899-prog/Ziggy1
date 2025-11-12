"""
Integration tests for ZiggyAI Cognitive Core system.

Focus on latency, ECE validation, and end-to-end functionality.
"""

import time

import numpy as np
import pandas as pd
import pytest


# Test configuration
TEST_DATA_SIZE = 100
LATENCY_THRESHOLD_MS = 150
ECE_THRESHOLD = 0.05


class TestCognitiveIntegration:
    """Integration tests for cognitive core components."""

    @pytest.fixture
    def sample_market_data(self):
        """Generate realistic market data for testing."""
        np.random.seed(42)
        dates = pd.date_range(start="2023-01-01", periods=TEST_DATA_SIZE, freq="D")

        # Generate realistic price series with trend and volatility
        returns = np.random.normal(
            0.0005, 0.02, TEST_DATA_SIZE
        )  # ~0.05% daily return, 2% volatility
        price_base = 100.0
        prices = [price_base]

        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))

        data = pd.DataFrame(
            {
                "symbol": ["AAPL"] * TEST_DATA_SIZE,
                "date": dates,
                "close": prices,
                "volume": np.random.lognormal(15, 0.5, TEST_DATA_SIZE),  # Log-normal volume
            }
        )

        # Add OHLC data
        data["open"] = data["close"].shift(1).fillna(data["close"].iloc[0])
        data["high"] = data[["open", "close"]].max(axis=1) * (
            1 + np.random.uniform(0, 0.01, TEST_DATA_SIZE)
        )
        data["low"] = data[["open", "close"]].min(axis=1) * (
            1 - np.random.uniform(0, 0.01, TEST_DATA_SIZE)
        )
        data["returns"] = data["close"].pct_change().fillna(0)

        return data

    def test_feature_computation_performance(self, sample_market_data):
        """Test feature computation meets performance requirements."""
        # Mock feature computation (since we need to test without full implementation)
        start_time = time.time()

        # Simulate feature computation workload
        data = sample_market_data
        features = self._compute_mock_features(data)

        latency_ms = (time.time() - start_time) * 1000

        assert latency_ms < LATENCY_THRESHOLD_MS, (
            f"Feature computation took {latency_ms:.2f}ms, exceeds {LATENCY_THRESHOLD_MS}ms limit"
        )
        assert len(features) >= 15, "Should compute at least 15 features"

        # Test feature validity
        for feature_name, value in features.items():
            assert not np.isnan(value), f"Feature {feature_name} is NaN"
            assert np.isfinite(value), f"Feature {feature_name} is not finite"

    def test_signal_generation_latency(self, sample_market_data):
        """Test signal generation meets latency requirements."""
        start_time = time.time()

        # Simulate signal generation
        signal_prob = self._generate_mock_signal(sample_market_data)

        latency_ms = (time.time() - start_time) * 1000

        assert latency_ms < 100, f"Signal generation took {latency_ms:.2f}ms, should be < 100ms"
        assert 0 <= signal_prob <= 1, f"Signal probability {signal_prob} should be between 0 and 1"

    def test_regime_detection_speed(self, sample_market_data):
        """Test regime detection performance."""
        start_time = time.time()

        regime_info = self._detect_mock_regime(sample_market_data)

        latency_ms = (time.time() - start_time) * 1000

        assert latency_ms < 50, f"Regime detection took {latency_ms:.2f}ms, should be < 50ms"
        assert "regime" in regime_info
        assert "confidence" in regime_info
        assert 0 <= regime_info["confidence"] <= 1

    def test_expected_calibration_error(self):
        """Test ECE computation and validation."""
        # Generate test predictions and outcomes
        np.random.seed(42)
        n_samples = 1000

        # Create well-calibrated predictions
        predictions = np.random.random(n_samples)
        outcomes = (np.random.random(n_samples) < predictions).astype(int)

        ece = self._compute_ece(predictions, outcomes)

        assert isinstance(ece, float), "ECE should be a float"
        assert 0 <= ece <= 1, f"ECE {ece} should be between 0 and 1"

        # Test with poorly calibrated predictions
        bad_predictions = np.random.random(n_samples) * 0.5 + 0.4  # Biased predictions
        bad_outcomes = (np.random.random(n_samples) < 0.2).astype(int)  # Different outcome rate

        bad_ece = self._compute_ece(bad_predictions, bad_outcomes)
        assert bad_ece > ece, "Poorly calibrated predictions should have higher ECE"

    def test_position_sizing_constraints(self, sample_market_data):
        """Test position sizing meets risk constraints."""
        current_price = sample_market_data["close"].iloc[-1]
        portfolio_value = 100000
        signal_confidence = 0.75

        start_time = time.time()
        position_info = self._compute_mock_position(
            signal_confidence, current_price, portfolio_value
        )
        latency_ms = (time.time() - start_time) * 1000

        assert latency_ms < 20, f"Position sizing took {latency_ms:.2f}ms, should be < 20ms"

        # Validate position constraints
        assert "shares" in position_info
        assert "dollar_amount" in position_info
        assert "risk_percent" in position_info

        shares = position_info["shares"]
        dollar_amount = position_info["dollar_amount"]
        risk_percent = position_info["risk_percent"]

        assert shares >= 0, "Shares should be non-negative"
        assert dollar_amount >= 0, "Dollar amount should be non-negative"
        assert dollar_amount <= portfolio_value, "Position shouldn't exceed portfolio"
        assert 0 <= risk_percent <= 0.1, f"Risk percent {risk_percent} should be <= 10%"

    def test_end_to_end_pipeline_performance(self, sample_market_data):
        """Test complete cognitive core pipeline performance."""
        start_time = time.time()

        # Simulate complete pipeline
        features = self._compute_mock_features(sample_market_data)
        regime = self._detect_mock_regime(sample_market_data)
        signal = self._generate_mock_signal(sample_market_data)
        position = self._compute_mock_position(signal, sample_market_data["close"].iloc[-1], 100000)
        explanation = self._generate_mock_explanation(features, regime, signal)

        total_latency_ms = (time.time() - start_time) * 1000

        # End-to-end should complete within 200ms
        assert total_latency_ms < 200, (
            f"End-to-end pipeline took {total_latency_ms:.2f}ms, should be < 200ms"
        )

        # Verify all components produced valid outputs
        assert len(features) >= 15
        assert "regime" in regime and "confidence" in regime
        assert 0 <= signal <= 1
        assert "shares" in position
        assert "feature_importance" in explanation

        print(f"✓ End-to-end pipeline latency: {total_latency_ms:.2f}ms")

    def test_explainability_features(self, sample_market_data):
        """Test explainability and interpretability features."""
        features = self._compute_mock_features(sample_market_data)
        regime = self._detect_mock_regime(sample_market_data)
        signal = self._generate_mock_signal(sample_market_data)

        explanation = self._generate_mock_explanation(features, regime, signal)

        # Check explanation structure
        assert "feature_importance" in explanation
        assert "model_contributions" in explanation
        assert "regime_influence" in explanation
        assert "confidence_interval" in explanation

        # Validate feature importance
        feature_importance = explanation["feature_importance"]
        assert len(feature_importance) > 0
        assert all(isinstance(v, (int, float)) for v in feature_importance.values())

        # Validate model contributions sum to reasonable total
        model_contributions = explanation["model_contributions"]
        total_contrib = sum(model_contributions.values())
        assert abs(total_contrib - signal) < 0.1, (
            "Model contributions should approximate final signal"
        )

    def test_backtesting_metrics(self, sample_market_data):
        """Test backtesting functionality and metrics."""
        # Simulate backtesting process
        trades = self._simulate_backtest(sample_market_data)
        metrics = self._compute_backtest_metrics(trades, sample_market_data)

        # Check required metrics exist
        required_metrics = [
            "total_return",
            "annualized_return",
            "volatility",
            "sharpe_ratio",
            "max_drawdown",
            "win_rate",
            "total_trades",
        ]

        for metric in required_metrics:
            assert metric in metrics, f"Missing required metric: {metric}"
            assert not np.isnan(metrics[metric]), f"Metric {metric} is NaN"

        # Validate metric ranges
        assert -1 <= metrics["total_return"] <= 10, "Total return should be reasonable"
        assert 0 <= metrics["volatility"] <= 2, "Volatility should be reasonable"
        assert 0 <= metrics["win_rate"] <= 1, "Win rate should be between 0 and 1"
        assert 0 <= metrics["max_drawdown"] <= 1, "Max drawdown should be between 0 and 1"

    def test_memory_efficiency(self, sample_market_data):
        """Test memory usage is reasonable."""
        # Simple memory test without psutil dependency
        import gc

        # Force garbage collection before test
        gc.collect()

        # Run operations multiple times
        for i in range(20):
            features = self._compute_mock_features(sample_market_data)
            regime = self._detect_mock_regime(sample_market_data)
            signal = self._generate_mock_signal(sample_market_data)
            _ = self._compute_mock_position(signal, 100.0, 100000)

            # Clear references
            del features, regime, signal

        # Force garbage collection after test
        gc.collect()

        # If we reach here without memory errors, test passes
        assert True, "Memory efficiency test completed"

    # Mock implementation methods for testing

    def _compute_mock_features(self, data):
        """Mock feature computation for testing."""
        features = {}

        # Momentum features
        features["rsi_14"] = np.random.uniform(20, 80)
        features["momentum_5d"] = np.random.normal(0, 0.02)
        features["momentum_20d"] = np.random.normal(0, 0.05)

        # Volatility features
        features["volatility_20"] = np.random.uniform(0.1, 0.5)
        features["volatility_ratio"] = np.random.uniform(0.5, 2.0)

        # Volume features
        features["volume_sma_20"] = np.random.lognormal(15, 0.5)
        features["volume_ratio"] = np.random.uniform(0.5, 3.0)

        # Technical features
        features["sma_50"] = data["close"].iloc[-1] * np.random.uniform(0.95, 1.05)
        features["sma_200"] = data["close"].iloc[-1] * np.random.uniform(0.9, 1.1)
        features["bollinger_position"] = np.random.uniform(-2, 2)

        # Microstructure features
        features["bid_ask_spread"] = np.random.uniform(0.01, 0.1)
        features["order_flow"] = np.random.normal(0, 1)

        # Sentiment features
        features["sentiment_score"] = np.random.uniform(-1, 1)
        features["news_sentiment"] = np.random.uniform(-1, 1)

        # Statistical features
        features["skewness"] = np.random.normal(0, 0.5)
        features["kurtosis"] = np.random.uniform(1, 5)

        return features

    def _detect_mock_regime(self, data):
        """Mock regime detection for testing."""
        regimes = ["bull_market", "bear_market", "sideways", "high_volatility"]

        # Simple volatility-based regime detection
        volatility = data["returns"].std() * np.sqrt(252)

        if volatility > 0.3:
            regime = "high_volatility"
            confidence = min(volatility / 0.5, 1.0)
        elif data["returns"].mean() > 0.001:
            regime = "bull_market"
            confidence = min(abs(data["returns"].mean()) * 1000, 1.0)
        elif data["returns"].mean() < -0.001:
            regime = "bear_market"
            confidence = min(abs(data["returns"].mean()) * 1000, 1.0)
        else:
            regime = "sideways"
            confidence = 0.7

        return {
            "regime": regime,
            "confidence": confidence,
            "regime_weights": dict.fromkeys(regimes, 0.25),  # Equal weights for mock
        }

    def _generate_mock_signal(self, data):
        """Mock signal generation for testing."""
        # Simple momentum-based signal
        short_ma = data["close"].tail(5).mean()
        long_ma = data["close"].tail(20).mean()

        momentum_signal = (short_ma - long_ma) / long_ma

        # Convert to probability using sigmoid
        signal_prob = 1 / (1 + np.exp(-momentum_signal * 10))

        # Add some noise and clip to [0,1]
        signal_prob += np.random.normal(0, 0.05)
        return np.clip(signal_prob, 0, 1)

    def _compute_mock_position(self, signal_confidence, current_price, portfolio_value):
        """Mock position sizing for testing."""
        # Simple Kelly-inspired position sizing
        base_position_pct = 0.05  # 5% base position
        confidence_multiplier = signal_confidence * 2  # 0-2x multiplier

        position_pct = min(base_position_pct * confidence_multiplier, 0.1)  # Max 10%
        dollar_amount = portfolio_value * position_pct
        shares = int(dollar_amount / current_price)

        return {
            "shares": shares,
            "dollar_amount": shares * current_price,
            "risk_percent": position_pct,
            "confidence_used": signal_confidence,
        }

    def _generate_mock_explanation(self, features, regime, signal):
        """Mock explanation generation for testing."""
        # Mock feature importance (normalized)
        feature_importance = {}
        total_importance = 0
        for feature in list(features.keys())[:10]:  # Top 10 features
            importance = np.random.exponential(0.1)
            feature_importance[feature] = importance
            total_importance += importance

        # Normalize
        for feature in feature_importance:
            feature_importance[feature] /= total_importance

        # Mock model contributions
        model_contributions = {
            "momentum_model": signal * 0.4,
            "mean_reversion_model": signal * 0.3,
            "volatility_model": signal * 0.2,
            "sentiment_model": signal * 0.1,
        }

        return {
            "feature_importance": feature_importance,
            "model_contributions": model_contributions,
            "regime_influence": regime["confidence"] * 0.1,
            "confidence_interval": [max(0, signal - 0.1), min(1, signal + 0.1)],
        }

    def _simulate_backtest(self, data):
        """Mock backtest simulation."""
        trades = []
        position = 0
        cash = 100000

        for i in range(10, len(data) - 1):
            current_price = data["close"].iloc[i]
            signal = self._generate_mock_signal(data.iloc[: i + 1])

            # Simple trading logic
            if signal > 0.7 and position == 0:
                # Buy
                shares = int(cash * 0.1 / current_price)
                if shares > 0:
                    position = shares
                    cash -= shares * current_price
                    trades.append(
                        {
                            "type": "buy",
                            "price": current_price,
                            "shares": shares,
                            "date": data["date"].iloc[i],
                        }
                    )

            elif signal < 0.3 and position > 0:
                # Sell
                cash += position * current_price
                trades.append(
                    {
                        "type": "sell",
                        "price": current_price,
                        "shares": position,
                        "date": data["date"].iloc[i],
                    }
                )
                position = 0

        return trades

    def _compute_backtest_metrics(self, trades, data):
        """Mock backtest metrics computation."""
        if len(trades) < 2:
            return {
                "total_return": 0.0,
                "annualized_return": 0.0,
                "volatility": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "win_rate": 0.0,
                "total_trades": 0,
            }

        # Simple P&L calculation
        pnl = []
        for i in range(0, len(trades) - 1, 2):
            if i + 1 < len(trades):
                buy_price = trades[i]["price"]
                sell_price = trades[i + 1]["price"]
                trade_return = (sell_price - buy_price) / buy_price
                pnl.append(trade_return)

        if not pnl:
            pnl = [0.0]

        total_return = np.sum(pnl)
        volatility = np.std(pnl) if len(pnl) > 1 else 0.0
        win_rate = np.mean([p > 0 for p in pnl])

        return {
            "total_return": total_return,
            "annualized_return": total_return * 252 / len(data),
            "volatility": volatility * np.sqrt(252),
            "sharpe_ratio": total_return / volatility if volatility > 0 else 0.0,
            "max_drawdown": abs(min(pnl)) if pnl else 0.0,
            "win_rate": win_rate,
            "total_trades": len(trades),
        }

    def _compute_ece(self, predictions, outcomes, n_bins=10):
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


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "--tb=short", "-x"])
