"""
Vector Memory for ZiggyAI Memory & Knowledge System

Provides similarity search capabilities for retrieval-augmented decisions.
Supports Qdrant, Redis Vector, and fallback OFF mode.

EMBEDDING MODEL: Uses sentence-transformers for semantic embeddings.
Default model: all-MiniLM-L6-v2 (384-dim, fast, accurate)
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime
from typing import Any


# Configuration from environment
VECDB_BACKEND = os.getenv("VECDB_BACKEND", "OFF")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "ziggy_events")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
EMBED_MODEL = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")
EMBED_MODEL_VERSION = "v1.0-transformer"  # Version for tracking embedding model changes

logger = logging.getLogger(__name__)


# Global connections (lazy-loaded)
_qdrant_client = None
_redis_client = None
_embedding_model = None


def _get_qdrant_client():
    """Get Qdrant client, creating if needed."""
    global _qdrant_client
    if _qdrant_client is None:
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, PointStruct, VectorParams

            _qdrant_client = QdrantClient(url=QDRANT_URL)

            # Ensure collection exists
            try:
                _qdrant_client.get_collection(QDRANT_COLLECTION)
            except Exception:
                # Create collection with 384-dim vectors (miniLM-L6 size)
                _qdrant_client.create_collection(
                    collection_name=QDRANT_COLLECTION,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
                )
                logger.info(f"Created Qdrant collection: {QDRANT_COLLECTION}")

        except ImportError:
            logger.warning("qdrant-client not installed, falling back to OFF mode")
            return None
        except Exception as e:
            logger.warning(
                f"Failed to connect to Qdrant: {e}, falling back to OFF mode"
            )
            return None

    return _qdrant_client


def _get_redis_client():
    """Get Redis client, creating if needed."""
    global _redis_client
    if _redis_client is None:
        try:
            import redis

            _redis_client = redis.from_url(REDIS_URL)
            # Test connection
            _redis_client.ping()
        except ImportError:
            logger.warning("redis not installed, falling back to OFF mode")
            return None
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}, falling back to OFF mode")
            return None

    return _redis_client


def _get_embedding_model():
    """Get sentence-transformer model, loading if needed."""
    global _embedding_model
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer

            logger.info(f"Loading embedding model: {EMBED_MODEL}")
            _embedding_model = SentenceTransformer(EMBED_MODEL)
            logger.info(
                f"Embedding model loaded successfully. Dim: {_embedding_model.get_sentence_embedding_dimension()}"
            )
        except ImportError:
            logger.warning(
                "sentence-transformers not installed, falling back to hash-based embeddings"
            )
            return None
        except Exception as e:
            logger.warning(
                f"Failed to load embedding model: {e}, falling back to hash-based embeddings"
            )
            return None

    return _embedding_model


def build_embedding(event: dict[str, Any], use_transformer: bool = True) -> list[float]:
    """
    Build embedding vector from event data.

    Uses sentence-transformers for semantic embeddings by default.
    Falls back to hash-based embeddings if transformer unavailable.

    Args:
        event: Event dictionary with ticker, regime, explain, etc.
        use_transformer: Whether to use transformer model (default: True)

    Returns:
        Embedding vector (384-dimensional for all-MiniLM-L6-v2)
    """
    # Extract key features for embedding
    ticker = event.get("ticker", "")
    regime = event.get("regime", "")

    # Get top features from explain data
    explain = event.get("explain", {})
    shap_top = explain.get("shap_top", [])

    # Build feature string for semantic embedding
    features = []
    if ticker:
        features.append(f"ticker: {ticker}")
    if regime:
        features.append(f"regime: {regime}")

    # Add top SHAP features with better formatting
    for feature_name, importance in shap_top[:5]:  # Top 5 features
        features.append(f"{feature_name}: {importance:.3f}")

    # Add headlines if available
    headlines = event.get("headlines", [])
    if headlines:
        first_headline = str(headlines[0]) if headlines else ""
        features.append(f"news: {first_headline[:100]}")  # First 100 chars

    # Combine features into semantic text
    text = ". ".join(features)

    # Try to use transformer model first
    if use_transformer:
        model = _get_embedding_model()
        if model is not None:
            try:
                # Encode using transformer
                embedding = model.encode(text, convert_to_numpy=True)
                return embedding.tolist()
            except Exception as e:
                logger.warning(
                    f"Transformer encoding failed: {e}, falling back to hash"
                )

    # Fallback to hash-based embedding
    embedding = _hash_to_embedding(text, dim=384)
    return embedding


def build_embeddings_batch(
    events: list[dict[str, Any]], use_transformer: bool = True
) -> list[list[float]]:
    """
    Build embeddings for multiple events in a batch (more efficient).

    Args:
        events: List of event dictionaries
        use_transformer: Whether to use transformer model (default: True)

    Returns:
        List of embedding vectors
    """
    if not events:
        return []

    # Extract texts from all events
    texts = []
    for event in events:
        ticker = event.get("ticker", "")
        regime = event.get("regime", "")
        explain = event.get("explain", {})
        shap_top = explain.get("shap_top", [])
        headlines = event.get("headlines", [])

        features = []
        if ticker:
            features.append(f"ticker: {ticker}")
        if regime:
            features.append(f"regime: {regime}")

        for feature_name, importance in shap_top[:5]:
            features.append(f"{feature_name}: {importance:.3f}")

        if headlines:
            first_headline = str(headlines[0]) if headlines else ""
            features.append(f"news: {first_headline[:100]}")

        text = ". ".join(features)
        texts.append(text)

    # Try batch encoding with transformer
    if use_transformer:
        model = _get_embedding_model()
        if model is not None:
            try:
                # Batch encode using transformer
                embeddings = model.encode(
                    texts, convert_to_numpy=True, show_progress_bar=len(texts) > 10
                )
                return [emb.tolist() for emb in embeddings]
            except Exception as e:
                logger.warning(
                    f"Batch transformer encoding failed: {e}, falling back to hash"
                )

    # Fallback to hash-based embedding
    return [_hash_to_embedding(text, dim=384) for text in texts]


def _hash_to_embedding(text: str, dim: int = 384) -> list[float]:
    """
    Convert text to deterministic embedding using hash.
    This is a placeholder for real embedding models.

    Args:
        text: Input text to embed
        dim: Embedding dimension

    Returns:
        Normalized embedding vector
    """
    # Create multiple hashes to fill dimension
    embedding = []

    for i in range(0, dim, 32):  # SHA-256 gives 32 bytes
        hash_input = f"{text}:{i}"
        hash_bytes = hashlib.sha256(hash_input.encode()).digest()

        # Convert bytes to floats
        for j in range(0, min(32, dim - i), 4):
            if j + 4 <= len(hash_bytes):
                # Convert 4 bytes to float
                int_val = int.from_bytes(hash_bytes[j : j + 4], byteorder="big")
                # Normalize to [-1, 1]
                float_val = (int_val / (2**31)) - 1.0
                embedding.append(float_val)

    # Ensure exact dimension
    embedding = embedding[:dim]
    while len(embedding) < dim:
        embedding.append(0.0)

    # L2 normalize
    norm = sum(x * x for x in embedding) ** 0.5
    if norm > 0:
        embedding = [x / norm for x in embedding]

    return embedding


def upsert_event(event_id: str, vec: list[float], metadata: dict[str, Any]) -> None:
    """
    Upsert an event vector into the vector database.

    Args:
        event_id: Unique event identifier
        vec: Embedding vector
        metadata: Additional metadata to store
    """
    # Add embedding model version to metadata
    metadata_with_version = {
        **metadata,
        "embed_model": EMBED_MODEL,
        "embed_model_version": EMBED_MODEL_VERSION,
    }

    if VECDB_BACKEND == "QDRANT":
        client = _get_qdrant_client()
        if client is None:
            return

        try:
            from qdrant_client.models import PointStruct

            point = PointStruct(id=event_id, vector=vec, payload=metadata_with_version)

            client.upsert(collection_name=QDRANT_COLLECTION, points=[point])

        except Exception as e:
            logger.error(f"Failed to upsert to Qdrant: {e}")

    elif VECDB_BACKEND == "REDIS":
        client = _get_redis_client()
        if client is None:
            return

        try:
            # Store as hash with vector and metadata
            key = f"event:{event_id}"
            data = {
                "vector": json.dumps(vec),
                "metadata": json.dumps(metadata_with_version),
                "updated_at": datetime.utcnow().isoformat(),
            }
            client.hset(key, mapping=data)

            # Add to search index (simplified)
            client.sadd("event_ids", event_id)

        except Exception as e:
            logger.error(f"Failed to upsert to Redis: {e}")

    elif VECDB_BACKEND == "OFF":
        # No-op for OFF mode
        pass

    else:
        logger.warning(f"Unknown VECDB_BACKEND: {VECDB_BACKEND}")


def search_similar(
    vec: list[float], k: int = 10, filter_metadata: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    """
    Search for similar events based on vector similarity.

    Args:
        vec: Query vector
        k: Number of results to return
        filter_metadata: Optional metadata filters

    Returns:
        List of similar events with id, score, and metadata
    """
    if VECDB_BACKEND == "QDRANT":
        client = _get_qdrant_client()
        if client is None:
            return []

        try:
            # Build filter if provided
            query_filter = None
            if filter_metadata:
                from qdrant_client.models import FieldCondition, Filter, MatchValue

                conditions = []
                for key, value in filter_metadata.items():
                    conditions.append(
                        FieldCondition(key=key, match=MatchValue(value=value))
                    )
                if conditions:
                    query_filter = Filter(must=conditions)

            # Perform search
            results = client.search(
                collection_name=QDRANT_COLLECTION,
                query_vector=vec,
                limit=k,
                query_filter=query_filter,
            )

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append(
                    {
                        "id": str(result.id),
                        "score": float(result.score),
                        "metadata": result.payload or {},
                    }
                )

            return formatted_results

        except Exception as e:
            logger.error(f"Failed to search Qdrant: {e}")
            return []

    elif VECDB_BACKEND == "REDIS":
        client = _get_redis_client()
        if client is None:
            return []

        try:
            # Get all event IDs
            event_ids = client.smembers("event_ids")

            # Calculate similarities (brute force for simplicity)
            similarities = []
            for event_id in event_ids:
                key = f"event:{event_id.decode()}"
                event_data = client.hgetall(key)

                if b"vector" in event_data:
                    stored_vec = json.loads(event_data[b"vector"].decode())
                    metadata = json.loads(event_data[b"metadata"].decode())

                    # Apply filter if provided
                    if filter_metadata:
                        matches = all(
                            metadata.get(k) == v for k, v in filter_metadata.items()
                        )
                        if not matches:
                            continue

                    # Calculate cosine similarity
                    similarity = _cosine_similarity(vec, stored_vec)
                    similarities.append(
                        {
                            "id": event_id.decode(),
                            "score": similarity,
                            "metadata": metadata,
                        }
                    )

            # Sort by similarity and return top k
            similarities.sort(key=lambda x: x["score"], reverse=True)
            return similarities[:k]

        except Exception as e:
            logger.error(f"Failed to search Redis: {e}")
            return []

    elif VECDB_BACKEND == "OFF":
        # Return empty results for OFF mode
        return []

    else:
        logger.warning(f"Unknown VECDB_BACKEND: {VECDB_BACKEND}")
        return []


def _cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """
    Calculate cosine similarity between two vectors.

    Args:
        vec1: First vector
        vec2: Second vector

    Returns:
        Cosine similarity score
    """
    if len(vec1) != len(vec2):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = sum(a * a for a in vec1) ** 0.5
    norm2 = sum(b * b for b in vec2) ** 0.5

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot_product / (norm1 * norm2)


def get_embedding_info() -> dict[str, Any]:
    """
    Get information about the embedding model.

    Returns:
        Dictionary with embedding model information
    """
    info = {
        "model_name": EMBED_MODEL,
        "model_version": EMBED_MODEL_VERSION,
        "dimension": 384,  # Default for all-MiniLM-L6-v2
        "status": "not_loaded",
    }

    model = _get_embedding_model()
    if model is not None:
        info["status"] = "loaded"
        try:
            info["dimension"] = model.get_sentence_embedding_dimension()
        except Exception:
            pass

    return info


def get_collection_stats() -> dict[str, Any]:
    """
    Get statistics about the vector collection.

    Returns:
        Dictionary with collection statistics
    """
    stats = {
        "backend": VECDB_BACKEND,
        "total_vectors": 0,
        "status": "unknown",
        "embedding_model": get_embedding_info(),
    }

    if VECDB_BACKEND == "QDRANT":
        client = _get_qdrant_client()
        if client is None:
            stats["status"] = "disconnected"
            return stats

        try:
            collection_info = client.get_collection(QDRANT_COLLECTION)
            stats["total_vectors"] = collection_info.points_count
            stats["status"] = "connected"
        except Exception as e:
            stats["status"] = f"error: {e}"

    elif VECDB_BACKEND == "REDIS":
        client = _get_redis_client()
        if client is None:
            stats["status"] = "disconnected"
            return stats

        try:
            event_count = client.scard("event_ids")
            stats["total_vectors"] = event_count
            stats["status"] = "connected"
        except Exception as e:
            stats["status"] = f"error: {e}"

    elif VECDB_BACKEND == "OFF":
        stats["status"] = "disabled"

    return stats


def clear_collection() -> bool:
    """
    Clear all vectors from the collection (for testing).

    Returns:
        True if successful, False otherwise
    """
    if VECDB_BACKEND == "QDRANT":
        client = _get_qdrant_client()
        if client is None:
            return False

        try:
            client.delete_collection(QDRANT_COLLECTION)
            # Recreate empty collection
            from qdrant_client.models import Distance, VectorParams

            client.create_collection(
                collection_name=QDRANT_COLLECTION,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )
            return True
        except Exception as e:
            logger.error(f"Failed to clear Qdrant collection: {e}")
            return False

    elif VECDB_BACKEND == "REDIS":
        client = _get_redis_client()
        if client is None:
            return False

        try:
            # Get all event IDs and delete them
            event_ids = client.smembers("event_ids")
            if event_ids:
                keys = [f"event:{event_id.decode()}" for event_id in event_ids]
                client.delete(*keys)
            client.delete("event_ids")
            return True
        except Exception as e:
            logger.error(f"Failed to clear Redis collection: {e}")
            return False

    elif VECDB_BACKEND == "OFF":
        return True  # Nothing to clear

    return False


# --- Compatibility for legacy tests that patch `redis` and `QdrantClient` ---
try:
    import redis  # type: ignore
except Exception:
    redis = None  # type: ignore

try:
    from qdrant_client import QdrantClient  # type: ignore
except Exception:
    QdrantClient = None  # type: ignore

__all__ = ["QdrantClient", "redis"]
