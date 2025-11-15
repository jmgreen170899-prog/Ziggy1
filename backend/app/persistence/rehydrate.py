from __future__ import annotations

import asyncio
import contextlib
import os
from pathlib import Path
from typing import Any

from app.core.logging import get_logger
from app.db import db_state, init_with_backoff
from app.models import base as models_base
from app.persistence import repository as repo
from app.persistence.audit_log import AuditLog
from app.tasks.paper_worker import get_paper_worker


logger = get_logger("ziggy.snapshotter")


def _env_path(key: str, default: str) -> str:
    p = os.getenv(key) or default
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    return p


async def ensure_db_with_fallback() -> None:
    """Ensure DB is connected; fallback to SQLite file if primary unreachable after backoff."""
    primary = os.getenv("DATABASE_URL")
    fallback_sqlite_path = _env_path(
        "DB_FALLBACK_SQLITE_PATH", str(Path("./data/ziggy_fallback.db").resolve())
    )

    # Attempt background init if not connected
    with contextlib.suppress(Exception):
        await init_with_backoff(primary)

    # If still not connected, force SQLite fallback
    if not bool(db_state.get("connected")):
        try:
            sqlite_url = f"sqlite:///{fallback_sqlite_path}"
            models_base.init_database(sqlite_url)
            with contextlib.suppress(Exception):
                models_base.create_tables()
            db_state["connected"] = True
            db_state["dialect"] = "sqlite"
            logger.warning("Postgres unreachable, using SQLite fallback.")
        except Exception as e:
            logger.warning("SQLite fallback failed", extra={"error": str(e)})


async def resume_from_persistence() -> dict[str, Any]:
    """Rehydrate runtime state from DB (or JSONL) when available.

    Strategy:
    - Ensure DB is connected (with fallback)
    - If RUN_RESUME=true and a worker is available, load latest run and apply states
    - If DB empty but audit log exists, replay to reconstruct and apply best-effort state
    """
    if (os.getenv("RUN_RESUME") or "true").strip().lower() not in {"1", "true", "yes"}:
        return {"ok": False, "reason": "resume_disabled"}

    await ensure_db_with_fallback()

    # Try to get worker (may not exist yet)
    worker = get_paper_worker()
    if not worker:
        # Defer: background attempt later until worker appears
        # Keep reference to avoid GC
        if not hasattr(resume_from_persistence, "_bg_tasks"):
            resume_from_persistence._bg_tasks = set()  # type: ignore[attr-defined]
        _t = asyncio.create_task(_retry_apply_when_worker())
        resume_from_persistence._bg_tasks.add(_t)  # type: ignore[attr-defined]
        _t.add_done_callback(resume_from_persistence._bg_tasks.discard)  # type: ignore[attr-defined]
        return {"ok": True, "deferred": True}

    return await _apply_resume_to_worker(worker)


async def _retry_apply_when_worker() -> None:
    for _ in range(30):  # ~15s
        await asyncio.sleep(0.5)
        worker = get_paper_worker()
        if worker:
            try:
                await _apply_resume_to_worker(worker)
            except Exception as e:
                logger.warning("Deferred resume failed", extra={"error": str(e)})
            return


async def _apply_resume_to_worker(worker) -> dict[str, Any]:
    # DB path first
    applied = False
    positions_n = trades_n = arms_k = 0
    learner_loaded = False

    if getattr(models_base, "SessionLocal", None):
        db = models_base.SessionLocal()
        try:
            run = repo.load_latest_run(db)
            if run:
                rid = getattr(run, "id", None)
                run_id = rid if isinstance(rid, str) else str(rid)
                positions = [
                    {"symbol": p.symbol, "qty": p.qty, "avg_price": p.avg_price}
                    for p in repo.load_positions(db, run_id)
                ]
                pnl_points = [
                    {"ts": r.ts.isoformat(), "equity": r.equity, "idx": r.idx or 0}
                    for r in repo.load_pnl_points(db, run_id)
                ]
                bandit = repo.load_bandit_latest(db, run_id)
                learner = repo.load_learner_latest(db, run_id)
                queue = repo.load_queue_latest(db, run_id)

                # Apply to components
                if hasattr(worker.engine, "set_state"):
                    await worker.engine.set_state(
                        {
                            "run_id": run_id,
                            "positions": positions,
                            "equity_curve": pnl_points[-500:],
                            "params": (run.meta or {}).get("params_json")
                            or (run.meta or {}),
                        }
                    )
                    positions_n = len(positions)
                if bandit and hasattr(worker.allocator, "set_state"):
                    payload = getattr(bandit, "payload", None) or {}
                    if asyncio.iscoroutinefunction(worker.allocator.set_state):
                        await worker.allocator.set_state({"arms": payload})
                    else:
                        worker.allocator.set_state({"arms": payload})
                    arms_k = len(payload) if isinstance(payload, dict) else 0
                if learner and hasattr(worker.learner, "set_state"):
                    worker.learner.set_state(learner.bytes, (learner.meta or {}))
                    learner_loaded = True
                if queue and hasattr(worker, "set_state"):
                    worker.set_state({"queues": queue.payload})
                applied = True

                logger.info(
                    "Boot resume complete",
                    extra={
                        "run_id": run_id,
                        "positions": positions_n,
                        "trades": trades_n,
                        "learner_loaded": learner_loaded,
                        "bandit_arms": arms_k,
                    },
                )
        finally:
            db.close()

    # If not applied, try audit log replay
    if not applied:
        audit_path = _env_path(
            "AUDIT_LOG_PATH", str(Path("./data/paper_events.jsonl").resolve())
        )
        audit = AuditLog(audit_path)
        latest_positions: dict[str, dict[str, Any]] = {}
        equity_curve: list[dict[str, Any]] = []
        bandit_payload: dict[str, Any] | None = None
        learner_meta: dict[str, Any] | None = None
        model_bytes: bytes | None = None
        for ev in audit.replay_events():
            et = ev.get("type")
            if et == "position":
                for p in ev.get("payload", []):
                    latest_positions[p["symbol"]] = p
            elif et == "pnl":
                eq = ev.get("payload", {}).get("equity_curve", [])
                if eq:
                    equity_curve = eq
            elif et == "bandit":
                bandit_payload = ev.get("payload")
            elif et == "learner":
                # JSONL carries meta only; model bytes cannot be recovered here
                learner_meta = (ev.get("payload") or {}).get("meta")
        # Apply best-effort to worker
        if hasattr(worker.engine, "set_state"):
            await worker.engine.set_state(
                {
                    "run_id": worker.engine.run_id or "recovered",
                    "positions": list(latest_positions.values()),
                    "equity_curve": equity_curve[-500:],
                    "params": {},
                }
            )
            positions_n = len(latest_positions)
        if bandit_payload and hasattr(worker.allocator, "set_state"):
            (
                await worker.allocator.set_state({"arms": bandit_payload})
                if asyncio.iscoroutinefunction(worker.allocator.set_state)
                else worker.allocator.set_state({"arms": bandit_payload})
            )
            arms_k = len(bandit_payload or {})
        if model_bytes and hasattr(worker.learner, "set_state"):
            worker.learner.set_state(model_bytes, learner_meta or {})
            learner_loaded = True
        logger.info(
            "Boot resume complete (audit replay)",
            extra={
                "positions": positions_n,
                "trades": trades_n,
                "learner_loaded": learner_loaded,
                "bandit_arms": arms_k,
            },
        )

    return {"ok": True}
