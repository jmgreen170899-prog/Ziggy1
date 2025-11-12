# app/main.py (header fix for optional SlowAPI)

import logging
from fastapi import FastAPI

# ---- logger must exist before optional imports/use ----
logger = logging.getLogger("backend")
if not logger.handlers:  # avoid duplicate handlers in reload
    logging.basicConfig(level=logging.INFO)

# ---- make SlowAPI optional ----
HAVE_SLOWAPI = False
try:
    from slowapi import Limiter  # type: ignore
    from slowapi.errors import RateLimitExceeded  # type: ignore
    from slowapi.middleware import SlowAPIMiddleware  # type: ignore
    from slowapi.util import get_remote_address  # type: ignore

    HAVE_SLOWAPI = True
except Exception as e:
    logger.warning("Rate limiting disabled (slowapi unavailable): %s", e)

app = FastAPI()

# If SlowAPI is available, wire it up
if HAVE_SLOWAPI:
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)

    from fastapi.responses import JSONResponse  # noqa: E402

    @app.exception_handler(RateLimitExceeded)
    async def _rate_limit_handler(request, exc):
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
        )

# ---- the rest of your routes/imports below ----
from fastapi.responses import JSONResponse  # noqa: E402

@app.get("/health")
async def health():
    return {"ok": True}
