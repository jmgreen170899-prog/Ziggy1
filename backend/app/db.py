from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine


# Database utilities: build engine and quickly verify connectivity.
#
# get_engine_with_connectivity(url: str | None) -> tuple[Engine | None, bool, str]
# - Creates a SQLAlchemy engine with sensible defaults (pool_pre_ping, small pool).
# - Attempts a quick connectivity check (SELECT 1) with a short connect timeout.
# - Returns (engine, connected, dialect).
#
# If in development and ALLOW_SQLITE_FALLBACK=true and not connected, builds a
# SQLite engine at ziggy_dev.db and returns it as connected with dialect='sqlite'.


def _dialect_from_url(url: str | None) -> str:
    if not url:
        return "unknown"
    low = url.lower()
    if low.startswith("postgres") or ":postgres" in low or "+psycopg" in low:
        return "postgres"
    if low.startswith("sqlite"):
        return "sqlite"
    return low.split(":", 1)[0]


logger = logging.getLogger("ziggy.db")

# Shared DB state exported for app-wide checks
db_state: dict[str, object] = {
    "configured": False,
    "connected": False,
    "dialect": "unknown",
    "fallback": False,  # True when we intentionally fall back to local SQLite
}


def get_engine_with_connectivity(url: str | None) -> tuple[Engine | None, bool, str]:
    env = (os.getenv("APP_ENV") or os.getenv("ENV") or "development").strip().lower()
    allow_fallback = (os.getenv("ALLOW_SQLITE_FALLBACK") or "false").strip().lower() in {
        "1",
        "true",
        "yes",
    }
    data_dir = Path(os.getenv("DATA_DIR", "./data")).resolve()
    data_dir.mkdir(parents=True, exist_ok=True)

    # Default to local SQLite when no URL provided
    if not url:
        url = f"sqlite:///{(data_dir / 'ziggy.db').as_posix()}"

    dialect = _dialect_from_url(url)
    engine: Engine | None = None
    connected = False

    if url:
        connect_args = {}
        if dialect == "postgres":
            # psycopg2 connect timeout (seconds)
            connect_args["connect_timeout"] = 2
        elif dialect == "sqlite":
            connect_args["check_same_thread"] = False
        try:
            engine = create_engine(
                url,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=5,
                pool_timeout=5,
                pool_recycle=1800,
                connect_args=connect_args,  # safe for postgres/sqlite
                echo=False,
            )
            # Apply SQLite PRAGMAs for durability (WAL) on connect
            if dialect == "sqlite":

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
                        pass

            # Quick connectivity check
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            connected = True
        except Exception:
            connected = False

    # Dev fallback to SQLite if allowed
    if env in {"development", "dev"} and not connected and allow_fallback:
        try:
            sqlite_url = "sqlite:///./ziggy_dev.db"
            engine = create_engine(
                sqlite_url,
                pool_pre_ping=True,
                echo=False,
            )
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            connected = True
            dialect = "sqlite"
        except Exception:
            engine = None
            connected = False
            dialect = "sqlite"

    return engine, connected, dialect


async def try_connect(url: str | None = None) -> bool:
    """Attempt a quick connectivity check and update db_state.

    Returns True if reachable, False otherwise. Does not initialize ORM sessions.
    """
    # Default to local SQLite when no URL provided
    if not url:
        data_dir = Path(os.getenv("DATA_DIR", "./data")).resolve()
        data_dir.mkdir(parents=True, exist_ok=True)
        url = f"sqlite:///{(data_dir / 'ziggy.db').as_posix()}"
    provided_dialect = _dialect_from_url(url)
    _, connected, dialect = get_engine_with_connectivity(url)
    # Update state atomically
    db_state["configured"] = bool(url)
    db_state["connected"] = bool(connected)
    db_state["dialect"] = dialect
    # Heuristic: if caller provided non-sqlite URL but we ended up with sqlite, treat as fallback
    db_state["fallback"] = bool(connected and dialect == "sqlite" and provided_dialect != "sqlite")
    if connected:
        logger.info("DB connectivity OK", extra={"dialect": dialect})
    else:
        logger.warning(
            "DB connectivity failed", extra={"configured": bool(url), "dialect": dialect}
        )
    return bool(connected)


async def init_with_backoff(
    url: str | None = None, fallback_sqlite_path: str | None = None
) -> None:
    """Background task: retry DB connect + ORM init with exponential backoff.

    Backoff sequence: 2s, 4s, 8s, ... capped at 60s. If still failing and a
    fallback path is provided, switch to SQLite and continue.
    On success, initializes ORM and flips db_state["connected"]=True.
    """
    from app.models import base as models_base  # lazy import to avoid cycles

    # Default to local SQLite when no URL provided
    if not url:
        data_dir = Path(os.getenv("DATA_DIR", "./data")).resolve()
        data_dir.mkdir(parents=True, exist_ok=True)
        url = f"sqlite:///{(data_dir / 'ziggy.db').as_posix()}"
    delay = 2.0
    max_delay = 60.0

    # Immediate SQLite fallback in development when no URL is provided
    if (not url) and fallback_sqlite_path:
        try:
            from app.models import base as models_base  # local import

            sqlite_url = f"sqlite:///{fallback_sqlite_path}"
            models_base.init_database(sqlite_url)
            import contextlib

            with contextlib.suppress(Exception):
                models_base.create_tables()
            db_state["connected"] = True
            db_state["dialect"] = "sqlite"
            db_state["fallback"] = True
            logger.warning(
                "Using SQLite fallback (no DATABASE_URL provided)",
                extra={"sqlite_path": fallback_sqlite_path},
            )
            return
        except Exception as e:  # pragma: no cover - defensive
            logger.warning("Immediate SQLite fallback failed", extra={"error": str(e)})

    attempts = 0
    while True:
        try:
            _, connected, dialect = get_engine_with_connectivity(url)
            db_state["configured"] = bool(url)
            db_state["dialect"] = dialect
            if connected:
                # Initialize ORM session factory once connected
                try:
                    models_base.init_database(url)
                    # Best-effort table creation when Alembic is not configured
                    import contextlib

                    with contextlib.suppress(Exception):
                        models_base.create_tables()
                except Exception as e:  # pragma: no cover - defensive
                    logger.warning("ORM init failed after DB connect", extra={"error": str(e)})
                    # keep going; SessionLocal may still be usable if engine bound
                db_state["connected"] = True
                db_state["fallback"] = False  # primary connected
                logger.info(
                    "Database ready",
                    extra={"dialect": dialect, "configured": bool(url)},
                )
                return
        except Exception as e:  # pragma: no cover - defensive
            logger.warning("DB init attempt error", extra={"error": str(e)})
        attempts += 1

        # Consider fallback to SQLite if provided; do not wait long in development
        if fallback_sqlite_path and attempts >= 1:
            try:
                import contextlib

                sqlite_url = f"sqlite:///{fallback_sqlite_path}"
                models_base.init_database(sqlite_url)
                with contextlib.suppress(Exception):
                    models_base.create_tables()
                db_state["connected"] = True
                db_state["dialect"] = "sqlite"
                db_state["fallback"] = True
                logger.warning(
                    "Postgres unreachable, using SQLite fallback.",
                    extra={"sqlite_path": fallback_sqlite_path},
                )
                return
            except Exception as e:
                logger.warning("SQLite fallback failed", extra={"error": str(e)})
                # continue retrying primary

        # Not connected yet - wait and retry
        db_state["connected"] = False
        logger.info("DB retry scheduled", extra={"delay_s": delay})
        await asyncio.sleep(delay)
        delay = min(max_delay, delay * 2)
