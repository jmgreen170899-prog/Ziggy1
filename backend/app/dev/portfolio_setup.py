# backend/app/dev/portfolio_setup.py
"""
Development Portfolio Setup for ZiggyAI Paper Trading

This module sets up a paper trading portfolio for the dev user with initial capital
and autonomous trading configuration. It integrates with the trading system to enable
ZiggyAI to make autonomous trading decisions within safe parameters.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

from app.models.trading import Portfolio, Position
from app.trading.signals import get_trading_manager


logger = logging.getLogger("ziggy.dev.portfolio")

# Default portfolio configuration for dev user
DEFAULT_PORTFOLIO_CONFIG = {
    "initial_capital": 100000.00,  # $100K paper trading capital
    "max_position_size": 0.05,  # 5% max per position (conservative)
    "risk_tolerance": "MODERATE",  # Balanced risk approach
    "max_daily_loss": 1000.00,  # $1K max daily loss limit
    "max_positions": 10,  # Max 10 concurrent positions
    "auto_trading_enabled": True,  # Enable autonomous trading
}


def ensure_dev_user_portfolio(user_id: str = "dev-user") -> dict[str, Any]:
    """
    Create or update the dev user's portfolio for paper trading.

    Args:
        user_id: The dev user ID (default: "dev-user")

    Returns:
        Dict containing portfolio status and configuration
    """
    from app.models.base import SessionLocal

    if not SessionLocal:
        logger.error("Database not initialized. Cannot create dev portfolio.")
        return {"status": "error", "error": "Database not initialized"}

    db = SessionLocal()
    try:
        # Check if portfolio exists
        portfolio = db.query(Portfolio).filter(Portfolio.name == f"{user_id}_portfolio").first()

        if portfolio:
            logger.info(f"Dev portfolio exists: ${portfolio.current_value:.2f} value")
            return {
                "status": "exists",
                "portfolio_id": portfolio.id,
                "current_value": float(portfolio.current_value),
                "cash_balance": float(portfolio.cash_balance),
                "initial_capital": float(portfolio.initial_capital),
                "is_paper_trading": portfolio.is_paper_trading,
                "created_at": portfolio.created_at.isoformat(),
            }

        # Create new portfolio
        portfolio = Portfolio(
            name=f"{user_id}_portfolio",
            description="ZiggyAI Development Paper Trading Portfolio",
            initial_capital=Decimal(str(DEFAULT_PORTFOLIO_CONFIG["initial_capital"])),
            current_value=Decimal(str(DEFAULT_PORTFOLIO_CONFIG["initial_capital"])),
            cash_balance=Decimal(str(DEFAULT_PORTFOLIO_CONFIG["initial_capital"])),
            max_position_size=Decimal(str(DEFAULT_PORTFOLIO_CONFIG["max_position_size"])),
            risk_tolerance=DEFAULT_PORTFOLIO_CONFIG["risk_tolerance"],
            is_active=True,
            is_paper_trading=True,
        )

        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)

        logger.info(
            f"Created dev portfolio with ${DEFAULT_PORTFOLIO_CONFIG['initial_capital']:,.2f} initial capital"
        )

        return {
            "status": "created",
            "portfolio_id": portfolio.id,
            "current_value": float(portfolio.current_value),
            "cash_balance": float(portfolio.cash_balance),
            "initial_capital": float(portfolio.initial_capital),
            "is_paper_trading": portfolio.is_paper_trading,
            "created_at": portfolio.created_at.isoformat(),
            "config": DEFAULT_PORTFOLIO_CONFIG,
        }

    except SQLAlchemyError as e:
        logger.error(f"Database error creating dev portfolio: {e}")
        return {"status": "error", "error": f"Database error: {e!s}"}
    except Exception as e:
        logger.error(f"Unexpected error creating dev portfolio: {e}")
        return {"status": "error", "error": f"Unexpected error: {e!s}"}
    finally:
        db.close()


def configure_autonomous_trading(portfolio_id: int) -> dict[str, Any]:
    """
    Configure autonomous trading parameters for ZiggyAI.

    Args:
        portfolio_id: The portfolio ID to configure

    Returns:
        Dict containing configuration status
    """
    try:
        # Get trading manager and enable paper trading
        manager = get_trading_manager()
        manager.enable_paper_trading()

        # Configure risk parameters
        config = {
            "portfolio_id": portfolio_id,
            "max_position_size_pct": DEFAULT_PORTFOLIO_CONFIG["max_position_size"] * 100,
            "max_daily_loss": DEFAULT_PORTFOLIO_CONFIG["max_daily_loss"],
            "max_positions": DEFAULT_PORTFOLIO_CONFIG["max_positions"],
            "auto_trading": DEFAULT_PORTFOLIO_CONFIG["auto_trading_enabled"],
            "paper_trading": True,
            "risk_tolerance": DEFAULT_PORTFOLIO_CONFIG["risk_tolerance"].lower(),
        }

        logger.info(f"Configured autonomous trading for portfolio {portfolio_id}")

        return {
            "status": "configured",
            "portfolio_id": portfolio_id,
            "trading_config": config,
            "message": "Autonomous trading configured successfully",
        }

    except Exception as e:
        logger.error(f"Error configuring autonomous trading: {e}")
        return {"status": "error", "error": f"Configuration error: {e!s}"}


def get_portfolio_status(user_id: str = "dev-user") -> dict[str, Any]:
    """
    Get current portfolio status and trading configuration.

    Args:
        user_id: The user ID to check

    Returns:
        Dict containing portfolio status
    """
    from app.models.base import SessionLocal

    if not SessionLocal:
        logger.error("Database not initialized.")
        return {"status": "error", "error": "Database not initialized"}

    db = SessionLocal()
    try:
        portfolio = db.query(Portfolio).filter(Portfolio.name == f"{user_id}_portfolio").first()

        if not portfolio:
            return {"status": "not_found", "message": "Portfolio not found for user"}

        # Get positions count
        positions_count = (
            db.query(Position)
            .filter(Position.portfolio_id == portfolio.id, Position.quantity != 0)
            .count()
        )

        # Get trading manager status
        manager = get_trading_manager()
        portfolio_summary = manager.get_portfolio_summary()

        return {
            "status": "active" if portfolio.is_active else "inactive",
            "portfolio_id": portfolio.id,
            "current_value": float(portfolio.current_value),
            "cash_balance": float(portfolio.cash_balance),
            "initial_capital": float(portfolio.initial_capital),
            "unrealized_pnl": portfolio_summary.get("total_pnl", 0.0),
            "positions_count": positions_count,
            "max_positions": DEFAULT_PORTFOLIO_CONFIG["max_positions"],
            "paper_trading": portfolio.is_paper_trading,
            "auto_trading_enabled": DEFAULT_PORTFOLIO_CONFIG["auto_trading_enabled"],
            "risk_tolerance": portfolio.risk_tolerance,
            "last_updated": portfolio.updated_at.isoformat(),
        }

    except Exception as e:
        logger.error(f"Error getting portfolio status: {e}")
        return {"status": "error", "error": f"Status check error: {e!s}"}
    finally:
        db.close()


def fund_portfolio(user_id: str = "dev-user", additional_capital: float = 0.0) -> dict[str, Any]:
    """
    Add additional capital to the dev user's portfolio.

    Args:
        user_id: The user ID
        additional_capital: Additional capital to add

    Returns:
        Dict containing funding status
    """
    if additional_capital <= 0:
        return {"status": "error", "error": "Additional capital must be positive"}

    from app.models.base import SessionLocal

    if not SessionLocal:
        logger.error("Database not initialized.")
        return {"status": "error", "error": "Database not initialized"}

    db = SessionLocal()
    try:
        portfolio = db.query(Portfolio).filter(Portfolio.name == f"{user_id}_portfolio").first()

        if not portfolio:
            return {"status": "error", "error": "Portfolio not found"}

        # Add capital to both current value and cash balance
        old_value = float(portfolio.current_value)
        old_cash = float(portfolio.cash_balance)

        portfolio.current_value += Decimal(str(additional_capital))
        portfolio.cash_balance += Decimal(str(additional_capital))
        portfolio.updated_at = datetime.utcnow()

        db.commit()

        logger.info(f"Added ${additional_capital:,.2f} to dev portfolio")

        return {
            "status": "funded",
            "portfolio_id": portfolio.id,
            "old_value": old_value,
            "new_value": float(portfolio.current_value),
            "old_cash": old_cash,
            "new_cash": float(portfolio.cash_balance),
            "added_capital": additional_capital,
        }

    except Exception as e:
        logger.error(f"Error funding portfolio: {e}")
        return {"status": "error", "error": f"Funding error: {e!s}"}
    finally:
        db.close()


if __name__ == "__main__":
    # Test the portfolio setup
    print("Setting up dev user portfolio...")
    result = ensure_dev_user_portfolio()
    print(f"Portfolio setup result: {result}")

    if result.get("status") in ["created", "exists"]:
        config_result = configure_autonomous_trading(result["portfolio_id"])
        print(f"Trading configuration result: {config_result}")

        status = get_portfolio_status()
        print(f"Portfolio status: {status}")
