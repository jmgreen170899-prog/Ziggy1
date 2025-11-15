import logging
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Make Qdrant optional
try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as qmodels

    QDRANT_AVAILABLE = True
except Exception as e:
    logger.warning("Qdrant unavailable, continuing without vector store: %s", e)

    # Create dummy classes for type compatibility
    class QdrantClient:
        def __init__(self, *args, **kwargs):
            pass

        def collection_exists(self, *args, **kwargs):
            return False

        def create_collection(self, *args, **kwargs):
            pass

        def upsert(self, *args, **kwargs):
            pass

        def search(self, *args, **kwargs):
            return []

        def delete_collection(self, *args, **kwargs):
            pass

    class _DummyModels:
        class VectorParams:
            def __init__(self, *args, **kwargs):
                pass

        class Distance:
            COSINE = "cosine"

        class PointStruct:
            def __init__(self, *args, **kwargs):
                pass

    qmodels = _DummyModels()
    QDRANT_AVAILABLE = False


def get_client():
    if not QDRANT_AVAILABLE:
        logger.warning("Qdrant client requested but not available")
        return None
    s = get_settings()
    try:
        return QdrantClient(url=s.QDRANT_URL, api_key=s.QDRANT_API_KEY)
    except Exception as e:
        logger.warning("Failed to connect to Qdrant: %s", e)
        return None


def ensure_collection(
    client: QdrantClient, collection: str | None = None, dim: int = 768
):
    if not QDRANT_AVAILABLE or client is None:
        logger.warning("Qdrant not available, skipping collection creation")
        return "dummy_collection"

    s = get_settings()
    coll = collection or s.QDRANT_COLLECTION
    try:
        if not client.collection_exists(coll):
            client.create_collection(
                collection_name=coll,
                vectors_config=qmodels.VectorParams(
                    size=dim, distance=qmodels.Distance.COSINE
                ),
            )
    except Exception as e:
        logger.warning("Failed to ensure collection: %s", e)
    return coll


def upsert_texts(
    client: QdrantClient,
    texts: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict[str, Any]],
    ids: list[str] | None = None,
    collection: str | None = None,
):
    if not QDRANT_AVAILABLE or client is None:
        logger.warning("Qdrant not available, skipping text upsert")
        return

    try:
        s = get_settings()
        coll = collection or s.QDRANT_COLLECTION
        ensure_collection(client, coll, len(embeddings[0]) if embeddings else 768)
        points = []
        for i, (t, e, m) in enumerate(zip(texts, embeddings, metadatas, strict=True)):
            pid = ids[i] if ids else str(i)
            payload = {"text": t, **m}
            points.append(qmodels.PointStruct(id=pid, vector=e, payload=payload))
        client.upsert(collection_name=coll, points=points)
    except Exception as e:
        logger.warning("Failed to upsert texts: %s", e)


def search(
    client: QdrantClient,
    query_vector: list[float],
    top_k: int = 5,
    collection: str | None = None,
):
    if not QDRANT_AVAILABLE or client is None:
        logger.warning("Qdrant not available, returning empty search results")
        return []

    try:
        s = get_settings()
        coll = collection or s.QDRANT_COLLECTION
        res = client.search(
            collection_name=coll,
            query_vector=query_vector,
            limit=top_k,
        )
        return [
            {
                "id": pt.id,
                "payload": pt.payload,
                "score": pt.score,
            }
            for pt in res
        ]
    except Exception as e:
        logger.warning("Search failed: %s", e)
        return []


def reset_collection(
    client: QdrantClient, collection: str | None = None, dim: int = 768
):
    if not QDRANT_AVAILABLE or client is None:
        logger.warning("Qdrant not available, skipping collection reset")
        return

    try:
        s = get_settings()
        coll = collection or s.QDRANT_COLLECTION
        if client.collection_exists(coll):
            client.delete_collection(coll)
        ensure_collection(client, coll, dim)
    except Exception as e:
        logger.warning("Failed to reset collection: %s", e)
