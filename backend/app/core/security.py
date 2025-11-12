# app/core/security.py
from __future__ import annotations

import logging
import os
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel


logger = logging.getLogger("ziggy.security")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "ziggy-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Security schemes
bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class TokenData(BaseModel):
    username: str | None = None
    scopes: list[str] = []
    exp: datetime | None = None


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool = False
    scopes: list[str] = []


class UserInDB(User):
    hashed_password: str


# Mock user database (replace with real database in production)
fake_users_db = {
    "ziggy": {
        "username": "ziggy",
        "full_name": "Ziggy AI",
        "email": "ziggy@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # password: "secret"
        "disabled": False,
        "scopes": ["admin", "trading", "market_data"],
    },
    "demo": {
        "username": "demo",
        "full_name": "Demo User",
        "email": "demo@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # password: "secret"
        "disabled": False,
        "scopes": ["read_only"],
    },
    "user": {
        "username": "user",
        "full_name": "ZiggyAI Dev User",
        "email": "dev@localhost",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # password: "secret"
        "disabled": False,
        "scopes": ["admin", "trading", "paper_trading", "dev_brain"],
    },
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def get_user(username: str) -> UserInDB | None:
    """Get user from database"""
    user_dict = fake_users_db.get(username)
    if user_dict:
        return UserInDB(**user_dict)
    return None


def authenticate_user(username: str, password: str) -> UserInDB | None:
    """Authenticate user with username and password"""
    user = get_user(username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> TokenData | None:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        scopes: list[str] = payload.get("scopes", [])
        exp_timestamp = payload.get("exp")

        exp = None
        if exp_timestamp:
            exp = datetime.fromtimestamp(exp_timestamp, tz=UTC)

        if not username or not isinstance(username, str):
            return None

        return TokenData(username=username, scopes=scopes, exp=exp)
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> User | None:
    """Get current user from JWT token"""
    if not credentials:
        return None

    token_data = verify_token(credentials.credentials)
    if not token_data or not token_data.username:
        return None

    user = get_user(token_data.username)
    if not user:
        return None

    return User(**user.model_dump())


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user (raises exception if not authenticated)"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if current_user.disabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user


def require_scope(required_scope: str):
    """Dependency factory for scope-based authorization"""

    async def scope_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if required_scope not in current_user.scopes and "admin" not in current_user.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires '{required_scope}' scope",
            )
        return current_user

    return scope_checker


# API Key authentication
API_KEYS = {
    "ziggy-admin-key": {"name": "Admin API Key", "scopes": ["admin", "trading", "market_data"]},
    "ziggy-readonly-key": {"name": "Read-Only API Key", "scopes": ["read_only"]},
}


async def get_api_key_user(api_key: str | None = Depends(api_key_header)) -> User | None:
    """Authenticate using API key"""
    if not api_key:
        return None

    key_info = API_KEYS.get(api_key)
    if not key_info:
        return None

    return User(
        username=f"api_key_{api_key[:8]}", full_name=key_info["name"], scopes=key_info["scopes"]
    )


async def get_current_user_flexible(
    token_user: User | None = Depends(get_current_user),
    api_key_user: User | None = Depends(get_api_key_user),
) -> User | None:
    """Get current user from either JWT token or API key"""
    return token_user or api_key_user


async def get_current_active_user_flexible(
    current_user: User | None = Depends(get_current_user_flexible),
) -> User:
    """Get current active user with flexible authentication"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide either Bearer token or X-API-Key header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if current_user.disabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user


# Security utilities
def is_strong_password(password: str) -> bool:
    """Check if password meets security requirements"""
    if len(password) < 8:
        return False
    if not any(c.isupper() for c in password):
        return False
    if not any(c.islower() for c in password):
        return False
    if not any(c.isdigit() for c in password):
        return False
    return True


def sanitize_log_data(data: dict[str, Any]) -> dict[str, Any]:
    """Remove sensitive fields from data before logging"""
    sensitive_fields = {
        "password",
        "token",
        "secret",
        "key",
        "credentials",
        "authorization",
        "x-api-key",
        "hashed_password",
    }

    sanitized = {}
    for key, value in data.items():
        if key.lower() in sensitive_fields:
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_log_data(value)
        else:
            sanitized[key] = value

    return sanitized
