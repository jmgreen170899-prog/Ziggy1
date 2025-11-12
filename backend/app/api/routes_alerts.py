# backend/app/api/routes_alerts.py
from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, HTTPException

# QUICK ACTIONS ++
from pydantic import BaseModel, Field  # type: ignore


# Market Brain Integration
try:
    from app.services.market_brain.simple_data_hub import DataSource, enhance_market_data

    BRAIN_AVAILABLE = True
    _enhance_market_data = enhance_market_data
    _DataSource = DataSource
except ImportError:
    BRAIN_AVAILABLE = False
    _enhance_market_data = None
    _DataSource = None

router = APIRouter()

# ──────────────────────────────────────────────────────────────────────────────
# Production Alert System Integration
# ──────────────────────────────────────────────────────────────────────────────
try:
    from app.services.alerts import (
        ProductionAlertSystem,
    )

    _production_alerts = ProductionAlertSystem()
    _HAS_PRODUCTION_ALERTS = True
except Exception as e:
    # Fallback to in-memory system if production alerts fail
    _production_alerts = None
    _HAS_PRODUCTION_ALERTS = False
    print(f"Warning: Production alerts not available: {e}")

# ──────────────────────────────────────────────────────────────────────────────
# Best-effort imports with safe fallbacks
# ──────────────────────────────────────────────────────────────────────────────
try:
    # Preferred newer API
    from app.tasks.scheduler import (  # type: ignore
        get_scan_enabled,
        scanner_status,
        set_scan_enabled,
        start_scanner,
        stop_scanner,
    )

    _HAS_SCANNER = True
except Exception:
    # Older alias (kept for backward compat in some builds)
    try:
        from app.tasks.scheduler import (
            get_scan_enabled,
            set_scan_enabled,
        )
        from app.tasks.scheduler import (  # type: ignore
            start_scheduler as start_scanner,  # alias
        )

        stop_scanner = None  # type: ignore
        scanner_status = None  # type: ignore
        _HAS_SCANNER = True
    except Exception:
        # Soft fallbacks so the app still starts without the task module
        _ENABLED = False

        def start_scanner() -> None:  # type: ignore
            pass

        def stop_scanner() -> None:  # type: ignore
            pass

        def get_scan_enabled() -> bool:  # type: ignore
            return _ENABLED

        def set_scan_enabled(v: bool) -> None:  # type: ignore
            nonlocal_enabled = v
            globals()["_ENABLED"] = bool(nonlocal_enabled)

        def scanner_status() -> dict[str, Any]:  # type: ignore
            return {
                "running": False,
                "enabled": get_scan_enabled(),
                "last_run": None,
                "last_error": "scheduler module unavailable",
                "last_symbols": [],
                "last_alerts": 0,
                "interval_s": None,
            }

        _HAS_SCANNER = False

# Telegram helpers (optional)
try:
    from app.tasks.telegram import tg_diag, tg_send  # type: ignore
except Exception:

    def tg_send(*_args: Any, **_kwargs: Any) -> bool:  # type: ignore
        return False

    def tg_diag() -> dict[str, Any]:  # type: ignore
        return {
            "token_set": False,
            "chat_set": False,
            "getme_ok": False,
            "last_error": "telegram module unavailable",
            "last_raw": {},
        }


# QUICK ACTIONS ++ optional alerts service integration
# We try several likely locations/signatures, falling back to a local in-memory store.
_ALERTS_INMEM: list[dict[str, Any]] = []
try:
    # Modern central alert API
    from app.services.alerts import create_alert as _create_alert_service  # type: ignore
except Exception:
    _create_alert_service = None  # type: ignore


def _create_alert_fallback(symbol: str, atype: str, params: dict[str, Any]) -> dict[str, Any]:
    """Very small in-memory placeholder when no alert service is present."""
    entry = {
        "id": f"inmem-{int(time.time() * 1000)}-{symbol}-{atype}",
        "symbol": symbol,
        "type": atype,
        "params": params or {},
        "created_at": time.time(),
        "status": "registered",
        "engine": "in-memory",
    }
    _ALERTS_INMEM.append(entry)
    return entry


def _create_alert(symbol: str, atype: str, params: dict[str, Any]) -> dict[str, Any]:
    """Dispatch to real service if available, else fallback."""
    if _create_alert_service:
        try:
            # We allow either positional or keyword dispatch depending on implementation
            try:
                return _create_alert_service(symbol, atype, **(params or {}))  # type: ignore
            except TypeError:
                return _create_alert_service(symbol=symbol, type=atype, params=params or {})  # type: ignore
        except Exception as e:
            # If the real service errors, we still provide a graceful response
            return {
                "id": f"error-{int(time.time() * 1000)}",
                "symbol": symbol,
                "type": atype,
                "params": params or {},
                "created_at": time.time(),
                "status": "error",
                "engine": "service",
                "error": str(e),
            }
    # Fallback
    return _create_alert_fallback(symbol, atype, params or {})


# ──────────────────────────────────────────────────────────────────────────────
# Alerts API
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/status")
def alerts_status():
    """
    Return current scanning status. If full scheduler status is available,
    include it; otherwise return the minimal enabled flag.
    """
    try:
        if callable(scanner_status):  # type: ignore
            st = scanner_status()  # type: ignore
            # Ensure minimal shape for the frontend
            st = dict(st or {})
            st["enabled"] = bool(st.get("enabled", get_scan_enabled()))
            st["asof"] = time.time()

            # Enhance with market brain intelligence
            if BRAIN_AVAILABLE and _enhance_market_data and _DataSource:
                st = _enhance_market_data(st, _DataSource.OVERVIEW)

            return st
    except Exception:
        # fall back to minimal
        pass

    result = {"enabled": bool(get_scan_enabled()), "asof": time.time()}

    # Enhance with market brain intelligence
    if BRAIN_AVAILABLE and _enhance_market_data and _DataSource:
        result = _enhance_market_data(result, _DataSource.OVERVIEW)

    return result


@router.post("/start")
def alerts_start():
    """
    Start (or ensure) the background scan loop and enable it.
    """
    try:
        try:
            start_scanner()
        except Exception:
            # best-effort: enabling the flag alone will still let the UI reflect the state
            pass
        set_scan_enabled(True)
        # Return fresh status if available
        try:
            st = scanner_status()  # type: ignore
        except Exception:
            st = {}
        return {
            "ok": True,
            "enabled": bool(get_scan_enabled()),
            "status": st or None,
            "asof": time.time(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "failed to start alerts", "reason": str(e)},
        )


@router.post("/stop")
def alerts_stop():
    """
    Disable the background scan loop. If stop_scanner is available, call it;
    otherwise we just flip the enable flag to pause alerts.
    """
    try:
        set_scan_enabled(False)
        try:
            if callable(stop_scanner):  # type: ignore
                stop_scanner()  # type: ignore
        except Exception:
            # fine: loop will naturally idle with enabled=False
            pass
        try:
            st = scanner_status()  # type: ignore
        except Exception:
            st = {}
        return {
            "ok": True,
            "enabled": bool(get_scan_enabled()),
            "status": st or None,
            "asof": time.time(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "failed to stop alerts", "reason": str(e)},
        )


@router.post("/ping/test")
def alerts_ping_test():
    """
    Send a Telegram test message.
    Success if tg_send() returns True OR last_raw.json.ok == True.
    """
    try:
        ok = tg_send("✅ Ziggy alerts test", kind="alerts-test")
    except Exception:
        ok = False

    d = tg_diag()
    delivered = bool(d.get("last_raw", {}).get("json", {}).get("ok") is True)

    if ok or delivered:
        return {"ok": True, "diag": d, "asof": time.time()}

    raise HTTPException(
        status_code=500,
        detail={
            "error": "Telegram send failed",
            "reason": d.get("last_error", "unknown"),
            "token_set": d.get("token_set"),
            "chat_set": d.get("chat_set"),
            "getme_ok": d.get("getme_ok"),
            "last_raw": d.get("last_raw"),
        },
    )


# ──────────────────────────────────────────────────────────────────────────────
# QUICK ACTIONS ++ Alert creation endpoints (additive; no breaking changes)
# ──────────────────────────────────────────────────────────────────────────────


class AlertCreateIn(BaseModel):
    """Generic alert creation schema."""

    symbol: str | None = Field(default=None, description="Symbol (e.g. AAPL)")
    ticker: str | None = Field(default=None, description="Alias for symbol")
    type: str = Field(default="sma", description="Alert type (e.g. sma)")
    window: int | None = Field(default=None, description="Lookback window (e.g. 50)")
    rule: str | None = Field(default="cross", description="Rule (e.g. cross, cross_up, cross_down)")
    # Any extra params are accepted pass-through
    # NOTE: FastAPI will store unknown keys under .__dict__ but not in model;
    # we'll accept an optional 'params' bag for explicit extra kwargs.
    params: dict[str, Any] | None = Field(default=None)


def _normalize_symbol(inp: str | None, alt: str | None) -> str:
    s = (inp or alt or "").strip()
    return s.upper()


def _build_params(body: AlertCreateIn) -> dict[str, Any]:
    params: dict[str, Any] = {}
    if body.window is not None:
        params["window"] = body.window
    if body.rule:
        params["rule"] = body.rule
    if body.params:
        params.update(dict(body.params))
    return params


@router.post("/create")
async def alerts_create(body: AlertCreateIn):
    """
    Generic alert creator - now uses production alert system.
    Example:
      { "symbol": "AAPL", "type": "sma", "window": 50, "rule": "cross" }
    """
    symbol = _normalize_symbol(body.symbol, body.ticker)
    if not symbol:
        raise HTTPException(status_code=400, detail={"error": "symbol required"})
    atype = (body.type or "sma").lower().strip()
    params = _build_params(body)

    try:
        # Try production alert system first
        if _HAS_PRODUCTION_ALERTS and _production_alerts:
            # Map legacy alert types to production conditions
            condition_map = {
                "sma": "price_above",  # Default mapping
                "price": "price_above",
                "volume": "volume_spike",
                "rsi": "rsi_overbought",
            }

            condition_type = condition_map.get(atype, "price_above")

            # Create production alert (synchronous method)
            alert_data = {
                "symbol": symbol,
                "condition_type": condition_type,
                "threshold": params.get("threshold", params.get("window", 50)),
                "comparison_value": params.get("comparison_value"),
                "notification_channels": ["in_app"],  # Default to in-app
                "message": f"{atype.upper()} alert for {symbol}",
                "metadata": params,
            }

            alert_id = _production_alerts.create_alert(**alert_data)

            # Get alerts to return the created alert
            alerts = _production_alerts.get_alerts(symbol=symbol)
            created_alert = next((a for a in alerts if a.get("id") == alert_id), None)

            return {
                "ok": True,
                "message": f"{atype.upper()} alert created",
                "alert": created_alert,
                "alert_id": alert_id,
                "production": True,
                "asof": time.time(),
            }
        else:
            # Fallback to legacy system
            rec = _create_alert(symbol, atype, params)
            msg = f"{atype.upper()} alert set"
            return {
                "ok": True,
                "message": msg,
                "alert": rec,
                "production": False,
                "asof": time.time(),
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail={"error": "failed to create alert", "reason": str(e)}
        )


@router.post("/sma50")
def alerts_sma50(body: dict[str, Any]):
    """
    Convenience endpoint: create a 50DMA cross alert.
    Accepts { symbol | ticker } and optional rule override.
    """
    symbol = _normalize_symbol(body.get("symbol"), body.get("ticker"))
    if not symbol:
        raise HTTPException(status_code=400, detail={"error": "symbol required"})
    rule = (body.get("rule") or "cross").strip().lower()
    try:
        rec = _create_alert(symbol, "sma", {"window": 50, "rule": rule})
        return {"ok": True, "message": "50DMA alert set", "alert": rec, "asof": time.time()}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail={"error": "failed to set 50DMA alert", "reason": str(e)}
        )


@router.post("/moving-average/50")
def alerts_ma50_alias(body: dict[str, Any]):
    """
    Alias for /alerts/sma50.
    """
    return alerts_sma50(body)


# Optional: simple list for debugging the in-memory store (no auth changes)
@router.get("/list")
def alerts_list():
    """
    Returns alerts from production system or in-memory fallback.
    """
    try:
        if _HAS_PRODUCTION_ALERTS and _production_alerts:
            # Get alerts from production system
            alerts = _production_alerts.get_alerts()
            result = {
                "items": alerts,
                "count": len(alerts),
                "production": True,
                "asof": time.time(),
            }

            # Enhance with market brain intelligence
            if BRAIN_AVAILABLE and _enhance_market_data and _DataSource:
                result = _enhance_market_data(result, _DataSource.OVERVIEW)

            return result
        else:
            # Fallback to in-memory
            result = {
                "items": list(_ALERTS_INMEM),
                "count": len(_ALERTS_INMEM),
                "production": False,
                "asof": time.time(),
            }

            # Enhance with market brain intelligence
            if BRAIN_AVAILABLE and _enhance_market_data and _DataSource:
                result = _enhance_market_data(result, _DataSource.OVERVIEW)

            return result
    except Exception as e:
        # Fallback on any error
        return {
            "items": list(_ALERTS_INMEM),
            "count": len(_ALERTS_INMEM),
            "production": False,
            "error": str(e),
            "asof": time.time(),
        }


# ──────────────────────────────────────────────────────────────────────────────
# Production Alert System Endpoints
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/production/status")
def alerts_production_status():
    """Check if production alert system is available."""
    return {
        "production_available": _HAS_PRODUCTION_ALERTS,
        "system_status": "active" if _HAS_PRODUCTION_ALERTS else "fallback",
        "asof": time.time(),
    }


@router.get("/history")
def alerts_history(alert_id: str | None = None, symbol: str | None = None, limit: int = 100):
    """Get alert trigger history."""
    if _HAS_PRODUCTION_ALERTS and _production_alerts:
        try:
            # Handle optional parameters properly
            kwargs = {"limit": limit}
            if alert_id:
                kwargs["alert_id"] = alert_id
            if symbol:
                kwargs["symbol"] = symbol

            history = _production_alerts.get_alert_history(**kwargs)
            return {
                "history": history,
                "count": len(history),
                "production": True,
                "asof": time.time(),
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail={"error": str(e)})
    else:
        return {
            "history": [],
            "count": 0,
            "production": False,
            "message": "Production alert system not available",
            "asof": time.time(),
        }


@router.delete("/{alert_id}")
def delete_alert(alert_id: str):
    """Delete a specific alert."""
    if _HAS_PRODUCTION_ALERTS and _production_alerts:
        try:
            success = _production_alerts.delete_alert(alert_id)
            if success:
                return {
                    "ok": True,
                    "message": f"Alert {alert_id} deleted",
                    "production": True,
                    "asof": time.time(),
                }
            else:
                raise HTTPException(status_code=404, detail={"error": "Alert not found"})
        except Exception as e:
            raise HTTPException(status_code=500, detail={"error": str(e)})
    else:
        raise HTTPException(
            status_code=503, detail={"error": "Production alert system not available"}
        )


@router.put("/{alert_id}/enable")
def enable_alert(alert_id: str):
    """Enable a specific alert."""
    if _HAS_PRODUCTION_ALERTS and _production_alerts:
        try:
            success = _production_alerts.update_alert_status(alert_id, "active")
            if success:
                return {
                    "ok": True,
                    "message": f"Alert {alert_id} enabled",
                    "production": True,
                    "asof": time.time(),
                }
            else:
                raise HTTPException(status_code=404, detail={"error": "Alert not found"})
        except Exception as e:
            raise HTTPException(status_code=500, detail={"error": str(e)})
    else:
        raise HTTPException(
            status_code=503, detail={"error": "Production alert system not available"}
        )


@router.put("/{alert_id}/disable")
def disable_alert(alert_id: str):
    """Disable a specific alert."""
    if _HAS_PRODUCTION_ALERTS and _production_alerts:
        try:
            success = _production_alerts.update_alert_status(alert_id, "disabled")
            if success:
                return {
                    "ok": True,
                    "message": f"Alert {alert_id} disabled",
                    "production": True,
                    "asof": time.time(),
                }
            else:
                raise HTTPException(status_code=404, detail={"error": "Alert not found"})
        except Exception as e:
            raise HTTPException(status_code=500, detail={"error": str(e)})
    else:
        raise HTTPException(
            status_code=503, detail={"error": "Production alert system not available"}
        )
