"""
Middleware package for ZiggyAI

Exports only request logging middleware. Rate limiting is wired in main.py
with a resilient no-op fallback if SlowAPI isn't installed.
"""

from .request_logging import RequestContextLoggerMiddleware

__all__ = ["RequestContextLoggerMiddleware"]
