from __future__ import annotations

import asyncio
import inspect
import os
import threading
import time
from typing import Any


# Optional screener (signals) + Telegram
try:
    from app.services.screener import run_screener  # type: ignore
except Exception:  # fallback if screener isn't available

    def run_screener() -> list[dict[str, Any]]:  # type: ignore
        return []


try:
    from app.tasks.telegram import tg_send  # type: ignore
except Exception:

    def tg_send(*_args: Any, **_kwargs: Any) -> bool:  # type: ignore
        return False


# Enhanced Telegram formatter
try:
    from app.tasks.telegram_formatter import (
        format_bulk_signals,
        format_signal_message,
    )  # type: ignore

    _HAS_FORMATTER = True
except Exception:
    _HAS_FORMATTER = False


# Provider chain (for cache warming and simple rules)
try:
    from app.services.provider_factory import get_price_provider  # type: ignore
except Exception:
    get_price_provider = None  # type: ignore


# ──────────────────────────────────────────────────────────────────────────────
# Env
# ──────────────────────────────────────────────────────────────────────────────
SCAN_SYMBOLS = os.getenv("SCAN_SYMBOLS", "AAPL,MSFT,NVDA,AMZN,TSLA,BTC-USD,ETH-USD")
SCAN_INTERVAL_S = int(os.getenv("SCAN_INTERVAL_S", "60"))

# Back-compat env knobs (still honored if set)
_DEFAULT_ON = os.getenv("ZIGGY_SCAN_DEFAULT", "1").lower() not in (
    "0",
    "false",
    "no",
    "off",
)
_DEBOUNCE = int(os.getenv("ZIGGY_SIGNAL_MIN_GAP", "900"))

# ──────────────────────────────────────────────────────────────────────────────
# Runtime flags/state
# ──────────────────────────────────────────────────────────────────────────────
_SCAN_ENABLED = _DEFAULT_ON
_STOP = False
_THREAD: threading.Thread | None = None
_LOCK = threading.RLock()

_last_sig: dict[str, tuple[str, float]] = {}  # ticker -> (last_signal, last_sent_ts)
_STATUS: dict[str, Any] = {
    "running": False,
    "enabled": _SCAN_ENABLED,
    "last_run": None,
    "last_error": None,
    "last_symbols": [],
    "last_alerts": 0,
    "interval_s": SCAN_INTERVAL_S,
}
_last_heartbeat_date: str | None = None


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


def _parse_list(s: str) -> list[str]:
    return [x.strip().upper() for x in str(s or "").split(",") if x.strip()]


def _should_alert(ticker: str, signal: str) -> bool:
    """Alert on BUY/SELL first seen, flips, or debounce expiry for same signal."""
    now = time.time()
    prev = _last_sig.get(ticker)
    if prev is None:
        _last_sig[ticker] = (signal, now)
        return signal in ("BUY", "SELL")
    prev_sig, prev_ts = prev
    if signal != prev_sig:
        _last_sig[ticker] = (signal, now)
        return signal in ("BUY", "SELL")
    if signal in ("BUY", "SELL") and now - prev_ts >= _DEBOUNCE:
        _last_sig[ticker] = (signal, now)
        return True
    return False


def _run_maybe_async(func_or_value, *args, **kwargs):
    """
    Robustly run a callable or awaitable from a **thread**:
      - If given a callable, call it; if the result is awaitable, run it.
      - If given an awaitable, run it.
      - Otherwise return the value.
    This avoids 'coroutine was never awaited' regardless of decorator/wrapper quirks.
    """
    try:
        # If it's callable, call it first
        result = (
            func_or_value(*args, **kwargs) if callable(func_or_value) else func_or_value
        )
        if inspect.isawaitable(result):
            # In this background thread there is no running loop → safe to use asyncio.run
            return asyncio.run(result)
        return result
    except Exception:
        # bubble up; caller handles and records status
        raise


def _warm_cache(symbols: list[str]) -> None:
    """Best-effort cache warm via provider (daily OHLC). Works for sync/async providers."""
    if not get_price_provider:
        return
    try:
        mp = get_price_provider()
        if hasattr(mp, "fetch_ohlc"):
            _run_maybe_async(mp.fetch_ohlc, symbols, period_days=120, adjusted=True)
        if hasattr(mp, "today_open_prices"):
            try:
                _run_maybe_async(mp.today_open_prices, symbols)  # may be sync or async
            except Exception:
                pass
    except Exception as e:
        try:
            tg_send(f"⚠️ Scanner warm-cache error: {e!r}", kind="scanner-error")
        except Exception:
            pass


def _heartbeat_daily() -> None:
    global _last_heartbeat_date
    try:
        today = time.strftime("%Y-%m-%d")
        if _last_heartbeat_date != today:
            _last_heartbeat_date = today
            tg_send("Ziggy online ✅", kind="heartbeat")
    except Exception:
        pass


# Global variable for tracking hourly pings
_hourly_pings_sent = {}


def _heartbeat_hourly() -> None:
    """Send thumbs up emoji every hour and half hour to confirm backend is running."""
    try:
        import datetime
        import tempfile

        global _hourly_pings_sent

        now = datetime.datetime.now()
        # Send ping on the hour (XX:00) and half hour (XX:30)
        if (
            now.minute in [0, 30] and now.second < 60
        ):  # within first minute of hour/half-hour
            # Check if we already sent a ping for this time slot to avoid spam
            current_slot = f"{now.hour:02d}:{now.minute:02d}"

            # Use a simple file-based check to avoid duplicate pings
            temp_dir = tempfile.gettempdir()
            ping_file = os.path.join(temp_dir, f"ziggy_ping_{current_slot}.lock")

            try:
                if not os.path.exists(ping_file):
                    # Create lock file and send ping
                    with open(ping_file, "w") as f:
                        f.write(str(time.time()))

                    # Send thumbs up emoji
                    tg_send("👍", kind="heartbeat-hourly")

                    # Clean up old lock files (older than 2 hours)
                    try:
                        import glob

                        pattern = os.path.join(temp_dir, "ziggy_ping_*.lock")
                        for old_file in glob.glob(pattern):
                            if (
                                os.path.getctime(old_file) < time.time() - 7200
                            ):  # 2 hours
                                os.remove(old_file)
                    except Exception:
                        pass
            except Exception:
                # Fallback: use in-memory tracking if file system fails
                if current_slot not in _hourly_pings_sent:
                    _hourly_pings_sent[current_slot] = time.time()
                    tg_send("👍", kind="heartbeat-hourly")

                    # Clean up old entries
                    cutoff = time.time() - 7200  # 2 hours ago
                    _hourly_pings_sent = {
                        k: v for k, v in _hourly_pings_sent.items() if v > cutoff
                    }

    except Exception:
        pass


# ──────────────────────────────────────────────────────────────────────────────
# Core loop
# ──────────────────────────────────────────────────────────────────────────────


def _loop():
    global _STOP
    with _LOCK:
        _STATUS.update({"running": True, "last_error": None})

    while not _STOP:
        t0 = time.time()
        syms = _parse_list(SCAN_SYMBOLS)
        try:
            _heartbeat_daily()
            _heartbeat_hourly()  # Send 👍 every hour and half hour

            if get_scan_enabled():
                # 1) Warm provider caches (so API calls are snappy)
                try:
                    _warm_cache(syms)
                except Exception as e:
                    try:
                        tg_send(f"⚠️ Cache warm error: {e!r}", kind="scanner-error")
                    except Exception:
                        pass

                # 2) Run screener (works whether sync or async)
                try:
                    results = _run_maybe_async(run_screener) or []
                    if not isinstance(results, (list, tuple)):
                        results = list(results)
                except Exception as e:
                    results = []
                    try:
                        tg_send(f"⚠️ Screener error: {e!r}", kind="scanner-error")
                    except Exception:
                        pass

                noteworthy = [
                    s
                    for s in results
                    if isinstance(s, dict) and s.get("signal") in ("BUY", "SELL")
                ]

                # Filter signals that should trigger alerts
                signals_to_send = []
                for s in noteworthy:
                    try:
                        tic = str(s.get("ticker", "")).upper()
                        sig = str(s.get("signal", ""))
                        if not tic or not sig:
                            continue
                        if not _should_alert(tic, sig):
                            continue
                        signals_to_send.append(s)
                    except Exception:
                        continue

                if signals_to_send:
                    try:
                        # Use enhanced formatter if available
                        if _HAS_FORMATTER:
                            # Send bulk summary first
                            summary = format_bulk_signals(
                                signals_to_send, max_signals=5
                            )
                            tg_send(
                                summary,
                                kind="scheduler-summary",
                                meta={"count": len(signals_to_send)},
                            )

                            # Then send detailed messages for each signal (limit to 3 to avoid spam)
                            for signal in signals_to_send[:3]:
                                try:
                                    detailed_msg = format_signal_message(signal)
                                    tg_send(
                                        detailed_msg,
                                        kind="scheduler-detail",
                                        meta={"ticker": signal.get("ticker")},
                                    )
                                    # Small delay between messages
                                    time.sleep(1)
                                except Exception:
                                    pass
                        else:
                            # Fallback to basic formatting
                            lines: list[str] = []
                            for s in signals_to_send:
                                try:
                                    tic = str(s.get("ticker", "")).upper()
                                    sig = str(s.get("signal", ""))
                                    conf = int(float(s.get("confidence", 0.0)) * 100)
                                    reason = (s.get("reason") or "").strip()
                                    lines.append(
                                        f"{tic}: {sig} ({conf}% conf)"
                                        + (f" — {reason}" if reason else "")
                                    )
                                except Exception:
                                    continue

                            if lines:
                                tg_send(
                                    "Ziggy Screener Alerts:\n" + "\n".join(lines),
                                    kind="scheduler",
                                    meta={"count": len(lines)},
                                )
                    except Exception:
                        pass

                with _LOCK:
                    _STATUS.update(
                        {
                            "last_run": time.time(),
                            "last_error": None,
                            "last_symbols": syms,
                            "last_alerts": len(signals_to_send),
                        }
                    )

        except Exception as e:
            try:
                tg_send(f"⚠️ Scanner loop error: {e!r}", kind="scanner-error")
            except Exception:
                pass
            with _LOCK:
                _STATUS.update({"last_run": time.time(), "last_error": repr(e)})

        # sleep remainder
        elapsed = max(0.0, time.time() - t0)
        pause = max(5.0, SCAN_INTERVAL_S - elapsed)
        for _ in range(int(pause)):
            if _STOP:
                break
            time.sleep(1.0)

    with _LOCK:
        _STATUS.update({"running": False})


# ──────────────────────────────────────────────────────────────────────────────
# Public API (used by routes_alerts and startup)
# ──────────────────────────────────────────────────────────────────────────────


def get_scan_enabled() -> bool:
    with _LOCK:
        return bool(_SCAN_ENABLED)


def set_scan_enabled(enabled: bool) -> None:
    global _SCAN_ENABLED
    with _LOCK:
        _SCAN_ENABLED = bool(enabled)
        _STATUS["enabled"] = _SCAN_ENABLED


def start_scanner() -> None:
    """Idempotent start of background scanner."""
    global _THREAD, _STOP
    with _LOCK:
        if _THREAD and _THREAD.is_alive():
            return
        _STOP = False
        _THREAD = threading.Thread(target=_loop, name="ziggy-scan-loop", daemon=True)
        _THREAD.start()


def stop_scanner() -> None:
    """Gracefully stop the scanner loop."""
    global _THREAD, _STOP
    with _LOCK:
        _STOP = True
    t = _THREAD
    if t and t.is_alive():
        t.join(timeout=5.0)
    with _LOCK:
        _THREAD = None
        _STATUS["running"] = False


def scanner_status() -> dict[str, Any]:
    with _LOCK:
        return dict(_STATUS)


# Back-compat names expected by existing routes/main
start_scheduler = start_scanner
