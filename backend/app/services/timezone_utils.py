"""
Timezone Utilities - Perception Layer

Normalize timestamps to exchange timezones and handle DST transitions.
Ensures all market data has proper timezone context for accurate analysis.
"""

from __future__ import annotations

import logging
import os
import re
from datetime import UTC, datetime
from typing import Any


logger = logging.getLogger(__name__)

# Environment configuration
EXCHANGE_TZ_FALLBACK = os.getenv("EXCHANGE_TZ_FALLBACK", "America/New_York")

# Try to import zoneinfo (Python 3.9+) or fallback to pytz
try:
    from zoneinfo import ZoneInfo

    TIMEZONE_BACKEND = "zoneinfo"
except ImportError:
    try:
        import pytz

        TIMEZONE_BACKEND = "pytz"

        def ZoneInfo(tz_name: str):
            """Compatibility wrapper for pytz."""
            return pytz.timezone(tz_name)

    except ImportError:
        TIMEZONE_BACKEND = "none"
        logger.warning("No timezone library available (zoneinfo or pytz)")

        def ZoneInfo(tz_name: str):
            """Fallback timezone that assumes UTC."""
            return UTC


# Exchange to timezone mapping
EXCHANGE_MAP = {
    # North American Exchanges
    "NYSE": "America/New_York",
    "NASDAQ": "America/New_York",
    "NYSE_AMERICAN": "America/New_York",
    "TSX": "America/Toronto",
    "TSE": "America/Toronto",
    # European Exchanges
    "LSE": "Europe/London",
    "LONDON": "Europe/London",
    "EURONEXT": "Europe/Paris",
    "XETRA": "Europe/Berlin",
    "DAX": "Europe/Berlin",
    "SIX": "Europe/Zurich",
    "OMX": "Europe/Stockholm",
    # Asian Exchanges
    "TSE_TOKYO": "Asia/Tokyo",
    "NIKKEI": "Asia/Tokyo",
    "SSE": "Asia/Shanghai",
    "SZSE": "Asia/Shanghai",
    "HKEX": "Asia/Hong_Kong",
    "SGX": "Asia/Singapore",
    "BSE": "Asia/Kolkata",
    "NSE": "Asia/Kolkata",
    "ASX": "Australia/Sydney",
    # Others
    "JSE": "Africa/Johannesburg",
    "B3": "America/Sao_Paulo",
    "BMV": "America/Mexico_City",
}

# Common timezone aliases
TIMEZONE_ALIASES = {
    "EST": "America/New_York",
    "EDT": "America/New_York",
    "PST": "America/Los_Angeles",
    "PDT": "America/Los_Angeles",
    "CST": "America/Chicago",
    "CDT": "America/Chicago",
    "MST": "America/Denver",
    "MDT": "America/Denver",
    "GMT": "Europe/London",
    "BST": "Europe/London",
    "CET": "Europe/Paris",
    "CEST": "Europe/Paris",
    "JST": "Asia/Tokyo",
    "HKT": "Asia/Hong_Kong",
    "SGT": "Asia/Singapore",
    "AEST": "Australia/Sydney",
    "AEDT": "Australia/Sydney",
}


def normalize_event_ts(source_ts: str | datetime, source_tz: str, exchange: str) -> dict[str, Any]:
    """
    Normalize event timestamp to exchange timezone with full context.

    Args:
        source_ts: Source timestamp (string or datetime)
        source_tz: Source timezone (IANA name or alias)
        exchange: Exchange identifier

    Returns:
        Dictionary with normalized timestamp information
    """
    try:
        # Handle timezone resolution
        resolved_source_tz = resolve_timezone(source_tz)
        exchange_tz_name = get_exchange_timezone(exchange)

        # Parse source timestamp
        if isinstance(source_ts, str):
            dt = parse_timestamp_string(source_ts, resolved_source_tz)
        elif isinstance(source_ts, datetime):
            dt = source_ts
            if dt.tzinfo is None:
                # Assume source timezone if naive
                dt = dt.replace(tzinfo=ZoneInfo(resolved_source_tz))
        else:
            raise ValueError(f"Invalid timestamp type: {type(source_ts)}")

        # Ensure datetime has timezone info
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo(resolved_source_tz))

        # Convert to UTC
        utc_dt = dt.astimezone(UTC)

        # Convert to exchange timezone
        exchange_tz = ZoneInfo(exchange_tz_name)
        local_dt = utc_dt.astimezone(exchange_tz)

        # Generate current timestamp
        ingest_utc = datetime.now(UTC)

        return {
            "event_ts_local": local_dt.isoformat(),
            "exchange_tz": exchange_tz_name,
            "ingest_ts_utc": ingest_utc.isoformat(),
            "source_tz": resolved_source_tz,
            "event_ts_utc": utc_dt.isoformat(),
            "timezone_backend": TIMEZONE_BACKEND,
            "dst_active": _is_dst_active(local_dt),
            "utc_offset_seconds": int(local_dt.utcoffset().total_seconds()),
            "success": True,
        }

    except Exception as e:
        logger.error(f"Timestamp normalization failed: {e}")

        # Return fallback with error info
        fallback_utc = datetime.now(UTC)
        fallback_tz = ZoneInfo(EXCHANGE_TZ_FALLBACK)
        fallback_local = fallback_utc.astimezone(fallback_tz)

        return {
            "event_ts_local": fallback_local.isoformat(),
            "exchange_tz": EXCHANGE_TZ_FALLBACK,
            "ingest_ts_utc": fallback_utc.isoformat(),
            "source_tz": source_tz,
            "event_ts_utc": fallback_utc.isoformat(),
            "timezone_backend": TIMEZONE_BACKEND,
            "dst_active": _is_dst_active(fallback_local),
            "utc_offset_seconds": int(fallback_local.utcoffset().total_seconds()),
            "success": False,
            "error": str(e),
            "fallback_used": True,
        }


def resolve_timezone(tz_input: str) -> str:
    """
    Resolve timezone string to IANA timezone name.

    Args:
        tz_input: Timezone string (IANA name, alias, or abbreviation)

    Returns:
        IANA timezone name
    """
    if not tz_input:
        return "UTC"

    # Clean input
    tz_clean = tz_input.strip().upper()

    # Check aliases first
    if tz_clean in TIMEZONE_ALIASES:
        return TIMEZONE_ALIASES[tz_clean]

    # Check if already a valid IANA name (case insensitive)
    tz_candidates = [
        tz_input,  # Original case
        tz_input.lower(),
        tz_input.title(),
        tz_input.replace("_", "/"),  # Handle underscore variants
        tz_input.replace("/", "_"),  # Handle slash variants
    ]

    for candidate in tz_candidates:
        if _is_valid_timezone(candidate):
            return candidate

    logger.warning(f"Unknown timezone '{tz_input}', using UTC")
    return "UTC"


def get_exchange_timezone(exchange: str) -> str:
    """
    Get IANA timezone for exchange.

    Args:
        exchange: Exchange identifier

    Returns:
        IANA timezone name
    """
    if not exchange:
        return EXCHANGE_TZ_FALLBACK

    # Normalize exchange identifier
    exchange_clean = exchange.strip().upper()

    # Direct lookup
    if exchange_clean in EXCHANGE_MAP:
        return EXCHANGE_MAP[exchange_clean]

    # Try partial matching for common patterns
    for exchange_key, tz_name in EXCHANGE_MAP.items():
        if exchange_clean in exchange_key or exchange_key in exchange_clean:
            return tz_name

    logger.warning(f"Unknown exchange '{exchange}', using fallback timezone")
    return EXCHANGE_TZ_FALLBACK


def parse_timestamp_string(ts_string: str, default_tz: str = "UTC") -> datetime:
    """
    Parse timestamp string with timezone handling.

    Args:
        ts_string: Timestamp string in various formats
        default_tz: Default timezone if none specified

    Returns:
        datetime object with timezone info
    """
    if not ts_string:
        raise ValueError("Empty timestamp string")

    # Clean timestamp string
    ts_clean = ts_string.strip()

    # Common timestamp patterns
    patterns = [
        # ISO formats
        r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2}))",
        r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)",
        # US formats
        r"(\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2}:\d{2}(?:\s*[AP]M)?)",
        r"(\d{1,2}-\d{1,2}-\d{4} \d{1,2}:\d{2}:\d{2}(?:\s*[AP]M)?)",
        # European formats
        r"(\d{1,2}\.\d{1,2}\.\d{4} \d{1,2}:\d{2}:\d{2})",
        # Unix timestamp
        r"^(\d{10})$",  # Seconds
        r"^(\d{13})$",  # Milliseconds
    ]

    # Try to parse with each pattern
    for pattern in patterns:
        match = re.search(pattern, ts_clean)
        if match:
            matched_ts = match.group(1)

            try:
                # Handle Unix timestamps
                if matched_ts.isdigit():
                    if len(matched_ts) == 10:  # Seconds
                        return datetime.fromtimestamp(int(matched_ts), tz=UTC)
                    elif len(matched_ts) == 13:  # Milliseconds
                        return datetime.fromtimestamp(int(matched_ts) / 1000, tz=UTC)

                # Try ISO parsing first
                try:
                    return datetime.fromisoformat(matched_ts.replace("Z", "+00:00"))
                except ValueError:
                    pass

                # Try other formats
                dt_formats = [
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%d %H:%M:%S.%f",
                    "%m/%d/%Y %H:%M:%S",
                    "%m/%d/%Y %I:%M:%S %p",
                    "%m-%d-%Y %H:%M:%S",
                    "%d.%m.%Y %H:%M:%S",
                ]

                for fmt in dt_formats:
                    try:
                        dt = datetime.strptime(matched_ts, fmt)
                        return dt.replace(tzinfo=ZoneInfo(default_tz))
                    except ValueError:
                        continue

            except Exception as e:
                logger.debug(f"Failed to parse timestamp '{matched_ts}': {e}")
                continue

    raise ValueError(f"Could not parse timestamp: {ts_string}")


def _is_valid_timezone(tz_name: str) -> bool:
    """Check if timezone name is valid."""
    try:
        ZoneInfo(tz_name)
        return True
    except Exception:
        return False


def _is_dst_active(dt: datetime) -> bool:
    """Check if daylight saving time is active for datetime."""
    try:
        if dt.tzinfo is None:
            return False
        return dt.dst() is not None and dt.dst().total_seconds() > 0
    except Exception:
        return False


def convert_market_time(
    timestamp: str | datetime, from_exchange: str, to_exchange: str
) -> dict[str, Any]:
    """
    Convert timestamp between exchange timezones.

    Args:
        timestamp: Source timestamp
        from_exchange: Source exchange
        to_exchange: Target exchange

    Returns:
        Conversion result with timestamps
    """
    try:
        # Get timezone names
        from_tz = get_exchange_timezone(from_exchange)
        to_tz = get_exchange_timezone(to_exchange)

        # Parse source timestamp
        if isinstance(timestamp, str):
            dt = parse_timestamp_string(timestamp, from_tz)
        else:
            dt = timestamp
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=ZoneInfo(from_tz))

        # Convert to target timezone
        target_dt = dt.astimezone(ZoneInfo(to_tz))

        return {
            "original_time": dt.isoformat(),
            "converted_time": target_dt.isoformat(),
            "from_exchange": from_exchange,
            "to_exchange": to_exchange,
            "from_timezone": from_tz,
            "to_timezone": to_tz,
            "time_difference_hours": (target_dt.utcoffset() - dt.utcoffset()).total_seconds()
            / 3600,
            "success": True,
        }

    except Exception as e:
        return {
            "error": str(e),
            "from_exchange": from_exchange,
            "to_exchange": to_exchange,
            "success": False,
        }


def get_market_hours(exchange: str, date: datetime | None = None) -> dict[str, Any]:
    """
    Get market hours for exchange (basic implementation).

    Args:
        exchange: Exchange identifier
        date: Date to check (uses today if None)

    Returns:
        Market hours information
    """
    if date is None:
        date = datetime.now()

    exchange_tz = get_exchange_timezone(exchange)

    # Basic market hours (can be expanded with real data)
    default_hours = {
        "NYSE": {"open": "09:30", "close": "16:00"},
        "NASDAQ": {"open": "09:30", "close": "16:00"},
        "LSE": {"open": "08:00", "close": "16:30"},
        "TSE_TOKYO": {"open": "09:00", "close": "15:00"},
        "HKEX": {"open": "09:30", "close": "16:00"},
    }

    hours = default_hours.get(exchange.upper(), {"open": "09:00", "close": "17:00"})

    return {
        "exchange": exchange,
        "timezone": exchange_tz,
        "date": date.strftime("%Y-%m-%d"),
        "market_open": hours["open"],
        "market_close": hours["close"],
        "is_trading_day": _is_trading_day(date),  # Basic implementation
        "dst_active": _is_dst_active(date.replace(tzinfo=ZoneInfo(exchange_tz))),
    }


def _is_trading_day(date: datetime) -> bool:
    """Basic trading day check (weekdays only)."""
    return date.weekday() < 5  # Monday=0, Friday=4


def validate_timezone_info(data: dict[str, Any]) -> dict[str, Any]:
    """
    Validate that data contains proper timezone information.

    Args:
        data: Data dictionary to validate

    Returns:
        Validation results
    """
    issues = []
    warnings = []

    # Check for required timezone fields
    required_fields = ["source_tz", "ingest_ts_utc"]
    for field in required_fields:
        if field not in data:
            issues.append(f"Missing required field: {field}")

    # Validate timezone field if present
    if "source_tz" in data:
        if not _is_valid_timezone(data["source_tz"]):
            warnings.append(f"Invalid timezone: {data['source_tz']}")

    # Check timestamp formats
    if "ingest_ts_utc" in data:
        try:
            datetime.fromisoformat(data["ingest_ts_utc"].replace("Z", "+00:00"))
        except Exception:
            issues.append(f"Invalid UTC timestamp format: {data['ingest_ts_utc']}")

    # Check for timezone-aware timestamps in data
    timestamp_fields = ["ts", "timestamp", "event_ts", "published"]
    timezone_aware_count = 0

    for field in timestamp_fields:
        if field in data:
            ts_value = data[field]
            if isinstance(ts_value, str):
                if "Z" in ts_value or "+" in ts_value or "T" in ts_value:
                    timezone_aware_count += 1

    if timestamp_fields and timezone_aware_count == 0:
        warnings.append("No timezone-aware timestamps found")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "timezone_fields_found": len([f for f in required_fields if f in data]),
        "timezone_aware_timestamps": timezone_aware_count,
    }


def get_timezone_stats() -> dict[str, Any]:
    """Get timezone system statistics."""
    return {
        "backend": TIMEZONE_BACKEND,
        "fallback_timezone": EXCHANGE_TZ_FALLBACK,
        "supported_exchanges": len(EXCHANGE_MAP),
        "timezone_aliases": len(TIMEZONE_ALIASES),
        "current_utc": datetime.now(UTC).isoformat(),
    }
