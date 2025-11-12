# backend/app/services/decision_log.py
"""
Ziggy AI Decision Log Service
Provides explainable, auditable timeline of AI decisions with append-only logging.
"""

import json
import logging
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)


@dataclass
class DecisionEvent:
    """
    Structured decision event for explainable AI.
    All events are immutable after creation except for outcome updates.
    """

    id: str
    ts: str  # ISO8601 UTC timestamp
    kind: str  # "signal", "plan", "execute", "cancel", "regime", "learning"
    ticker: str | None = None
    regime: str | None = None  # "Panic", "RiskOff", "Chop", "RiskOn"
    signal_name: str | None = None  # "MeanReversion", "Momentum", etc.
    params_version: str = "v1.0"
    rules_fired: list[str] = None
    confidence: float | None = None  # calibrated P(up|h)
    expected_move: dict[str, str | float] | None = None  # {"h":"5d","pct":1.8}
    risk: dict[str, float] | None = None  # ATR, stop_mult, tp_mult, qty, risk_pct
    decision: dict[str, str] | None = None  # {"action":"BUY","reason":"..."}
    order_ref: str | None = None
    costs: dict[str, float] | None = None  # {"fees":0.0,"slippage_bp":4}
    outcome: dict[str, str | float | bool] | None = None  # filled later
    links: dict[str, str] | None = None
    meta: dict[str, Any] | None = None

    def __post_init__(self):
        if self.rules_fired is None:
            self.rules_fired = []
        if self.links is None:
            self.links = {}
        if self.meta is None:
            self.meta = {}


class DecisionLogger:
    """
    Append-only decision logging system for explainable AI.
    Persists to JSONL files organized by date for efficient querying.
    """

    def __init__(self, data_dir: str = "./data/decisions"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)

        # Create monthly directories for organization
        self._ensure_monthly_dirs()

    def _ensure_monthly_dirs(self):
        """Ensure monthly directory structure exists."""
        now = datetime.now(UTC)
        monthly_dir = self.data_dir / f"{now.year:04d}-{now.month:02d}"
        monthly_dir.mkdir(exist_ok=True)

    def _get_log_file_path(self, event_date: datetime = None) -> Path:
        """Get the log file path for a given date."""
        if event_date is None:
            event_date = datetime.now(UTC)

        monthly_dir = self.data_dir / f"{event_date.year:04d}-{event_date.month:02d}"
        monthly_dir.mkdir(exist_ok=True)

        filename = (
            f"decision_log-{event_date.year:04d}{event_date.month:02d}{event_date.day:02d}.jsonl"
        )
        return monthly_dir / filename

    def append_event(self, event_data: dict[str, Any]) -> str:
        """
        Append a new decision event to the log.

        Args:
            event_data: Event data dictionary (will be validated and enhanced)

        Returns:
            event_id: Unique identifier for the logged event
        """
        try:
            # Generate ID and timestamp if not provided
            event_id = event_data.get("id", str(uuid.uuid4()))
            timestamp = event_data.get("ts")
            if not timestamp:
                timestamp = datetime.now(UTC).isoformat()

            # Create structured event
            event = DecisionEvent(
                id=event_id,
                ts=timestamp,
                kind=event_data.get("kind", "signal"),
                ticker=event_data.get("ticker"),
                regime=event_data.get("regime"),
                signal_name=event_data.get("signal_name"),
                params_version=event_data.get("params_version", "v1.0"),
                rules_fired=event_data.get("rules_fired", []),
                confidence=event_data.get("confidence"),
                expected_move=event_data.get("expected_move"),
                risk=event_data.get("risk"),
                decision=event_data.get("decision"),
                order_ref=event_data.get("order_ref"),
                costs=event_data.get("costs"),
                outcome=event_data.get("outcome"),
                links=event_data.get("links", {}),
                meta=event_data.get("meta", {}),
            )

            # Add metadata
            event.meta.update({"logged_at": datetime.now(UTC).isoformat(), "logger_version": "1.0"})

            # Write to JSONL file
            log_file = self._get_log_file_path()
            with open(log_file, "a", encoding="utf-8") as f:
                json.dump(asdict(event), f, ensure_ascii=False)
                f.write("\n")

            self.logger.info(
                f"Logged decision event: {event.kind} {event.ticker or ''} [{event_id}]"
            )
            return event_id

        except Exception as e:
            self.logger.error(f"Failed to append decision event: {e}")
            raise

    def load_event(self, event_id: str) -> dict[str, Any] | None:
        """
        Load a specific event by ID.

        Args:
            event_id: Unique event identifier

        Returns:
            Event data dictionary or None if not found
        """
        try:
            # Search through recent log files (last 3 months)
            search_files = []
            now = datetime.now(UTC)

            for months_back in range(3):
                if months_back == 0:
                    search_date = now
                else:
                    # Simple month subtraction
                    year = now.year
                    month = now.month - months_back
                    if month <= 0:
                        month += 12
                        year -= 1
                    search_date = datetime(year, month, 1)
                monthly_dir = self.data_dir / f"{search_date.year:04d}-{search_date.month:02d}"

                if monthly_dir.exists():
                    search_files.extend(monthly_dir.glob("decision_log-*.jsonl"))

            # Search through files
            for log_file in sorted(search_files, reverse=True):
                try:
                    with open(log_file, encoding="utf-8") as f:
                        for line in f:
                            event = json.loads(line.strip())
                            if event.get("id") == event_id:
                                return event
                except Exception as e:
                    self.logger.warning(f"Error reading {log_file}: {e}")
                    continue

            return None

        except Exception as e:
            self.logger.error(f"Failed to load event {event_id}: {e}")
            return None

    def query_events(
        self,
        filters: dict[str, Any] | None = None,
        since: str | None = None,
        until: str | None = None,
        limit: int = 50,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        """
        Query events with filtering, pagination, and sorting.

        Args:
            filters: Filter criteria (kind, ticker, signal_name, etc.)
            since: ISO8601 start timestamp
            until: ISO8601 end timestamp
            limit: Maximum number of events to return
            cursor: Pagination cursor (timestamp for continuation)

        Returns:
            Dictionary with 'items' list and 'next_cursor' for pagination
        """
        try:
            events = []
            filters = filters or {}

            # Parse date range
            since_dt = datetime.fromisoformat(since.replace("Z", "+00:00")) if since else None
            until_dt = datetime.fromisoformat(until.replace("Z", "+00:00")) if until else None
            cursor_dt = datetime.fromisoformat(cursor.replace("Z", "+00:00")) if cursor else None

            # Determine which files to search
            search_files = self._get_search_files(since_dt, until_dt)

            # Search through files in reverse chronological order
            for log_file in sorted(search_files, reverse=True):
                if len(events) >= limit:
                    break

                try:
                    with open(log_file, encoding="utf-8") as f:
                        file_events = []
                        for line in f:
                            try:
                                event = json.loads(line.strip())
                                file_events.append(event)
                            except json.JSONDecodeError:
                                continue

                        # Sort events in file by timestamp (newest first)
                        file_events.sort(key=lambda x: x.get("ts", ""), reverse=True)

                        # Apply filters and date range
                        for event in file_events:
                            if len(events) >= limit:
                                break

                            # Check cursor (pagination)
                            event_dt = datetime.fromisoformat(event["ts"].replace("Z", "+00:00"))
                            if cursor_dt and event_dt >= cursor_dt:
                                continue

                            # Check date range
                            if since_dt and event_dt < since_dt:
                                continue
                            if until_dt and event_dt > until_dt:
                                continue

                            # Apply filters
                            if self._matches_filters(event, filters):
                                events.append(event)

                except Exception as e:
                    self.logger.warning(f"Error reading {log_file}: {e}")
                    continue

            # Determine next cursor
            next_cursor = None
            if len(events) == limit and events:
                next_cursor = events[-1]["ts"]

            return {"items": events, "next_cursor": next_cursor, "total_returned": len(events)}

        except Exception as e:
            self.logger.error(f"Failed to query events: {e}")
            return {"items": [], "next_cursor": None, "total_returned": 0}

    def _get_search_files(self, since_dt: datetime | None, until_dt: datetime | None) -> list[Path]:
        """Get list of log files to search based on date range."""
        from datetime import timedelta

        search_files = []

        if not since_dt:
            since_dt = datetime.now(UTC) - timedelta(days=30)  # Default to last 30 days
        if not until_dt:
            until_dt = datetime.now(UTC)

        # Find all monthly directories in range
        current_dt = since_dt.replace(day=1)  # Start of month
        end_dt = until_dt.replace(day=1)

        while current_dt <= end_dt:
            monthly_dir = self.data_dir / f"{current_dt.year:04d}-{current_dt.month:02d}"
            if monthly_dir.exists():
                search_files.extend(monthly_dir.glob("decision_log-*.jsonl"))

            # Move to next month
            if current_dt.month == 12:
                current_dt = current_dt.replace(year=current_dt.year + 1, month=1)
            else:
                current_dt = current_dt.replace(month=current_dt.month + 1)

        return search_files

    def _matches_filters(self, event: dict[str, Any], filters: dict[str, Any]) -> bool:
        """Check if event matches filter criteria."""
        for key, value in filters.items():
            if key == "kind":
                if isinstance(value, list):
                    if event.get("kind") not in value:
                        return False
                else:
                    if event.get("kind") != value:
                        return False
            elif key == "ticker":
                if event.get("ticker") != value:
                    return False
            elif key == "signal_name":
                if event.get("signal_name") != value:
                    return False
            elif key == "regime":
                if event.get("regime") != value:
                    return False
            elif key == "has_outcome":
                has_outcome = event.get("outcome") is not None
                if has_outcome != value:
                    return False

        return True

    def update_event_outcome(self, event_id: str, outcome: dict[str, str | float | bool]) -> bool:
        """
        Update the outcome of an existing event.

        Args:
            event_id: Event identifier
            outcome: Outcome data {"h":"5d","pnl":123.45,"hit":true}

        Returns:
            Success status
        """
        try:
            # Load existing event
            event = self.load_event(event_id)
            if not event:
                self.logger.warning(f"Event {event_id} not found for outcome update")
                return False

            # Update outcome
            event["outcome"] = outcome
            event["meta"]["outcome_updated_at"] = datetime.now(UTC).isoformat()

            # Log updated event (append-only approach)
            updated_id = self.append_event(event)
            self.logger.info(f"Updated outcome for event {event_id} -> {updated_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to update event outcome {event_id}: {e}")
            return False

    def get_stats_summary(self, window_days: int = 30) -> dict[str, Any]:
        """
        Get summary statistics for the decision log.

        Args:
            window_days: Number of days to look back

        Returns:
            Summary statistics dictionary
        """
        try:
            from datetime import timedelta

            since = (datetime.now(UTC) - timedelta(days=window_days)).isoformat()

            # Get all events in window
            result = self.query_events(since=since, limit=10000)
            events = result["items"]

            if not events:
                return {
                    "total_events": 0,
                    "events_by_kind": {},
                    "hit_rate": None,
                    "avg_confidence": None,
                    "brier_score": None,
                    "signals": {},
                }

            # Basic counts
            events_by_kind = {}
            for event in events:
                kind = event.get("kind", "unknown")
                events_by_kind[kind] = events_by_kind.get(kind, 0) + 1

            # Signal analysis
            signal_events = [e for e in events if e.get("kind") == "signal" and e.get("outcome")]
            hit_rate = None
            avg_confidence = None
            brier_score = None
            signals_summary = {}

            if signal_events:
                hits = sum(1 for e in signal_events if e.get("outcome", {}).get("hit", False))
                hit_rate = hits / len(signal_events)

                confidences = [
                    e.get("confidence") for e in signal_events if e.get("confidence") is not None
                ]
                if confidences:
                    avg_confidence = sum(confidences) / len(confidences)

                    # Calculate Brier score
                    brier_sum = 0
                    brier_count = 0
                    for event in signal_events:
                        conf = event.get("confidence")
                        hit = event.get("outcome", {}).get("hit", False)
                        if conf is not None:
                            brier_sum += (conf - (1.0 if hit else 0.0)) ** 2
                            brier_count += 1

                    if brier_count > 0:
                        brier_score = brier_sum / brier_count

                # Per-signal analysis
                signals = {}
                for event in signal_events:
                    signal_name = event.get("signal_name", "unknown")
                    if signal_name not in signals:
                        signals[signal_name] = {"count": 0, "hits": 0, "total_confidence": 0}

                    signals[signal_name]["count"] += 1
                    if event.get("outcome", {}).get("hit", False):
                        signals[signal_name]["hits"] += 1
                    if event.get("confidence") is not None:
                        signals[signal_name]["total_confidence"] += event.get("confidence")

                for signal_name, data in signals.items():
                    data["hit_rate"] = data["hits"] / data["count"] if data["count"] > 0 else 0
                    data["avg_confidence"] = (
                        data["total_confidence"] / data["count"] if data["count"] > 0 else 0
                    )

                signals_summary = signals

            return {
                "window_days": window_days,
                "total_events": len(events),
                "events_by_kind": events_by_kind,
                "hit_rate": hit_rate,
                "avg_confidence": avg_confidence,
                "brier_score": brier_score,
                "signals": signals_summary,
            }

        except Exception as e:
            self.logger.error(f"Failed to get stats summary: {e}")
            return {"total_events": 0, "error": str(e)}


# Global logger instance
_decision_logger: DecisionLogger | None = None


def get_decision_logger() -> DecisionLogger:
    """Get the global decision logger instance."""
    global _decision_logger
    if _decision_logger is None:
        _decision_logger = DecisionLogger()
    return _decision_logger


# Convenience functions
def log_decision_event(event_data: dict[str, Any]) -> str:
    """Log a decision event using the global logger."""
    logger = get_decision_logger()
    return logger.append_event(event_data)


def log_signal_event(
    ticker: str,
    signal_name: str,
    confidence: float,
    rules_fired: list[str],
    decision: dict[str, str],
    risk: dict[str, float] | None = None,
    **kwargs,
) -> str:
    """Log a signal decision event."""
    event_data = {
        "kind": "signal",
        "ticker": ticker,
        "signal_name": signal_name,
        "confidence": confidence,
        "rules_fired": rules_fired,
        "decision": decision,
        "risk": risk,
        **kwargs,
    }
    return log_decision_event(event_data)


def log_regime_event(regime: str, confidence: float, rules_fired: list[str], **kwargs) -> str:
    """Log a regime change event."""
    event_data = {
        "kind": "regime",
        "regime": regime,
        "confidence": confidence,
        "rules_fired": rules_fired,
        **kwargs,
    }
    return log_decision_event(event_data)


def log_learning_event(
    params_version: str, gates_passed: list[str], gates_failed: list[str], **kwargs
) -> str:
    """Log a learning system event."""
    event_data = {
        "kind": "learning",
        "params_version": params_version,
        "rules_fired": gates_passed + [f"FAILED: {g}" for g in gates_failed],
        "decision": {
            "action": "PROMOTE" if not gates_failed else "REJECT",
            "reason": f"Gates passed: {len(gates_passed)}, failed: {len(gates_failed)}",
        },
        **kwargs,
    }
    return log_decision_event(event_data)


if __name__ == "__main__":
    # Test the decision logger

    logger = DecisionLogger()

    # Test logging events
    print("Testing decision logger...")

    # Log a signal event
    signal_id = log_signal_event(
        ticker="AAPL",
        signal_name="MeanReversion",
        confidence=0.75,
        rules_fired=["RSI < 30", "Price < BB_Lower", "Volume > 1.5x avg"],
        decision={"action": "BUY", "reason": "Oversold conditions with volume confirmation"},
        risk={"atr": 2.5, "stop_mult": 1.5, "qty": 100, "risk_pct": 1.0},
    )
    print(f"Logged signal event: {signal_id}")

    # Log a regime event
    regime_id = log_regime_event(
        regime="RiskOff",
        confidence=0.85,
        rules_fired=["VIX > 25", "SPX < MA200", "Credit spreads widening"],
    )
    print(f"Logged regime event: {regime_id}")

    # Query events
    result = logger.query_events(limit=10)
    print(f"Query result: {len(result['items'])} events")

    # Get stats
    stats = logger.get_stats_summary()
    print(f"Stats: {stats}")

    print("Decision logger test complete!")
