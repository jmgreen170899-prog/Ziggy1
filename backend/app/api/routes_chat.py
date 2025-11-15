# backend/app/api/routes_chat.py
from __future__ import annotations

import os
from collections.abc import AsyncIterator
from typing import Any, Literal

import httpx  # type: ignore
from fastapi import APIRouter, HTTPException  # type: ignore
from fastapi.responses import JSONResponse, StreamingResponse  # type: ignore
from pydantic import BaseModel, Field, field_validator  # type: ignore


router = APIRouter(prefix="/chat", tags=["chat"])


# ──────────────────────────── Response Models ────────────────────────────


class ChatHealthResponse(BaseModel):
    """Chat service health check response."""

    provider: str = Field(..., description="LLM provider (openai or local)")
    base: str = Field(..., description="Base URL for the provider")
    model: str = Field(..., description="Model being used")
    ok: bool = Field(..., description="Health check passed")
    status_code: int | None = Field(None, description="HTTP status code from provider")
    detail: str | None = Field(None, description="Error details if health check failed")
    error: str | None = Field(None, description="Exception error if check failed")


class ChatConfigResponse(BaseModel):
    """Chat service configuration response."""

    provider: str = Field(..., description="LLM provider (openai or local)")
    base: str = Field(..., description="Base URL for the provider")
    default_model: str = Field(..., description="Default model name")
    timeout_sec: float = Field(..., description="Request timeout in seconds")
    use_openai: bool = Field(..., description="Whether OpenAI is being used")


# ──────────────────────────── Config helpers ────────────────────────────


def _env(name: str, default: str | None = None) -> str | None:
    v = os.getenv(name)
    return v if (v is not None and v != "") else default


USE_OPENAI = (_env("USE_OPENAI", "false") or "false").lower() in {"1", "true", "yes"}
OPENAI_BASE = _env("OPENAI_BASE", "https://api.openai.com/v1")
OPENAI_API_KEY = _env("OPENAI_API_KEY")
OPENAI_MODEL = _env("OPENAI_MODEL", "gpt-4o-mini")

LOCAL_BASE = _env("LOCAL_LLM_BASE_URL", "http://localhost:11434/v1")  # Ollama default
LOCAL_MODEL = _env("LOCAL_LLM_MODEL", "llama3.2:3b")
LOCAL_TEMP = float(_env("LOCAL_LLM_TEMPERATURE", "0.6") or "0.6")
LOCAL_MAXTOK = int(_env("LOCAL_LLM_MAX_TOKENS", "1024") or "1024")

REQUEST_TIMEOUT = float(_env("CHAT_REQUEST_TIMEOUT_SEC", "90") or "90")


def _provider_base() -> str:
    return (
        (OPENAI_BASE or LOCAL_BASE or "")
        if USE_OPENAI
        else (LOCAL_BASE or OPENAI_BASE or "")
    )


def _provider_model() -> str:
    return (
        (OPENAI_MODEL or LOCAL_MODEL or "")
        if USE_OPENAI
        else (LOCAL_MODEL or OPENAI_MODEL or "")
    )


def _provider_auth_header() -> str:
    # Local servers generally ignore this header, but many expect that it exists.
    if USE_OPENAI:
        if not OPENAI_API_KEY:
            raise HTTPException(
                status_code=400, detail="OPENAI_API_KEY is not set but USE_OPENAI=true"
            )
        return f"Bearer {OPENAI_API_KEY}"
    return "Bearer local"


# ──────────────────────────── Schemas ────────────────────────────

Role = Literal["system", "user", "assistant"]


class ChatMessage(BaseModel):
    role: Role
    content: str

    @field_validator("content", mode="before")
    def _strip(cls, v) -> str:
        return v if isinstance(v, str) else str(v)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(..., description="OpenAI-style messages")
    model: str | None = Field(None, description="Override model name")
    temperature: float | None = Field(None, ge=0, le=2)
    max_tokens: int | None = Field(None, ge=1, le=8192)
    stream: bool = False
    extra: dict[str, Any] | None = Field(
        default=None,
        description="Additional fields to pass through to the provider",
    )


# ──────────────────────────── Core call ────────────────────────────


async def _post_chat(json_body: dict[str, Any], stream: bool) -> httpx.Response:
    url = f"{_provider_base().rstrip('/')}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": _provider_auth_header(),
    }
    timeout = httpx.Timeout(REQUEST_TIMEOUT)
    client = httpx.AsyncClient(timeout=timeout)
    try:
        # httpx uses 'stream=True' to stream the response body
        resp = await client.post(url, headers=headers, json=json_body)
        # For streaming, some providers send 200 but stream in the body. We still return resp as-is.
        return resp
    finally:
        # do not close here when streaming; StreamingResponse will handle the aiter
        if not stream:
            await client.aclose()


# ──────────────────────────── Endpoints ────────────────────────────


@router.post("/complete", response_model=None)
async def chat_complete(req: ChatRequest):
    """
    OpenAI-compatible chat completion proxy (non-streaming by default, SSE if stream=true).

    - If USE_OPENAI=true, forwards to OpenAI.
    - Otherwise forwards to LOCAL_LLM_BASE_URL (Ollama/LM Studio).
    """
    model = req.model or _provider_model()
    payload: dict[str, Any] = {
        "model": model,
        "messages": [m.dict() for m in req.messages],
        "temperature": (
            req.temperature
            if req.temperature is not None
            else LOCAL_TEMP if not USE_OPENAI else req.temperature
        ),
        "max_tokens": (
            req.max_tokens
            if req.max_tokens is not None
            else LOCAL_MAXTOK if not USE_OPENAI else req.max_tokens
        ),
        "stream": req.stream,
    }

    if req.extra:
        payload.update(req.extra)

    # Non-streaming path
    if not req.stream:
        resp = await _post_chat(payload, stream=False)
        if not resp.is_success:
            text = await _safe_text(resp)
            raise HTTPException(
                status_code=resp.status_code, detail=_fmt_detail(resp, text)
            )
        try:
            data = resp.json()
        except Exception:
            text = await _safe_text(resp)
            raise HTTPException(
                status_code=502, detail=f"Invalid JSON from provider: {text[:500]}"
            )
        return JSONResponse(content=data, status_code=resp.status_code)

    # Streaming (SSE) path — pass provider's SSE through unchanged
    async def sse_iter() -> AsyncIterator[bytes]:
        url = f"{_provider_base().rstrip('/')}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": _provider_auth_header(),
        }
        timeout = httpx.Timeout(REQUEST_TIMEOUT)
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as r:
                if not r.is_success:
                    text = await r.aread()
                    # emit one SSE error event then end
                    yield f"data: { {'error': _fmt_detail(r, text.decode(errors='ignore'))} }\n\n".encode()
                    return
                async for chunk in r.aiter_bytes():
                    # Provider already sends 'data: ...\n\n'; forward bytes directly
                    yield chunk

    return StreamingResponse(sse_iter(), media_type="text/event-stream")


@router.get("/health", response_model=ChatHealthResponse)
async def chat_health() -> ChatHealthResponse:
    """
    Quick connectivity probe against the configured provider.

    Tests LLM provider with a minimal no-op call.
    Does NOT consume tokens on local servers; on OpenAI this is a minimal request.
    """
    try:
        payload = {
            "model": _provider_model(),
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 1,
            "temperature": 0,
            "stream": False,
        }
        resp = await _post_chat(payload, stream=False)
        ok = bool(resp.status_code == 200)
        detail = None if ok else await _safe_text(resp)
        return ChatHealthResponse(
            provider="openai" if USE_OPENAI else "local",
            base=_provider_base(),
            model=_provider_model(),
            ok=ok,
            status_code=resp.status_code,
            detail=(detail[:400] if detail else None),
            error=None,
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        return ChatHealthResponse(
            provider="openai" if USE_OPENAI else "local",
            base=_provider_base(),
            model=_provider_model(),
            ok=False,
            status_code=None,
            detail=None,
            error=str(e),
        )


@router.get("/config", response_model=ChatConfigResponse)
async def chat_config() -> ChatConfigResponse:
    """
    Get non-sensitive chat configuration snapshot.

    Returns current LLM provider configuration for debugging.
    Note: Never returns API keys.
    """
    return ChatConfigResponse(
        provider="openai" if USE_OPENAI else "local",
        base=_provider_base(),
        default_model=_provider_model(),
        timeout_sec=REQUEST_TIMEOUT,
        use_openai=USE_OPENAI,
    )


# ──────────────────────────── Utils ────────────────────────────


async def _safe_text(resp: httpx.Response) -> str:
    try:
        return await resp.aread().decode("utf-8", errors="ignore")
    except Exception:
        try:
            return resp.text
        except Exception:
            return ""


def _fmt_detail(resp: httpx.Response, body: str | bytes | None) -> str:
    tail = ""
    if isinstance(body, bytes):
        try:
            body = body.decode("utf-8", errors="ignore")
        except Exception:
            body = ""
    if body:
        tail = f" — {body[:500]}"
    hint = ""
    if resp.status_code in (0, 404):
        hint = " • Is the LLM server running on the expected port?"
    elif resp.status_code == 401:
        hint = " • Unauthorized. Check OPENAI_API_KEY or local server auth."
    elif resp.status_code == 403:
        hint = " • Forbidden. CORS or project permissions may be blocking."
    elif resp.status_code >= 500:
        hint = " • Provider error. Check provider logs."
    return f"provider error: {resp.status_code} {resp.reason_phrase}{hint}{tail}"
