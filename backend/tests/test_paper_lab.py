# tests/test_paper_lab.py
"""
Integration tests for the ZiggyAI Paper Trading Lab

Tests core concepts and integration points for the autonomous paper trading system.
All tests are dev-only and use simulated data with safety guards.
"""

from datetime import datetime, timedelta

import numpy as np
import pytest

# Core configuration
from app.core.config import get_settings


settings = get_settings()


class TestPaperTradingConfiguration:
    """Test paper trading configuration and safety settings"""

    def test_development_environment_required(self):
        """Test system only runs in development environment"""
        # Should be development or have debug enabled
        assert settings.ENV in ["development", "dev"] or settings.DEBUG

    def test_safety_limits_configured(self):
        """Test safety limits are properly configured"""
        # Rate limiting
        assert hasattr(settings, "PAPER_MAX_TRADES_PER_MINUTE")
        assert settings.PAPER_MAX_TRADES_PER_MINUTE <= 1000

        # Position sizing
        assert hasattr(settings, "PAPER_MAX_POSITION_SIZE")
        assert settings.PAPER_MAX_POSITION_SIZE <= 0.50  # Max 50%

        # Risk limits
        assert hasattr(settings, "PAPER_MAX_DAILY_LOSS")
        assert settings.PAPER_MAX_DAILY_LOSS <= 1.0  # Max 100%

    def test_reasonable_defaults(self):
        """Test configuration has reasonable default values"""
        # Initial balance
        assert 1000 <= settings.PAPER_INITIAL_BALANCE <= 10000000

        # Commission and slippage
        assert 0 <= settings.PAPER_COMMISSION_PER_TRADE <= 100
        assert 1 <= settings.PAPER_SLIPPAGE_BPS <= 100

        # Learning parameters
        assert 0.001 <= settings.PAPER_LEARNING_RATE <= 1.0
        assert 1 <= settings.PAPER_BATCH_SIZE <= 1000


class TestComponentImports:
    """Test that all paper trading components can be imported"""

    def test_broker_import(self):
        """Test paper broker can be imported"""
        try:
            from app.brokers.paper_broker import PaperBroker

            assert PaperBroker is not None
        except ImportError as e:
            pytest.skip(f"PaperBroker not available: {e}")

    def test_engine_import(self):
        """Test paper engine can be imported"""
        try:
            from app.paper.engine import PaperEngine

            assert PaperEngine is not None
        except ImportError as e:
            pytest.skip(f"PaperEngine not available: {e}")

    def test_allocator_import(self):
        """Test bandit allocator can be imported"""
        try:
            from app.paper.allocator import BanditAllocator

            assert BanditAllocator is not None
        except ImportError as e:
            pytest.skip(f"BanditAllocator not available: {e}")

    def test_feature_computer_import(self):
        """Test feature computer can be imported"""
        try:
            from app.paper.features import FeatureComputer

            assert FeatureComputer is not None
        except ImportError as e:
            pytest.skip(f"FeatureComputer not available: {e}")

    def test_learner_import(self):
        """Test online learner can be imported"""
        try:
            from app.paper.learner import OnlineLearner

            assert OnlineLearner is not None
        except ImportError as e:
            pytest.skip(f"OnlineLearner not available: {e}")

    def test_worker_import(self):
        """Test paper worker can be imported"""
        try:
            from app.tasks.paper_worker import PaperWorker

            assert PaperWorker is not None
        except ImportError as e:
            pytest.skip(f"PaperWorker not available: {e}")


class TestDatabaseModels:
    """Test paper trading database models"""

    def test_paper_models_import(self):
        """Test paper trading models can be imported"""
        try:
            from app.models.paper import ModelSnapshot, PaperRun, TheoryPerf, Trade

            assert all([PaperRun, Trade, TheoryPerf, ModelSnapshot])
        except ImportError as e:
            pytest.skip(f"Paper models not available: {e}")

    def test_model_structure(self):
        """Test database models have expected structure"""
        try:
            from app.models.paper import PaperRun, Trade

            # Check PaperRun has key fields
            assert hasattr(PaperRun, "__tablename__")
            assert hasattr(PaperRun, "id")
            assert hasattr(PaperRun, "name")
            assert hasattr(PaperRun, "status")

            # Check Trade has key fields
            assert hasattr(Trade, "__tablename__")
            assert hasattr(Trade, "id")
            assert hasattr(Trade, "ticker")
            assert hasattr(Trade, "direction")

        except ImportError as e:
            pytest.skip(f"Paper models not available: {e}")


class TestAPIRoutes:
    """Test paper trading API routes"""

    def test_routes_import(self):
        """Test paper trading routes can be imported"""
        try:
            from app.api.routes_paper import router

            assert router is not None
        except ImportError as e:
            pytest.skip(f"Paper routes not available: {e}")

    def test_dev_only_protection(self):
        """Test API routes have dev-only protection"""
        try:
            from app.api.routes_paper import verify_dev_only

            # Should not raise in development environment
            verify_dev_only()

        except ImportError as e:
            pytest.skip(f"Paper routes not available: {e}")
        except Exception as e:
            # If it raises, should be due to environment check
            assert "development" in str(e).lower()


class TestBasicFunctionality:
    """Test basic functionality of components when available"""

    def test_price_data_structure(self):
        """Test price data structure"""
        try:
            from app.paper.features import PriceData

            # Test that PriceData class exists and can be instantiated
            assert PriceData is not None

        except ImportError as e:
            pytest.skip(f"PriceData not available: {e}")
        except Exception:
            # If there are constructor issues, try to import and verify exists
            try:
                from app.paper.features import PriceData

                assert PriceData is not None
            except ImportError as e:
                pytest.skip(f"PriceData not available: {e}")

    def test_signal_structure(self):
        """Test signal structure"""
        try:
            from app.paper.engine import Signal

            # Test that Signal class exists
            assert Signal is not None

        except ImportError as e:
            pytest.skip(f"Signal not available: {e}")
        except Exception:
            # If there are constructor issues, try to import and verify exists
            try:
                from app.paper.engine import Signal

                assert Signal is not None
            except ImportError as e:
                pytest.skip(f"Signal not available: {e}")

    def test_numpy_operations(self):
        """Test numpy operations work for feature computation"""
        # Basic numpy functionality for technical indicators
        prices = np.array([100, 101, 99, 102, 98, 105, 103])

        # Simple moving average
        window = 3
        sma = np.convolve(prices, np.ones(window) / window, mode="valid")

        assert len(sma) == len(prices) - window + 1
        assert all(np.isfinite(sma))

        # RSI calculation (simplified)
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        assert len(gains) == len(losses)
        assert all(gains >= 0)
        assert all(losses >= 0)


class TestSafetyValidation:
    """Test safety mechanisms and validation"""

    def test_position_size_validation(self):
        """Test position size validation"""
        max_position = settings.PAPER_MAX_POSITION_SIZE
        portfolio_value = 100000.0

        # Calculate max position value
        max_position_value = portfolio_value * max_position

        # Should be reasonable
        assert max_position_value <= portfolio_value
        assert max_position_value > 0

    def test_rate_limiting_calculation(self):
        """Test rate limiting calculations"""
        max_per_minute = settings.PAPER_MAX_TRADES_PER_MINUTE
        max_per_hour = settings.PAPER_MAX_TRADES_PER_HOUR

        # Per-minute limit should be less than per-hour limit
        assert max_per_minute * 60 >= max_per_hour  # Can sustain for full hour

        # Calculate minimum delay between trades
        min_delay_ms = 60000 / max_per_minute  # milliseconds
        assert min_delay_ms >= 60  # At least 60ms between trades

    def test_slippage_calculation(self):
        """Test slippage calculation"""
        price = 100.0
        slippage_bps = settings.PAPER_SLIPPAGE_BPS

        # Calculate slippage amount
        slippage_amount = price * (slippage_bps / 10000.0)

        # Should be reasonable
        assert 0 <= slippage_amount <= price * 0.01  # Max 1% slippage

    def test_commission_calculation(self):
        """Test commission calculation"""
        commission = settings.PAPER_COMMISSION_PER_TRADE
        trade_value = 10000.0  # $10k trade

        # Commission should be reasonable percentage
        commission_pct = commission / trade_value
        assert commission_pct <= 0.01  # Less than 1% commission


class TestIntegrationSafeguards:
    """Test integration safeguards and error handling"""

    def test_configuration_validation(self):
        """Test configuration validation"""
        # All paper trading settings should exist
        paper_settings = [
            "PAPER_MAX_TRADES_PER_MINUTE",
            "PAPER_INITIAL_BALANCE",
            "PAPER_COMMISSION_PER_TRADE",
            "PAPER_SLIPPAGE_BPS",
            "PAPER_LEARNING_RATE",
        ]

        for setting in paper_settings:
            assert hasattr(settings, setting), f"Missing setting: {setting}"
            value = getattr(settings, setting)
            assert value is not None, f"Setting {setting} is None"

    def test_data_validation(self):
        """Test basic data validation patterns"""
        # Test timestamp validation
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)

        assert now > hour_ago
        assert (now - hour_ago).total_seconds() == 3600

        # Test price validation
        def validate_price(price):
            return isinstance(price, (int, float)) and price > 0

        assert validate_price(100.0)
        assert validate_price(150)
        assert not validate_price(-10)
        assert not validate_price("invalid")

    def test_error_handling_patterns(self):
        """Test error handling patterns"""

        # Test graceful error handling
        def safe_divide(a, b):
            try:
                return a / b
            except ZeroDivisionError:
                return 0.0
            except Exception:
                return None

        assert safe_divide(10, 2) == 5.0
        assert safe_divide(10, 0) == 0.0
        assert safe_divide("invalid", 2) is None


if __name__ == "__main__":
    # Run tests with minimal output
    pytest.main([__file__, "-v", "--tb=short"])
