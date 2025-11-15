"""
Production Alert System with Persistent Storage
Replaces the in-memory placeholder with a robust, persistent alert system.
"""

import asyncio
import json
import logging
import sqlite3
import threading
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any


logger = logging.getLogger("ziggy")


class AlertConditionType(Enum):
    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"
    PRICE_CHANGE_PCT = "price_change_pct"
    VOLUME_SPIKE = "volume_spike"
    RSI_OVERSOLD = "rsi_oversold"
    RSI_OVERBOUGHT = "rsi_overbought"
    CUSTOM_EXPRESSION = "custom_expression"


class AlertStatus(Enum):
    ACTIVE = "active"
    TRIGGERED = "triggered"
    DISABLED = "disabled"
    EXPIRED = "expired"


class NotificationChannel(Enum):
    TELEGRAM = "telegram"
    EMAIL = "email"
    WEBHOOK = "webhook"
    IN_APP = "in_app"


class Alert:
    """Enhanced alert with complex conditions and multiple notification channels."""

    def __init__(
        self,
        symbol: str,
        condition_type: AlertConditionType,
        condition_value: float,
        name: str = "",
        description: str = "",
        channels: list[NotificationChannel] | None = None,
        expires_at: datetime | None = None,
        repeat_interval: int | None = None,
        custom_expression: str = "",
    ):
        self.id = str(uuid.uuid4())
        self.symbol = symbol.upper()
        self.condition_type = condition_type
        self.condition_value = condition_value
        self.name = name or f"{symbol} Alert"
        self.description = description
        self.channels = channels or [NotificationChannel.IN_APP]
        self.status = AlertStatus.ACTIVE
        self.expires_at = expires_at
        self.repeat_interval = repeat_interval  # seconds
        self.custom_expression = custom_expression

        self.created_at = datetime.now(UTC)
        self.updated_at = self.created_at
        self.last_triggered_at: datetime | None = None
        self.trigger_count = 0

        # Runtime data
        self.last_checked_price = 0.0
        self.last_checked_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert alert to dictionary for API responses."""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "condition_type": self.condition_type.value,
            "condition_value": self.condition_value,
            "name": self.name,
            "description": self.description,
            "channels": [c.value for c in self.channels],
            "status": self.status.value,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "repeat_interval": self.repeat_interval,
            "custom_expression": self.custom_expression,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_triggered_at": (
                self.last_triggered_at.isoformat() if self.last_triggered_at else None
            ),
            "trigger_count": self.trigger_count,
            "last_checked_price": self.last_checked_price,
            "last_checked_at": (
                self.last_checked_at.isoformat() if self.last_checked_at else None
            ),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Alert":
        """Create alert from dictionary."""
        alert = cls(
            symbol=data["symbol"],
            condition_type=AlertConditionType(data["condition_type"]),
            condition_value=data["condition_value"],
            name=data.get("name", ""),
            description=data.get("description", ""),
            channels=[NotificationChannel(c) for c in data.get("channels", ["in_app"])],
            expires_at=(
                datetime.fromisoformat(data["expires_at"])
                if data.get("expires_at")
                else None
            ),
            repeat_interval=data.get("repeat_interval"),
            custom_expression=data.get("custom_expression", ""),
        )

        alert.id = data["id"]
        alert.status = AlertStatus(data["status"])
        alert.created_at = datetime.fromisoformat(data["created_at"])
        alert.updated_at = datetime.fromisoformat(data["updated_at"])
        alert.last_triggered_at = (
            datetime.fromisoformat(data["last_triggered_at"])
            if data.get("last_triggered_at")
            else None
        )
        alert.trigger_count = data.get("trigger_count", 0)
        alert.last_checked_price = data.get("last_checked_price", 0.0)
        alert.last_checked_at = (
            datetime.fromisoformat(data["last_checked_at"])
            if data.get("last_checked_at")
            else None
        )

        return alert


class AlertTrigger:
    """Record of an alert trigger event."""

    def __init__(
        self,
        alert_id: str,
        symbol: str,
        condition_met: str,
        trigger_price: float,
        message: str,
    ):
        self.id = str(uuid.uuid4())
        self.alert_id = alert_id
        self.symbol = symbol
        self.condition_met = condition_met
        self.trigger_price = trigger_price
        self.message = message
        self.triggered_at = datetime.now(UTC)
        self.notified_channels: list[str] = []

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "alert_id": self.alert_id,
            "symbol": self.symbol,
            "condition_met": self.condition_met,
            "trigger_price": self.trigger_price,
            "message": self.message,
            "triggered_at": self.triggered_at.isoformat(),
            "notified_channels": self.notified_channels,
        }


class ProductionAlertSystem:
    """Enhanced alert system with persistent storage and complex conditions."""

    def __init__(self, db_path: str = "data/alerts.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)

        self.alerts: dict[str, Alert] = {}
        self.triggers: list[AlertTrigger] = []
        self.notification_handlers: dict[NotificationChannel, Callable] = {}
        self.price_cache: dict[str, float] = {}

        self._lock = threading.Lock()
        self._running = False
        self._check_task = None

    # Database initialization moved to controlled init to avoid double-init on reload.
    # Call init_alerts_once() at application startup.

    def _init_database(self):
        """Initialize SQLite database for persistent storage."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS alerts (
                        id TEXT PRIMARY KEY,
                        data TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS alert_triggers (
                        id TEXT PRIMARY KEY,
                        alert_id TEXT NOT NULL,
                        data TEXT NOT NULL,
                        triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (alert_id) REFERENCES alerts (id)
                    )
                """
                )

                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_alerts_symbol
                    ON alerts(json_extract(data, '$.symbol'))
                """
                )

                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_alerts_status
                    ON alerts(json_extract(data, '$.status'))
                """
                )

                conn.commit()
                logger.info("Alert database initialized")
        except Exception:
            logger.exception("Failed to initialize alert database")

    def _load_alerts(self):
        """Load alerts from database on startup."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT data FROM alerts")
                for (data_json,) in cursor.fetchall():
                    data = json.loads(data_json)
                    alert = Alert.from_dict(data)
                    self.alerts[alert.id] = alert

            logger.info(f"Loaded {len(self.alerts)} alerts from database")
        except Exception:
            logger.exception("Failed to load alerts from database")

    def _save_alert(self, alert: Alert):
        """Save alert to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                data_json = json.dumps(alert.to_dict())
                conn.execute(
                    """
                    INSERT OR REPLACE INTO alerts (id, data, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """,
                    (alert.id, data_json),
                )
                conn.commit()
        except Exception:
            logger.exception(f"Failed to save alert {alert.id}")

    def _save_trigger(self, trigger: AlertTrigger):
        """Save trigger event to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                data_json = json.dumps(trigger.to_dict())
                conn.execute(
                    """
                    INSERT INTO alert_triggers (id, alert_id, data)
                    VALUES (?, ?, ?)
                """,
                    (trigger.id, trigger.alert_id, data_json),
                )
                conn.commit()
        except Exception:
            logger.exception(f"Failed to save trigger {trigger.id}")

    def create_alert(self, **kwargs) -> str:
        """Create a new alert."""
        try:
            alert = Alert(**kwargs)

            with self._lock:
                self.alerts[alert.id] = alert
                self._save_alert(alert)

            logger.info(f"Created alert {alert.id} for {alert.symbol}")
            return alert.id
        except Exception:
            logger.exception("Failed to create alert")
            raise

    def update_alert(self, alert_id: str, **kwargs) -> bool:
        """Update an existing alert."""
        try:
            with self._lock:
                if alert_id not in self.alerts:
                    return False

                alert = self.alerts[alert_id]

                # Update fields
                for key, value in kwargs.items():
                    if hasattr(alert, key):
                        setattr(alert, key, value)

                alert.updated_at = datetime.now(UTC)
                self._save_alert(alert)

            logger.info(f"Updated alert {alert_id}")
            return True
        except Exception:
            logger.exception(f"Failed to update alert {alert_id}")
            return False

    def delete_alert(self, alert_id: str) -> bool:
        """Delete an alert."""
        try:
            with self._lock:
                if alert_id not in self.alerts:
                    return False

                del self.alerts[alert_id]

                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("DELETE FROM alerts WHERE id = ?", (alert_id,))
                    conn.commit()

            logger.info(f"Deleted alert {alert_id}")
            return True
        except Exception:
            logger.exception(f"Failed to delete alert {alert_id}")
            return False

    def get_alerts(
        self, symbol: str | None = None, status: AlertStatus | None = None
    ) -> list[dict[str, Any]]:
        """Get alerts, optionally filtered by symbol and status."""
        try:
            with self._lock:
                alerts = list(self.alerts.values())

            if symbol:
                alerts = [a for a in alerts if a.symbol == symbol.upper()]
            if status:
                alerts = [a for a in alerts if a.status == status]

            return [a.to_dict() for a in alerts]
        except Exception:
            logger.exception("Failed to get alerts")
            return []

    def get_alert_history(
        self, alert_id: str | None = None, symbol: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Get alert trigger history."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if alert_id:
                    cursor = conn.execute(
                        """
                        SELECT data FROM alert_triggers
                        WHERE alert_id = ?
                        ORDER BY triggered_at DESC
                        LIMIT ?
                    """,
                        (alert_id, limit),
                    )
                elif symbol:
                    cursor = conn.execute(
                        """
                        SELECT data FROM alert_triggers
                        WHERE json_extract(data, '$.symbol') = ?
                        ORDER BY triggered_at DESC
                        LIMIT ?
                    """,
                        (symbol.upper(), limit),
                    )
                else:
                    cursor = conn.execute(
                        """
                        SELECT data FROM alert_triggers
                        ORDER BY triggered_at DESC
                        LIMIT ?
                    """,
                        (limit,),
                    )

                return [json.loads(data_json) for (data_json,) in cursor.fetchall()]
        except Exception:
            logger.exception("Failed to get alert history")
            return []

    def register_notification_handler(
        self, channel: NotificationChannel, handler: Callable[[AlertTrigger], bool]
    ):
        """Register a notification handler for a specific channel."""
        self.notification_handlers[channel] = handler
        logger.info(f"Registered notification handler for {channel.value}")

    async def check_alerts(self, market_data: dict[str, float]):
        """Check all active alerts against current market data."""
        try:
            current_time = datetime.now(UTC)
            triggered_alerts = []

            with self._lock:
                alerts_to_check = [
                    a for a in self.alerts.values() if a.status == AlertStatus.ACTIVE
                ]

            for alert in alerts_to_check:
                try:
                    if alert.symbol not in market_data:
                        continue

                    current_price = market_data[alert.symbol]
                    alert.last_checked_price = current_price
                    alert.last_checked_at = current_time

                    # Check if alert should trigger
                    should_trigger = self._evaluate_condition(alert, current_price)

                    if should_trigger:
                        # Check repeat interval
                        if (
                            alert.last_triggered_at
                            and alert.repeat_interval
                            and (current_time - alert.last_triggered_at).total_seconds()
                            < alert.repeat_interval
                        ):
                            continue

                        # Create trigger
                        trigger = self._create_trigger(alert, current_price)
                        triggered_alerts.append(trigger)

                        # Update alert
                        alert.last_triggered_at = current_time
                        alert.trigger_count += 1

                        # Check if should disable after trigger
                        if not alert.repeat_interval:
                            alert.status = AlertStatus.TRIGGERED

                        self._save_alert(alert)
                        self._save_trigger(trigger)

                    # Check expiration
                    if alert.expires_at and current_time > alert.expires_at:
                        alert.status = AlertStatus.EXPIRED
                        self._save_alert(alert)

                except Exception:
                    logger.exception(f"Error checking alert {alert.id}")

            # Send notifications
            for trigger in triggered_alerts:
                await self._send_notifications(trigger)

            return len(triggered_alerts)

        except Exception:
            logger.exception("Error during alert checking")
            return 0

    def _evaluate_condition(self, alert: Alert, current_price: float) -> bool:
        """Evaluate if alert condition is met."""
        try:
            if alert.condition_type == AlertConditionType.PRICE_ABOVE:
                return current_price > alert.condition_value
            elif alert.condition_type == AlertConditionType.PRICE_BELOW:
                return current_price < alert.condition_value
            elif alert.condition_type == AlertConditionType.PRICE_CHANGE_PCT:
                if alert.last_checked_price > 0:
                    change_pct = (
                        (current_price - alert.last_checked_price)
                        / alert.last_checked_price
                    ) * 100
                    return abs(change_pct) >= abs(alert.condition_value)
            elif alert.condition_type == AlertConditionType.CUSTOM_EXPRESSION:
                # Simple expression evaluation (in production, use a safer evaluator)
                context = {
                    "price": current_price,
                    "last_price": alert.last_checked_price,
                }
                return eval(alert.custom_expression, {"__builtins__": {}}, context)

            return False
        except Exception:
            logger.exception(f"Error evaluating condition for alert {alert.id}")
            return False

    def _create_trigger(self, alert: Alert, trigger_price: float) -> AlertTrigger:
        """Create a trigger event."""
        condition_met = f"{alert.condition_type.value}: {alert.condition_value}"
        message = f"{alert.name} - {alert.symbol} {condition_met} (Current: ${trigger_price:.2f})"

        if alert.description:
            message += f" - {alert.description}"

        return AlertTrigger(
            alert_id=alert.id,
            symbol=alert.symbol,
            condition_met=condition_met,
            trigger_price=trigger_price,
            message=message,
        )

    async def _send_notifications(self, trigger: AlertTrigger):
        """Send notifications through all configured channels."""
        alert = self.alerts.get(trigger.alert_id)
        if not alert:
            return

        for channel in alert.channels:
            try:
                handler = self.notification_handlers.get(channel)
                if handler:
                    success = (
                        await handler(trigger)
                        if asyncio.iscoroutinefunction(handler)
                        else handler(trigger)
                    )
                    if success:
                        trigger.notified_channels.append(channel.value)
                else:
                    logger.warning(
                        f"No handler registered for notification channel {channel.value}"
                    )
            except Exception:
                logger.exception(f"Failed to send notification via {channel.value}")


# Global instance and init guard
_alert_system: ProductionAlertSystem | None = None
_alerts_ready: bool = False


async def init_alerts_once(db_path: str = "data/alerts.db") -> None:
    """Initialize the global alert system once in a reload-safe way.

    Idempotent: multiple calls are safe; initialization logs only once.
    """
    global _alert_system, _alerts_ready
    if _alerts_ready and _alert_system is not None:
        return
    try:
        system = ProductionAlertSystem(db_path=db_path)
        # Perform DB init and load now, once
        system._init_database()
        system._load_alerts()
        _alert_system = system
        _alerts_ready = True
        logger.info("Alert database initialized")
    except Exception:
        logger.exception("Failed to initialize alert system")
        _alert_system = None
        _alerts_ready = False


# Public API functions
def create_alert(**kwargs) -> str:
    """Create a new alert."""
    if _alert_system is None:
        raise RuntimeError("Alert system not initialized")
    return _alert_system.create_alert(**kwargs)


def update_alert(alert_id: str, **kwargs) -> bool:
    """Update an existing alert."""
    if _alert_system is None:
        raise RuntimeError("Alert system not initialized")
    return _alert_system.update_alert(alert_id, **kwargs)


def delete_alert(alert_id: str) -> bool:
    """Delete an alert."""
    if _alert_system is None:
        raise RuntimeError("Alert system not initialized")
    return _alert_system.delete_alert(alert_id)


def get_alerts(
    symbol: str | None = None, status: str | None = None
) -> list[dict[str, Any]]:
    """Get alerts."""
    status_enum = AlertStatus(status) if status else None
    if _alert_system is None:
        raise RuntimeError("Alert system not initialized")
    return _alert_system.get_alerts(symbol, status_enum)


def get_alert_history(
    alert_id: str | None = None, symbol: str | None = None, limit: int = 100
) -> list[dict[str, Any]]:
    """Get alert history."""
    if _alert_system is None:
        raise RuntimeError("Alert system not initialized")
    return _alert_system.get_alert_history(alert_id, symbol, limit)


def get_alert_system() -> ProductionAlertSystem:
    """Get the global alert system instance."""
    if _alert_system is None:
        raise RuntimeError("Alert system not initialized")
    return _alert_system


async def check_alerts(market_data: dict[str, float]) -> int:
    """Check alerts against market data."""
    if _alert_system is None:
        raise RuntimeError("Alert system not initialized")
    return await _alert_system.check_alerts(market_data)
