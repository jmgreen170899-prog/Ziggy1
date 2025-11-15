from __future__ import annotations

import asyncio
import contextlib
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.logging import get_logger
from app.models import base as models_base
from app.persistence import repository as repo
from app.persistence.audit_log import AuditLog
from app.tasks.paper_worker import get_paper_worker


logger = get_logger("ziggy.snapshotter")


def _env_path(key: str, default: str) -> str:
    p = os.getenv(key) or default
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    return p


class Snapshotter:
    def __init__(self) -> None:
        self.snapshot_dir = _env_path(
            "SNAPSHOT_DIR", str(Path("./data/snapshots").resolve())
        )
        self.audit_log_path = _env_path(
            "AUDIT_LOG_PATH", str(Path("./data/paper_events.jsonl").resolve())
        )
        self.interval_sec = int(os.getenv("CHECKPOINT_INTERVAL_SEC") or "60")
        self.run_resume = (os.getenv("RUN_RESUME") or "true").strip().lower() in {
            "1",
            "true",
            "yes",
        }
        self.audit = AuditLog(self.audit_log_path, fsync_every=25)
        self._task: asyncio.Task | None = None
        self._last_checkpoint_ts: datetime | None = None

    async def start_periodic(self) -> None:
        if self._task and not self._task.done():
            return
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
            with contextlib.suppress(Exception):
                await self._task
        self.audit.flush()

    async def _loop(self) -> None:
        logger.info("Snapshotter loop started", extra={"interval": self.interval_sec})
        try:
            while True:
                try:
                    await self.checkpoint_once()
                except Exception as e:
                    logger.warning("Snapshot error", extra={"error": str(e)})
                await asyncio.sleep(self.interval_sec)
        except asyncio.CancelledError:
            logger.info("Snapshotter loop cancelled")

    async def checkpoint_once(self) -> dict[str, Any]:
        worker = get_paper_worker()
        if worker is None:
            return {"ok": False, "reason": "worker_not_running"}

        # Collect state from subsystems
        engine = worker.engine
        allocator = worker.allocator
        learner = worker.learner

        # Engine state
        engine_state = await _safe_get_state(engine, component="engine")
        bandit_state = _safe_get_state_sync(allocator, component="bandit")
        learner_state = _safe_get_state_sync(learner, component="learner")
        queues_state = _safe_get_state_sync(worker, component="queues")

        # Persist to DB if connected
        persisted = False
        run_id = (engine_state or {}).get("run_id") or "unknown"
        if getattr(models_base, "SessionLocal", None):
            try:
                db = models_base.SessionLocal()
                try:
                    # ensure run exists
                    repo.open_or_resume_run(
                        db,
                        meta={
                            "run_id": run_id,
                            "meta": engine_state.get("params") if engine_state else {},
                        },
                    )
                    # positions
                    for pos in (engine_state or {}).get("positions", []):
                        repo.upsert_position(
                            db,
                            run_id,
                            pos["symbol"],
                            pos["qty"],
                            pos["avg_price"],
                            datetime.utcnow(),
                        )
                    # pnl
                    pnl_points = (engine_state or {}).get("equity_curve", [])
                    if pnl_points:
                        repo.append_pnl_points(db, run_id, pnl_points)
                    # bandit
                    if bandit_state:
                        repo.save_bandit_snapshot(db, run_id, bandit_state)
                    # learner
                    if learner_state:
                        lb = learner_state.get("bytes")
                        if isinstance(lb, (bytes, bytearray)):
                            repo.save_learner_checkpoint(
                                db,
                                run_id,
                                learner_state.get("algo"),
                                bytes(lb),
                                learner_state.get("meta"),
                            )
                    # queues
                    if queues_state:
                        repo.save_queue_snapshot(db, run_id, queues_state)
                    persisted = True
                finally:
                    db.close()
            except Exception as e:
                logger.warning("DB snapshot failed", extra={"error": str(e)})

        # Always append audit JSONL events (dual write)
        now_iso = datetime.utcnow().isoformat()
        if engine_state:
            self.audit.append_event(
                {
                    "ts": now_iso,
                    "type": "pnl",
                    "run_id": run_id,
                    "payload": {"equity_curve": engine_state.get("equity_curve", [])},
                }
            )
            self.audit.append_event(
                {
                    "ts": now_iso,
                    "type": "position",
                    "run_id": run_id,
                    "payload": engine_state.get("positions", []),
                }
            )
        if bandit_state:
            self.audit.append_event(
                {
                    "ts": now_iso,
                    "type": "bandit",
                    "run_id": run_id,
                    "payload": bandit_state,
                }
            )
        if learner_state:
            # Don't dump raw bytes to JSONL; include only meta
            self.audit.append_event(
                {
                    "ts": now_iso,
                    "type": "learner",
                    "run_id": run_id,
                    "payload": {
                        "algo": learner_state.get("algo"),
                        "meta": learner_state.get("meta"),
                    },
                }
            )
        if queues_state:
            self.audit.append_event(
                {
                    "ts": now_iso,
                    "type": "queue",
                    "run_id": run_id,
                    "payload": queues_state,
                }
            )

        self._last_checkpoint_ts = datetime.utcnow()
        logger.info(
            "Checkpoint complete", extra={"persisted": persisted, "run_id": run_id}
        )
        return {
            "ok": True,
            "persisted": persisted,
            "run_id": run_id,
            "ts": self._last_checkpoint_ts.isoformat(),
        }

    def last_checkpoint_iso(self) -> str | None:
        return (
            self._last_checkpoint_ts.isoformat() if self._last_checkpoint_ts else None
        )


async def _safe_get_state(obj: Any, component: str) -> dict[str, Any] | None:
    try:
        if hasattr(obj, "get_state") and asyncio.iscoroutinefunction(obj.get_state):
            return await obj.get_state()  # type: ignore[attr-defined]
        elif hasattr(obj, "get_state"):
            return obj.get_state()  # type: ignore[attr-defined]
    except Exception as e:
        logger.warning(
            "State collection failed", extra={"component": component, "error": str(e)}
        )
    return None


def _safe_get_state_sync(obj: Any, component: str) -> dict[str, Any] | None:
    try:
        if hasattr(obj, "get_state"):
            return obj.get_state()  # type: ignore[attr-defined]
    except Exception as e:
        logger.warning(
            "State collection failed", extra={"component": component, "error": str(e)}
        )
    return None
