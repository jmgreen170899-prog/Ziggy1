"""
Data Quarantine System - Perception Layer

Isolates failed data for analysis and prevents corrupt data from entering
the processing pipeline. Provides audit trail for data quality issues.
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


logger = logging.getLogger(__name__)

# Environment configuration
QUARANTINE_PATH = os.getenv("QUARANTINE_PATH", "/data/quarantine/")
QUARANTINE_MAX_PAYLOAD_SIZE = int(os.getenv("QUARANTINE_MAX_PAYLOAD_SIZE", "100000"))
QUARANTINE_RETENTION_DAYS = int(os.getenv("QUARANTINE_RETENTION_DAYS", "30"))


def write(
    dataset: str, reason: str, payload: dict | pd.DataFrame | Any, metadata: dict[str, Any] = None
) -> str:
    """
    Write failed data to quarantine with metadata.

    Args:
        dataset: Dataset type (e.g., 'ohlcv', 'news', 'quotes')
        reason: Reason for quarantine (error message)
        payload: Data that failed validation
        metadata: Additional context (vendor, ticker, etc.)

    Returns:
        Quarantine file path/ID
    """
    try:
        # Ensure quarantine directory exists
        quarantine_dir = Path(QUARANTINE_PATH)
        quarantine_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename with timestamp
        timestamp_ms = int(time.time() * 1000)
        filename = f"{dataset}_{timestamp_ms}_{os.getpid()}.json"
        file_path = quarantine_dir / filename

        # Prepare quarantine record
        quarantine_record = {
            "timestamp": datetime.now().isoformat(),
            "dataset": dataset,
            "reason": reason,
            "metadata": metadata or {},
            "payload_type": type(payload).__name__,
            "payload_size": _get_payload_size(payload),
        }

        # Serialize payload with size limit
        try:
            if isinstance(payload, pd.DataFrame):
                # Convert DataFrame to dict for serialization
                payload_data = {
                    "shape": payload.shape,
                    "columns": payload.columns.tolist(),
                    "dtypes": payload.dtypes.astype(str).to_dict(),
                    "head": payload.head().to_dict(),
                    "sample_rows": min(10, len(payload)),
                }
                if len(payload) > 0:
                    payload_data["tail"] = payload.tail().to_dict()
            else:
                payload_data = payload

            # Convert to string and truncate if too large
            payload_str = json.dumps(payload_data, default=str, ensure_ascii=False)
            if len(payload_str) > QUARANTINE_MAX_PAYLOAD_SIZE:
                # Truncate and add marker
                payload_str = payload_str[: QUARANTINE_MAX_PAYLOAD_SIZE - 100] + "...[TRUNCATED]"
                quarantine_record["payload_truncated"] = True

            quarantine_record["payload"] = payload_str

        except Exception as e:
            # Fallback if serialization fails
            quarantine_record["payload"] = f"Serialization failed: {e}"
            quarantine_record["payload_error"] = str(e)

        # Write to file
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(quarantine_record, f, ensure_ascii=False, indent=2)

        logger.warning(f"Data quarantined: {dataset} -> {file_path} (reason: {reason})")

        return str(file_path)

    except Exception as e:
        logger.error(f"Failed to quarantine data: {e}")
        # Return a fallback identifier
        return f"quarantine_failed_{int(time.time())}"


def _get_payload_size(payload: Any) -> int:
    """Estimate payload size in bytes."""
    try:
        if isinstance(payload, pd.DataFrame):
            return int(payload.memory_usage(deep=True).sum())
        elif isinstance(payload, (dict, list)):
            return len(json.dumps(payload, default=str))
        else:
            return len(str(payload))
    except Exception:
        return 0


def list_recent(n: int = 50, dataset: str = None) -> list[dict[str, Any]]:
    """
    List recent quarantine entries.

    Args:
        n: Maximum number of entries to return
        dataset: Filter by dataset type (optional)

    Returns:
        List of quarantine entries with metadata
    """
    try:
        quarantine_dir = Path(QUARANTINE_PATH)
        if not quarantine_dir.exists():
            return []

        # Get all quarantine files
        quarantine_files = list(quarantine_dir.glob("*.json"))

        # Sort by modification time (newest first)
        quarantine_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        # Filter by dataset if specified
        if dataset:
            quarantine_files = [f for f in quarantine_files if f.name.startswith(f"{dataset}_")]

        # Load metadata from files
        entries = []
        for file_path in quarantine_files[:n]:
            try:
                with open(file_path, encoding="utf-8") as f:
                    record = json.load(f)

                # Add file info
                record["file_path"] = str(file_path)
                record["file_size"] = file_path.stat().st_size
                record["file_modified"] = datetime.fromtimestamp(
                    file_path.stat().st_mtime
                ).isoformat()

                # Remove large payload for listing
                if "payload" in record:
                    record["payload_preview"] = (
                        record["payload"][:200] + "..."
                        if len(record["payload"]) > 200
                        else record["payload"]
                    )
                    del record["payload"]

                entries.append(record)

            except Exception as e:
                logger.warning(f"Failed to read quarantine file {file_path}: {e}")
                continue

        return entries

    except Exception as e:
        logger.error(f"Failed to list quarantine entries: {e}")
        return []


def get_by_id(quarantine_id: str) -> dict[str, Any]:
    """
    Get quarantine entry by ID (file path).

    Args:
        quarantine_id: Quarantine file path or ID

    Returns:
        Quarantine record with full payload
    """
    try:
        file_path = Path(quarantine_id)
        if not file_path.exists():
            # Try relative to quarantine directory
            file_path = Path(QUARANTINE_PATH) / quarantine_id

        if not file_path.exists():
            return {}

        with open(file_path, encoding="utf-8") as f:
            record = json.load(f)

        # Add file info
        record["file_path"] = str(file_path)
        record["file_size"] = file_path.stat().st_size

        return record

    except Exception as e:
        logger.error(f"Failed to get quarantine entry {quarantine_id}: {e}")
        return {}


def cleanup_old_entries(days: int = None) -> int:
    """
    Clean up old quarantine entries.

    Args:
        days: Age threshold in days (uses QUARANTINE_RETENTION_DAYS if None)

    Returns:
        Number of files cleaned up
    """
    try:
        days = days or QUARANTINE_RETENTION_DAYS
        cutoff_time = time.time() - (days * 24 * 3600)

        quarantine_dir = Path(QUARANTINE_PATH)
        if not quarantine_dir.exists():
            return 0

        # Find old files
        old_files = []
        for file_path in quarantine_dir.glob("*.json"):
            if file_path.stat().st_mtime < cutoff_time:
                old_files.append(file_path)

        # Remove old files
        removed_count = 0
        for file_path in old_files:
            try:
                file_path.unlink()
                removed_count += 1
            except Exception as e:
                logger.warning(f"Failed to remove old quarantine file {file_path}: {e}")

        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old quarantine entries (>{days} days)")

        return removed_count

    except Exception as e:
        logger.error(f"Failed to cleanup quarantine entries: {e}")
        return 0


def get_stats() -> dict[str, Any]:
    """
    Get quarantine statistics.

    Returns:
        Dictionary with quarantine metrics
    """
    try:
        quarantine_dir = Path(QUARANTINE_PATH)
        if not quarantine_dir.exists():
            return {"total_entries": 0, "total_size_bytes": 0, "datasets": {}, "recent_24h": 0}

        # Count files and sizes
        files = list(quarantine_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in files)

        # Group by dataset
        datasets = {}
        recent_cutoff = time.time() - (24 * 3600)  # 24 hours ago
        recent_count = 0

        for file_path in files:
            # Extract dataset from filename
            dataset = file_path.name.split("_")[0]
            datasets[dataset] = datasets.get(dataset, 0) + 1

            # Count recent entries
            if file_path.stat().st_mtime > recent_cutoff:
                recent_count += 1

        return {
            "total_entries": len(files),
            "total_size_bytes": total_size,
            "datasets": datasets,
            "recent_24h": recent_count,
            "quarantine_path": QUARANTINE_PATH,
        }

    except Exception as e:
        logger.error(f"Failed to get quarantine stats: {e}")
        return {"error": str(e)}


def write_provider_failure(
    provider: str, ticker: str, error: Exception, metadata: dict[str, Any] = None
) -> str:
    """
    Quarantine a provider failure with context.

    Args:
        provider: Provider name
        ticker: Ticker symbol
        error: Exception that occurred
        metadata: Additional context

    Returns:
        Quarantine file path
    """
    failure_metadata = {
        "provider": provider,
        "ticker": ticker,
        "error_type": type(error).__name__,
        "error_message": str(error),
        **(metadata or {}),
    }

    return write(
        dataset="provider_failure",
        reason=f"Provider {provider} failed for {ticker}: {error}",
        payload={"error": str(error), "traceback": None},  # Could add traceback if needed
        metadata=failure_metadata,
    )


def write_contract_violation(
    contract_name: str, violation_reason: str, data_sample: Any, metadata: dict[str, Any] = None
) -> str:
    """
    Quarantine a contract violation with data sample.

    Args:
        contract_name: Name of violated contract
        violation_reason: Reason for violation
        data_sample: Sample of violating data
        metadata: Additional context

    Returns:
        Quarantine file path
    """
    violation_metadata = {
        "contract": contract_name,
        "violation_type": "data_contract",
        **(metadata or {}),
    }

    return write(
        dataset="contract_violation",
        reason=f"Contract {contract_name}: {violation_reason}",
        payload=data_sample,
        metadata=violation_metadata,
    )
