# app/dev/bootstrap_user.py
"""
Development user bootstrap for ZiggyAI
Creates a dev user for paper trading and central-brain development
"""

from __future__ import annotations

import logging

from sqlalchemy.exc import IntegrityError

from app.core.security import get_password_hash
from app.models.users import User


logger = logging.getLogger("ziggy.dev.bootstrap")


def ensure_dev_user(session_local) -> dict:
    """Ensure the development user exists with proper configuration.

    Only call this when the DB is connected. Returns a status dict.
    {"ok": True|False, "created": bool}
    """
    db = session_local()
    try:
        # Look for existing user
        existing_user = db.query(User).filter(User.username == "user").first()

        if existing_user:
            # Update if missing paper trading flag
            updated = False
            if not getattr(existing_user, "paper_trading_enabled", False):
                existing_user.paper_trading_enabled = True  # type: ignore[assignment]
                updated = True

            if not getattr(existing_user, "is_dev", False):
                existing_user.is_dev = True  # type: ignore[assignment]
                updated = True

            # Ensure roles are set
            current_roles = getattr(existing_user, "roles", None) or []
            required_roles = ["DEV_BRAIN", "PAPER_TRADER"]
            for role in required_roles:
                if role not in current_roles:
                    current_roles.append(role)
                    updated = True

            if updated:
                existing_user.roles = current_roles  # type: ignore[assignment]
                db.commit()
                logger.info("Updated dev user 'user' with missing flags/roles")
            return {"ok": True, "created": False}

        # Create new dev user
        dev_user = User(
            username="user",
            email="dev@ziggy.local",
            full_name="ZiggyAI Dev User",
            hashed_password=get_password_hash("user"),
            is_active=True,
            is_dev=True,
            paper_trading_enabled=True,
            roles=["DEV_BRAIN", "PAPER_TRADER"],
            scopes=["trading:paper", "brain:dev", "signals:read"],
            profile_note="Dev account for ZiggyAI central brain & paper trading",
        )

        db.add(dev_user)
        db.commit()
        db.refresh(dev_user)
        logger.info("Dev user bootstrap succeeded")
        return {"ok": True, "created": True}

    except IntegrityError:
        db.rollback()
        # Likely a duplicate username/race condition — treat as already exists
        logger.info("Dev user bootstrap: user 'user' already exists")
        return {"ok": True, "created": False}
    except Exception as e:
        db.rollback()
        logger.error("Dev user bootstrap failed", extra={"error": repr(e)})
        return {"ok": False, "created": False}
    finally:
        db.close()


def get_dev_user_info() -> dict | None:
    """
    Get information about the dev user for health checks.

    Returns:
        dict: User info or None if user doesn't exist
    """
    from app.models.base import get_db

    db = next(get_db())
    try:
        user = db.query(User).filter(User.username == "user").first()
        if not user:
            return None

        return {
            "exists": True,
            "roles": getattr(user, "roles", None) or [],
            "paper_trading_enabled": getattr(user, "paper_trading_enabled", False),
            "is_dev": getattr(user, "is_dev", False),
            "is_active": getattr(user, "is_active", True),
            "scopes": getattr(user, "scopes", None) or [],
        }
    except Exception as e:
        logger.error(f"Failed to get dev user info: {e}")
        return None
    finally:
        db.close()
