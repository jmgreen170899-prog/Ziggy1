# app/main.py (header fix for optional SlowAPI)

import logging
import os
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

# ---- FastAPI app with docs toggle ----
_docs_enabled = os.getenv("DOCS_ENABLED", "true").lower() not in {"false", "0", "no"}
app = FastAPI(
    title="ZiggyAI",
    version="0.1.0",
    docs_url="/docs" if _docs_enabled else None,
    redoc_url="/redoc" if _docs_enabled else None,
    openapi_url="/openapi.json" if _docs_enabled else None,
)

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

# ---- Explicit router includes ----
# Import and register all discovered routers
# Note: Routers with their own prefix are registered as-is
# Routers without prefix get a sensible default based on their module name

try:
    from app.api.routes import router as core_router
    app.include_router(core_router, prefix="/api")
except Exception as e:
    logger.warning("Failed to include core router: %s", e)

try:
    from app.api.routes_alerts import router as alerts_router
    app.include_router(alerts_router, prefix="/alerts")
except Exception as e:
    logger.warning("Failed to include alerts router: %s", e)

try:
    from app.api.routes_chat import router as chat_router
    app.include_router(chat_router)  # already has prefix="/chat"
except Exception as e:
    logger.warning("Failed to include chat router: %s", e)

try:
    from app.api.routes_cognitive import router as cognitive_router
    app.include_router(cognitive_router)  # already has prefix="/cognitive"
except Exception as e:
    logger.warning("Failed to include cognitive router: %s", e)

try:
    from app.api.routes_crypto import router as crypto_router
    app.include_router(crypto_router, prefix="/crypto")
except Exception as e:
    logger.warning("Failed to include crypto router: %s", e)

try:
    from app.api.routes_dev import router as dev_router
    app.include_router(dev_router, prefix="/dev")
except Exception as e:
    logger.warning("Failed to include dev router: %s", e)

try:
    from app.api.routes_explain import router as explain_router
    app.include_router(explain_router)  # already has prefix="/signal"
except Exception as e:
    logger.warning("Failed to include explain router: %s", e)

try:
    from app.api.routes_feedback import router as feedback_router
    app.include_router(feedback_router)  # already has prefix="/feedback"
except Exception as e:
    logger.warning("Failed to include feedback router: %s", e)

try:
    from app.api.routes_integration import router as integration_router
    app.include_router(integration_router)  # already has prefix="/integration"
except Exception as e:
    logger.warning("Failed to include integration router: %s", e)

try:
    from app.api.routes_learning import router as learning_router
    app.include_router(learning_router, prefix="/learning")
except Exception as e:
    logger.warning("Failed to include learning router: %s", e)

try:
    from app.api.routes_market import router as market_router
    app.include_router(market_router, prefix="/market")
except Exception as e:
    logger.warning("Failed to include market router: %s", e)

try:
    from app.api.routes_market_calendar import router as market_calendar_router
    app.include_router(market_calendar_router)  # already has prefix="/market"
except Exception as e:
    logger.warning("Failed to include market_calendar router: %s", e)

try:
    from app.api.routes_news import router as news_router
    app.include_router(news_router, prefix="/news")
except Exception as e:
    logger.warning("Failed to include news router: %s", e)

try:
    from app.api.routes_paper import router as paper_router
    app.include_router(paper_router, prefix="/paper")
except Exception as e:
    logger.warning("Failed to include paper router: %s", e)

try:
    from app.api.routes_performance import router as performance_router
    app.include_router(performance_router)  # already has prefix="/api/performance"
except Exception as e:
    logger.warning("Failed to include performance router: %s", e)

try:
    from app.api.routes_risk_lite import router as risk_router
    app.include_router(risk_router, prefix="/risk")
except Exception as e:
    logger.warning("Failed to include risk router: %s", e)

try:
    from app.api.routes_screener import router as screener_router
    app.include_router(screener_router)  # already has prefix="/screener"
except Exception as e:
    logger.warning("Failed to include screener router: %s", e)

try:
    from app.api.routes_signals import router as signals_router
    app.include_router(signals_router)  # already has prefix="/signals"
except Exception as e:
    logger.warning("Failed to include signals router: %s", e)

try:
    from app.api.routes_trace import router as trace_router
    app.include_router(trace_router)  # already has prefix="/signal"
except Exception as e:
    logger.warning("Failed to include trace router: %s", e)

try:
    from app.api.routes_trading import router as trading_router
    app.include_router(trading_router, prefix="/trading")
except Exception as e:
    logger.warning("Failed to include trading router: %s", e)

try:
    from app.web.browse_router import router as browse_router
    app.include_router(browse_router)  # routes already include /web prefix
except Exception as e:
    logger.warning("Failed to include browse router: %s", e)

try:
    from app.trading.router import router as trade_router
    app.include_router(trade_router)  # already has prefix="/trade"
except Exception as e:
    logger.warning("Failed to include trade router: %s", e)

# ---- Auto-discovery fallback (catch missed routers) ----
# Note: Auto-discovery is disabled because all routers are explicitly registered above.
# The auto-discovery system is available in app.core.router_auto if needed in the future.
# To enable: uncomment the code below and ensure no duplicate registrations occur.
# try:
#     from app.core.router_auto import discover_and_register_routers
#     discover_and_register_routers(app)
# except Exception as e:
#     # log but do not crash startup
#     import logging
#     logging.getLogger("ziggy.router_auto").warning("Router auto-discovery skipped: %s", e)
