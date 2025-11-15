from __future__ import annotations

import json
import logging
import time
import uuid
from contextvars import ContextVar
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


# Context variable to store request_id for the current task
_request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)


def get_request_id() -> str | None:
    return _request_id_var.get()


def _set_request_id(value: str | None) -> None:
    _request_id_var.set(value)


def json_log(level: int, message: str, **fields: Any) -> None:
    """Emit a single JSON log line with request_id automatically attached.

    Usage: json_log(logging.INFO, "event_name", key=value, ...)
    """
    data: dict[str, Any] = {
        "msg": message,
        "level": logging.getLevelName(level),
        "request_id": get_request_id(),
        **fields,
    }
    try:
        logging.getLogger("ziggy").log(level, json.dumps(data, default=str))
    except Exception:
        # Best effort: fallback to plain log
        logging.getLogger("ziggy").log(level, f"{message} | {fields}")


class RequestContextLoggerMiddleware(BaseHTTPMiddleware):
    """Assigns/propagates X-Request-ID and emits JSON access logs with duration."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        _set_request_id(rid)

        start = time.perf_counter()
        response: Response | None = None
        status: int = 0
        try:
            response = await call_next(request)
            status = getattr(response, "status_code", 0)
            return response
        except Exception:
            # In case of exception, still log with 500 status downstream
            status = 500
            raise
        finally:
            dur_ms = int((time.perf_counter() - start) * 1000)
            # Add header for clients
            try:
                # Only set header if response exists in scope
                if response is not None:
                    response.headers["X-Request-ID"] = rid
            except Exception:
                pass

            json_log(
                logging.INFO,
                "http_access",
                method=request.method,
                path=request.url.path,
                status=status,
                dur_ms=dur_ms,
                client_ip=getattr(request.client, "host", None),
                ua=request.headers.get("user-agent"),
            )
