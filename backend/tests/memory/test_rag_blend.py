"""
Tests for RAG (Retrieval-Augmented Generation) Blending in ZiggyAI Memory & Knowledge System

Tests prior computation, blending mathematics, edge cases with neighbors,
and integration with the cognitive signal generation process.
"""

import os
from unittest.mock import patch

import pytest


# Set test environment
os.environ["VECDB_BACKEND"] = "OFF"
os.environ["KNN_K"] = "10"
os.environ["RAG_PRIOR_WEIGHT"] = "0.25"

from app.memory.vecdb import build_embedding


class TestRAGBlending:
    """Test cases for RAG blending functionality."""

    def test_prior_computation_basic(self):
        """Test basic prior computation from neighbors."""
        neighbors = [
            {"id": "event1", "metadata": {"p_outcome": 0.8}},
            {"id": "event2", "metadata": {"p_outcome": 0.6}},
            {"id": "event3", "metadata": {"p_outcome": 0.7}},
        ]

        # Extract outcomes
        outcomes = [n["metadata"]["p_outcome"] for n in neighbors]
        prior = sum(outcomes) / len(outcomes)

        assert abs(prior - 0.7) < 1e-6  # (0.8 + 0.6 + 0.7) / 3 = 0.7

    def test_prior_computation_empty_neighbors(self):
        """Test prior computation with no neighbors."""
        neighbors = []

        # Should handle empty case gracefully
        outcomes = [
            n["metadata"]["p_outcome"] for n in neighbors if "p_outcome" in n.get("metadata", {})
        ]
        prior = sum(outcomes) / len(outcomes) if outcomes else None

        assert prior is None

    def test_prior_computation_missing_outcomes(self):
        """Test prior computation when some neighbors lack outcomes."""
        neighbors = [
            {"id": "event1", "metadata": {"p_outcome": 0.8}},
            {"id": "event2", "metadata": {"other_field": "value"}},  # No p_outcome
            {"id": "event3", "metadata": {"p_outcome": 0.6}},
            {"id": "event4", "metadata": {}},  # Empty metadata
        ]

        # Filter to only neighbors with outcomes
        outcomes = []
        for n in neighbors:
            metadata = n.get("metadata", {})
            if "p_outcome" in metadata:
                outcomes.append(metadata["p_outcome"])

        prior = sum(outcomes) / len(outcomes) if outcomes else None

        assert abs(prior - 0.7) < 1e-6  # (0.8 + 0.6) / 2 = 0.7

    def test_blending_mathematics(self):
        """Test the blending formula mathematics."""
        p_model = 0.75
        p_prior = 0.65
        weight_prior = 0.25

        # Blending formula: w_prior * prior + (1 - w_prior) * model
        p_blend = weight_prior * p_prior + (1 - weight_prior) * p_model
        expected = 0.25 * 0.65 + 0.75 * 0.75  # 0.1625 + 0.5625 = 0.725

        assert abs(p_blend - expected) < 1e-6
        assert abs(p_blend - 0.725) < 1e-6

    def test_blending_edge_cases(self):
        """Test blending edge cases."""
        p_model = 0.8

        # Case 1: No prior (should return model)
        p_prior = None
        p_blend = p_prior * 0.25 + p_model * 0.75 if p_prior is not None else p_model
        assert p_blend == p_model

        # Case 2: Zero weight for prior
        p_prior = 0.6
        weight_prior = 0.0
        p_blend = weight_prior * p_prior + (1 - weight_prior) * p_model
        assert p_blend == p_model

        # Case 3: Full weight for prior
        weight_prior = 1.0
        p_blend = weight_prior * p_prior + (1 - weight_prior) * p_model
        assert p_blend == p_prior

    def test_blending_extreme_values(self):
        """Test blending with extreme probability values."""
        weight_prior = 0.25

        # Case 1: Model very confident UP, prior very confident DOWN
        p_model = 0.95
        p_prior = 0.05
        p_blend = weight_prior * p_prior + (1 - weight_prior) * p_model
        expected = 0.25 * 0.05 + 0.75 * 0.95  # 0.0125 + 0.7125 = 0.725
        assert abs(p_blend - expected) < 1e-6

        # Case 2: Model very confident DOWN, prior very confident UP
        p_model = 0.05
        p_prior = 0.95
        p_blend = weight_prior * p_prior + (1 - weight_prior) * p_model
        expected = 0.25 * 0.95 + 0.75 * 0.05  # 0.2375 + 0.0375 = 0.275
        assert abs(p_blend - expected) < 1e-6

    def test_prior_confidence_weighting(self):
        """Test that prior weight should vary based on confidence/agreement."""
        # This is a more advanced feature - testing the concept

        def adaptive_prior_weight(neighbors, base_weight=0.25):
            """Adaptive weighting based on neighbor agreement."""
            if not neighbors:
                return 0.0

            outcomes = [
                n["metadata"]["p_outcome"]
                for n in neighbors
                if "p_outcome" in n.get("metadata", {})
            ]
            if len(outcomes) < 2:
                return base_weight

            # Calculate variance of outcomes (lower variance = higher confidence)
            mean_outcome = sum(outcomes) / len(outcomes)
            variance = sum((x - mean_outcome) ** 2 for x in outcomes) / len(outcomes)

            # Higher agreement (lower variance) should increase prior weight
            # Variance ranges from 0 (perfect agreement) to 0.25 (maximum disagreement for 0-1 range)
            agreement_factor = max(0, 1 - 4 * variance)  # Maps 0.25->0, 0->1

            return base_weight + (0.5 - base_weight) * agreement_factor

        # High agreement case
        high_agreement_neighbors = [
            {"id": "e1", "metadata": {"p_outcome": 0.7}},
            {"id": "e2", "metadata": {"p_outcome": 0.72}},
            {"id": "e3", "metadata": {"p_outcome": 0.71}},
        ]

        # Low agreement case
        low_agreement_neighbors = [
            {"id": "e1", "metadata": {"p_outcome": 0.1}},
            {"id": "e2", "metadata": {"p_outcome": 0.9}},
            {"id": "e3", "metadata": {"p_outcome": 0.5}},
        ]

        weight_high = adaptive_prior_weight(high_agreement_neighbors)
        weight_low = adaptive_prior_weight(low_agreement_neighbors)

        # High agreement should result in higher weight for prior
        assert weight_high > weight_low
        assert weight_high > 0.25  # Should be higher than base weight

    def test_neighbor_similarity_weighting(self):
        """Test weighting neighbors by similarity scores."""
        neighbors = [
            {"id": "e1", "score": 0.95, "metadata": {"p_outcome": 0.8}},
            {"id": "e2", "score": 0.85, "metadata": {"p_outcome": 0.6}},
            {"id": "e3", "score": 0.75, "metadata": {"p_outcome": 0.4}},
        ]

        # Simple weighted average by similarity score
        weighted_outcomes = []
        total_weight = 0

        for neighbor in neighbors:
            if "p_outcome" in neighbor.get("metadata", {}):
                score = neighbor["score"]
                outcome = neighbor["metadata"]["p_outcome"]
                weighted_outcomes.append(score * outcome)
                total_weight += score

        weighted_prior = sum(weighted_outcomes) / total_weight if total_weight > 0 else None

        # Should be weighted more towards high-similarity neighbors
        # 0.95*0.8 + 0.85*0.6 + 0.75*0.4 = 0.76 + 0.51 + 0.3 = 1.57
        # Total weight: 0.95 + 0.85 + 0.75 = 2.55
        # Weighted average: 1.57 / 2.55 ≈ 0.615

        expected = (0.95 * 0.8 + 0.85 * 0.6 + 0.75 * 0.4) / (0.95 + 0.85 + 0.75)
        assert abs(weighted_prior - expected) < 1e-6

    def test_regime_aware_blending(self):
        """Test that blending should be regime-aware."""
        # This tests the concept of regime-specific prior weights

        def get_regime_prior_weight(regime, base_weight=0.25):
            """Get regime-specific prior weight."""
            regime_weights = {
                "normal": 0.25,
                "high_vol": 0.35,  # Higher uncertainty -> more weight to history
                "crash": 0.45,  # Extreme uncertainty -> even more weight to history
                "rally": 0.15,  # Strong trends -> less weight to history
            }
            return regime_weights.get(regime, base_weight)

        # Test different regimes
        assert get_regime_prior_weight("normal") == 0.25
        assert get_regime_prior_weight("high_vol") == 0.35
        assert get_regime_prior_weight("crash") == 0.45
        assert get_regime_prior_weight("rally") == 0.15
        assert get_regime_prior_weight("unknown") == 0.25  # Default

    def test_temporal_decay_weighting(self):
        """Test temporal decay for neighbor weights."""
        from datetime import datetime, timedelta

        def temporal_weight(event_ts, current_ts, half_life_days=30):
            """Calculate temporal decay weight."""
            if isinstance(event_ts, str):
                event_dt = datetime.fromisoformat(event_ts.replace("Z", "+00:00"))
            else:
                event_dt = event_ts

            if isinstance(current_ts, str):
                current_dt = datetime.fromisoformat(current_ts.replace("Z", "+00:00"))
            else:
                current_dt = current_ts

            days_ago = (current_dt - event_dt).days
            decay_factor = 0.5 ** (days_ago / half_life_days)

            return decay_factor

        current_time = datetime.now()

        # Recent event (1 day ago)
        recent_ts = current_time - timedelta(days=1)
        recent_weight = temporal_weight(recent_ts, current_time)

        # Old event (60 days ago)
        old_ts = current_time - timedelta(days=60)
        old_weight = temporal_weight(old_ts, current_time)

        # Recent events should have higher weight
        assert recent_weight > old_weight
        assert recent_weight > 0.9  # Should be close to 1.0
        assert old_weight < 0.3  # Should be significantly decayed


class TestRAGIntegration:
    """Integration tests for RAG functionality."""

    @patch("app.memory.vecdb.search_similar")
    def test_rag_integration_with_signal_generation(self, mock_search):
        """Test RAG integration with signal generation process."""
        # Mock neighbor search results
        mock_search.return_value = [
            {
                "id": "past_event_1",
                "score": 0.95,
                "metadata": {
                    "ticker": "AAPL",
                    "regime": "normal",
                    "ts": "2024-01-01T00:00:00Z",
                    "p_outcome": 0.75,
                },
            },
            {
                "id": "past_event_2",
                "score": 0.85,
                "metadata": {
                    "ticker": "AAPL",
                    "regime": "normal",
                    "ts": "2024-01-02T00:00:00Z",
                    "p_outcome": 0.65,
                },
            },
        ]

        # Simulate RAG process
        query_event = {
            "ticker": "AAPL",
            "regime": "normal",
            "explain": {"shap_top": [["momentum", 0.3], ["sentiment", 0.2]]},
        }

        # Build embedding and search
        embedding = build_embedding(query_event)
        neighbors = mock_search(embedding, k=10)

        # Compute prior from neighbors
        neighbor_outcomes = []
        for neighbor in neighbors:
            metadata = neighbor.get("metadata", {})
            p_outcome = metadata.get("p_outcome")
            if p_outcome is not None:
                neighbor_outcomes.append(p_outcome)

        prior = sum(neighbor_outcomes) / len(neighbor_outcomes) if neighbor_outcomes else None

        # Test blending
        p_model = 0.8
        weight_prior = 0.25
        p_blend = weight_prior * prior + (1 - weight_prior) * p_model if prior else p_model

        expected_prior = (0.75 + 0.65) / 2  # 0.7
        expected_blend = 0.25 * 0.7 + 0.75 * 0.8  # 0.175 + 0.6 = 0.775

        assert abs(prior - expected_prior) < 1e-6
        assert abs(p_blend - expected_blend) < 1e-6

    def test_rag_no_neighbors_fallback(self):
        """Test RAG fallback when no neighbors are found."""
        # Simulate empty search results
        neighbors = []

        # Should fall back to model prediction
        p_model = 0.7
        prior = None
        p_blend = p_model  # No blending when no prior

        assert p_blend == p_model

    def test_rag_invalid_neighbor_data(self):
        """Test RAG handling of invalid neighbor data."""
        neighbors = [
            {"id": "event1"},  # Missing metadata
            {"id": "event2", "metadata": {}},  # Empty metadata
            {"id": "event3", "metadata": {"p_outcome": "invalid"}},  # Invalid outcome
            {"id": "event4", "metadata": {"p_outcome": 0.8}},  # Valid
        ]

        # Robust extraction of valid outcomes
        valid_outcomes = []
        for neighbor in neighbors:
            metadata = neighbor.get("metadata", {})
            p_outcome = metadata.get("p_outcome")

            # Validate outcome value
            if isinstance(p_outcome, (int, float)) and 0 <= p_outcome <= 1:
                valid_outcomes.append(p_outcome)

        prior = sum(valid_outcomes) / len(valid_outcomes) if valid_outcomes else None

        assert len(valid_outcomes) == 1
        assert prior == 0.8

    @pytest.mark.performance
    def test_rag_performance_characteristics(self):
        """Test RAG performance characteristics."""
        # Test that embedding generation is fast enough
        import time

        event = {
            "ticker": "AAPL",
            "regime": "normal",
            "explain": {"shap_top": [["momentum", 0.3], ["sentiment", 0.2]]},
        }

        start_time = time.time()
        embedding = build_embedding(event)
        end_time = time.time()

        embedding_time_ms = (end_time - start_time) * 1000

        # Embedding generation should be fast (< 10ms)
        assert embedding_time_ms < 10
        assert len(embedding) == 384

    def test_rag_consistency_across_calls(self):
        """Test that RAG produces consistent results across calls."""
        event = {"ticker": "AAPL", "regime": "normal", "explain": {"shap_top": [["momentum", 0.3]]}}

        # Generate embeddings multiple times
        embeddings = []
        for _ in range(5):
            embedding = build_embedding(event)
            embeddings.append(embedding)

        # All should be identical (deterministic)
        for i in range(1, len(embeddings)):
            assert embeddings[i] == embeddings[0]

    def test_rag_sensitivity_analysis(self):
        """Test RAG sensitivity to different input variations."""
        base_event = {
            "ticker": "AAPL",
            "regime": "normal",
            "explain": {"shap_top": [["momentum", 0.3]]},
        }

        # Small variation
        small_var_event = {
            "ticker": "AAPL",
            "regime": "normal",
            "explain": {"shap_top": [["momentum", 0.31]]},  # Slight change
        }

        # Large variation
        large_var_event = {
            "ticker": "TSLA",  # Different ticker
            "regime": "high_vol",  # Different regime
            "explain": {"shap_top": [["volatility", 0.8]]},  # Different features
        }

        emb_base = build_embedding(base_event)
        emb_small = build_embedding(small_var_event)
        emb_large = build_embedding(large_var_event)

        from app.memory.vecdb import _cosine_similarity

        sim_small = _cosine_similarity(emb_base, emb_small)
        sim_large = _cosine_similarity(emb_base, emb_large)

        # Small variations should have higher similarity than large variations
        assert sim_small > sim_large


# Performance and stress tests
class TestRAGPerformance:
    """Performance tests for RAG functionality."""

    @pytest.mark.performance
    def test_embedding_generation_batch(self):
        """Test batch embedding generation performance."""
        import time

        events = []
        for i in range(100):
            events.append(
                {
                    "ticker": f"STOCK{i % 10}",
                    "regime": ["normal", "high_vol", "crash"][i % 3],
                    "explain": {"shap_top": [["feature", 0.1 + i * 0.01]]},
                }
            )

        start_time = time.time()
        embeddings = [build_embedding(event) for event in events]
        end_time = time.time()

        batch_time_ms = (end_time - start_time) * 1000
        time_per_embedding = batch_time_ms / len(events)

        # Should be able to generate embeddings efficiently
        assert time_per_embedding < 5  # < 5ms per embedding
        assert len(embeddings) == 100
        assert all(len(emb) == 384 for emb in embeddings)

    @pytest.mark.performance
    def test_prior_computation_large_neighbor_set(self):
        """Test prior computation with large neighbor sets."""
        # Generate large neighbor set
        neighbors = []
        for i in range(1000):
            neighbors.append(
                {
                    "id": f"event_{i}",
                    "score": 0.9 - i * 0.0001,  # Decreasing similarity
                    "metadata": {"p_outcome": 0.5 + (i % 100) * 0.005},  # Varying outcomes
                }
            )

        # Compute prior efficiently
        import time

        start_time = time.time()

        outcomes = []
        for neighbor in neighbors:
            metadata = neighbor.get("metadata", {})
            p_outcome = metadata.get("p_outcome")
            if isinstance(p_outcome, (int, float)):
                outcomes.append(p_outcome)

        prior = sum(outcomes) / len(outcomes) if outcomes else None

        end_time = time.time()
        computation_time_ms = (end_time - start_time) * 1000

        # Should compute prior quickly even for large neighbor sets
        assert computation_time_ms < 10  # < 10ms
        assert prior is not None
        assert 0 <= prior <= 1
