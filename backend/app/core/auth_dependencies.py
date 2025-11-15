"""
Authentication Dependencies for ZiggyAI

Provides flexible authentication dependencies that can be enabled/disabled
via environment variables for local dev vs staging/production.

Usage:
    from app.core.auth_dependencies import require_auth_trading

    @router.post("/trade/execute", dependencies=[Depends(require_auth_trading)])
    def execute_trade(...):
        ...
"""

from __future__ import annotations

import os
from typing import Any

from fastapi import Depends, HTTPException, status

from app.core.security import (
    User,
    get_current_active_user_flexible,
    require_scope,
)


def _get_auth_setting(key: str, default: bool = False) -> bool:
    """Get authentication setting from environment"""
    value = os.getenv(key, str(default)).lower()
    return value in {"true", "1", "yes", "enabled"}


# Global auth enablement
ENABLE_AUTH = _get_auth_setting("ENABLE_AUTH", False)

# Per-domain auth requirements
REQUIRE_AUTH_TRADING = _get_auth_setting("REQUIRE_AUTH_TRADING", False)
REQUIRE_AUTH_PAPER = _get_auth_setting("REQUIRE_AUTH_PAPER", False)
REQUIRE_AUTH_COGNITIVE = _get_auth_setting("REQUIRE_AUTH_COGNITIVE", False)
REQUIRE_AUTH_INTEGRATION = _get_auth_setting("REQUIRE_AUTH_INTEGRATION", False)


async def optional_auth() -> User | None:
    """Optional authentication - returns user if authenticated, None otherwise"""
    if not ENABLE_AUTH:
        return None

    try:
        return await get_current_active_user_flexible()
    except HTTPException:
        return None


async def require_auth() -> User:
    """Require authentication - raises 401 if not authenticated"""
    if not ENABLE_AUTH:
        # Return a fake dev user when auth is disabled
        return User(
            username="dev_user",
            full_name="Development User",
            email="dev@localhost",
            scopes=["admin", "trading", "paper_trading", "dev_brain"],
        )

    return await get_current_active_user_flexible()


async def require_auth_trading() -> User:
    """Require authentication for trading endpoints"""
    if not ENABLE_AUTH and not REQUIRE_AUTH_TRADING:
        return User(
            username="dev_user",
            full_name="Development User",
            scopes=["admin", "trading"],
        )

    user = await get_current_active_user_flexible()

    # Check trading scope
    if "trading" not in user.scopes and "admin" not in user.scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Trading access required",
        )

    return user


async def require_auth_paper() -> User:
    """Require authentication for paper trading endpoints"""
    if not ENABLE_AUTH and not REQUIRE_AUTH_PAPER:
        return User(
            username="dev_user",
            full_name="Development User",
            scopes=["admin", "paper_trading"],
        )

    user = await get_current_active_user_flexible()

    # Check paper trading scope
    if "paper_trading" not in user.scopes and "admin" not in user.scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Paper trading access required",
        )

    return user


async def require_auth_cognitive() -> User:
    """Require authentication for cognitive/decision enhancement endpoints"""
    if not ENABLE_AUTH and not REQUIRE_AUTH_COGNITIVE:
        return User(
            username="dev_user",
            full_name="Development User",
            scopes=["admin", "dev_brain"],
        )

    user = await get_current_active_user_flexible()

    # Check cognitive/dev_brain scope
    if "dev_brain" not in user.scopes and "admin" not in user.scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cognitive enhancement access required",
        )

    return user


async def require_auth_integration() -> User:
    """Require authentication for integration/apply endpoints"""
    if not ENABLE_AUTH and not REQUIRE_AUTH_INTEGRATION:
        return User(
            username="dev_user",
            full_name="Development User",
            scopes=["admin"],
        )

    user = await get_current_active_user_flexible()

    # Check admin scope for integration endpoints
    if "admin" not in user.scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required for integration endpoints",
        )

    return user


def get_auth_status() -> dict[str, Any]:
    """Get current authentication configuration status"""
    return {
        "auth_enabled": ENABLE_AUTH,
        "trading_protected": REQUIRE_AUTH_TRADING or ENABLE_AUTH,
        "paper_protected": REQUIRE_AUTH_PAPER or ENABLE_AUTH,
        "cognitive_protected": REQUIRE_AUTH_COGNITIVE or ENABLE_AUTH,
        "integration_protected": REQUIRE_AUTH_INTEGRATION or ENABLE_AUTH,
    }
