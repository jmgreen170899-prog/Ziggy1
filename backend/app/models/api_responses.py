# app/models/api_responses.py
"""
Standardized API response models for consistent contract across all endpoints.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standardized error response for all API errors."""

    detail: str = Field(..., description="Human-readable error message")
    code: str = Field(..., description="Machine-readable error code")
    meta: dict[str, Any] = Field(
        default_factory=dict, description="Additional error context and metadata"
    )


class AckResponse(BaseModel):
    """Simple acknowledgment response for operations that don't return data."""

    ok: bool = Field(True, description="Operation succeeded")
    message: str | None = Field(None, description="Optional success message")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Health status (ok, degraded, error)")
    details: dict[str, Any] = Field(default_factory=dict, description="Health check details")


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str = Field(..., description="Response message")
    data: dict[str, Any] | None = Field(None, description="Optional response data")
