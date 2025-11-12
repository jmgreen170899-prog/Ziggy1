"""
Telegram notification handlers for ZiggyAI alerts
Integrates enhanced message formatting with the alert system.
"""

from __future__ import annotations

import logging
from typing import Any

from app.services.alerts import AlertTrigger, NotificationChannel


logger = logging.getLogger(__name__)


# Import telegram sender
try:
    from app.tasks.telegram import tg_send
except Exception:
    logger.warning("Telegram module not available")

    def tg_send(*_args: Any, **_kwargs: Any) -> bool:
        return False


# Import enhanced formatter
try:
    from app.tasks.telegram_formatter import format_alert_triggered_message
except Exception:
    logger.warning("Telegram formatter not available")

    def format_alert_triggered_message(alert_data: dict[str, Any]) -> str:
        # Fallback basic formatting
        symbol = alert_data.get("symbol", "UNKNOWN")
        price = alert_data.get("trigger_price", 0.0)
        condition = alert_data.get("condition_met", "condition met")
        return f"🔔 ALERT: {symbol} @ ${price:.2f} - {condition}"


def telegram_notification_handler(trigger: AlertTrigger) -> bool:
    """
    Enhanced Telegram notification handler for alert triggers.

    Args:
        trigger: AlertTrigger object with alert details

    Returns:
        True if notification was sent successfully
    """
    try:
        # Convert trigger to dict for formatter
        alert_data = trigger.to_dict()

        # Format message with enhanced formatter
        message = format_alert_triggered_message(alert_data)

        # Send via Telegram
        success = tg_send(
            message,
            kind="alert-trigger",
            meta={
                "alert_id": trigger.alert_id,
                "symbol": trigger.symbol,
                "trigger_price": trigger.trigger_price,
            },
        )

        if success:
            logger.info(f"Telegram notification sent for alert {trigger.alert_id}")
        else:
            logger.warning(f"Failed to send Telegram notification for alert {trigger.alert_id}")

        return success

    except Exception as e:
        logger.error(f"Error in telegram notification handler: {e}")
        return False


def register_telegram_handlers(alert_system: Any) -> None:
    """
    Register Telegram notification handlers with the alert system.

    Args:
        alert_system: ProductionAlertSystem instance
    """
    try:
        alert_system.register_notification_handler(
            NotificationChannel.TELEGRAM,
            telegram_notification_handler,
        )
        logger.info("Telegram notification handler registered")
    except Exception as e:
        logger.error(f"Failed to register Telegram notification handler: {e}")
