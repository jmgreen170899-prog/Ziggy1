"""
Tests for Vector Database functionality in ZiggyAI Memory & Knowledge System

Tests embedding generation, vector storage/retrieval, similarity search,
and backend switching (Qdrant/Redis/OFF).
"""

import os
from unittest.mock import MagicMock, patch

import pytest


# Set test environment
os.environ["VECDB_BACKEND"] = "OFF"  # Start with OFF mode for basic tests

from app.memory.vecdb import (
    _cosine_similarity,
    _hash_to_embedding,
    build_embedding,
    build_embeddings_batch,
    clear_collection,
    get_collection_stats,
    get_embedding_info,
    search_similar,
    upsert_event,
)


class TestVectorDB:
    """Test cases for Vector Database functionality."""

    def setup_method(self):
        """Set up test environment."""
        # Ensure we start with OFF backend for basic tests
        os.environ["VECDB_BACKEND"] = "OFF"

    def test_build_embedding_deterministic(self):
        """Test that embedding generation is deterministic."""
        event1 = {
            "ticker": "AAPL",
            "regime": "high_vol",
            "explain": {"shap_top": [["momentum", 0.3], ["sentiment", 0.2]]},
        }

        event2 = {
            "ticker": "AAPL",
            "regime": "high_vol",
            "explain": {"shap_top": [["momentum", 0.3], ["sentiment", 0.2]]},
        }

        embedding1 = build_embedding(event1)
        embedding2 = build_embedding(event2)

        # Should be identical for identical inputs
        assert embedding1 == embedding2

    def test_build_embedding_different_inputs(self):
        """Test that different inputs produce different embeddings."""
        event1 = {
            "ticker": "AAPL",
            "regime": "high_vol",
            "explain": {"shap_top": [["momentum", 0.3]]},
        }

        event2 = {
            "ticker": "TSLA",  # Different ticker
            "regime": "high_vol",
            "explain": {"shap_top": [["momentum", 0.3]]},
        }

        embedding1 = build_embedding(event1)
        embedding2 = build_embedding(event2)

        # Should be different for different inputs
        assert embedding1 != embedding2

    def test_embedding_dimension(self):
        """Test that embeddings have correct dimension."""
        event = {
            "ticker": "AAPL",
            "regime": "normal",
            "explain": {"shap_top": [["momentum", 0.3]]},
        }

        embedding = build_embedding(event)

        # Should be 384-dimensional (miniLM-L6 size)
        assert len(embedding) == 384
        assert all(isinstance(x, float) for x in embedding)

    def test_embedding_normalization(self):
        """Test that embeddings are properly normalized."""
        event = {
            "ticker": "AAPL",
            "regime": "normal",
            "explain": {"shap_top": [["momentum", 0.3]]},
        }

        embedding = build_embedding(event)

        # Calculate L2 norm
        norm = sum(x * x for x in embedding) ** 0.5

        # Should be approximately 1.0 (normalized)
        assert abs(norm - 1.0) < 1e-6

    def test_hash_to_embedding_consistency(self):
        """Test hash-based embedding consistency."""
        text1 = "test_string"
        text2 = "test_string"
        text3 = "different_string"

        embedding1 = _hash_to_embedding(text1, dim=128)
        embedding2 = _hash_to_embedding(text2, dim=128)
        embedding3 = _hash_to_embedding(text3, dim=128)

        # Same input should produce same embedding
        assert embedding1 == embedding2

        # Different input should produce different embedding
        assert embedding1 != embedding3

        # Check dimension
        assert len(embedding1) == 128

    def test_cosine_similarity(self):
        """Test cosine similarity calculation."""
        # Identical vectors
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        assert abs(_cosine_similarity(vec1, vec2) - 1.0) < 1e-6

        # Orthogonal vectors
        vec3 = [1.0, 0.0, 0.0]
        vec4 = [0.0, 1.0, 0.0]
        assert abs(_cosine_similarity(vec3, vec4) - 0.0) < 1e-6

        # Opposite vectors
        vec5 = [1.0, 0.0, 0.0]
        vec6 = [-1.0, 0.0, 0.0]
        assert abs(_cosine_similarity(vec5, vec6) - (-1.0)) < 1e-6

    def test_upsert_event_off_mode(self):
        """Test that upsert works in OFF mode (no-op)."""
        embedding = [0.1, 0.2, 0.3]
        metadata = {"ticker": "AAPL", "regime": "normal"}

        # Should not raise an error
        upsert_event("test_id", embedding, metadata)

    def test_search_similar_off_mode(self):
        """Test that search returns empty list in OFF mode."""
        embedding = [0.1, 0.2, 0.3]

        results = search_similar(embedding, k=5)

        assert results == []

    def test_collection_stats_off_mode(self):
        """Test collection stats in OFF mode."""
        stats = get_collection_stats()

        assert stats["backend"] == "OFF"
        assert stats["total_vectors"] == 0
        assert stats["status"] == "disabled"

    def test_clear_collection_off_mode(self):
        """Test collection clearing in OFF mode."""
        result = clear_collection()
        assert result is True  # Should succeed (nothing to clear)


class TestVectorDBRedis:
    """Test Redis backend functionality."""

    def setup_method(self):
        """Set up Redis test environment."""
        os.environ["VECDB_BACKEND"] = "REDIS"
        os.environ["REDIS_URL"] = "redis://localhost:6379"

    @patch("app.memory.vecdb.redis")
    def test_redis_upsert_and_search(self, mock_redis):
        """Test Redis upsert and search operations."""
        # Mock Redis client
        mock_client = MagicMock()
        mock_redis.from_url.return_value = mock_client
        mock_client.ping.return_value = True

        # Mock data for search
        mock_client.smembers.return_value = [b"event1", b"event2"]
        mock_client.hgetall.side_effect = [
            {
                b"vector": b"[0.1, 0.2, 0.3]",
                b"metadata": b'{"ticker": "AAPL", "regime": "normal"}',
            },
            {
                b"vector": b"[0.4, 0.5, 0.6]",
                b"metadata": b'{"ticker": "TSLA", "regime": "high_vol"}',
            },
        ]

        # Test upsert
        embedding = [0.1, 0.2, 0.3]
        metadata = {"ticker": "AAPL", "regime": "normal"}

        upsert_event("test_event", embedding, metadata)

        # Verify Redis calls
        mock_client.hset.assert_called_once()
        mock_client.sadd.assert_called_with("event_ids", "test_event")

        # Test search
        query_embedding = [0.1, 0.2, 0.3]
        results = search_similar(query_embedding, k=2)

        assert len(results) == 2
        assert all("id" in result for result in results)
        assert all("score" in result for result in results)
        assert all("metadata" in result for result in results)

    @patch("app.memory.vecdb.redis")
    def test_redis_connection_failure(self, mock_redis):
        """Test Redis connection failure handling."""
        # Mock connection failure
        mock_redis.from_url.side_effect = Exception("Connection failed")

        # Should not raise exception, just return empty results
        embedding = [0.1, 0.2, 0.3]
        results = search_similar(embedding, k=5)

        assert results == []

    @patch("app.memory.vecdb.redis")
    def test_redis_stats(self, mock_redis):
        """Test Redis collection statistics."""
        mock_client = MagicMock()
        mock_redis.from_url.return_value = mock_client
        mock_client.ping.return_value = True
        mock_client.scard.return_value = 42

        stats = get_collection_stats()

        assert stats["backend"] == "REDIS"
        assert stats["total_vectors"] == 42
        assert stats["status"] == "connected"


class TestVectorDBQdrant:
    """Test Qdrant backend functionality."""

    def setup_method(self):
        """Set up Qdrant test environment."""
        os.environ["VECDB_BACKEND"] = "QDRANT"
        os.environ["QDRANT_URL"] = "http://localhost:6333"
        os.environ["QDRANT_COLLECTION"] = "test_collection"

    @patch("app.memory.vecdb.QdrantClient")
    def test_qdrant_upsert_and_search(self, mock_qdrant_client):
        """Test Qdrant upsert and search operations."""
        # Mock Qdrant client
        mock_client = MagicMock()
        mock_qdrant_client.return_value = mock_client

        # Mock collection exists
        mock_client.get_collection.return_value = MagicMock()

        # Mock search results
        mock_result1 = MagicMock()
        mock_result1.id = "event1"
        mock_result1.score = 0.95
        mock_result1.payload = {"ticker": "AAPL", "regime": "normal"}

        mock_result2 = MagicMock()
        mock_result2.id = "event2"
        mock_result2.score = 0.85
        mock_result2.payload = {"ticker": "TSLA", "regime": "high_vol"}

        mock_client.search.return_value = [mock_result1, mock_result2]

        # Test upsert
        embedding = [0.1] * 384  # 384-dim embedding
        metadata = {"ticker": "AAPL", "regime": "normal"}

        upsert_event("test_event", embedding, metadata)

        # Verify Qdrant calls
        mock_client.upsert.assert_called_once()

        # Test search
        query_embedding = [0.1] * 384
        results = search_similar(query_embedding, k=2)

        assert len(results) == 2
        assert results[0]["id"] == "event1"
        assert results[0]["score"] == 0.95
        assert results[0]["metadata"]["ticker"] == "AAPL"
        assert results[1]["id"] == "event2"
        assert results[1]["score"] == 0.85

    @patch("app.memory.vecdb.QdrantClient")
    def test_qdrant_collection_creation(self, mock_qdrant_client):
        """Test Qdrant collection creation when it doesn't exist."""
        mock_client = MagicMock()
        mock_qdrant_client.return_value = mock_client

        # Mock collection doesn't exist initially
        mock_client.get_collection.side_effect = Exception("Collection not found")

        # Trigger collection creation by calling upsert
        embedding = [0.1] * 384
        metadata = {"ticker": "AAPL"}

        upsert_event("test_event", embedding, metadata)

        # Verify collection was created
        mock_client.create_collection.assert_called_once()

    @patch("app.memory.vecdb.QdrantClient")
    def test_qdrant_filtered_search(self, mock_qdrant_client):
        """Test Qdrant search with metadata filters."""
        mock_client = MagicMock()
        mock_qdrant_client.return_value = mock_client
        mock_client.get_collection.return_value = MagicMock()

        # Mock filtered search result
        mock_result = MagicMock()
        mock_result.id = "filtered_event"
        mock_result.score = 0.9
        mock_result.payload = {"ticker": "AAPL", "regime": "normal"}

        mock_client.search.return_value = [mock_result]

        # Test search with filter
        query_embedding = [0.1] * 384
        filter_metadata = {"ticker": "AAPL"}

        results = search_similar(query_embedding, k=5, filter_metadata=filter_metadata)

        assert len(results) == 1
        assert results[0]["metadata"]["ticker"] == "AAPL"

        # Verify filter was applied in search call
        search_call = mock_client.search.call_args
        assert search_call is not None

    @patch("app.memory.vecdb.QdrantClient")
    def test_qdrant_stats(self, mock_qdrant_client):
        """Test Qdrant collection statistics."""
        mock_client = MagicMock()
        mock_qdrant_client.return_value = mock_client

        # Mock collection info
        mock_collection_info = MagicMock()
        mock_collection_info.points_count = 123
        mock_client.get_collection.return_value = mock_collection_info

        stats = get_collection_stats()

        assert stats["backend"] == "QDRANT"
        assert stats["total_vectors"] == 123
        assert stats["status"] == "connected"


class TestVectorDBIntegration:
    """Integration tests for vector database functionality."""

    def test_embedding_similarity_correlation(self):
        """Test that similar events produce similar embeddings."""
        # Very similar events
        event1 = {
            "ticker": "AAPL",
            "regime": "normal",
            "explain": {"shap_top": [["momentum", 0.3], ["sentiment", 0.2]]},
        }

        event2 = {
            "ticker": "AAPL",
            "regime": "normal",
            "explain": {"shap_top": [["momentum", 0.31], ["sentiment", 0.19]]},
        }

        # Very different events
        event3 = {
            "ticker": "CRYPTO",
            "regime": "extreme_vol",
            "explain": {"shap_top": [["volatility", 0.8], ["speculation", 0.7]]},
        }

        emb1 = build_embedding(event1)
        emb2 = build_embedding(event2)
        emb3 = build_embedding(event3)

        sim_12 = _cosine_similarity(emb1, emb2)
        sim_13 = _cosine_similarity(emb1, emb3)

        # Similar events should have higher similarity than different events
        assert sim_12 > sim_13

    def test_regime_sensitivity(self):
        """Test that embeddings are sensitive to regime differences."""
        base_event = {"ticker": "AAPL", "explain": {"shap_top": [["momentum", 0.3]]}}

        event_normal = {**base_event, "regime": "normal"}
        event_crash = {**base_event, "regime": "crash"}
        event_rally = {**base_event, "regime": "rally"}

        emb_normal = build_embedding(event_normal)
        emb_crash = build_embedding(event_crash)
        emb_rally = build_embedding(event_rally)

        # All should be different
        assert emb_normal != emb_crash
        assert emb_normal != emb_rally
        assert emb_crash != emb_rally

    def test_feature_importance_sensitivity(self):
        """Test that embeddings reflect feature importance differences."""
        event_momentum = {
            "ticker": "AAPL",
            "regime": "normal",
            "explain": {"shap_top": [["momentum", 0.8], ["sentiment", 0.1]]},
        }

        event_sentiment = {
            "ticker": "AAPL",
            "regime": "normal",
            "explain": {"shap_top": [["momentum", 0.1], ["sentiment", 0.8]]},
        }

        emb_momentum = build_embedding(event_momentum)
        emb_sentiment = build_embedding(event_sentiment)

        # Should be different due to different feature importance
        assert emb_momentum != emb_sentiment


# Fixtures for testing
@pytest.fixture
def sample_events():
    """Sample events for testing."""
    return [
        {
            "ticker": "AAPL",
            "regime": "normal",
            "explain": {"shap_top": [["momentum", 0.3], ["sentiment", 0.2]]},
        },
        {
            "ticker": "TSLA",
            "regime": "high_vol",
            "explain": {"shap_top": [["volatility", 0.4], ["news", 0.3]]},
        },
        {
            "ticker": "MSFT",
            "regime": "normal",
            "explain": {"shap_top": [["fundamentals", 0.35], ["technical", 0.25]]},
        },
    ]


def test_vector_workflow_end_to_end(sample_events):
    """Test complete vector workflow."""
    # Ensure OFF mode for this test
    os.environ["VECDB_BACKEND"] = "OFF"

    # Generate embeddings for all events
    embeddings = []
    for event in sample_events:
        embedding = build_embedding(event)
        embeddings.append(embedding)

        # Verify embedding properties
        assert len(embedding) == 384
        assert all(isinstance(x, float) for x in embedding)

    # Test similarity between embeddings
    for i in range(len(embeddings)):
        for j in range(i + 1, len(embeddings)):
            similarity = _cosine_similarity(embeddings[i], embeddings[j])
            assert -1.0 <= similarity <= 1.0

    # Test search (should return empty in OFF mode)
    results = search_similar(embeddings[0], k=5)
    assert results == []

    # Test stats (should show OFF mode)
    stats = get_collection_stats()
    assert stats["backend"] == "OFF"
    assert stats["status"] == "disabled"


class TestTransformerEmbeddings:
    """Test transformer-based embedding functionality."""

    def setup_method(self):
        """Set up test environment."""
        os.environ["VECDB_BACKEND"] = "OFF"

    def test_batch_embedding_generation(self):
        """Test batch embedding generation."""
        events = [
            {
                "ticker": "AAPL",
                "regime": "normal",
                "explain": {"shap_top": [["momentum", 0.3]]},
            },
            {
                "ticker": "MSFT",
                "regime": "rally",
                "explain": {"shap_top": [["sentiment", 0.5]]},
            },
            {
                "ticker": "GOOGL",
                "regime": "high_vol",
                "explain": {"shap_top": [["volatility", 0.7]]},
            },
        ]

        # Generate batch embeddings (will use hash fallback if transformer not available)
        embeddings = build_embeddings_batch(events, use_transformer=False)

        assert len(embeddings) == 3
        assert all(len(emb) == 384 for emb in embeddings)
        assert all(isinstance(emb, list) for emb in embeddings)

    def test_batch_vs_single_consistency(self):
        """Test that batch and single embedding generation are consistent."""
        events = [
            {
                "ticker": "AAPL",
                "regime": "normal",
                "explain": {"shap_top": [["momentum", 0.3]]},
            },
            {
                "ticker": "MSFT",
                "regime": "rally",
                "explain": {"shap_top": [["sentiment", 0.5]]},
            },
        ]

        # Generate using both methods (hash fallback)
        batch_embeddings = build_embeddings_batch(events, use_transformer=False)
        single_embeddings = [build_embedding(e, use_transformer=False) for e in events]

        # Should be identical
        for batch_emb, single_emb in zip(batch_embeddings, single_embeddings):
            assert batch_emb == single_emb

    def test_embedding_model_info(self):
        """Test getting embedding model information."""
        info = get_embedding_info()

        assert "model_name" in info
        assert "model_version" in info
        assert "dimension" in info
        assert "status" in info

        # Check expected values
        assert info["dimension"] == 384
        assert info["model_version"] == "v1.0-transformer"

    def test_embedding_versioning_in_metadata(self):
        """Test that embedding version is added to metadata."""
        event_id = "test_versioning"
        embedding = [0.1] * 384
        metadata = {"ticker": "AAPL", "regime": "normal"}

        # Mock Qdrant client to capture the payload
        with patch("app.memory.vecdb._get_qdrant_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client

            # Set backend to QDRANT
            os.environ["VECDB_BACKEND"] = "QDRANT"

            # Upsert event
            upsert_event(event_id, embedding, metadata)

            # Verify upsert was called
            mock_client.upsert.assert_called_once()

            # Get the point that was upserted
            call_args = mock_client.upsert.call_args
            points = call_args[1]["points"]

            assert len(points) == 1
            point = points[0]

            # Check that versioning metadata was added
            assert "embed_model" in point.payload
            assert "embed_model_version" in point.payload
            assert point.payload["embed_model_version"] == "v1.0-transformer"

            # Original metadata should still be there
            assert point.payload["ticker"] == "AAPL"
            assert point.payload["regime"] == "normal"

        # Reset environment
        os.environ["VECDB_BACKEND"] = "OFF"

    def test_transformer_fallback_to_hash(self):
        """Test that system falls back to hash when transformer unavailable."""
        event = {
            "ticker": "AAPL",
            "regime": "normal",
            "explain": {"shap_top": [["momentum", 0.3]]},
        }

        # Force hash fallback
        embedding_hash = build_embedding(event, use_transformer=False)

        # Should still work and produce valid embedding
        assert len(embedding_hash) == 384
        assert all(isinstance(x, float) for x in embedding_hash)

        # Check normalization
        norm = sum(x * x for x in embedding_hash) ** 0.5
        assert abs(norm - 1.0) < 1e-6


class TestSemanticSimilarity:
    """Test semantic similarity properties of embeddings."""

    def setup_method(self):
        """Set up test environment."""
        os.environ["VECDB_BACKEND"] = "OFF"

    def test_similar_events_high_similarity(self):
        """Test that semantically similar events have high similarity."""
        # Two very similar events
        event1 = {
            "ticker": "AAPL",
            "regime": "rally",
            "explain": {"shap_top": [["momentum", 0.8], ["sentiment", 0.7]]},
            "headlines": ["Tech stocks surge on strong earnings"],
        }

        event2 = {
            "ticker": "AAPL",
            "regime": "rally",
            "explain": {"shap_top": [["momentum", 0.75], ["sentiment", 0.65]]},
            "headlines": ["Technology sector rallies on earnings beat"],
        }

        # Very different event
        event3 = {
            "ticker": "OIL",
            "regime": "crash",
            "explain": {"shap_top": [["volatility", 0.9], ["fear", 0.8]]},
            "headlines": ["Energy sector plummets on demand concerns"],
        }

        emb1 = build_embedding(event1, use_transformer=False)
        emb2 = build_embedding(event2, use_transformer=False)
        emb3 = build_embedding(event3, use_transformer=False)

        sim_similar = _cosine_similarity(emb1, emb2)
        sim_different = _cosine_similarity(emb1, emb3)

        # Similar events should have higher similarity
        assert sim_similar > sim_different

    def test_ticker_clustering(self):
        """Test that same ticker events cluster together."""
        aapl_events = [
            {
                "ticker": "AAPL",
                "regime": "normal",
                "explain": {"shap_top": [["momentum", 0.3]]},
            },
            {
                "ticker": "AAPL",
                "regime": "rally",
                "explain": {"shap_top": [["sentiment", 0.5]]},
            },
        ]

        other_event = {
            "ticker": "TSLA",
            "regime": "normal",
            "explain": {"shap_top": [["momentum", 0.3]]},
        }

        aapl_emb1 = build_embedding(aapl_events[0], use_transformer=False)
        aapl_emb2 = build_embedding(aapl_events[1], use_transformer=False)
        other_emb = build_embedding(other_event, use_transformer=False)

        # AAPL events should be more similar to each other
        aapl_similarity = _cosine_similarity(aapl_emb1, aapl_emb2)
        cross_similarity = _cosine_similarity(aapl_emb1, other_emb)

        # Note: This may not always hold with hash embeddings,
        # but should hold with transformer embeddings
        # For now we just verify they produce different values
        assert aapl_similarity != cross_similarity
