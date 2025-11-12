"""
Configuration package for ZiggyAI.

This package contains:
- settings.py: Main Settings class and get_settings() function
- time_tuning.py: Centralized timeout, retry, and queue configuration

For backward compatibility, Settings and get_settings are re-exported at package level.
"""

from app.core.config.settings import Settings, get_settings


__all__ = ["Settings", "get_settings"]
