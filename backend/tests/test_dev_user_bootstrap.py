# tests/test_dev_user_bootstrap.py
"""
Unit tests for development user bootstrap functionality
"""

import os
import tempfile

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import verify_password
from app.dev.bootstrap_user import ensure_dev_user, get_dev_user_info
from app.models.base import Base
from app.models.users import User


class TestDevUserBootstrap:
    """Test development user bootstrap functionality"""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        # Create temporary SQLite database
        temp_db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        temp_db_path = temp_db_file.name
        temp_db_file.close()

        # Create engine and session
        engine = create_engine(f"sqlite:///{temp_db_path}")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        # Monkey patch the global SessionLocal
        original_session = None
        base = None
        bootstrap_user = None
        try:
            from app.dev import bootstrap_user
            from app.models import base

            original_session = base.SessionLocal
            base.SessionLocal = SessionLocal

            # Also import and patch the bootstrap module's reference
            bootstrap_user.SessionLocal = SessionLocal

            yield SessionLocal
        finally:
            # Cleanup - close all connections first
            try:
                engine.dispose()
            except Exception:
                pass

            # Restore original session
            if original_session and base and bootstrap_user:
                base.SessionLocal = original_session
                bootstrap_user.SessionLocal = original_session

            # Remove temp file
            try:
                os.unlink(temp_db_path)
            except Exception:
                pass  # Ignore cleanup errors on Windows

    def test_create_dev_user(self, temp_db):
        """Test creating a new dev user"""
        # Ensure user doesn't exist initially
        db = temp_db()
        existing_user = db.query(User).filter(User.username == "user").first()
        assert existing_user is None
        db.close()

        # Create dev user
        user_created = ensure_dev_user()
        assert user_created is True

        # Verify user was created
        db = temp_db()
        user = db.query(User).filter(User.username == "user").first()
        assert user is not None
        assert user.username == "user"
        assert user.email == "dev@ziggy.local"
        assert user.full_name == "ZiggyAI Dev User"
        assert getattr(user, "is_active", False) is True
        assert getattr(user, "is_dev", False) is True
        assert getattr(user, "paper_trading_enabled", False) is True
        assert getattr(user, "is_superuser", False) is False

        # Verify password is hashed correctly
        assert verify_password("user", user.hashed_password) is True
        assert user.hashed_password != "user"  # Should not be plaintext

        # Verify roles
        roles = getattr(user, "roles", None) or []
        assert "DEV_BRAIN" in roles
        assert "PAPER_TRADER" in roles

        # Verify scopes
        scopes = getattr(user, "scopes", None) or []
        assert "trading:paper" in scopes
        assert "brain:dev" in scopes
        assert "signals:read" in scopes

        # Verify profile note
        profile_note = getattr(user, "profile_note", None)
        assert profile_note == "Dev account for ZiggyAI central brain & paper trading"

        db.close()

    def test_idempotent_creation(self, temp_db):
        """Test that running ensure_dev_user multiple times is idempotent"""
        # First creation
        user_created_1 = ensure_dev_user()
        assert user_created_1 is True

        # Second call should not create user
        user_created_2 = ensure_dev_user()
        assert user_created_2 is False

        # Verify only one user exists
        db = temp_db()
        users = db.query(User).filter(User.username == "user").all()
        assert len(users) == 1
        db.close()

    def test_update_existing_user_without_flags(self, temp_db):
        """Test updating existing user that lacks paper trading flags"""
        # Create user without dev flags
        db = temp_db()
        user = User(
            username="user",
            email="test@example.com",
            hashed_password="dummy_hash",
            is_active=True,
            is_dev=False,
            paper_trading_enabled=False,
            roles=[],
        )
        db.add(user)
        db.commit()
        user_id = user.id
        db.close()

        # Run bootstrap
        user_created = ensure_dev_user()
        assert user_created is False  # User existed but was updated

        # Verify user was updated
        db = temp_db()
        updated_user = db.query(User).filter(User.id == user_id).first()
        assert getattr(updated_user, "is_dev", False) is True
        assert getattr(updated_user, "paper_trading_enabled", False) is True

        roles = getattr(updated_user, "roles", None) or []
        assert "DEV_BRAIN" in roles
        assert "PAPER_TRADER" in roles
        db.close()

    def test_get_dev_user_info(self, temp_db):
        """Test getting dev user information"""
        # Test when user doesn't exist
        info = get_dev_user_info()
        assert info is None

        # Create dev user
        ensure_dev_user()

        # Test getting user info
        info = get_dev_user_info()
        assert info is not None
        assert info["exists"] is True
        assert info["paper_trading_enabled"] is True
        assert info["is_dev"] is True
        assert info["is_active"] is True
        assert "DEV_BRAIN" in info["roles"]
        assert "PAPER_TRADER" in info["roles"]
        assert "trading:paper" in info["scopes"]

    def test_no_admin_privileges(self, temp_db):
        """Test that dev user doesn't get admin/superuser privileges"""
        ensure_dev_user()

        db = temp_db()
        user = db.query(User).filter(User.username == "user").first()
        assert getattr(user, "is_superuser", False) is False

        # Verify admin-related scopes are not granted
        scopes = getattr(user, "scopes", None) or []
        roles = getattr(user, "roles", None) or []

        admin_indicators = ["admin", "superuser", "ADMIN", "SUPERUSER"]
        for indicator in admin_indicators:
            assert indicator not in scopes
            assert indicator not in roles

        db.close()


if __name__ == "__main__":
    pytest.main([__file__])
