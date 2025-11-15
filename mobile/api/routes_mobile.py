"""
Mobile-Optimized API Routes for ZiggyAI Android Application

This module provides lightweight, mobile-friendly endpoints optimized for:
- Reduced payload sizes
- Battery-efficient polling intervals
- Offline-first data structures
- Mobile authentication (JWT tokens)
- Push notification support
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Header, Query, status
from pydantic import BaseModel, Field

# Mobile-specific router
router = APIRouter(prefix="/mobile", tags=["mobile"])


# ═══════════════════════════════════════════════════════════════════════════
# Data Models - Optimized for Mobile
# ═══════════════════════════════════════════════════════════════════════════


class MobileAuthRequest(BaseModel):
    """Authentication request for mobile devices"""

    username: str
    password: str
    device_id: str = Field(..., description="Unique device identifier")
    device_name: str = Field(
        default="Android Device", description="Human-readable device name"
    )


class MobileAuthResponse(BaseModel):
    """Authentication response with tokens"""

    access_token: str
    refresh_token: str
    expires_in: int = Field(default=3600, description="Token expiration in seconds")
    user_id: str
    preferences: dict[str, Any] = Field(default_factory=dict)


class MobileQuoteCompact(BaseModel):
    """Compact quote data for mobile - minimal bandwidth"""

    symbol: str
    price: float
    change: float = 0.0
    change_pct: float = 0.0
    volume: int = 0
    timestamp: int = Field(default_factory=lambda: int(datetime.now().timestamp()))


class MobileMarketSnapshot(BaseModel):
    """Aggregated market data snapshot for mobile dashboard"""

    quotes: list[MobileQuoteCompact]
    market_status: Literal["open", "closed", "pre", "post"] = "closed"
    updated_at: int = Field(default_factory=lambda: int(datetime.now().timestamp()))
    cache_ttl: int = Field(
        default=60, description="Seconds until data should be refreshed"
    )


class MobileSignal(BaseModel):
    """Compact trading signal for mobile"""

    id: str
    symbol: str
    action: Literal["BUY", "SELL", "HOLD"]
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    timestamp: int = Field(default_factory=lambda: int(datetime.now().timestamp()))
    expires_at: int | None = None


class MobileAlert(BaseModel):
    """Price alert for mobile notifications"""

    id: str
    symbol: str
    condition: Literal["above", "below"]
    price: float
    current_price: float | None = None
    triggered: bool = False
    created_at: int = Field(default_factory=lambda: int(datetime.now().timestamp()))


class MobilePortfolio(BaseModel):
    """Compact portfolio summary for mobile"""

    total_value: float
    cash: float
    day_change: float = 0.0
    day_change_pct: float = 0.0
    positions: list[dict[str, Any]] = Field(default_factory=list)
    updated_at: int = Field(default_factory=lambda: int(datetime.now().timestamp()))


class MobileNewsItem(BaseModel):
    """Compact news item for mobile feed"""

    id: str
    title: str
    summary: str | None = None
    symbol: str | None = None
    sentiment: float | None = Field(default=None, ge=-1.0, le=1.0)
    published_at: int = Field(default_factory=lambda: int(datetime.now().timestamp()))
    source: str = "Unknown"


class MobileSyncResponse(BaseModel):
    """Efficient sync response containing all recent updates"""

    quotes: list[MobileQuoteCompact] = Field(default_factory=list)
    signals: list[MobileSignal] = Field(default_factory=list)
    alerts: list[MobileAlert] = Field(default_factory=list)
    news: list[MobileNewsItem] = Field(default_factory=list)
    portfolio: MobilePortfolio | None = None
    sync_token: str = Field(..., description="Token for next incremental sync")
    has_more: bool = False


class MobileDeviceInfo(BaseModel):
    """Device registration information"""

    device_id: str
    device_name: str
    push_token: str | None = Field(
        default=None, description="FCM push notification token"
    )
    os_version: str | None = None
    app_version: str | None = None


# ═══════════════════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════════════════


async def get_current_user(authorization: str | None = Header(None)) -> dict[str, Any]:
    """
    Extract and validate user from JWT token in Authorization header.

    In production, this should validate the JWT and return user info.
    For now, this is a placeholder that should be implemented with proper auth.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # TODO: Implement proper JWT validation
    # For now, return a mock user
    return {
        "user_id": "mobile_user_1",
        "username": "mobile_user",
        "device_id": "mock_device",
    }


# ═══════════════════════════════════════════════════════════════════════════
# Authentication Endpoints
# ═══════════════════════════════════════════════════════════════════════════


@router.post("/auth/login", response_model=MobileAuthResponse)
async def mobile_login(auth_req: MobileAuthRequest):
    """
    Authenticate mobile device and return access tokens.

    This endpoint should be called when the user logs in from the Android app.
    It returns JWT tokens that should be stored securely on the device.
    """
    # TODO: Implement actual authentication logic
    # For now, return mock response
    return MobileAuthResponse(
        access_token="mock_access_token_" + auth_req.device_id,
        refresh_token="mock_refresh_token_" + auth_req.device_id,
        expires_in=3600,
        user_id=auth_req.username,
        preferences={
            "theme": "dark",
            "notifications_enabled": True,
            "default_watchlist": ["AAPL", "GOOGL", "MSFT"],
        },
    )


@router.post("/auth/refresh")
async def mobile_refresh_token(refresh_token: str):
    """
    Refresh access token using refresh token.

    Call this endpoint when the access token expires to get a new one
    without requiring the user to log in again.
    """
    # TODO: Implement token refresh logic
    return {"access_token": "new_access_token", "expires_in": 3600}


@router.post("/auth/logout")
async def mobile_logout(current_user: dict[str, Any] = Depends(get_current_user)):
    """
    Logout and invalidate tokens for the current device.
    """
    # TODO: Implement token invalidation
    return {"status": "logged_out"}


# ═══════════════════════════════════════════════════════════════════════════
# Device Management
# ═══════════════════════════════════════════════════════════════════════════


@router.post("/device/register")
async def register_device(
    device_info: MobileDeviceInfo,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """
    Register device for push notifications and tracking.

    This should be called after login to register the device for
    push notifications (FCM token) and track device information.
    """
    # TODO: Store device info in database
    return {
        "status": "registered",
        "device_id": device_info.device_id,
        "push_enabled": device_info.push_token is not None,
    }


@router.delete("/device/unregister")
async def unregister_device(
    device_id: str, current_user: dict[str, Any] = Depends(get_current_user)
):
    """
    Unregister device and stop push notifications.
    """
    # TODO: Remove device from database
    return {"status": "unregistered", "device_id": device_id}


# ═══════════════════════════════════════════════════════════════════════════
# Market Data Endpoints - Mobile Optimized
# ═══════════════════════════════════════════════════════════════════════════


@router.get("/market/snapshot", response_model=MobileMarketSnapshot)
async def get_market_snapshot(
    symbols: str = Query(..., description="Comma-separated list of symbols (max 20)"),
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """
    Get compact market snapshot for watchlist symbols.

    Optimized for mobile:
    - Minimal payload size
    - Includes cache TTL for client-side caching
    - Batched quotes in single request

    Example: /mobile/market/snapshot?symbols=AAPL,GOOGL,MSFT
    """
    symbol_list = [s.strip().upper() for s in symbols.split(",")][:20]

    # TODO: Fetch real market data
    # For now, return mock data
    quotes = [
        MobileQuoteCompact(
            symbol=symbol,
            price=150.0 + hash(symbol) % 100,
            change=0.5,
            change_pct=0.33,
            volume=1000000,
        )
        for symbol in symbol_list
    ]

    return MobileMarketSnapshot(quotes=quotes, market_status="open", cache_ttl=60)


@router.get("/market/quote/{symbol}", response_model=MobileQuoteCompact)
async def get_mobile_quote(
    symbol: str, current_user: dict[str, Any] = Depends(get_current_user)
):
    """
    Get single quote for a symbol.

    Use the snapshot endpoint for multiple symbols to reduce API calls.
    """
    # TODO: Fetch real quote data
    return MobileQuoteCompact(
        symbol=symbol.upper(), price=150.0, change=0.5, change_pct=0.33, volume=1000000
    )


# ═══════════════════════════════════════════════════════════════════════════
# Trading Signals - Mobile Optimized
# ═══════════════════════════════════════════════════════════════════════════


@router.get("/signals", response_model=list[MobileSignal])
async def get_mobile_signals(
    limit: int = Query(default=10, ge=1, le=50),
    symbols: str | None = Query(default=None, description="Filter by symbols"),
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """
    Get recent trading signals optimized for mobile display.

    Signals are sorted by confidence and recency.
    Use the sync endpoint for incremental updates.
    """
    # TODO: Fetch real signals
    return [
        MobileSignal(
            id="sig_1",
            symbol="AAPL",
            action="BUY",
            confidence=0.85,
            reason="Strong upward momentum with positive sentiment",
        ),
        MobileSignal(
            id="sig_2",
            symbol="GOOGL",
            action="HOLD",
            confidence=0.65,
            reason="Consolidating in range, waiting for breakout",
        ),
    ]


# ═══════════════════════════════════════════════════════════════════════════
# Portfolio - Mobile Optimized
# ═══════════════════════════════════════════════════════════════════════════


@router.get("/portfolio", response_model=MobilePortfolio)
async def get_mobile_portfolio(
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """
    Get compact portfolio summary for mobile display.

    Includes:
    - Total value and cash
    - Day change statistics
    - List of positions with key metrics
    """
    # TODO: Fetch real portfolio data
    return MobilePortfolio(
        total_value=100000.0,
        cash=25000.0,
        day_change=1250.0,
        day_change_pct=1.25,
        positions=[
            {"symbol": "AAPL", "shares": 100, "value": 15000.0, "change_pct": 1.5},
            {"symbol": "GOOGL", "shares": 50, "value": 10000.0, "change_pct": -0.5},
        ],
    )


# ═══════════════════════════════════════════════════════════════════════════
# Alerts Management
# ═══════════════════════════════════════════════════════════════════════════


@router.get("/alerts", response_model=list[MobileAlert])
async def get_mobile_alerts(
    active_only: bool = Query(default=True),
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """
    Get price alerts for mobile notifications.
    """
    # TODO: Fetch real alerts
    return [
        MobileAlert(
            id="alert_1",
            symbol="AAPL",
            condition="above",
            price=160.0,
            current_price=155.0,
            triggered=False,
        )
    ]


@router.post("/alerts")
async def create_mobile_alert(
    symbol: str,
    condition: Literal["above", "below"],
    price: float,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """
    Create a new price alert.

    When the alert triggers, a push notification will be sent to the device.
    """
    # TODO: Create alert in database
    return {
        "id": "alert_new",
        "status": "created",
        "symbol": symbol,
        "condition": condition,
        "price": price,
    }


@router.delete("/alerts/{alert_id}")
async def delete_mobile_alert(
    alert_id: str, current_user: dict[str, Any] = Depends(get_current_user)
):
    """
    Delete a price alert.
    """
    # TODO: Delete alert from database
    return {"status": "deleted", "alert_id": alert_id}


# ═══════════════════════════════════════════════════════════════════════════
# News Feed - Mobile Optimized
# ═══════════════════════════════════════════════════════════════════════════


@router.get("/news", response_model=list[MobileNewsItem])
async def get_mobile_news(
    limit: int = Query(default=20, ge=1, le=100),
    symbols: str | None = Query(default=None, description="Filter by symbols"),
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """
    Get recent news items optimized for mobile feed.

    News items include:
    - Compact title and summary
    - Sentiment score
    - Associated symbols
    """
    # TODO: Fetch real news
    return [
        MobileNewsItem(
            id="news_1",
            title="Apple announces new product lineup",
            summary="Apple unveiled new products at their latest event...",
            symbol="AAPL",
            sentiment=0.7,
            source="TechNews",
        )
    ]


# ═══════════════════════════════════════════════════════════════════════════
# Efficient Data Sync - Mobile Optimized
# ═══════════════════════════════════════════════════════════════════════════


@router.get("/sync", response_model=MobileSyncResponse)
async def mobile_sync(
    since: int | None = Query(
        default=None, description="Unix timestamp for incremental sync"
    ),
    include: str = Query(
        default="all",
        description="Comma-separated: quotes,signals,alerts,news,portfolio",
    ),
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """
    Efficient sync endpoint for mobile - get all updates in one request.

    This is the recommended endpoint for periodic updates as it:
    - Reduces number of API calls (battery efficient)
    - Returns only changed data when 'since' is provided
    - Batches all data types in single response
    - Includes sync token for next incremental sync

    Usage:
    1. Initial sync: GET /mobile/sync (gets all data)
    2. Incremental: GET /mobile/sync?since=<timestamp> (gets only updates)

    The 'include' parameter allows filtering what data to sync:
    - all: everything (default)
    - quotes,signals: only quotes and signals
    - portfolio: only portfolio data
    """
    # TODO: Implement incremental sync logic
    # For now, return full snapshot

    return MobileSyncResponse(
        quotes=[
            MobileQuoteCompact(symbol="AAPL", price=155.0, change=1.5, change_pct=0.97)
        ],
        signals=[
            MobileSignal(
                id="sig_1",
                symbol="AAPL",
                action="BUY",
                confidence=0.85,
                reason="Strong momentum",
            )
        ],
        alerts=[],
        news=[],
        portfolio=MobilePortfolio(
            total_value=100000.0,
            cash=25000.0,
            day_change=1250.0,
            day_change_pct=1.25,
            positions=[],
        ),
        sync_token=str(int(datetime.now().timestamp())),
        has_more=False,
    )


# ═══════════════════════════════════════════════════════════════════════════
# Health Check
# ═══════════════════════════════════════════════════════════════════════════


@router.get("/health")
async def mobile_health():
    """
    Health check endpoint for mobile API.

    Returns API version and status.
    """
    return {
        "status": "ok",
        "api_version": "1.0.0",
        "timestamp": int(datetime.now().timestamp()),
    }
