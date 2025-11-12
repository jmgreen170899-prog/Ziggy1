"""
Brain Write-Through Integration - Perception Layer

Routes all market data through Ziggy's brain for learning and recall.
Ensures vendor stamping, metadata enrichment, and proper event formatting.
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime
from typing import Any


logger = logging.getLogger(__name__)

# Brain write-through configuration
BRAIN_WRITE_ENABLED = bool(int(os.getenv("BRAIN_WRITE_ENABLED", "1")))
BRAIN_ASYNC_MODE = bool(int(os.getenv("BRAIN_ASYNC_MODE", "1")))
BRAIN_BATCH_SIZE = int(os.getenv("BRAIN_BATCH_SIZE", "50"))
BRAIN_FLUSH_INTERVAL = int(os.getenv("BRAIN_FLUSH_INTERVAL", "30"))

# Availability is decided during application startup; avoid DB/file I/O on import.
BRAIN_AVAILABLE: bool = False
_brain_availability_logged: bool = False


def set_brain_availability(available: bool) -> None:
    """Set brain availability flag; log once at startup."""
    global BRAIN_AVAILABLE, _brain_availability_logged
    BRAIN_AVAILABLE = available
    if not _brain_availability_logged:
        logger.info(
            "Market Brain system %s",
            "enabled" if BRAIN_AVAILABLE else "legacy_mode",
        )
        _brain_availability_logged = True


class BrainWriteThrough:
    """
    Brain write-through handler for perception layer data.

    Ensures all market data flows through Ziggy's brain with proper
    vendor stamps, metadata, and learning context.
    """

    def __init__(self):
        self._pending_batch = []
        self._last_flush = datetime.now()
        self._lock = asyncio.Lock() if BRAIN_ASYNC_MODE else None

    async def write_market_data(
        self,
        data: dict[str, Any],
        data_type: str = "market_data",
        vendor_stamp: dict[str, Any] | None = None,
        timezone_info: dict[str, Any] | None = None,
    ) -> str:
        """
        Write market data through brain with metadata enrichment.

        Args:
            data: Market data (OHLCV, quotes, news, etc.)
            data_type: Type of data for classification
            vendor_stamp: Provider metadata
            timezone_info: Timezone normalization results

        Returns:
            Event ID or batch ID
        """
        if not BRAIN_WRITE_ENABLED or not BRAIN_AVAILABLE:
            return "brain_disabled"

        try:
            # Build enriched event
            enriched_event = await self._enrich_market_event(
                data, data_type, vendor_stamp, timezone_info
            )

            if BRAIN_ASYNC_MODE:
                return await self._handle_async_write(enriched_event)
            else:
                return self._handle_sync_write(enriched_event)

        except Exception as e:
            logger.error(f"Brain write-through failed: {e}")
            return f"error_{str(e)[:50]}"

    async def write_nlp_analysis(
        self,
        news_data: dict[str, Any],
        nlp_results: dict[str, Any],
        vendor_stamp: dict[str, Any] | None = None,
    ) -> str:
        """
        Write NLP analysis results through brain.

        Args:
            news_data: Original news data
            nlp_results: NLP analysis results (entities, sentiment, etc.)
            vendor_stamp: Provider metadata

        Returns:
            Event ID
        """
        if not BRAIN_WRITE_ENABLED or not BRAIN_AVAILABLE:
            return "brain_disabled"

        try:
            # Build NLP event
            nlp_event = await self._enrich_nlp_event(news_data, nlp_results, vendor_stamp)

            if BRAIN_ASYNC_MODE:
                return await self._handle_async_write(nlp_event)
            else:
                return self._handle_sync_write(nlp_event)

        except Exception as e:
            logger.error(f"NLP brain write failed: {e}")
            return f"error_{str(e)[:50]}"

    async def write_provider_health(
        self, provider_name: str, health_metrics: dict[str, Any]
    ) -> str:
        """
        Write provider health metrics through brain.

        Args:
            provider_name: Provider identifier
            health_metrics: Health scoring data

        Returns:
            Event ID
        """
        if not BRAIN_WRITE_ENABLED or not BRAIN_AVAILABLE:
            return "brain_disabled"

        try:
            health_event = {
                "event_type": "provider_health",
                "provider": provider_name,
                "health_score": health_metrics.get("health_score", 0.0),
                "success_rate": health_metrics.get("success_rate", 0.0),
                "avg_latency_ms": health_metrics.get("avg_latency_ms", 0.0),
                "contract_compliance": health_metrics.get("contract_compliance", 0.0),
                "last_success": health_metrics.get("last_success"),
                "event_count": health_metrics.get("event_count", 0),
                "vendor_stamp": {
                    "source": "provider_health_tracker",
                    "version": "1.0.0",
                    "timestamp": datetime.now().isoformat(),
                },
            }

            return self._handle_sync_write(health_event)

        except Exception as e:
            logger.error(f"Provider health brain write failed: {e}")
            return f"error_{str(e)[:50]}"

    async def write_contract_violation(
        self, violation_data: dict[str, Any], quarantine_info: dict[str, Any]
    ) -> str:
        """
        Write contract violation through brain for learning.

        Args:
            violation_data: Contract violation details
            quarantine_info: Quarantine system data

        Returns:
            Event ID
        """
        if not BRAIN_WRITE_ENABLED or not BRAIN_AVAILABLE:
            return "brain_disabled"

        try:
            violation_event = {
                "event_type": "contract_violation",
                "violation_type": violation_data.get("violation_type"),
                "provider": violation_data.get("provider"),
                "data_type": violation_data.get("data_type"),
                "violation_details": violation_data.get("details", {}),
                "quarantine_id": quarantine_info.get("quarantine_id"),
                "quarantine_path": quarantine_info.get("path"),
                "learning_priority": 0.8,  # High priority for violations
                "vendor_stamp": {
                    "source": "contract_validator",
                    "version": "1.0.0",
                    "timestamp": datetime.now().isoformat(),
                },
            }

            return self._handle_sync_write(violation_event)

        except Exception as e:
            logger.error(f"Contract violation brain write failed: {e}")
            return f"error_{str(e)[:50]}"

    async def flush_pending(self) -> list[str]:
        """Flush pending batch writes."""
        if not BRAIN_ASYNC_MODE or not self._pending_batch:
            return []

        try:
            if self._lock:
                async with self._lock:
                    return await self._flush_batch()
            else:
                return await self._flush_batch()
        except Exception as e:
            logger.error(f"Brain batch flush failed: {e}")
            return []

    async def _enrich_market_event(
        self,
        data: dict[str, Any],
        data_type: str,
        vendor_stamp: dict[str, Any] | None,
        timezone_info: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Enrich market data with brain-first metadata."""

        # Extract ticker information
        ticker = self._extract_ticker(data)

        # Build base event
        event = {
            "event_type": "market_data_ingestion",
            "data_type": data_type,
            "ticker": ticker,
            "data_payload": data,
            "ingestion_ts": datetime.now().isoformat(),
            "learning_priority": self._calculate_market_priority(data, data_type),
        }

        # Add vendor stamp
        if vendor_stamp:
            event["vendor_stamp"] = vendor_stamp

        # Add timezone information
        if timezone_info:
            event["timezone_info"] = timezone_info

        # Add microstructure features if available
        if data_type == "ohlcv" and "microstructure" in data:
            event["microstructure_features"] = data["microstructure"]
            event["learning_priority"] = min(event["learning_priority"] + 0.2, 1.0)

        # Add data quality metrics
        event["data_quality"] = self._assess_data_quality(data, data_type)

        return event

    async def _enrich_nlp_event(
        self,
        news_data: dict[str, Any],
        nlp_results: dict[str, Any],
        vendor_stamp: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Enrich NLP data with brain-first metadata."""

        event = {
            "event_type": "nlp_analysis",
            "news_data": news_data,
            "nlp_results": nlp_results,
            "analysis_ts": datetime.now().isoformat(),
            "learning_priority": self._calculate_nlp_priority(nlp_results),
        }

        # Add vendor stamp
        if vendor_stamp:
            event["vendor_stamp"] = vendor_stamp

        # Extract key insights for quick access
        event["insights"] = {
            "tickers_mentioned": nlp_results.get("tickers", []),
            "sentiment_polarity": nlp_results.get("overall_sentiment", {}).get("polarity", 0.0),
            "event_type": nlp_results.get("event_classification", "unknown"),
            "entity_count": len(nlp_results.get("entities", [])),
            "novelty_score": nlp_results.get("novelty_score", 0.0),
        }

        return event

    async def _handle_async_write(self, event: dict[str, Any]) -> str:
        """Handle asynchronous batch writing."""
        if self._lock:
            async with self._lock:
                self._pending_batch.append(event)

                # Check if we should flush
                should_flush = (
                    len(self._pending_batch) >= BRAIN_BATCH_SIZE
                    or (datetime.now() - self._last_flush).total_seconds() >= BRAIN_FLUSH_INTERVAL
                )

                if should_flush:
                    await self._flush_batch()

                return f"batch_{len(self._pending_batch)}"
        else:
            self._pending_batch.append(event)
            return f"batch_{len(self._pending_batch)}"

    def _handle_sync_write(self, event: dict[str, Any]) -> str:
        """Handle synchronous writing."""
        try:
            # Lazy import to avoid import-time side effects when brain is disabled
            from app.memory.events import append_event as _append

            return _append(event)
        except Exception as e:
            logger.error(f"Sync brain write failed: {e}")
            return f"sync_error_{str(e)[:30]}"

    async def _flush_batch(self) -> list[str]:
        """Flush pending batch to brain."""
        if not self._pending_batch:
            return []

        event_ids = []
        batch_to_flush = self._pending_batch.copy()
        self._pending_batch.clear()
        self._last_flush = datetime.now()

        # Import once for the whole batch to avoid per-event import overhead
        try:
            from app.memory.events import append_event as _append
        except Exception as e:
            logger.error(f"Brain append not available: {e}")
            return [f"error_{str(e)[:20]}"] * len(batch_to_flush)

        for event in batch_to_flush:
            try:
                event_id = _append(event)
                event_ids.append(event_id)
            except Exception as e:
                logger.error(f"Failed to write event to brain: {e}")
                event_ids.append(f"error_{str(e)[:20]}")

        logger.info(f"Flushed {len(event_ids)} events to brain")
        return event_ids

    def _extract_ticker(self, data: dict[str, Any]) -> str | None:
        """Extract ticker from data payload."""
        # Try common ticker field names
        for field in ["ticker", "symbol", "instrument", "asset"]:
            if field in data:
                return data[field]

        # Try nested structures
        if "metadata" in data and "ticker" in data["metadata"]:
            return data["metadata"]["ticker"]

        return None

    def _calculate_market_priority(self, data: dict[str, Any], data_type: str) -> float:
        """Calculate learning priority for market data."""
        priority = 0.5  # Base priority

        # Higher priority for certain data types
        priority_map = {
            "ohlcv": 0.6,
            "real_time_quotes": 0.8,
            "news": 0.7,
            "earnings": 0.9,
            "splits": 0.8,
            "dividends": 0.7,
        }

        priority = priority_map.get(data_type, priority)

        # Boost priority for unusual market conditions
        if "volume" in data:
            volume = data.get("volume", 0)
            if volume > 0 and "avg_volume" in data:
                # High volume gets priority boost
                volume_ratio = volume / max(data["avg_volume"], 1)
                if volume_ratio > 2.0:  # Unusually high volume
                    priority = min(priority + 0.2, 1.0)

        # Boost for volatile price movements
        if "change_percent" in data:
            abs_change = abs(data.get("change_percent", 0))
            if abs_change > 5.0:  # >5% move
                priority = min(priority + 0.1, 1.0)

        return priority

    def _calculate_nlp_priority(self, nlp_results: dict[str, Any]) -> float:
        """Calculate learning priority for NLP results."""
        priority = 0.6  # Base priority for NLP

        # Boost for high sentiment magnitude
        sentiment = nlp_results.get("overall_sentiment", {})
        if sentiment:
            magnitude = abs(sentiment.get("polarity", 0.0))
            if magnitude > 0.7:
                priority = min(priority + 0.2, 1.0)

        # Boost for multiple tickers mentioned
        tickers = nlp_results.get("tickers", [])
        if len(tickers) > 1:
            priority = min(priority + 0.1, 1.0)

        # Boost for important event types
        event_type = nlp_results.get("event_classification", "")
        high_priority_events = ["earnings", "merger", "acquisition", "guidance", "split"]
        if any(event in event_type.lower() for event in high_priority_events):
            priority = min(priority + 0.2, 1.0)

        # Boost for high novelty
        novelty = nlp_results.get("novelty_score", 0.0)
        if novelty > 0.8:
            priority = min(priority + 0.15, 1.0)

        return priority

    def _assess_data_quality(self, data: dict[str, Any], data_type: str) -> dict[str, Any]:
        """Assess data quality metrics."""
        quality = {"completeness": 1.0, "freshness": 1.0, "consistency": 1.0, "issues": []}

        # Check completeness
        required_fields = {
            "ohlcv": ["open", "high", "low", "close", "volume"],
            "quotes": ["bid", "ask", "timestamp"],
            "news": ["headline", "published", "source"],
        }

        if data_type in required_fields:
            required = required_fields[data_type]
            missing = [field for field in required if field not in data or data[field] is None]
            if missing:
                quality["completeness"] = max(0.0, 1.0 - len(missing) / len(required))
                quality["issues"].append(f"Missing fields: {missing}")

        # Check freshness (basic implementation)
        if "timestamp" in data or "published" in data:
            ts_field = "timestamp" if "timestamp" in data else "published"
            try:
                # Simple age check - can be enhanced
                if isinstance(data[ts_field], str):
                    # Assume recent if we can't parse easily
                    quality["freshness"] = 0.9
            except Exception:
                quality["freshness"] = 0.8
                quality["issues"].append("Timestamp parsing issue")

        # Check for obvious inconsistencies
        if data_type == "ohlcv":
            try:
                open_price, high_price, low_price, close_price = (
                    data.get("open", 0),
                    data.get("high", 0),
                    data.get("low", 0),
                    data.get("close", 0),
                )
                if high_price < max(open_price, close_price) or low_price > min(
                    open_price, close_price
                ):
                    quality["consistency"] = 0.5
                    quality["issues"].append("OHLC price inconsistency")
            except (TypeError, ValueError):
                quality["consistency"] = 0.7
                quality["issues"].append("Price type error")

        return quality


# Global brain write-through instance
brain_writer = BrainWriteThrough()


# Convenience functions for common operations
async def write_market_data_to_brain(
    data: dict[str, Any],
    data_type: str = "market_data",
    vendor_stamp: dict[str, Any] | None = None,
    timezone_info: dict[str, Any] | None = None,
) -> str:
    """Write market data to brain (convenience function)."""
    return await brain_writer.write_market_data(data, data_type, vendor_stamp, timezone_info)


async def write_nlp_to_brain(
    news_data: dict[str, Any],
    nlp_results: dict[str, Any],
    vendor_stamp: dict[str, Any] | None = None,
) -> str:
    """Write NLP analysis to brain (convenience function)."""
    return await brain_writer.write_nlp_analysis(news_data, nlp_results, vendor_stamp)


async def write_provider_health_to_brain(provider_name: str, health_metrics: dict[str, Any]) -> str:
    """Write provider health to brain (convenience function)."""
    return await brain_writer.write_provider_health(provider_name, health_metrics)


async def write_contract_violation_to_brain(
    violation_data: dict[str, Any], quarantine_info: dict[str, Any]
) -> str:
    """Write contract violation to brain (convenience function)."""
    return await brain_writer.write_contract_violation(violation_data, quarantine_info)


def get_brain_stats() -> dict[str, Any]:
    """Get brain write-through statistics."""
    return {
        "enabled": BRAIN_WRITE_ENABLED,
        "available": BRAIN_AVAILABLE,
        "async_mode": BRAIN_ASYNC_MODE,
        "batch_size": BRAIN_BATCH_SIZE,
        "flush_interval": BRAIN_FLUSH_INTERVAL,
        "pending_events": len(brain_writer._pending_batch) if BRAIN_ASYNC_MODE else 0,
    }
