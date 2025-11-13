# app/api/routes_dev.py
"""
Development-only routes for ZiggyAI
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from app.core.config import get_settings
from app.db import db_state, init_with_backoff
from app.dev.bootstrap_user import get_dev_user_info
from app.dev.portfolio_setup import (
    configure_autonomous_trading,
    ensure_dev_user_portfolio,
    fund_portfolio,
    get_portfolio_status,
)
from app.models import base as models_base
from app.persistence.snapshotter import Snapshotter
from app.tasks.paper_worker import get_paper_worker


logger = logging.getLogger("ziggy.api.dev")
settings = get_settings()

router = APIRouter()


class PortfolioFundingRequest(BaseModel):
    additional_capital: float


@router.get("/user", response_model=dict[str, Any])
async def get_dev_user_status():
    """
    Get development user status (dev environments only)

    Returns:
        dict: User existence and configuration status
    """
    # Temporarily remove environment check for debugging
    # if settings.ENV not in ["development", "dev"] and not settings.DEBUG:
    #     raise HTTPException(status_code=404, detail="Not found")

    try:
        user_info = get_dev_user_info()
        if user_info is None:
            return {
                "exists": False,
                "roles": [],
                "paper_trading_enabled": False,
                "is_dev": False,
                "is_active": False,
                "scopes": [],
            }

        return user_info

    except HTTPException:
        # Re-raise HTTPException (e.g., 503 for DB unavailable) without modification
        raise
    except Exception as e:
        logger.error(f"Failed to get dev user status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.post("/portfolio/setup", response_model=dict[str, Any])
async def setup_dev_portfolio():
    """
    Set up portfolio for dev user with initial capital for autonomous trading

    Returns:
        dict: Portfolio setup status and configuration
    """
    try:
        result = ensure_dev_user_portfolio()

        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("error"))

        # Configure autonomous trading if portfolio was created or exists
        if result.get("portfolio_id"):
            config_result = configure_autonomous_trading(result["portfolio_id"])
            result["trading_config"] = config_result

        return result

    except Exception as e:
        logger.error(f"Failed to setup dev portfolio: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.get("/portfolio/status", response_model=dict[str, Any])
async def get_dev_portfolio_status():
    """
    Get current portfolio status and trading configuration

    Returns:
        dict: Portfolio status, balances, and autonomous trading settings
    """
    try:
        status = get_portfolio_status()

        if status.get("status") == "error":
            # Return 503 for database or service unavailable errors
            error_detail = status.get("error", "Service unavailable")
            raise HTTPException(status_code=503, detail=error_detail)

        if status.get("status") == "not_found":
            raise HTTPException(status_code=404, detail="Portfolio not found")

        return status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get portfolio status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.post("/portfolio/fund", response_model=dict[str, Any])
async def fund_dev_portfolio(funding_request: PortfolioFundingRequest):
    """
    Add additional capital to the dev user's portfolio

    Args:
        funding_request: Request containing additional capital amount

    Returns:
        dict: Funding status and updated balances
    """
    try:
        if funding_request.additional_capital <= 0:
            raise HTTPException(status_code=400, detail="Additional capital must be positive")

        result = fund_portfolio(additional_capital=funding_request.additional_capital)

        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("error"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fund portfolio: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.post("/trading/enable", response_model=dict[str, Any])
async def enable_autonomous_trading():
    """
    Enable autonomous trading for ZiggyAI

    Returns:
        dict: Trading enablement status
    """
    try:
        from app.trading.signals import get_trading_manager

        # Ensure portfolio exists first
        portfolio_result = ensure_dev_user_portfolio()
        if portfolio_result.get("status") == "error":
            raise HTTPException(status_code=500, detail="Portfolio setup failed")

        # Configure autonomous trading
        config_result = configure_autonomous_trading(portfolio_result["portfolio_id"])
        if config_result.get("status") == "error":
            raise HTTPException(status_code=500, detail=config_result.get("error"))

        # Enable paper trading mode
        manager = get_trading_manager()
        manager.enable_paper_trading()

        return {
            "status": "enabled",
            "portfolio_id": portfolio_result["portfolio_id"],
            "trading_mode": "paper",
            "autonomous_trading": True,
            "message": "ZiggyAI autonomous trading enabled successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to enable autonomous trading: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.get("/db/status", response_model=dict[str, Any])
async def dev_db_status():
    """Quick DB status endpoint: returns db_state and a ping result if connected."""
    state = {
        "configured": bool(db_state.get("configured")),
        "connected": bool(db_state.get("connected")),
        "dialect": db_state.get("dialect"),
    }
    ping_ok = False
    try:
        if state["connected"] and getattr(models_base, "engine", None):
            with models_base.engine.connect() as conn:  # type: ignore[attr-defined]
                conn.execute(text("SELECT 1"))
            ping_ok = True
    except Exception:
        ping_ok = False
    return {"db": state, "ping": ping_ok}


@router.post("/db/init", response_model=dict[str, Any])
async def dev_db_init():
    """Trigger background DB init with backoff (no-op if already connected)."""
    if bool(db_state.get("connected")):
        return {"scheduled": False, "already_connected": True}
    # Kick off a background initializer; do not await long operations here
    # Keep a reference to avoid GC
    if not hasattr(router, "_bg_tasks"):
        router._bg_tasks = set()  # type: ignore[attr-defined]
    _task = asyncio.create_task(init_with_backoff())
    router._bg_tasks.add(_task)  # type: ignore[attr-defined]
    _task.add_done_callback(router._bg_tasks.discard)  # type: ignore[attr-defined]
    return {"scheduled": True}


@router.post("/snapshot/now", response_model=dict[str, Any])
async def snapshot_now():
    """Trigger an immediate snapshot checkpoint."""
    worker = get_paper_worker()
    if not worker:
        return {"ok": False, "reason": "worker_not_running"}
    snap = Snapshotter()
    result = await snap.checkpoint_once()
    return result


@router.get("/state/summary", response_model=dict[str, Any])
async def state_summary():
    """Return basic summary of current durable state and last checkpoint time."""
    worker = get_paper_worker()
    if not worker:
        return {"ok": False, "reason": "worker_not_running"}
    snap = Snapshotter()
    last = snap.last_checkpoint_iso()
    engine_status = await worker.engine.get_status()
    return {
        "ok": True,
        "last_checkpoint": last,
        "engine": engine_status,
    }
