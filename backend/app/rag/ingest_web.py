from typing import Any

import requests
import trafilatura
from duckduckgo_search import DDGS

from app.rag.chunking import chunk_document
from app.rag.embeddings import embed_texts
from app.rag.vectorstore import ensure_collection, get_client, upsert_texts


def search_web(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    out = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            out.append({"title": r.get("title"), "url": r.get("href"), "snippet": r.get("body")})
    return out


def fetch_and_extract(url: str) -> str:
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return ""
        text = trafilatura.extract(downloaded, include_comments=False, include_tables=False) or ""
        return text
    except Exception:
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            return trafilatura.extract(resp.text) or ""
        except Exception:
            return ""


def ingest_from_web(query: str, max_results: int = 5) -> dict[str, Any]:
    results = search_web(query, max_results=max_results)
    client = get_client()
    ensure_collection(client)

    total_chunks, sources = 0, []
    for r in results:
        url = r.get("url")
        title = r.get("title") or url
        if not url:
            continue
        text = fetch_and_extract(url)
        if not text:
            continue
        chunks = chunk_document(text)
        if not chunks:
            continue
        vecs = embed_texts(chunks)
        metas = [{"source": "web", "url": url, "title": title, "type": "web"} for _ in chunks]
        upsert_texts(client, chunks, vecs, metas)
        total_chunks += len(chunks)
        sources.append({"title": title, "url": url, "chunks": len(chunks)})
    return {"sources_indexed": sources, "chunks_indexed": total_chunks}
