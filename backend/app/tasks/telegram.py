from __future__ import annotations

import asyncio
import os
import time
from typing import Any


# Try to import the logger; fall back to a no-op if unavailable.
try:
    from app.tasks.tg_log import log_telegram
except Exception:  # pragma: no cover

    def log_telegram(**_kw):  # type: ignore
        pass


try:
    import httpx
except Exception:  # pragma: no cover
    httpx = None  # type: ignore

# Diagnostics (safe to expose via tg_diag)
_last_err: str | None = None
_last_raw: dict[str, Any] | None = None
_env_loaded_once = False


# ──────────────────────────────────────────────────────────────────────────────
# Env helpers
# ──────────────────────────────────────────────────────────────────────────────


def _force_load_env_if_needed() -> None:
    """Lazily load .env if TELEGRAM_* are missing. Never raises."""
    global _env_loaded_once
    if _env_loaded_once:
        return
    if os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"):
        _env_loaded_once = True
        return
    try:  # optional dependency
        from dotenv import find_dotenv, load_dotenv  # type: ignore

        for candidate in (".env", "backend/.env"):
            p = find_dotenv(candidate, usecwd=True)
            if p:
                load_dotenv(p, override=False)
    except Exception:
        # It's fine if python-dotenv isn't installed
        pass
    finally:
        _env_loaded_once = True


def _clean(s: str | None) -> str | None:
    if not isinstance(s, str):
        return None
    s = s.split("#", 1)[0].strip()
    if (s.startswith('"') and s.endswith('"')) or (
        s.startswith("'") and s.endswith("'")
    ):
        s = s[1:-1].strip()
    return s or None


def _env() -> tuple[str | None, str | None, str | None]:
    _force_load_env_if_needed()
    bot = _clean(os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TG_BOT_TOKEN"))
    chat = _clean(os.getenv("TELEGRAM_CHAT_ID") or os.getenv("TG_CHAT_ID"))
    parse = _clean(os.getenv("TELEGRAM_PARSE_MODE"))
    return bot, chat, parse


# ──────────────────────────────────────────────────────────────────────────────
# Core sender (async, httpx.AsyncClient)
# ──────────────────────────────────────────────────────────────────────────────


async def send_message(text: str, parse_mode: str = "HTML") -> bool:
    """
    Send a Telegram message. Returns True/False. Never raises.

    - Reads TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID (or TG_* fallbacks).
    - Uses httpx.AsyncClient(timeout=10).
    - Stores diagnostics in module-level _last_raw/_last_err.
    """
    global _last_err, _last_raw
    _last_raw = None
    bot, chat, parse_env = _env()

    if not bot or not chat or httpx is None:
        _last_err = "missing TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID or httpx not available"
        # No logging here; wrapper tg_send() handles logging
        return False

    # Prepare payload (truncate to Telegram max ~4096)
    msg = text if isinstance(text, str) else str(text)
    if len(msg) > 4096:
        msg = msg[:4000] + "…(truncated)"

    payload: dict[str, Any] = {
        "chat_id": chat,
        "text": msg,
        "disable_web_page_preview": True,
    }
    if parse_env or parse_mode:
        payload["parse_mode"] = parse_env or parse_mode

    ok = False
    try:
        async with httpx.AsyncClient(
            base_url=f"https://api.telegram.org/bot{bot}", timeout=10.0
        ) as client:
            resp = await client.post("/sendMessage", json=payload)
            try:
                j = resp.json()
            except Exception:
                j = {"parse_error": (resp.text if hasattr(resp, "text") else "")}
            _last_raw = {"status_code": resp.status_code, "json": j}
            ok = bool(resp.is_success and bool(j.get("ok")))
            _last_err = (
                None if ok else (j.get("description") or f"HTTP {resp.status_code}")
            )
    except Exception as e:  # network/timeout/etc
        _last_err = repr(e)
        _last_raw = {"exception": _last_err}
        ok = False

    return ok


# ──────────────────────────────────────────────────────────────────────────────
# Compatibility wrapper used across the codebase
# ──────────────────────────────────────────────────────────────────────────────


def tg_send(
    text: str, *, kind: str = "misc", meta: dict[str, Any] | None = None
) -> bool:
    """
    Synchronous wrapper that calls the async sender and logs the attempt.
    Safe to use from threads, sync routes, or background jobs.
    """
    ts = time.time()
    try:
        # Run the async sender. Since this function is called from sync contexts
        # (regular FastAPI def endpoints, threads), asyncio.run is appropriate.
        ok = asyncio.run(send_message(text))
    except RuntimeError:
        # If we're already in an event loop (rare in our sync callers), fall back
        # to a short-lived, blocking HTTP send via httpx (still no crash on error).
        ok = False
        if httpx is not None:
            try:
                bot, chat, parse_env = _env()
                if bot and chat:
                    with httpx.Client(
                        base_url=f"https://api.telegram.org/bot{bot}", timeout=10.0
                    ) as client:
                        payload = {
                            "chat_id": chat,
                            "text": text if isinstance(text, str) else str(text),
                            "disable_web_page_preview": True,
                        }
                        if parse_env:
                            payload["parse_mode"] = parse_env
                        resp = client.post("/sendMessage", json=payload)
                        j = (
                            resp.json()
                            if resp.headers.get("content-type", "").startswith(
                                "application/json"
                            )
                            else {}
                        )
                        global _last_raw, _last_err
                        _last_raw = {"status_code": resp.status_code, "json": j}
                        ok = bool(resp.is_success and bool(j.get("ok")))
                        _last_err = (
                            None
                            if ok
                            else (j.get("description") or f"HTTP {resp.status_code}")
                        )
            except Exception as e:
                _last_err = repr(e)
                _last_raw = {"exception": _last_err}
                ok = False
        else:
            ok = False

    # Always log the attempt
    try:
        log_telegram(ts=ts, kind=kind, text=text, ok=ok, error=_last_err, meta=meta)
    except Exception:
        pass
    return ok


def tg_diag() -> dict:
    """Return safe diagnostics (no token leakage)."""
    bot, chat, _ = _env()
    out = {
        "token_set": bool(bot),
        "chat_set": bool(chat),
        "getme_ok": None,
        "last_error": _last_err,
        "last_raw": _last_raw,
    }
    # Best-effort getMe check (sync; minimal overhead)
    try:
        if httpx is not None and bot:
            with httpx.Client(
                base_url=f"https://api.telegram.org/bot{bot}", timeout=5.0
            ) as client:
                r = client.get("/getMe")
                try:
                    j = r.json()
                except Exception:
                    j = {}
                out["getme_ok"] = bool(r.is_success and bool(j.get("ok")))
    except Exception as e:
        out["getme_ok"] = False
        out["last_error"] = f"getMe: {e!r}"
    return out
