# app/main.py - Complete ZiggyAI FastAPI Application with ALL Routers

import logging
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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


# ---- Lifespan management for streaming services ----
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup streaming services"""
    logger.info("🚀 Starting ZiggyAI streaming services...")
    
    # Start news streaming
    try:
        from app.services.news_streaming import start_news_streaming
        await start_news_streaming()
        logger.info("✅ News streaming started")
    except Exception as e:
        logger.warning(f"⚠️ News streaming not started: {e}")
    
    # Start alert monitoring if available
    try:
        from app.services.alert_monitoring import start_alert_monitoring
        await start_alert_monitoring()
        logger.info("✅ Alert monitoring started")
    except Exception as e:
        logger.warning(f"⚠️ Alert monitoring not started: {e}")
    
    # Start portfolio streaming if available
    try:
        from app.services.portfolio_streaming import start_portfolio_streaming
        await start_portfolio_streaming()
        logger.info("✅ Portfolio streaming started")
    except Exception as e:
        logger.warning(f"⚠️ Portfolio streaming not started: {e}")
    
    logger.info("✅ ZiggyAI backend ready!")
    
    yield  # Server runs here
    
    # Cleanup on shutdown
    logger.info("🛑 Shutting down ZiggyAI streaming services...")
    
    try:
        from app.services.news_streaming import stop_news_streaming
        await stop_news_streaming()
    except Exception as e:
        logger.debug(f"News streaming cleanup: {e}")
    
    try:
        from app.core.websocket import connection_manager
        await connection_manager.stop()
    except Exception as e:
        logger.debug(f"WebSocket cleanup: {e}")
    
    logger.info("✅ ZiggyAI backend shutdown complete")


# ---- FastAPI app with docs toggle and security schemes ----
_docs_enabled = os.getenv("DOCS_ENABLED", "true").lower() not in {"false", "0", "no"}

app = FastAPI(
    title="ZiggyAI",
    version="0.1.0",
    docs_url="/docs" if _docs_enabled else None,
    redoc_url="/redoc" if _docs_enabled else None,
    openapi_url="/openapi.json" if _docs_enabled else None,
    lifespan=lifespan,
)

# ---- Add OpenAPI Security Schemes ----
# These define the authentication methods available in the API
def customize_openapi():
    """Customize OpenAPI schema to include security schemes"""
    if app.openapi_schema:
        return app.openapi_schema
    
    from fastapi.openapi.utils import get_openapi
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description="ZiggyAI Trading Platform API with optional authentication",
        routes=app.routes,
    )
    
    # Add security schemes to OpenAPI
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token obtained from /auth/login endpoint",
        },
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key for programmatic access",
        },
    }
    
    # Add security info
    openapi_schema["info"]["x-security-info"] = {
        "authentication": "Optional authentication via JWT Bearer token or API Key",
        "development": "Authentication disabled by default in development mode",
        "production": "Authentication can be enabled via ENABLE_AUTH environment variable",
        "public_endpoints": ["/health", "/health/detailed", "/docs", "/redoc", "/openapi.json"],
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = customize_openapi

# ---- CORS Middleware ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Rate Limiting Setup ----
if HAVE_SLOWAPI:
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)

    @app.exception_handler(RateLimitExceeded)
    async def _rate_limit_handler(request, exc):
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded", "code": "rate_limit_exceeded", "meta": {}},
        )


# ---- Global Exception Handlers for Standardized Error Responses ----
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """
    Standardize HTTPException responses to use ErrorResponse format.
    
    Converts HTTPException detail to standardized {detail, code, meta} format.
    """
    from app.models import ErrorResponse

    # If detail is already a dict with our format, use it
    if isinstance(exc.detail, dict):
        detail_str = exc.detail.get("detail", str(exc.detail.get("error", "An error occurred")))
        code = exc.detail.get("code", f"http_{exc.status_code}")
        meta = exc.detail.get("meta", exc.detail.copy())
        # Remove standard keys from meta to avoid duplication
        meta.pop("detail", None)
        meta.pop("code", None)
    else:
        # Simple string detail
        detail_str = str(exc.detail)
        code = f"http_{exc.status_code}"
        meta = {}

    error_response = ErrorResponse(detail=detail_str, code=code, meta=meta)
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """
    Catch-all handler for unexpected exceptions.
    
    Returns standardized error response for internal server errors.
    """
    from app.models import ErrorResponse

    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    error_response = ErrorResponse(
        detail="An internal server error occurred",
        code="internal_server_error",
        meta={"type": type(exc).__name__},
    )
    return JSONResponse(
        status_code=500,
        content=error_response.model_dump(),
    )


# ---- Router Registration with Error Handling ----
def register_router_safely(
    router_module: str,
    router_name: str = "router",
    prefix: str = "",
    tags: list[str] | None = None,
):
    """Safely register a router with graceful error handling."""
    try:
        module = __import__(router_module, fromlist=[router_name])
        router = getattr(module, router_name)

        # Use existing router prefix if available, otherwise use provided prefix
        existing_prefix = getattr(router, "prefix", None)
        final_prefix = existing_prefix if existing_prefix else prefix

        # Use existing router tags if available, otherwise use provided tags
        existing_tags = getattr(router, "tags", None)
        final_tags = existing_tags if existing_tags else (tags or [])

        # Register router with appropriate parameters
        if final_prefix and final_tags:
            app.include_router(router, prefix=final_prefix, tags=final_tags)  # type: ignore
        elif final_prefix:
            app.include_router(router, prefix=final_prefix)
        elif final_tags:
            app.include_router(router, tags=final_tags)  # type: ignore
        else:
            app.include_router(router)
        logger.info(
            f"✅ Registered router: {router_module} "
            f"(prefix: '{final_prefix}', tags: {final_tags})"
        )
        return True

    except ImportError as e:
        logger.error(f"❌ Import error for {router_module}: {e}")
        return False
    except AttributeError as e:
        logger.error(f"❌ Router not found in {router_module}: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error registering {router_module}: {e}")
        return False


# ---- Authentication Routes ----
register_router_safely("app.api.routes_auth", prefix="/api")

# ---- Core API Routes ----
register_router_safely("app.api.routes", prefix="/api")

# ---- Trading & Market Routes ----
register_router_safely("app.api.routes_trading", prefix="/api")
register_router_safely("app.trading.router")  # Has its own /trade prefix
register_router_safely("app.api.routes_market", prefix="/api")
register_router_safely("app.api.routes_market_calendar")  # Has its own /market prefix
register_router_safely("app.api.routes_crypto", prefix="/api")
register_router_safely("app.api.routes_screener")  # Has its own /screener prefix
register_router_safely("app.api.routes_paper", prefix="/api")
register_router_safely("app.api.routes_risk_lite", prefix="/api")

# ---- AI & Cognitive Routes ----
register_router_safely("app.api.routes_signals")  # Has its own /signals prefix
register_router_safely("app.api.routes_cognitive")  # Has its own /cognitive prefix
register_router_safely("app.api.routes_chat")  # Has its own /chat prefix
register_router_safely("app.api.routes_explain")  # Has its own /signal prefix for explanations
register_router_safely("app.api.routes_trace")  # Has its own /signal prefix for tracing
register_router_safely("app.api.routes_learning", prefix="/api")

# ---- News & Data Routes ----
register_router_safely("app.api.routes_news", prefix="/api")
register_router_safely("app.api.routes_alerts", prefix="/api")

# ---- Integration & Feedback Routes ----
register_router_safely("app.api.routes_integration")  # Has its own /integration prefix
register_router_safely("app.api.routes_feedback")  # Has its own /feedback prefix

# ---- Development & Monitoring Routes ----
register_router_safely("app.api.routes_dev", prefix="/api")
register_router_safely("app.api.routes_performance")  # Has its own /api/performance prefix

# ---- Web Browsing Routes ----
register_router_safely("app.web.browse_router")


# ---- Basic Health Endpoint ----
from app.models import AckResponse, HealthResponse


@app.get("/health", response_model=AckResponse)
async def health() -> AckResponse:
    """Basic health check endpoint."""
    return AckResponse(ok=True, message=None)


# ---- Enhanced Health Check ----
@app.get("/health/detailed", response_model=HealthResponse)
async def detailed_health() -> HealthResponse:
    """
    Detailed health check with router information.
    
    Returns service status, version, and registered routes.
    """
    routes_info: list[dict[str, Any]] = []
    for route in app.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            route_path = getattr(route, "path", "unknown")
            route_methods = getattr(route, "methods", set())
            routes_info.append(
                {
                    "path": route_path,
                    "methods": list(route_methods) if route_methods else [],
                    "name": getattr(route, "name", "unnamed"),
                }
            )

    return HealthResponse(
        status="ok",
        details={
            "service": "ZiggyAI Backend",
            "version": "0.1.0",
            "total_routes": len(routes_info),
            "routes": routes_info[:10],  # First 10 for brevity
            "has_slowapi": HAVE_SLOWAPI,
        },
    )


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

    app.include_router(
        performance_router
    )  # already has prefix="/api/performance"
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
