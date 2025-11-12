"""
Telemetry System - Perception Layer

Emits metrics and violations for monitoring data quality and provider health.
Integrates with observability systems for real-time alerting.
"""

from __future__ import annotations

import logging
import os
import queue
import threading
import time
from datetime import datetime
from threading import Lock
from typing import Any

import requests

from app.core.config.time_tuning import QUEUE_LIMITS, TIMEOUTS


logger = logging.getLogger(__name__)

# Environment configuration
TELEMETRY_ENDPOINT = os.getenv("TELEMETRY_ENDPOINT", "http://localhost:8123/ingest")
TELEMETRY_SAMPLE = float(os.getenv("TELEMETRY_SAMPLE", "1.0"))
TELEMETRY_TIMEOUT = TIMEOUTS["telemetry_http"]
TELEMETRY_BATCH_SIZE = QUEUE_LIMITS["telemetry_batch_size"]
TELEMETRY_FLUSH_INTERVAL = QUEUE_LIMITS["telemetry_flush_interval"]


class TelemetryEmitter:
    """
    Batched telemetry emitter with async processing.
    """

    def __init__(self):
        self.queue = queue.Queue(maxsize=QUEUE_LIMITS["telemetry_events"])
        self.batch = []
        self.batch_lock = Lock()
        self.stats = {
            "events_emitted": 0,
            "events_dropped": 0,
            "events_failed": 0,
            "last_flush": None,
        }

        # Start background worker
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()

    def emit(self, event_type: str, data: dict[str, Any], metadata: dict[str, Any] = None) -> None:
        """
        Emit a telemetry event.

        Args:
            event_type: Type of event (violation, metric, etc.)
            data: Event data
            metadata: Additional metadata
        """
        # Sample events based on configuration
        if TELEMETRY_SAMPLE < 1.0:
            import random

            if random.random() > TELEMETRY_SAMPLE:
                return

        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": data,
            "metadata": metadata or {},
            "source": "ziggy-perception",
        }

        try:
            self.queue.put_nowait(event)
            self.stats["events_emitted"] += 1
        except queue.Full:
            self.stats["events_dropped"] += 1
            logger.warning("Telemetry queue full, dropping event")

    def _worker(self) -> None:
        """Background worker to process telemetry events."""
        while True:
            try:
                # Collect events into batch
                events_to_send = []
                timeout_start = time.time()

                # Wait for events or timeout
                while (
                    len(events_to_send) < TELEMETRY_BATCH_SIZE
                    and (time.time() - timeout_start) < TELEMETRY_FLUSH_INTERVAL
                ):
                    try:
                        event = self.queue.get(timeout=TIMEOUTS["telemetry_queue_get"])
                        events_to_send.append(event)
                        self.queue.task_done()
                    except queue.Empty:
                        continue

                # Send batch if we have events
                if events_to_send:
                    self._send_batch(events_to_send)

            except Exception as e:
                logger.error(f"Telemetry worker error: {e}")
                time.sleep(5)  # Brief pause before retrying

    def _send_batch(self, events: list) -> None:
        """Send batch of events to telemetry endpoint."""
        try:
            payload = {
                "source": "ziggy-perception",
                "timestamp": datetime.now().isoformat(),
                "events": events,
                "count": len(events),
            }

            response = requests.post(
                TELEMETRY_ENDPOINT,
                json=payload,
                timeout=TELEMETRY_TIMEOUT,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 200:
                logger.debug(f"Sent {len(events)} telemetry events")
                self.stats["last_flush"] = datetime.now().isoformat()
            else:
                logger.warning(f"Telemetry endpoint returned {response.status_code}")
                self.stats["events_failed"] += len(events)

        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to send telemetry: {e}")
            self.stats["events_failed"] += len(events)
        except Exception as e:
            logger.error(f"Unexpected telemetry error: {e}")
            self.stats["events_failed"] += len(events)

    def get_stats(self) -> dict[str, Any]:
        """Get telemetry statistics."""
        return self.stats.copy()


# Global emitter instance
_emitter = TelemetryEmitter()


def emit_violation(kind: str, vendor: str, meta: dict[str, Any] = None) -> None:
    """
    Emit a data contract violation event.

    Args:
        kind: Type of violation (contract, provider, etc.)
        vendor: Provider/vendor name
        meta: Additional metadata
    """
    data = {"violation_type": kind, "vendor": vendor, "severity": "warning"}

    metadata = {"component": "data_contracts", **(meta or {})}

    _emitter.emit("violation", data, metadata)
    logger.warning(f"Violation emitted: {kind} from {vendor}")


def emit_provider_metric(
    vendor: str, latency_ms: int, ok: bool, metadata: dict[str, Any] = None
) -> None:
    """
    Emit provider performance metrics.

    Args:
        vendor: Provider name
        latency_ms: Request latency in milliseconds
        ok: Whether request succeeded
        metadata: Additional context
    """
    data = {
        "vendor": vendor,
        "latency_ms": latency_ms,
        "success": ok,
        "timestamp_ms": int(time.time() * 1000),
    }

    meta = {"component": "provider_health", "metric_type": "performance", **(metadata or {})}

    _emitter.emit("provider_metric", data, meta)


def emit_contract_validation(
    dataset_type: str,
    ticker: str,
    passed: bool,
    validation_time_ms: float = None,
    metadata: dict[str, Any] = None,
) -> None:
    """
    Emit contract validation result.

    Args:
        dataset_type: Type of dataset validated
        ticker: Ticker symbol
        passed: Whether validation passed
        validation_time_ms: Time taken for validation
        metadata: Additional context
    """
    data = {
        "dataset_type": dataset_type,
        "ticker": ticker,
        "validation_passed": passed,
        "validation_time_ms": validation_time_ms,
    }

    meta = {"component": "data_contracts", "metric_type": "validation", **(metadata or {})}

    _emitter.emit("contract_validation", data, meta)


def emit_quarantine_event(dataset_type: str, reason: str, metadata: dict[str, Any] = None) -> None:
    """
    Emit quarantine event when data is isolated.

    Args:
        dataset_type: Type of dataset quarantined
        reason: Reason for quarantine
        metadata: Additional context
    """
    data = {"dataset_type": dataset_type, "quarantine_reason": reason, "severity": "error"}

    meta = {"component": "quarantine", "event_type": "data_quarantined", **(metadata or {})}

    _emitter.emit("quarantine", data, meta)


def emit_ingestion_metric(
    source: str,
    records_processed: int,
    processing_time_ms: float,
    errors: int = 0,
    metadata: dict[str, Any] = None,
) -> None:
    """
    Emit data ingestion metrics.

    Args:
        source: Data source name
        records_processed: Number of records processed
        processing_time_ms: Total processing time
        errors: Number of errors encountered
        metadata: Additional context
    """
    data = {
        "source": source,
        "records_processed": records_processed,
        "processing_time_ms": processing_time_ms,
        "errors": errors,
        "records_per_second": records_processed / max(processing_time_ms / 1000, 0.001),
    }

    meta = {"component": "data_ingestion", "metric_type": "throughput", **(metadata or {})}

    _emitter.emit("ingestion_metric", data, meta)


def emit_brain_event(event_type: str, event_id: str, metadata: dict[str, Any] = None) -> None:
    """
    Emit brain/memory layer events.

    Args:
        event_type: Type of brain event
        event_id: Event identifier
        metadata: Additional context
    """
    data = {"brain_event_type": event_type, "event_id": event_id}

    meta = {"component": "brain_layer", "event_type": "memory_operation", **(metadata or {})}

    _emitter.emit("brain_event", data, meta)


def emit_nlp_metric(
    document_count: int,
    entities_extracted: int,
    sentiment_score: float = None,
    processing_time_ms: float = None,
    metadata: dict[str, Any] = None,
) -> None:
    """
    Emit NLP processing metrics.

    Args:
        document_count: Number of documents processed
        entities_extracted: Number of entities extracted
        sentiment_score: Average sentiment score
        processing_time_ms: Processing time
        metadata: Additional context
    """
    data = {
        "document_count": document_count,
        "entities_extracted": entities_extracted,
        "entities_per_doc": entities_extracted / max(document_count, 1),
        "sentiment_score": sentiment_score,
        "processing_time_ms": processing_time_ms,
    }

    meta = {"component": "nlp_processor", "metric_type": "extraction", **(metadata or {})}

    _emitter.emit("nlp_metric", data, meta)


def emit_custom_metric(
    metric_name: str, value: float, tags: dict[str, str] = None, metadata: dict[str, Any] = None
) -> None:
    """
    Emit custom metric for monitoring.

    Args:
        metric_name: Name of the metric
        value: Metric value
        tags: Metric tags/labels
        metadata: Additional context
    """
    data = {"metric_name": metric_name, "value": value, "tags": tags or {}}

    meta = {"component": "custom_metrics", "metric_type": "gauge", **(metadata or {})}

    _emitter.emit("custom_metric", data, meta)


def get_telemetry_stats() -> dict[str, Any]:
    """Get telemetry system statistics."""
    return _emitter.get_stats()


def flush_telemetry() -> None:
    """Force flush telemetry queue (useful for testing)."""
    # Wait for queue to be processed
    _emitter.queue.join()


class TelemetryContext:
    """Context manager for telemetry tracking."""

    def __init__(self, operation: str, metadata: dict[str, Any] = None):
        self.operation = operation
        self.metadata = metadata or {}
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000

        success = exc_type is None

        emit_custom_metric(
            "operation_duration_ms",
            duration_ms,
            tags={"operation": self.operation, "success": str(success)},
            metadata=self.metadata,
        )

        if not success:
            emit_violation(
                "operation_failure",
                self.operation,
                {
                    "error_type": exc_type.__name__ if exc_type else "Unknown",
                    "error_message": str(exc_val) if exc_val else "Unknown error",
                    **self.metadata,
                },
            )
