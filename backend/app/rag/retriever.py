from typing import Any

from app.rag.embeddings import embed_query
from app.rag.vectorstore import get_client, search
from app.utils.text import clean_text


def retrieve(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    vec = embed_query(query)
    client = get_client()
    results = search(client, vec, top_k=top_k)
    for r in results:
        r["text"] = clean_text(r.get("text", ""))
    return results


def stitch_answer(
    query: str, passages: list[dict[str, Any]], max_chars: int = 1000
) -> str:
    if not passages:
        return "I couldn't find anything relevant yet. Try ingesting sources or broadening the query."
    acc, total = [], 0
    for p in passages:
        t = p.get("text", "")
        take = t[: max_chars - total]
        if not take:
            continue
        acc.append(take)
        total += len(take)
        if total >= max_chars:
            break
    return "\n\n".join(acc)
