from typing import Any

from pypdf import PdfReader

from app.rag.chunking import chunk_document
from app.rag.embeddings import embed_texts
from app.rag.vectorstore import ensure_collection, get_client, upsert_texts


def extract_pdf_text(file_path: str) -> str:
    reader = PdfReader(file_path)
    parts = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n".join(parts)


def ingest_pdf(file_path: str, source_url: str | None = None) -> dict[str, Any]:
    text = extract_pdf_text(file_path)
    chunks = chunk_document(text)
    vecs = embed_texts(chunks)
    metas = [
        {"source": "pdf", "url": source_url, "title": source_url or file_path, "type": "pdf"}
        for _ in chunks
    ]
    client = get_client()
    ensure_collection(client)
    upsert_texts(client, chunks, vecs, metas)
    return {"chunks_indexed": len(chunks), "source": source_url or file_path}
