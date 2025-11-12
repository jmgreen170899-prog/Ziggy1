from app.core.config import get_settings
from app.utils.text import chunk_text, clean_text


def chunk_document(text: str) -> list[str]:
    s = get_settings()
    text = clean_text(text or "")
    return chunk_text(text, s.CHUNK_SIZE, s.CHUNK_OVERLAP)
