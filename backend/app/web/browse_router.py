# app/web/browse_router.py
from __future__ import annotations

import os
from typing import Any

import httpx
from fastapi import APIRouter, Query


router = APIRouter(tags=["browse-legacy"])


def _use_tavily() -> bool:
    prov = (os.getenv("SEARCH_PROVIDER") or "").lower()
    return prov in {"tavily", "tvly"} and bool(os.getenv("TAVILY_API_KEY"))


@router.get("/web/browse/search")
def browse_search(q: str = Query(..., min_length=2), max_results: int = 5):
    """
    Legacy router mounted at /web/browse/search to avoid conflicting with /browse/search.
    Prefer app.api.routes:/browse/search which supports provider overrides.
    """
    q = q.strip()
    max_results = max(1, min(int(max_results or 5), 20))
    results: list[dict[str, Any]] = []
    provider = "duckduckgo"

    if _use_tavily():
        provider = "tavily"
        api_key = os.getenv("TAVILY_API_KEY")
        payload = {
            "api_key": api_key,
            "query": q,
            "search_depth": "basic",
            "include_domains": [],
            "max_results": max_results,
            "include_answer": False,
        }
        with httpx.Client(timeout=30.0) as c:
            r = c.post("https://api.tavily.com/search", json=payload)
            r.raise_for_status()
            data = r.json()
        for item in data.get("results") or []:
            results.append(
                {
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "snippet": item.get("content") or item.get("snippet") or "",
                }
            )
    else:
        try:
            from duckduckgo_search import DDGS  # type: ignore
        except Exception as e:
            return {
                "provider": "duckduckgo",
                "query": q,
                "results": [],
                "error": f"duckduckgo-search not installed: {e}",
                "hint": "pip install duckduckgo-search",
            }

        REGION = os.getenv("SEARCH_REGION", "us-en")
        SAFE = os.getenv("SEARCH_SAFE", "moderate")  # off|moderate|strict
        TIME = os.getenv("SEARCH_TIME", "")  # "", "d", "w", "m", "y"

        with DDGS() as ddgs:
            for item in ddgs.text(
                q,
                region=REGION,
                safesearch=SAFE,
                timelimit=TIME or None,
                max_results=max_results,
            ):
                results.append(
                    {
                        "title": item.get("title"),
                        "url": item.get("href"),
                        "snippet": item.get("body") or "",
                    }
                )

    return {"provider": provider, "query": q, "results": results}


@router.get("/web/browse")
def browse_alias(q: str = Query(..., min_length=2), max_results: int = 5):
    return browse_search(q=q, max_results=max_results)
