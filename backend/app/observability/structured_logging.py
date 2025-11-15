"""
Standardized structured logging for ZiggyAI.

Provides consistent logging keys across all subsystems:
- subsystem: Module/domain name (e.g., "trading", "cognitive", "paper_lab")
- ticker: Stock symbol when applicable
- run_id: Paper trading or backtest run identifier
- theory_name: Cognitive theory or strategy name
- operation: Type of operation being performed
- duration_sec: Operation duration
- error: Error message if applicable

Usage:
    from app.observability.structured_logging import get_structured_logger, log_operation

    logger = get_structured_logger("trading")

    with log_operation(logger, "backtest", ticker="AAPL", strategy="sma50_cross"):
        # Your code here
        pass
"""

import logging
import time
from contextlib import contextmanager
from typing import Any, Optional


def get_structured_logger(subsystem: str) -> logging.Logger:
    """
    Get a logger with standardized subsystem name.

    Args:
        subsystem: Module/domain name (e.g., "trading", "cognitive")

    Returns:
        Logger instance configured for the subsystem
    """
    return logging.getLogger(f"backend.{subsystem}")


@contextmanager
def log_operation(
    logger: logging.Logger,
    operation: str,
    ticker: Optional[str] = None,
    run_id: Optional[str] = None,
    theory_name: Optional[str] = None,
    strategy: Optional[str] = None,
    **extra_context: Any,
):
    """
    Context manager for logging operations with standardized keys.

    Automatically logs operation start, completion, and timing.
    Captures exceptions and logs them with full context.

    Args:
        logger: Logger instance
        operation: Operation name (e.g., "backtest", "enhance_decision")
        ticker: Stock symbol (optional)
        run_id: Run identifier (optional)
        theory_name: Cognitive theory name (optional)
        strategy: Strategy name (optional)
        **extra_context: Additional context to log

    Example:
        with log_operation(logger, "backtest", ticker="AAPL", strategy="sma50_cross"):
            result = run_backtest(...)
    """
    # Build context dict with standardized keys
    context = {
        "operation": operation,
    }

    if ticker:
        context["ticker"] = ticker
    if run_id:
        context["run_id"] = run_id
    if theory_name:
        context["theory_name"] = theory_name
    if strategy:
        context["strategy"] = strategy

    # Add any extra context
    context.update(extra_context)

    # Log operation start
    logger.info(f"Starting {operation}", extra=context)

    start_time = time.time()
    error_occurred = False

    try:
        yield context  # Yield context so caller can add to it

    except Exception as e:
        error_occurred = True
        duration = time.time() - start_time

        error_context = {
            **context,
            "duration_sec": round(duration, 3),
            "error": str(e),
            "error_type": type(e).__name__,
        }

        logger.error(f"Failed {operation}", extra=error_context, exc_info=True)
        raise

    finally:
        if not error_occurred:
            duration = time.time() - start_time

            complete_context = {**context, "duration_sec": round(duration, 3)}

            logger.info(f"Completed {operation}", extra=complete_context)


def log_external_call(
    logger: logging.Logger,
    provider: str,
    operation: str,
    duration_sec: float,
    status: str = "success",
    timeout_sec: Optional[float] = None,
    **extra: Any,
):
    """
    Log an external service call with timing and timeout info.

    Args:
        logger: Logger instance
        provider: External service name (e.g., "yfinance", "openai")
        operation: Operation performed (e.g., "fetch_ohlc", "chat_completion")
        duration_sec: Call duration in seconds
        status: Call status ("success", "timeout", "error")
        timeout_sec: Configured timeout (optional)
        **extra: Additional context
    """
    context = {
        "provider": provider,
        "operation": operation,
        "duration_sec": round(duration_sec, 3),
        "status": status,
    }

    if timeout_sec:
        context["timeout_sec"] = timeout_sec
        context["timeout_exceeded"] = duration_sec > timeout_sec

    context.update(extra)

    if status == "timeout":
        logger.warning(f"External call timeout: {provider}.{operation}", extra=context)
    elif status == "error":
        logger.error(f"External call failed: {provider}.{operation}", extra=context)
    elif duration_sec > 5.0:  # Log slow calls
        logger.warning(f"Slow external call: {provider}.{operation}", extra=context)
    else:
        logger.debug(f"External call: {provider}.{operation}", extra=context)


def log_slowdown(
    logger: logging.Logger,
    operation: str,
    duration_sec: float,
    threshold_sec: float = 5.0,
    **context: Any,
):
    """
    Log when an operation exceeds expected duration.

    Args:
        logger: Logger instance
        operation: Operation name
        duration_sec: Actual duration
        threshold_sec: Expected duration threshold
        **context: Additional context
    """
    if duration_sec > threshold_sec:
        log_context = {
            "operation": operation,
            "duration_sec": round(duration_sec, 3),
            "threshold_sec": threshold_sec,
            "slowdown_factor": round(duration_sec / threshold_sec, 2),
            **context,
        }

        logger.warning(f"Slow operation detected: {operation}", extra=log_context)


# ---- Pre-configured loggers for common subsystems ----

trading_logger = get_structured_logger("trading")
cognitive_logger = get_structured_logger("cognitive")
paper_lab_logger = get_structured_logger("paper_lab")
screener_logger = get_structured_logger("screener")
learning_logger = get_structured_logger("learning")
chat_logger = get_structured_logger("chat")
market_data_logger = get_structured_logger("market_data")
signals_logger = get_structured_logger("signals")
