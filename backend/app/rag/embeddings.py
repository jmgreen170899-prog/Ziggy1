from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.core.config import get_settings


@lru_cache
def _get_model():
    settings = get_settings()
    model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return model, settings.EMBEDDING_INSTRUCTION


def embed_texts(texts: list[str]) -> list[list[float]]:
    model, instruction = _get_model()
    inst_texts = [instruction + (t or "") for t in texts]
    vecs = model.encode(inst_texts, normalize_embeddings=True).tolist()
    return vecs


def embed_query(query: str) -> list[float]:
    return embed_texts([query])[0]
