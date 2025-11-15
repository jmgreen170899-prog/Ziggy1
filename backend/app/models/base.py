# app/models/base.py
from __future__ import annotations

import os
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import MetaData, create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")
DATA_DIR = os.getenv("DATA_DIR", "./data")
DB_SQLITE_PRAGMAS = os.getenv("DB_SQLITE_PRAGMAS", "ON").strip().lower() in {
    "1",
    "true",
    "on",
    "yes",
}

# SQLAlchemy setup
Base = declarative_base()
metadata = MetaData()

# Engine and session (will be initialized later)
engine = None
SessionLocal = None


def init_database(database_url: str | None = None) -> None:
    """Initialize database connection"""
    global engine, SessionLocal

    url = database_url or DATABASE_URL
    if not url:
        # Default to SQLite for development under DATA_DIR
        data_dir = Path(DATA_DIR).resolve()
        data_dir.mkdir(parents=True, exist_ok=True)
        url = f"sqlite:///{(data_dir / 'ziggy.db').as_posix()}"

    # Ensure DATA_DIR exists if using SQLite
    if url.startswith("sqlite"):
        try:
            # If relative sqlite path like sqlite:///./data/ziggy.db ensure the folder exists
            if ":///" in url:
                # Try to derive path after the scheme
                db_path = url.split(":///", 1)[1]
                # Strip query string if present
                db_path = db_path.split("?", 1)[0]
                p = Path(db_path)
                if not p.is_absolute():
                    p = Path.cwd() / p
                p.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    connect_args = {}
    if url.startswith("sqlite"):
        # Needed for threaded FastAPI + SQLite
        connect_args["check_same_thread"] = False

    engine = create_engine(
        url,
        pool_pre_ping=True,
        echo=False,  # Set to True for SQL logging
        connect_args=connect_args,
    )

    # Apply SQLite PRAGMAs for durability and performance (WAL)
    if DB_SQLITE_PRAGMAS and url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def _set_sqlite_pragmas(dbapi_conn, _):  # type: ignore[no-redef]
            try:
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA journal_mode=WAL;")
                cursor.execute("PRAGMA synchronous=NORMAL;")
                cursor.execute("PRAGMA foreign_keys=ON;")
                cursor.execute("PRAGMA busy_timeout=5000;")
                cursor.close()
            except Exception:
                # Non-fatal in case driver doesn't support PRAGMA here
                pass

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables() -> None:
    """Create all tables"""
    if engine:
        Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency to get database session"""
    if not SessionLocal:
        # Return a clean 503 for DB-backed endpoints when DB is unavailable
        # FastAPI will serialize this as a JSON error response
        raise HTTPException(
            status_code=503, detail={"status": "down", "reason": "db_unavailable"}
        )

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
