"""
Tests for Signal Routes with RAG Integration in ZiggyAI Memory & Knowledge System

Tests cognitive signal endpoint with RAG functionality, neighbor blending,
prior computation, and response format validation.
"""

import os
import shutil
import tempfile
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient


# Set test environment
os.environ["VECDB_BACKEND"] = "OFF"  # Start with OFF for basic tests
os.environ["KNN_K"] = "5"
os.environ["RAG_PRIOR_WEIGHT"] = "0.25"
os.environ["MEMORY_MODE"] = "JSONL"
os.environ["MEMORY_PATH"] = "test_signal_events.jsonl"

from app.api.routes_signals import router


# Create test app
app = FastAPI()
app.include_router(router)
client = TestClient(app)


class TestSignalWithRAG:
    """Test cases for signal generation with RAG integration."""

    def setup_method(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_dir, "test_signal_events.jsonl")
        os.environ["MEMORY_PATH"] = self.test_file

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch("app.api.routes_signals.COGNITIVE_CORE_AVAILABLE", True)
    @patch("app.api.routes_signals.RAG_ENABLED", False)
    @patch("app.api.routes_signals.compute_features")
    @patch("app.api.routes_signals.detect_regime")
    @patch("app.api.routes_signals.fused_probability")
    @patch("app.api.routes_signals.compute_position")
    def test_cognitive_signal_without_rag(
        self, mock_position, mock_fused, mock_regime, mock_features
    ):
        """Test cognitive signal generation without RAG (OFF mode)."""
        # Mock feature computation
        mock_features.return_value = {"momentum": 0.3, "sentiment": 0.2}

        # Mock regime detection
        mock_regime.return_value = {"regime": "normal", "confidence": 0.8}

        # Mock signal fusion
        mock_fused.return_value = {
            "p_up": 0.75,
            "confidence": 0.85,
            "shap_top": [["momentum", 0.4], ["sentiment", 0.3]],
        }

        # Mock position sizing
        mock_position.return_value = {
            "size": 0.15,
            "method": "volatility_target",
            "risk_pct": 2.0,
        }

        # Make request
        request_data = {
            "symbol": "AAPL",
            "interval": "1D",
            "include_explanations": True,
        }

        response = client.post("/signals/cognitive/signal", json=request_data)

        assert response.status_code == 200
        result = response.json()

        # Verify response structure
        assert result["symbol"] == "AAPL"
        assert result["p_up"] == 0.75
        assert result["p_up_model"] == 0.75
        assert result["p_up_prior"] is None
        assert result["p_up_blend"] == 0.75  # Same as model when no RAG
        assert result["confidence"] == 0.85
        assert result["regime"] == "normal"
        assert len(result["shap_top"]) == 2
        assert result["neighbors"] == []  # Empty when RAG is OFF
        assert result["event_id"] is not None

    @patch("app.api.routes_signals.COGNITIVE_CORE_AVAILABLE", True)
    @patch("app.api.routes_signals.RAG_ENABLED", True)
    @patch("app.api.routes_signals.compute_features")
    @patch("app.api.routes_signals.detect_regime")
    @patch("app.api.routes_signals.fused_probability")
    @patch("app.api.routes_signals.search_similar")
    @patch("app.api.routes_signals.build_embedding")
    @patch("app.api.routes_signals.upsert_event")
    def test_cognitive_signal_with_rag_neighbors(
        self,
        mock_upsert,
        mock_embedding,
        mock_search,
        mock_fused,
        mock_regime,
        mock_features,
    ):
        """Test cognitive signal generation with RAG neighbors."""
        # Mock feature computation
        mock_features.return_value = {"momentum": 0.3, "sentiment": 0.2}

        # Mock regime detection
        mock_regime.return_value = {"regime": "normal", "confidence": 0.8}

        # Mock signal fusion
        mock_fused.return_value = {
            "p_up": 0.75,
            "confidence": 0.85,
            "shap_top": [["momentum", 0.4], ["sentiment", 0.3]],
        }

        # Mock embedding generation
        mock_embedding.return_value = [0.1] * 384

        # Mock neighbor search with realistic results
        mock_search.return_value = [
            {
                "id": "past_event_1",
                "score": 0.95,
                "metadata": {
                    "ticker": "AAPL",
                    "regime": "normal",
                    "p_outcome": 0.8,  # Good historical outcome
                },
            },
            {
                "id": "past_event_2",
                "score": 0.88,
                "metadata": {
                    "ticker": "AAPL",
                    "regime": "normal",
                    "p_outcome": 0.6,  # Moderate historical outcome
                },
            },
        ]

        # Make request
        request_data = {
            "symbol": "AAPL",
            "interval": "1D",
            "include_explanations": True,
        }

        response = client.post("/signals/cognitive/signal", json=request_data)

        assert response.status_code == 200
        result = response.json()

        # Verify RAG integration
        assert result["symbol"] == "AAPL"
        assert result["p_up_model"] == 0.75

        # Calculate expected prior: (0.8 + 0.6) / 2 = 0.7
        expected_prior = 0.7
        assert abs(result["p_up_prior"] - expected_prior) < 0.01

        # Calculate expected blend: 0.25 * 0.7 + 0.75 * 0.75 = 0.175 + 0.5625 = 0.7375
        expected_blend = 0.25 * 0.7 + 0.75 * 0.75
        assert abs(result["p_up_blend"] - expected_blend) < 0.01
        assert abs(result["p_up"] - expected_blend) < 0.01  # p_up should be the blend

        # Verify neighbors are included
        assert len(result["neighbors"]) == 2
        assert result["neighbors"][0]["id"] == "past_event_1"
        assert result["neighbors"][0]["score"] == 0.95

        # Verify event storage calls
        mock_upsert.assert_called_once()

    @patch("app.api.routes_signals.COGNITIVE_CORE_AVAILABLE", True)
    @patch("app.api.routes_signals.RAG_ENABLED", True)
    @patch("app.api.routes_signals.compute_features")
    @patch("app.api.routes_signals.detect_regime")
    @patch("app.api.routes_signals.fused_probability")
    @patch("app.api.routes_signals.search_similar")
    def test_cognitive_signal_no_neighbor_outcomes(
        self, mock_search, mock_fused, mock_regime, mock_features
    ):
        """Test cognitive signal when neighbors have no outcome data."""
        # Mock components
        mock_features.return_value = {"momentum": 0.3}
        mock_regime.return_value = {"regime": "normal", "confidence": 0.8}
        mock_fused.return_value = {
            "p_up": 0.65,
            "confidence": 0.7,
            "shap_top": [["momentum", 0.5]],
        }

        # Mock neighbors without p_outcome
        mock_search.return_value = [
            {
                "id": "event_1",
                "score": 0.9,
                "metadata": {"ticker": "AAPL", "regime": "normal"},
                # No p_outcome
            },
            {
                "id": "event_2",
                "score": 0.85,
                "metadata": {"ticker": "AAPL", "other_field": "value"},
            },
        ]

        request_data = {"symbol": "AAPL", "interval": "1D"}
        response = client.post("/signals/cognitive/signal", json=request_data)

        assert response.status_code == 200
        result = response.json()

        # Should fall back to model prediction when no outcomes available
        assert result["p_up_model"] == 0.65
        assert result["p_up_prior"] is None
        assert result["p_up_blend"] == 0.65  # Should equal model when no prior
        assert result["p_up"] == 0.65

    @patch("app.api.routes_signals.COGNITIVE_CORE_AVAILABLE", True)
    @patch("app.api.routes_signals.RAG_ENABLED", True)
    @patch("app.api.routes_signals.compute_features")
    @patch("app.api.routes_signals.detect_regime")
    @patch("app.api.routes_signals.fused_probability")
    @patch("app.api.routes_signals.search_similar")
    def test_cognitive_signal_mixed_neighbor_outcomes(
        self, mock_search, mock_fused, mock_regime, mock_features
    ):
        """Test cognitive signal with mixed neighbor outcome quality."""
        # Mock components
        mock_features.return_value = {"momentum": 0.4, "sentiment": 0.3}
        mock_regime.return_value = {"regime": "high_vol", "confidence": 0.9}
        mock_fused.return_value = {
            "p_up": 0.8,
            "confidence": 0.9,
            "shap_top": [["momentum", 0.6], ["sentiment", 0.4]],
        }

        # Mock neighbors with mixed outcome data
        mock_search.return_value = [
            {
                "id": "event_1",
                "score": 0.95,
                "metadata": {"p_outcome": 0.9},
            },  # Very good outcome
            {
                "id": "event_2",
                "score": 0.88,
                "metadata": {"p_outcome": 0.1},
            },  # Poor outcome
            {"id": "event_3", "score": 0.82, "metadata": {}},  # No outcome data
            {
                "id": "event_4",
                "score": 0.75,
                "metadata": {"p_outcome": 0.7},
            },  # Good outcome
        ]

        request_data = {"symbol": "TSLA", "interval": "1D"}
        response = client.post("/signals/cognitive/signal", json=request_data)

        assert response.status_code == 200
        result = response.json()

        # Should only use neighbors with valid outcomes: (0.9 + 0.1 + 0.7) / 3 = 0.567
        expected_prior = (0.9 + 0.1 + 0.7) / 3
        assert abs(result["p_up_prior"] - expected_prior) < 0.01

        # Verify blending
        expected_blend = 0.25 * expected_prior + 0.75 * 0.8
        assert abs(result["p_up_blend"] - expected_blend) < 0.01

    @patch("app.api.routes_signals.COGNITIVE_CORE_AVAILABLE", True)
    @patch("app.api.routes_signals.RAG_ENABLED", True)
    @patch("app.api.routes_signals.search_similar")
    def test_cognitive_signal_rag_failure_fallback(self, mock_search):
        """Test cognitive signal fallback when RAG components fail."""
        # Mock RAG failure
        mock_search.side_effect = Exception("Vector search failed")

        with (
            patch("app.api.routes_signals.compute_features") as mock_features,
            patch("app.api.routes_signals.detect_regime") as mock_regime,
            patch("app.api.routes_signals.fused_probability") as mock_fused,
        ):
            mock_features.return_value = {"momentum": 0.3}
            mock_regime.return_value = {"regime": "normal", "confidence": 0.8}
            mock_fused.return_value = {
                "p_up": 0.7,
                "confidence": 0.8,
                "shap_top": [["momentum", 0.5]],
            }

            request_data = {"symbol": "AAPL", "interval": "1D"}
            response = client.post("/signals/cognitive/signal", json=request_data)

            assert response.status_code == 200
            result = response.json()

            # Should fall back gracefully to model prediction
            assert result["p_up_model"] == 0.7
            assert result["p_up_prior"] is None
            assert result["p_up_blend"] == 0.7
            assert result["neighbors"] == []

    def test_cognitive_signal_core_unavailable(self):
        """Test cognitive signal when core components are unavailable."""
        with patch("app.api.routes_signals.COGNITIVE_CORE_AVAILABLE", False):
            request_data = {"symbol": "AAPL", "interval": "1D"}
            response = client.post("/signals/cognitive/signal", json=request_data)

            assert response.status_code == 503
            assert "not available" in response.json()["detail"]

    @patch("app.api.routes_signals.COGNITIVE_CORE_AVAILABLE", True)
    @patch("app.api.routes_signals.RAG_ENABLED", True)
    def test_cognitive_signal_response_format_validation(self):
        """Test that cognitive signal response has correct format."""
        with (
            patch("app.api.routes_signals.compute_features") as mock_features,
            patch("app.api.routes_signals.detect_regime") as mock_regime,
            patch("app.api.routes_signals.fused_probability") as mock_fused,
            patch("app.api.routes_signals.search_similar") as mock_search,
        ):
            # Mock all components
            mock_features.return_value = {"momentum": 0.3}
            mock_regime.return_value = {"regime": "normal", "confidence": 0.8}
            mock_fused.return_value = {
                "p_up": 0.72,
                "confidence": 0.82,
                "shap_top": [["momentum", 0.5], ["sentiment", 0.3]],
            }
            mock_search.return_value = [
                {"id": "event1", "score": 0.9, "metadata": {"p_outcome": 0.8}}
            ]

            request_data = {"symbol": "AAPL", "interval": "1D"}
            response = client.post("/signals/cognitive/signal", json=request_data)

            assert response.status_code == 200
            result = response.json()

            # Verify all required fields are present
            required_fields = [
                "symbol",
                "p_up",
                "p_up_model",
                "p_up_prior",
                "p_up_blend",
                "confidence",
                "regime",
                "shap_top",
                "neighbors",
                "latency_ms",
                "cache_hit",
                "event_id",
            ]

            for field in required_fields:
                assert field in result, f"Missing required field: {field}"

            # Verify field types
            assert isinstance(result["symbol"], str)
            assert isinstance(result["p_up"], (int, float))
            assert isinstance(result["p_up_model"], (int, float))
            assert isinstance(result["confidence"], (int, float))
            assert isinstance(result["regime"], str)
            assert isinstance(result["shap_top"], list)
            assert isinstance(result["neighbors"], list)
            assert isinstance(result["latency_ms"], (int, float))
            assert isinstance(result["cache_hit"], bool)
            assert isinstance(result["event_id"], str)

            # Verify probability ranges
            assert 0 <= result["p_up"] <= 1
            assert 0 <= result["p_up_model"] <= 1
            if result["p_up_prior"] is not None:
                assert 0 <= result["p_up_prior"] <= 1
            assert 0 <= result["p_up_blend"] <= 1
            assert 0 <= result["confidence"] <= 1


class TestSignalRAGPerformance:
    """Performance tests for signal generation with RAG."""

    def setup_method(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_dir, "perf_test_events.jsonl")
        os.environ["MEMORY_PATH"] = self.test_file

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch("app.api.routes_signals.COGNITIVE_CORE_AVAILABLE", True)
    @patch("app.api.routes_signals.RAG_ENABLED", True)
    def test_signal_generation_latency(self):
        """Test that signal generation meets latency requirements."""
        with (
            patch("app.api.routes_signals.compute_features") as mock_features,
            patch("app.api.routes_signals.detect_regime") as mock_regime,
            patch("app.api.routes_signals.fused_probability") as mock_fused,
            patch("app.api.routes_signals.search_similar") as mock_search,
        ):
            # Mock fast responses
            mock_features.return_value = {"momentum": 0.3}
            mock_regime.return_value = {"regime": "normal", "confidence": 0.8}
            mock_fused.return_value = {
                "p_up": 0.7,
                "confidence": 0.8,
                "shap_top": [["momentum", 0.5]],
            }
            mock_search.return_value = []  # No neighbors for faster test

            import time

            start_time = time.time()

            request_data = {"symbol": "AAPL", "interval": "1D"}
            response = client.post("/signals/cognitive/signal", json=request_data)

            end_time = time.time()
            actual_latency = (end_time - start_time) * 1000  # Convert to ms

            assert response.status_code == 200
            result = response.json()

            # Verify latency is reported and reasonable
            reported_latency = result["latency_ms"]
            assert reported_latency > 0
            assert actual_latency < 500  # Should complete within 500ms

    @patch("app.api.routes_signals.COGNITIVE_CORE_AVAILABLE", True)
    @patch("app.api.routes_signals.RAG_ENABLED", True)
    def test_signal_generation_with_many_neighbors(self):
        """Test signal generation performance with many neighbors."""
        with (
            patch("app.api.routes_signals.compute_features") as mock_features,
            patch("app.api.routes_signals.detect_regime") as mock_regime,
            patch("app.api.routes_signals.fused_probability") as mock_fused,
            patch("app.api.routes_signals.search_similar") as mock_search,
        ):
            # Mock components
            mock_features.return_value = {"momentum": 0.3}
            mock_regime.return_value = {"regime": "normal", "confidence": 0.8}
            mock_fused.return_value = {
                "p_up": 0.7,
                "confidence": 0.8,
                "shap_top": [["momentum", 0.5]],
            }

            # Mock many neighbors
            many_neighbors = []
            for i in range(100):  # Large neighbor set
                many_neighbors.append(
                    {
                        "id": f"event_{i}",
                        "score": 0.9 - i * 0.001,
                        "metadata": {"p_outcome": 0.5 + (i % 50) * 0.01},
                    }
                )

            mock_search.return_value = many_neighbors

            request_data = {"symbol": "AAPL", "interval": "1D"}
            response = client.post("/signals/cognitive/signal", json=request_data)

            assert response.status_code == 200
            result = response.json()

            # Should handle many neighbors efficiently
            assert len(result["neighbors"]) == 100
            assert result["p_up_prior"] is not None
            assert 0 <= result["p_up_prior"] <= 1


class TestSignalRAGEdgeCases:
    """Edge case tests for signal generation with RAG."""

    def setup_method(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_dir, "edge_case_events.jsonl")
        os.environ["MEMORY_PATH"] = self.test_file

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch("app.api.routes_signals.COGNITIVE_CORE_AVAILABLE", True)
    @patch("app.api.routes_signals.RAG_ENABLED", True)
    def test_signal_with_extreme_prior_values(self):
        """Test signal generation with extreme prior values."""
        with (
            patch("app.api.routes_signals.compute_features") as mock_features,
            patch("app.api.routes_signals.detect_regime") as mock_regime,
            patch("app.api.routes_signals.fused_probability") as mock_fused,
            patch("app.api.routes_signals.search_similar") as mock_search,
        ):
            mock_features.return_value = {"momentum": 0.3}
            mock_regime.return_value = {"regime": "normal", "confidence": 0.8}
            mock_fused.return_value = {
                "p_up": 0.5,  # Neutral model prediction
                "confidence": 0.7,
                "shap_top": [["momentum", 0.3]],
            }

            # Mock neighbors with extreme outcomes
            mock_search.return_value = [
                {
                    "id": "event1",
                    "score": 0.9,
                    "metadata": {"p_outcome": 0.0},
                },  # Extreme bear
                {
                    "id": "event2",
                    "score": 0.85,
                    "metadata": {"p_outcome": 1.0},
                },  # Extreme bull
                {
                    "id": "event3",
                    "score": 0.8,
                    "metadata": {"p_outcome": 0.0},
                },  # Another bear
            ]

            request_data = {"symbol": "AAPL", "interval": "1D"}
            response = client.post("/signals/cognitive/signal", json=request_data)

            assert response.status_code == 200
            result = response.json()

            # Prior should be average: (0.0 + 1.0 + 0.0) / 3 = 0.333
            expected_prior = (0.0 + 1.0 + 0.0) / 3
            assert abs(result["p_up_prior"] - expected_prior) < 0.01

            # Blend should be reasonable
            expected_blend = 0.25 * expected_prior + 0.75 * 0.5
            assert abs(result["p_up_blend"] - expected_blend) < 0.01

    @patch("app.api.routes_signals.COGNITIVE_CORE_AVAILABLE", True)
    @patch("app.api.routes_signals.RAG_ENABLED", True)
    def test_signal_with_invalid_neighbor_data(self):
        """Test signal generation with malformed neighbor data."""
        with (
            patch("app.api.routes_signals.compute_features") as mock_features,
            patch("app.api.routes_signals.detect_regime") as mock_regime,
            patch("app.api.routes_signals.fused_probability") as mock_fused,
            patch("app.api.routes_signals.search_similar") as mock_search,
        ):
            mock_features.return_value = {"momentum": 0.4}
            mock_regime.return_value = {"regime": "normal", "confidence": 0.8}
            mock_fused.return_value = {
                "p_up": 0.65,
                "confidence": 0.75,
                "shap_top": [["momentum", 0.4]],
            }

            # Mock neighbors with various data quality issues
            mock_search.return_value = [
                {"id": "event1"},  # Missing metadata entirely
                {"id": "event2", "metadata": {}},  # Empty metadata
                {"id": "event3", "metadata": {"p_outcome": "invalid"}},  # Invalid type
                {"id": "event4", "metadata": {"p_outcome": -0.5}},  # Out of range
                {"id": "event5", "metadata": {"p_outcome": 1.5}},  # Out of range
                {"id": "event6", "metadata": {"p_outcome": 0.7}},  # Valid
            ]

            request_data = {"symbol": "AAPL", "interval": "1D"}
            response = client.post("/signals/cognitive/signal", json=request_data)

            assert response.status_code == 200
            result = response.json()

            # Should only use the one valid neighbor
            assert result["p_up_prior"] == 0.7  # Only valid outcome

            # Should include all neighbors in response for transparency
            assert len(result["neighbors"]) == 6

    @patch("app.api.routes_signals.COGNITIVE_CORE_AVAILABLE", True)
    def test_signal_with_datetime_parsing(self):
        """Test signal generation with various datetime formats."""
        with (
            patch("app.api.routes_signals.compute_features") as mock_features,
            patch("app.api.routes_signals.detect_regime") as mock_regime,
            patch("app.api.routes_signals.fused_probability") as mock_fused,
        ):
            mock_features.return_value = {"momentum": 0.3}
            mock_regime.return_value = {"regime": "normal", "confidence": 0.8}
            mock_fused.return_value = {
                "p_up": 0.6,
                "confidence": 0.7,
                "shap_top": [["momentum", 0.4]],
            }

            # Test various datetime formats
            datetime_formats = [
                "2024-01-15T10:30:00Z",
                "2024-01-15T10:30:00+00:00",
                None,  # Should use current time
            ]

            for dt_str in datetime_formats:
                request_data = {"symbol": "AAPL", "interval": "1D", "dt": dt_str}

                response = client.post("/signals/cognitive/signal", json=request_data)

                assert response.status_code == 200
                result = response.json()
                assert result["symbol"] == "AAPL"
                assert "event_id" in result
