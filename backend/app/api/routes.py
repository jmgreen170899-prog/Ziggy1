# backend/app/api/routes.py
from __future__ import annotations

import os
from typing import Any

import httpx
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


router = APIRouter(tags=["core"])

# ───────────────────────────── Models ─────────────────────────────


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5


class Citation(BaseModel):
    url: str | None = None
    title: str | None = None
    score: float = 0.0
    snippet: str = ""


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    contexts: list[str] = Field(default_factory=list)


class WebIngestRequest(BaseModel):
    query: str
    max_results: int = 5


class WebIngestResponse(BaseModel):
    chunks_indexed: int
    sources_indexed: list[dict[str, Any]] = Field(default_factory=list)


class AgentRequest(BaseModel):
    query: str
    max_steps: int = 5
    approvals: bool = False  # if True, return pending_approval instead of executing


class AgentResponse(BaseModel):
    final: str | None = None
    steps: list[dict[str, Any]] = Field(default_factory=list)
    pending_approval: dict[str, Any] | None = None


class WatchReq(BaseModel):
    topic: str
    cron: str = "0 9 * * *"  # default: 09:00 daily
    job_id: str | None = None


class CancelReq(BaseModel):
    job_id: str


# ───────────────────────────── Helpers ─────────────────────────────


def _get_settings():
    """Import settings only if available."""
    try:
        from app.core.config import get_settings  # type: ignore

        return get_settings()
    except Exception:

        class _S:  # minimal shim
            SEARCH_PROVIDER = os.getenv("SEARCH_PROVIDER", "duckduckgo")
            TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
            REDIS_URL = os.getenv("REDIS_URL")
            POSTGRES_DSN = os.getenv("DATABASE_URL")

        return _S()


# ───────────────────────────── Health / Debug ─────────────────────────────
# Use a different path than the root /health defined in main.py
@router.get("/core/health")
def core_health():
    """
    Checks FastAPI + optional dependencies (Qdrant, Postgres, Redis, Scheduler).
    Returns {"status":"ok","details":{...}}.
    """
    s = _get_settings()
    details: dict[str, Any] = {"fastapi": "ok"}

    # Qdrant (optional)
    try:
        from app.rag.vectorstore import ensure_collection, get_client  # type: ignore

        client = get_client()
        ensure_collection(client)
        details["qdrant"] = "ok"
    except Exception as e:
        details["qdrant"] = f"unavailable: {e!s}"

    # Postgres (optional)
    if getattr(s, "POSTGRES_DSN", None):
        try:
            import psycopg2  # type: ignore

            conn = psycopg2.connect(s.POSTGRES_DSN)
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchall()
            conn.close()
            details["postgres"] = "ok"
        except Exception as e:
            details["postgres"] = f"error: {e!s}"
    else:
        details["postgres"] = "not-configured"

    # Redis (optional)
    if getattr(s, "REDIS_URL", None):
        try:
            import redis  # type: ignore

            r = redis.from_url(s.REDIS_URL)
            r.ping()
            details["redis"] = "ok"
        except Exception as e:
            details["redis"] = f"error: {e!s}"
    else:
        details["redis"] = "not-configured"

    # Scheduler (optional)
    try:
        from app.tasks.scheduler import start_scheduler  # type: ignore

        start_scheduler()
        details["scheduler"] = "ok"
    except Exception as e:
        details["scheduler"] = f"unavailable: {e!s}"

    return {"status": "ok", "details": details}


# ───────────────────────────── RAG Query ─────────────────────────────


@router.post("/query", response_model=QueryResponse)
def api_query(req: QueryRequest) -> QueryResponse:
    """
    RAG query over the local vector store.
    Lazily imports RAG pieces so the API still boots when RAG is not configured.
    """
    try:
        from app.rag.retriever import retrieve, stitch_answer  # type: ignore
    except Exception as e:
        raise HTTPException(status_code=501, detail=f"RAG not available: {e!s}")

    passages = retrieve(req.query, top_k=req.top_k)
    answer = stitch_answer(req.query, passages)

    citations: list[Citation] = []
    contexts: list[str] = []
    for p in passages:
        citations.append(
            Citation(
                url=p.get("url"),
                title=p.get("title"),
                score=float(p.get("score", 0.0)),
                snippet=(p.get("text", "")[:250]),
            )
        )
        contexts.append(p.get("text", ""))
    return QueryResponse(answer=answer, citations=citations, contexts=contexts)


# ───────────────────────────── Ingestion ─────────────────────────────


@router.post("/ingest/web", response_model=WebIngestResponse)
def api_ingest_web(req: WebIngestRequest) -> WebIngestResponse:
    try:
        from app.rag.ingest_web import ingest_from_web  # type: ignore
    except Exception as e:
        raise HTTPException(status_code=501, detail=f"Ingest (web) not available: {e!s}")

    res = ingest_from_web(req.query, max_results=req.max_results)
    return WebIngestResponse(**res)


@router.post("/ingest/pdf")
def api_ingest_pdf(file: UploadFile = File(...), source_url: str | None = Form(None)):
    try:
        from app.rag.ingest_pdf import ingest_pdf  # type: ignore
    except Exception as e:
        raise HTTPException(status_code=501, detail=f"Ingest (pdf) not available: {e!s}")

    import os as _os
    import tempfile

    suffix = _os.path.splitext(file.filename or "doc.pdf")[1] or ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file.file.read())
        tmp.flush()
        path = tmp.name
    try:
        res = ingest_pdf(path, source_url=source_url)
        return res
    finally:
        try:
            _os.remove(path)
        except Exception:
            pass


@router.post("/reset")
def api_reset():
    try:
        from app.rag.vectorstore import get_client, reset_collection  # type: ignore
    except Exception as e:
        raise HTTPException(status_code=501, detail=f"Vector store not available: {e!s}")

    client = get_client()
    reset_collection(client)
    return {"status": "ok", "message": "Qdrant collection reset"}


# ───────────────────────────── Agent (optional) ─────────────────────────────


@router.post("/agent", response_model=AgentResponse)
def api_agent(req: AgentRequest):
    """
    Tool-using LLM loop: lets Ziggy plan and call tools (web search/fetch, KB retrieve).
    Set approvals=True to return the first tool action for human approval instead of executing.
    """
    try:
        from app.agent.agent import run_agent  # type: ignore
    except Exception as e:
        raise HTTPException(status_code=501, detail=f"Agent not available: {e!s}")

    try:
        result = run_agent(req.query, max_steps=req.max_steps, approvals=req.approvals)
        return result  # shaped like AgentResponse
    except Exception as e:
        import logging

        logging.getLogger("ziggy").exception("AGENT_ERROR")
        raise HTTPException(status_code=500, detail=str(e))


# ───────────────────────────── Scheduler / tasks (optional) ─────────────────────────────


@router.post("/tasks/watch")
def api_tasks_watch(req: WatchReq):
    """
    Schedule a repeating agent run for a topic.
    cron examples:
      - '0 9 * * *'     -> every day at 09:00
      - '0 */2 * * *'   -> every 2 hours
      - '30 8 * * 1-5'  -> 08:30 on weekdays
    """
    try:
        from app.tasks.scheduler import schedule_watch_topic, start_scheduler  # type: ignore
    except Exception as e:
        raise HTTPException(status_code=501, detail=f"Scheduler not available: {e!s}")

    start_scheduler()
    jid = schedule_watch_topic(req.topic, req.cron, req.job_id)
    return {"status": "scheduled", "job_id": jid, "topic": req.topic, "cron": req.cron}


@router.get("/tasks")
def api_tasks_list():
    """List scheduled jobs."""
    try:
        from app.tasks.scheduler import list_jobs, start_scheduler  # type: ignore
    except Exception as e:
        raise HTTPException(status_code=501, detail=f"Scheduler not available: {e!s}")

    start_scheduler()
    return {"jobs": list_jobs()}


@router.delete("/tasks")
def api_tasks_cancel(req: CancelReq):
    """Cancel a job by id."""
    try:
        from app.tasks.scheduler import remove_job, start_scheduler  # type: ignore
    except Exception as e:
        raise HTTPException(status_code=501, detail=f"Scheduler not available: {e!s}")

    start_scheduler()
    remove_job(req.job_id)
    return {"status": "cancelled", "job_id": req.job_id}


# ───────────────────────────── Simple web browse (search) ─────────────────────────────


def _which_provider(override: str | None = None) -> str:
    """
    Decide which provider to use.
    - prefer explicit per-request override (?provider=...)
    - else use settings (Pydantic) if available
    - else fallback to environment variable
    Defaults to 'duckduckgo' when unknown.
    """
    s = _get_settings()
    prov = (
        (override or "").strip().lower()
        or (getattr(s, "SEARCH_PROVIDER", None) or "").strip().lower()
        or (os.getenv("SEARCH_PROVIDER") or "").strip().lower()
        or "duckduckgo"
    )
    return "tavily" if prov in {"tavily", "tvly"} else "duckduckgo"


@router.get("/browse/search")
def browse_search(
    q: str = Query(..., min_length=2),
    max_results: int = 5,
    provider: str | None = Query(
        None, description="force 'tavily' or 'duckduckgo' for this request"
    ),
    tavily_key: str | None = Query(
        None, description="optional: override TAVILY_API_KEY for this request"
    ),
):
    """
    Lightweight search endpoint used by the UI's /browse command.
    Providers:
      - Tavily (if chosen; requires an API key)
      - DuckDuckGo (default, no API key)

    Always returns 200 with an {error: "..."} on failure.
    """
    q = q.strip()
    max_results = max(1, min(int(max_results or 5), 20))

    try:
        results: list[dict[str, Any]] = []
        used_provider = _which_provider(provider)
        # debug visibility via logger
        import logging

        logging.getLogger("ziggy").debug("[browse] provider=%s q=%r", used_provider, q)

        if used_provider == "tavily":
            s = _get_settings()
            api_key = (
                tavily_key or getattr(s, "TAVILY_API_KEY", None) or os.getenv("TAVILY_API_KEY")
            )
            if not api_key:
                return JSONResponse(
                    {
                        "provider": "tavily",
                        "query": q,
                        "results": [],
                        "error": "Missing TAVILY_API_KEY (pass ?tavily_key=..., set it in .env/settings).",
                    },
                    status_code=200,
                )

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
                        "snippet": (item.get("content") or item.get("snippet") or ""),
                    }
                )

        else:
            # DuckDuckGo (pip install duckduckgo-search)
            try:
                from duckduckgo_search import DDGS  # type: ignore
            except Exception as e:
                return JSONResponse(
                    {
                        "provider": "duckduckgo",
                        "query": q,
                        "results": [],
                        "error": f"duckduckgo-search not installed: {e}",
                        "hint": "pip install duckduckgo-search",
                    },
                    status_code=200,
                )

            REGION = os.getenv("SEARCH_REGION", "wt-wt")  # e.g. "us-en"
            SAFE = os.getenv("SEARCH_SAFE", "moderate")  # off|moderate|strict
            TIME = os.getenv("SEARCH_TIME", "")  # "", "d", "w", "m", "y"
            BACKEND = (
                os.getenv("SEARCH_BACKEND") or "html"
            ).lower()  # "html" avoids many rate limits

            with DDGS() as ddgs:
                for item in ddgs.text(
                    q,
                    region=REGION,
                    safesearch=SAFE,
                    timelimit=TIME or None,
                    backend=BACKEND,
                    max_results=max_results,
                ):
                    results.append(
                        {
                            "title": item.get("title"),
                            "url": item.get("href"),
                            "snippet": item.get("body") or "",
                        }
                    )

        return {"provider": used_provider, "query": q, "results": results}

    except Exception as e:
        import logging

        logging.getLogger("ziggy").exception("BROWSE_ERROR")
        return JSONResponse(
            {"provider": _which_provider(provider), "query": q, "results": [], "error": str(e)},
            status_code=200,
        )


@router.get("/browse")
def browse_alias(
    q: str = Query(..., min_length=2),
    max_results: int = 5,
    provider: str | None = None,
    tavily_key: str | None = None,
):
    return browse_search(q=q, max_results=max_results, provider=provider, tavily_key=tavily_key)
