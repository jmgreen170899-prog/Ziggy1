from __future__ import annotations

import contextlib

from app.core.logging import get_logger
from app.models import base as models_base
from app.persistence import repository as repo
from app.persistence.snapshotter import Snapshotter
from app.tasks.paper_worker import get_paper_worker


logger = get_logger("ziggy.snapshotter")


class ShutdownManager:
    def __init__(self, snapshotter: Snapshotter) -> None:
        self.snapshotter = snapshotter

    async def on_shutdown(self) -> None:
        """Force a final snapshot and close the run."""
        try:
            await self.snapshotter.checkpoint_once()
        except Exception as e:
            logger.warning("Final checkpoint failed", extra={"error": str(e)})
        # Close run in DB if present
        worker = get_paper_worker()
        if worker and getattr(models_base, "SessionLocal", None):
            run_id = getattr(worker.engine, "run_id", None)
            if run_id:
                try:
                    db = models_base.SessionLocal()
                    try:
                        repo.close_run(db, run_id)
                    finally:
                        db.close()
                except Exception as e:
                    logger.warning("Close run failed", extra={"error": str(e)})
        # Flush JSONL buffers
        with contextlib.suppress(Exception):
            self.snapshotter.audit.flush()
