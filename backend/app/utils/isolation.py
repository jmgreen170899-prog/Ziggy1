"""
Strict isolation utilities for paper trading.
Ensures no live broker credentials are present when paper trading is enabled.
"""

import os

from app.core.logging import get_logger


logger = get_logger("ziggy.isolation")

# Comprehensive list of live broker environment variables
LIVE_BROKER_VARS = [
    # Alpaca
    "ALPACA_API_KEY",
    "ALPACA_SECRET_KEY",
    "ALPACA_API_SECRET",
    "ALPACA_BASE_URL",
    "ALPACA_PAPER_BASE_URL",
    # Interactive Brokers
    "IB_HOST",
    "IB_PORT",
    "IB_CLIENT_ID",
    "IB_ACCOUNT",
    "IB_GATEWAY_PORT",
    # TD Ameritrade
    "TDA_API_KEY",
    "TDA_CLIENT_ID",
    "TDA_REDIRECT_URI",
    "TDA_ACCOUNT",
    "TDA_REFRESH_TOKEN",
    # E*TRADE
    "ETRADE_API_KEY",
    "ETRADE_SECRET_KEY",
    "ETRADE_SANDBOX",
    # Robinhood
    "ROBINHOOD_USERNAME",
    "ROBINHOOD_PASSWORD",
    "ROBINHOOD_MFA_CODE",
    # Other common broker vars
    "BROKER_API_KEY",
    "BROKER_SECRET",
    "TRADING_API_KEY",
    "LIVE_TRADING_ENABLED",
]


def check_strict_isolation() -> tuple[bool, list[str]]:
    """
    Check if strict paper trading isolation is maintained.

    Returns:
        Tuple of (is_isolated, detected_vars)
        - is_isolated: True if no live broker vars detected
        - detected_vars: List of detected live broker environment variables
    """
    detected_vars = []

    for var in LIVE_BROKER_VARS:
        value = os.getenv(var)
        if value:
            detected_vars.append(var)

    is_isolated = len(detected_vars) == 0

    # Gated logging: only WARN in production with trading actually enabled.
    # Otherwise, log at DEBUG level without values (names only) and no stack traces.
    if not is_isolated:
        env = (
            (os.getenv("APP_ENV") or os.getenv("ENV") or "development").strip().lower()
        )
        trading_enabled = (os.getenv("TRADING_ENABLED") or "false").strip().lower() in {
            "1",
            "true",
            "yes",
        }
        if env == "production" and trading_enabled:
            logger.warning(
                "Strict isolation violation detected",
                extra={"detected_vars": detected_vars, "count": len(detected_vars)},
            )
        else:
            logger.debug(
                "Strict isolation note (dev/paper-only)",
                extra={"detected_vars": detected_vars, "count": len(detected_vars)},
            )

    return is_isolated, detected_vars


def enforce_strict_isolation() -> None:
    """
    Enforce strict isolation by raising an exception if live broker vars are detected.

    Raises:
        RuntimeError: If live broker environment variables are detected
    """
    is_isolated, detected_vars = check_strict_isolation()

    if not is_isolated:
        # Keep message names-only (values redacted by design)
        error_msg = (
            "Strict paper trading isolation violated. Live broker environment variables detected: "
            f"{detected_vars}"
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    logger.info("Strict paper trading isolation verified")


def should_enforce_isolation() -> bool:
    """
    Check if strict isolation should be enforced based on environment settings.

    Returns:
        True if isolation should be enforced
    """
    paper_enabled = os.getenv("PAPER_TRADING_ENABLED", "false").lower() == "true"
    strict_isolation = os.getenv("PAPER_STRICT_ISOLATION", "false").lower() == "true"

    return paper_enabled and strict_isolation
