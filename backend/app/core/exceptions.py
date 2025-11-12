# app/core/exceptions.py
from __future__ import annotations

import logging
from typing import Any

from fastapi import HTTPException, status


logger = logging.getLogger("ziggy.exceptions")


class ZiggyBaseException(Exception):
    """Base exception for all Ziggy-specific errors"""

    def __init__(
        self, message: str, details: dict[str, Any] | None = None, correlation_id: str | None = None
    ):
        self.message = message
        self.details = details or {}
        self.correlation_id = correlation_id
        super().__init__(message)


class ConfigurationError(ZiggyBaseException):
    """Raised when configuration is invalid or missing"""

    pass


class ProviderError(ZiggyBaseException):
    """Raised when external data provider fails"""

    pass


class ProviderTimeoutError(ProviderError):
    """Raised when provider request times out"""

    pass


class ProviderUnavailableError(ProviderError):
    """Raised when all providers in chain fail"""

    pass


class DataValidationError(ZiggyBaseException):
    """Raised when data validation fails"""

    pass


class AuthenticationError(ZiggyBaseException):
    """Raised when authentication fails"""

    pass


class AuthorizationError(ZiggyBaseException):
    """Raised when user lacks required permissions"""

    pass


class RateLimitError(ZiggyBaseException):
    """Raised when rate limit is exceeded"""

    pass


class TradingError(ZiggyBaseException):
    """Raised when trading operations fail"""

    pass


class MarketDataError(ProviderError):
    """Raised when market data is unavailable or invalid"""

    pass


# HTTP Exception mapping
def ziggy_exception_to_http(exc: ZiggyBaseException) -> HTTPException:
    """Convert Ziggy exceptions to HTTP exceptions"""

    status_mapping = {
        ConfigurationError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        ProviderError: status.HTTP_503_SERVICE_UNAVAILABLE,
        ProviderTimeoutError: status.HTTP_504_GATEWAY_TIMEOUT,
        ProviderUnavailableError: status.HTTP_503_SERVICE_UNAVAILABLE,
        DataValidationError: status.HTTP_422_UNPROCESSABLE_ENTITY,
        AuthenticationError: status.HTTP_401_UNAUTHORIZED,
        AuthorizationError: status.HTTP_403_FORBIDDEN,
        RateLimitError: status.HTTP_429_TOO_MANY_REQUESTS,
        TradingError: status.HTTP_400_BAD_REQUEST,
        MarketDataError: status.HTTP_503_SERVICE_UNAVAILABLE,
    }

    status_code = status_mapping.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)

    detail = {
        "error": exc.__class__.__name__,
        "message": exc.message,
        "details": exc.details,
    }

    if exc.correlation_id:
        detail["correlation_id"] = exc.correlation_id

    return HTTPException(status_code=status_code, detail=detail)


class ErrorResponse:
    """Standardized error response format"""

    @staticmethod
    def create(
        error_type: str,
        message: str,
        details: dict[str, Any] | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        response = {
            "success": False,
            "error": {
                "type": error_type,
                "message": message,
                "timestamp": None,  # Will be set by middleware
            },
        }

        if details:
            response["error"]["details"] = details

        if correlation_id:
            response["error"]["correlation_id"] = correlation_id

        return response


def safe_execute(func, default_value=None, log_errors=True):
    """Execute function safely with error handling"""
    try:
        return func()
    except Exception as e:
        if log_errors:
            logger.exception(f"Safe execution failed: {e}")
        return default_value
