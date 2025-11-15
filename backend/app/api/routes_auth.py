"""
Authentication Routes for ZiggyAI

Provides login, token refresh, and auth status endpoints.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.auth_dependencies import get_auth_status
from app.core.security import (
    User,
    authenticate_user,
    create_access_token,
    get_current_active_user_flexible,
    get_current_user_flexible,
)


router = APIRouter(prefix="/auth", tags=["authentication"])


# ---- Request/Response Models ----


class LoginRequest(BaseModel):
    """Login credentials"""

    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


class TokenResponse(BaseModel):
    """JWT token response"""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(
        default="bearer", description="Token type (always 'bearer')"
    )
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: dict[str, Any] = Field(..., description="User information")


class AuthStatusResponse(BaseModel):
    """Authentication status response"""

    authenticated: bool = Field(..., description="Whether user is authenticated")
    user: dict[str, Any] | None = Field(
        None, description="User information if authenticated"
    )
    auth_config: dict[str, Any] = Field(..., description="Authentication configuration")


class UserInfoResponse(BaseModel):
    """User information response"""

    username: str
    email: str | None
    full_name: str | None
    scopes: list[str]


# ---- Endpoints ----


@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest) -> TokenResponse:
    """
    Authenticate user and return JWT token.

    **Note:** Authentication may be disabled in development mode.
    Check `/auth/status` to see if authentication is required.

    **Default credentials:**
    - Username: `ziggy`, Password: `secret` (admin)
    - Username: `demo`, Password: `secret` (read-only)
    - Username: `user`, Password: `secret` (dev user)
    """
    # Authenticate user
    user = authenticate_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is disabled",
        )

    # Create access token
    from app.core.security import ACCESS_TOKEN_EXPIRE_MINUTES

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "scopes": user.scopes},
        expires_delta=access_token_expires,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "scopes": user.scopes,
        },
    )


@router.get("/status", response_model=AuthStatusResponse)
async def auth_status(
    current_user: User | None = Depends(get_current_user_flexible),
) -> AuthStatusResponse:
    """
    Get authentication status and configuration.

    Returns whether authentication is enabled and current user info if authenticated.
    """
    return AuthStatusResponse(
        authenticated=current_user is not None,
        user=(
            {
                "username": current_user.username,
                "email": current_user.email,
                "full_name": current_user.full_name,
                "scopes": current_user.scopes,
            }
            if current_user
            else None
        ),
        auth_config=get_auth_status(),
    )


@router.get("/me", response_model=UserInfoResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user_flexible),
) -> UserInfoResponse:
    """
    Get current authenticated user information.

    Requires authentication (JWT token or API key).
    """
    return UserInfoResponse(
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        scopes=current_user.scopes,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    current_user: User = Depends(get_current_active_user_flexible),
) -> TokenResponse:
    """
    Refresh JWT token.

    Requires valid JWT token. Returns new token with extended expiration.
    """
    from app.core.security import ACCESS_TOKEN_EXPIRE_MINUTES

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": current_user.username, "scopes": current_user.scopes},
        expires_delta=access_token_expires,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "username": current_user.username,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "scopes": current_user.scopes,
        },
    )
