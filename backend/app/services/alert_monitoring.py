"""
Real-time alert monitoring and triggering system for ZiggyAI
Monitors market conditions and triggers alerts via WebSocket
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any

from app.core.websocket import connection_manager


logger = logging.getLogger(__name__)


@dataclass
class Alert:
    """Alert definition"""

    id: str
    user_id: str | None
    symbol: str
    condition_type: str  # 'price_above', 'price_below', 'volume_spike', 'news_sentiment'
    threshold: float
    current_value: float | None = None
    triggered: bool = False
    created_at: float = 0.0
    triggered_at: float | None = None
    message: str = ""


class AlertMonitor:
    """Real-time alert monitoring and triggering system"""

    def __init__(self):
        self.alerts: dict[str, Alert] = {}
        self.monitoring_task: asyncio.Task | None = None
        self.market_data_cache: dict[str, dict[str, Any]] = {}
        self.check_interval = 5  # Check alerts every 5 seconds
        self.is_monitoring = False

    async def start_monitoring(self):
        """Start alert monitoring background task"""
        if self.monitoring_task and not self.monitoring_task.done():
            logger.info("Alert monitoring already running")
            return

        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Alert monitoring started")

    async def stop_monitoring(self):
        """Stop alert monitoring"""
        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Alert monitoring stopped")

    def add_alert(self, alert: Alert) -> bool:
        """Add a new alert to monitor"""
        try:
            alert.created_at = time.time()
            self.alerts[alert.id] = alert
            logger.info(
                f"Added alert {alert.id} for {alert.symbol} {alert.condition_type} {alert.threshold}"
            )
            return True
        except Exception as e:
            logger.error(f"Error adding alert {alert.id}: {e}")
            return False

    def remove_alert(self, alert_id: str) -> bool:
        """Remove an alert"""
        if alert_id in self.alerts:
            del self.alerts[alert_id]
            logger.info(f"Removed alert {alert_id}")
            return True
        return False

    def update_market_data(self, symbol: str, market_data: dict[str, Any]):
        """Update market data cache for alert evaluation"""
        self.market_data_cache[symbol] = {
            "price": market_data.get("price", 0.0),
            "volume": market_data.get("volume", 0),
            "change_percent": market_data.get("change_percent", 0.0),
            "timestamp": market_data.get("timestamp", time.time()),
        }

    async def _monitoring_loop(self):
        """Main alert monitoring loop"""
        try:
            while self.is_monitoring:
                try:
                    await self._check_alerts()
                    await asyncio.sleep(self.check_interval)

                except Exception as e:
                    logger.error(f"Error in alert monitoring loop: {e}")
                    await asyncio.sleep(self.check_interval)

        except asyncio.CancelledError:
            logger.info("Alert monitoring loop cancelled")
        except Exception as e:
            logger.error(f"Alert monitoring loop error: {e}")

    async def _check_alerts(self):
        """Check all alerts for trigger conditions"""
        if not self.alerts:
            return

        triggered_alerts = []

        for alert_id, alert in self.alerts.items():
            if alert.triggered:
                continue

            try:
                # Get current market data for the symbol
                market_data = self.market_data_cache.get(alert.symbol)
                if not market_data:
                    # No market data available, skip this alert
                    continue

                # Check if alert condition is met
                triggered = await self._evaluate_alert_condition(alert, market_data)

                if triggered:
                    alert.triggered = True
                    alert.triggered_at = time.time()
                    alert.current_value = self._get_current_value(alert, market_data)
                    triggered_alerts.append(alert)

            except Exception as e:
                logger.error(f"Error checking alert {alert_id}: {e}")

        # Broadcast triggered alerts
        for alert in triggered_alerts:
            await self._broadcast_alert_triggered(alert)

    async def _evaluate_alert_condition(self, alert: Alert, market_data: dict[str, Any]) -> bool:
        """Evaluate if an alert condition is met"""
        try:
            if alert.condition_type == "price_above":
                current_price = market_data.get("price", 0.0)
                return current_price > alert.threshold

            elif alert.condition_type == "price_below":
                current_price = market_data.get("price", 0.0)
                return current_price < alert.threshold

            elif alert.condition_type == "volume_spike":
                current_volume = market_data.get("volume", 0)
                return current_volume > alert.threshold

            elif alert.condition_type == "change_percent_above":
                change_percent = market_data.get("change_percent", 0.0)
                return abs(change_percent) > alert.threshold

            else:
                logger.warning(f"Unknown alert condition type: {alert.condition_type}")
                return False

        except Exception as e:
            logger.error(f"Error evaluating alert condition for {alert.id}: {e}")
            return False

    def _get_current_value(self, alert: Alert, market_data: dict[str, Any]) -> float:
        """Get the current value for the alert condition"""
        if alert.condition_type in ["price_above", "price_below"]:
            return market_data.get("price", 0.0)
        elif alert.condition_type == "volume_spike":
            return market_data.get("volume", 0)
        elif alert.condition_type == "change_percent_above":
            return market_data.get("change_percent", 0.0)
        return 0.0

    async def _broadcast_alert_triggered(self, alert: Alert):
        """Broadcast alert triggered notification"""
        try:
            message = {
                "type": "alert_triggered",
                "data": {
                    "id": alert.id,
                    "symbol": alert.symbol,
                    "condition_type": alert.condition_type,
                    "threshold": alert.threshold,
                    "current_value": alert.current_value,
                    "message": alert.message
                    or f"{alert.symbol} {alert.condition_type} {alert.threshold}",
                    "triggered_at": alert.triggered_at,
                    "created_at": alert.created_at,
                },
                "timestamp": time.time(),
            }

            # Broadcast to all alert connections
            await connection_manager.broadcast_to_type(message, "alerts")

            logger.info(
                f"Alert triggered: {alert.symbol} {alert.condition_type} {alert.threshold} (current: {alert.current_value})"
            )

        except Exception as e:
            logger.error(f"Error broadcasting alert {alert.id}: {e}")

    def get_active_alerts(self) -> list[dict[str, Any]]:
        """Get all active (non-triggered) alerts"""
        return [
            {
                "id": alert.id,
                "symbol": alert.symbol,
                "condition_type": alert.condition_type,
                "threshold": alert.threshold,
                "current_value": alert.current_value,
                "triggered": alert.triggered,
                "created_at": alert.created_at,
                "message": alert.message,
            }
            for alert in self.alerts.values()
            if not alert.triggered
        ]

    def get_triggered_alerts(self, hours: int = 24) -> list[dict[str, Any]]:
        """Get recently triggered alerts"""
        cutoff_time = time.time() - (hours * 3600)
        return [
            {
                "id": alert.id,
                "symbol": alert.symbol,
                "condition_type": alert.condition_type,
                "threshold": alert.threshold,
                "current_value": alert.current_value,
                "triggered": alert.triggered,
                "triggered_at": alert.triggered_at,
                "created_at": alert.created_at,
                "message": alert.message,
            }
            for alert in self.alerts.values()
            if alert.triggered and alert.triggered_at and alert.triggered_at > cutoff_time
        ]


# Global alert monitor instance
alert_monitor = AlertMonitor()


async def start_alert_monitoring():
    """Start alert monitoring (call during app startup)"""
    await alert_monitor.start_monitoring()


async def stop_alert_monitoring():
    """Stop alert monitoring (call during app shutdown)"""
    await alert_monitor.stop_monitoring()


# Convenience functions for adding common alert types
def create_price_alert(
    symbol: str, price: float, above: bool = True, user_id: str | None = None
) -> Alert:
    """Create a price alert"""
    alert_id = f"{symbol}_{int(time.time())}"
    condition_type = "price_above" if above else "price_below"
    direction = "above" if above else "below"
    message = f"{symbol} price {direction} ${price:.2f}"

    return Alert(
        id=alert_id,
        user_id=user_id,
        symbol=symbol,
        condition_type=condition_type,
        threshold=price,
        message=message,
    )


def create_volume_alert(symbol: str, volume: int, user_id: str | None = None) -> Alert:
    """Create a volume spike alert"""
    alert_id = f"{symbol}_vol_{int(time.time())}"
    message = f"{symbol} volume spike above {volume:,}"

    return Alert(
        id=alert_id,
        user_id=user_id,
        symbol=symbol,
        condition_type="volume_spike",
        threshold=float(volume),
        message=message,
    )
