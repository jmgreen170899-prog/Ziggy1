# backend/app/services/integration_hub.py
"""
Ziggy AI System Integration Hub
Connects learning system, brain intelligence, and market data processing.
"""

import logging
import time
from dataclasses import dataclass
from typing import Any


logger = logging.getLogger(__name__)


@dataclass
class IntegratedDecision:
    """Complete decision with brain intelligence and learning context."""

    # Core decision data
    timestamp: float
    ticker: str
    decision_type: str  # 'signal', 'trade', 'risk_adjustment'

    # Brain intelligence
    market_regime: str
    regime_confidence: float
    brain_features: dict[str, float]
    brain_insights: list[str]

    # Learning context
    active_rules_version: str
    parameters_used: dict[str, Any]
    predicted_probability: float | None
    calibrated_probability: float | None

    # Decision details
    action: str  # 'buy', 'sell', 'hold', 'adjust'
    quantity: float
    confidence: float
    reasoning: list[str]

    # Risk management
    stop_loss: float | None
    take_profit: float | None
    risk_score: float

    def to_learning_record(self) -> dict[str, Any]:
        """Convert to format suitable for learning system."""
        return {
            "timestamp": self.timestamp,
            "ticker": self.ticker,
            "regime": self.market_regime,
            "features_used": self.brain_features,
            "signal_name": self.decision_type,
            "params_used": self.parameters_used,
            "predicted_prob": self.predicted_probability,
            "position_qty": self.quantity if self.action in ["buy", "sell"] else 0,
            "entry_price": 0.0,  # To be filled by execution system
            "stop_price": self.stop_loss,
            "take_profit": self.take_profit,
            "rule_version": self.active_rules_version,
        }


class ZiggyIntegrationHub:
    """
    Central integration hub connecting all Ziggy systems.
    Orchestrates brain intelligence, learning, and decision making.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Import systems with graceful fallbacks
        self._brain_available = False
        self._learning_available = False
        self._calibration_available = False

        self._initialize_systems()

    def _initialize_systems(self):
        """Initialize all integrated systems."""
        # Initialize brain system
        try:
            from .market_brain.simple_data_hub import DataSource, enhance_market_data

            self._enhance_market_data = enhance_market_data
            self._DataSource = DataSource
            self._brain_available = True
            self.logger.info("Brain system integration: ACTIVE")
        except ImportError as e:
            self.logger.warning(f"Brain system integration: OFFLINE ({e})")
            self._enhance_market_data = None
            self._DataSource = None

        # Initialize learning system
        try:
            from .data_log import log_trading_decision, update_trading_outcome
            from .learner import StrictLearner, create_default_rule_set

            self._learner = StrictLearner()
            self._create_default_rules = create_default_rule_set
            self._log_decision = log_trading_decision
            self._update_outcome = update_trading_outcome
            self._learning_available = True
            self.logger.info("Learning system integration: ACTIVE")
        except ImportError as e:
            self.logger.warning(f"Learning system integration: OFFLINE ({e})")
            self._learner = None

        # Initialize calibration system
        try:
            from .calibration import load_and_apply_calibrator

            self._apply_calibration = load_and_apply_calibrator
            self._calibration_available = True
            self.logger.info("Calibration system integration: ACTIVE")
        except ImportError as e:
            self.logger.warning(f"Calibration system integration: OFFLINE ({e})")
            self._apply_calibration = None

    def enhance_with_brain_intelligence(
        self, data: dict[str, Any], source: str, symbols: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Enhance data with brain intelligence.

        Args:
            data: Raw market data
            source: Data source type
            symbols: Optional symbol list for context

        Returns:
            Brain-enhanced data
        """
        if (
            not self._brain_available
            or self._enhance_market_data is None
            or self._DataSource is None
        ):
            return data

        try:
            # Map source string to DataSource enum
            source_mapping = {
                "market_overview": self._DataSource.OVERVIEW,
                "market_breadth": self._DataSource.BREADTH,
                "risk_lite": self._DataSource.RISK_LITE,
                "market_calendar": self._DataSource.CALENDAR,
                "news_feeds": self._DataSource.NEWS,
                "crypto_data": self._DataSource.CRYPTO,
                "learning_system": self._DataSource.LEARNING,
                "trading_signals": self._DataSource.SIGNALS,
            }

            data_source = source_mapping.get(source, self._DataSource.OVERVIEW)
            enhanced = self._enhance_market_data(data, data_source, symbols=symbols)

            return enhanced

        except Exception as e:
            self.logger.error(f"Brain enhancement failed: {e}")
            return data

    def get_current_market_context(self) -> dict[str, Any]:
        """Get current market context from brain intelligence."""
        if not self._brain_available:
            return {
                "regime": "unknown",
                "regime_confidence": 0.0,
                "market_stress": 0.5,
                "volatility_regime": "normal",
            }

        try:
            # Get overview data and enhance with brain
            overview_data = {"timestamp": time.time()}
            enhanced = self.enhance_with_brain_intelligence(
                overview_data, "market_overview"
            )

            return {
                "regime": enhanced.get("market_regime", "unknown"),
                "regime_confidence": enhanced.get("regime_confidence", 0.0),
                "market_stress": enhanced.get("market_stress", 0.5),
                "volatility_regime": enhanced.get("volatility_regime", "normal"),
                "brain_insights": enhanced.get("insights", []),
            }

        except Exception as e:
            self.logger.error(f"Failed to get market context: {e}")
            return {
                "regime": "error",
                "regime_confidence": 0.0,
                "market_stress": 0.5,
                "volatility_regime": "unknown",
            }

    def get_active_rules(self) -> dict[str, Any]:
        """Get currently active trading rules."""
        if not self._learning_available:
            # Return default rules
            return {
                "version": "default_v1.0",
                "parameters": {
                    "rsi_oversold": 30.0,
                    "rsi_overbought": 70.0,
                    "atr_stop_multiplier": 2.0,
                    "regime_strength_threshold": 0.6,
                },
            }

        try:
            default_rules = self._create_default_rules()
            return {
                "version": default_rules.version,
                "parameters": {
                    name: param.current_value
                    for name, param in default_rules.parameters.items()
                },
            }
        except Exception as e:
            self.logger.error(f"Failed to get active rules: {e}")
            return {"version": "error", "parameters": {}}

    def apply_probability_calibration(
        self, raw_probabilities: list[float]
    ) -> list[float]:
        """Apply learned probability calibration."""
        if not self._calibration_available or self._apply_calibration is None:
            return raw_probabilities

        try:
            import numpy as np

            probs_array = np.array(raw_probabilities)
            calibrated = self._apply_calibration(probs_array)
            return calibrated.tolist()
        except Exception as e:
            self.logger.error(f"Calibration failed: {e}")
            return raw_probabilities

    def make_integrated_decision(
        self,
        ticker: str,
        market_data: dict[str, Any],
        signal_data: dict[str, Any],
        decision_type: str = "signal",
    ) -> IntegratedDecision:
        """
        Make a complete integrated decision using all systems.

        Args:
            ticker: Symbol being analyzed
            market_data: Current market data
            signal_data: Signal generation data
            decision_type: Type of decision being made

        Returns:
            Complete integrated decision
        """
        timestamp = time.time()

        # Get market context from brain
        market_context = self.get_current_market_context()

        # Get active rules from learning system
        active_rules = self.get_active_rules()

        # Extract brain features
        brain_features = {
            "rsi": signal_data.get("rsi", 50.0),
            "atr": signal_data.get("atr", 1.0),
            "volume_ratio": signal_data.get("volume_ratio", 1.0),
            "price_momentum": signal_data.get("price_momentum", 0.0),
            "regime_strength": market_context.get("regime_confidence", 0.5),
        }

        # Calculate raw probability
        raw_probability = self._calculate_signal_probability(
            signal_data, active_rules["parameters"]
        )

        # Apply calibration
        calibrated_prob = None
        if raw_probability is not None:
            calibrated_probs = self.apply_probability_calibration([raw_probability])
            calibrated_prob = (
                calibrated_probs[0] if calibrated_probs else raw_probability
            )

        # Determine action based on calibrated probability and rules
        action, quantity, confidence, reasoning = self._determine_action(
            ticker,
            calibrated_prob or raw_probability,
            brain_features,
            active_rules["parameters"],
        )

        # Calculate risk management levels
        stop_loss, take_profit, risk_score = self._calculate_risk_levels(
            market_data, brain_features, active_rules["parameters"]
        )

        decision = IntegratedDecision(
            timestamp=timestamp,
            ticker=ticker,
            decision_type=decision_type,
            market_regime=market_context["regime"],
            regime_confidence=market_context["regime_confidence"],
            brain_features=brain_features,
            brain_insights=market_context.get("brain_insights", []),
            active_rules_version=active_rules["version"],
            parameters_used=active_rules["parameters"],
            predicted_probability=raw_probability,
            calibrated_probability=calibrated_prob,
            action=action,
            quantity=quantity,
            confidence=confidence,
            reasoning=reasoning,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_score=risk_score,
        )

        # Log decision for learning
        if self._learning_available and action in ["buy", "sell"]:
            try:
                learning_record = decision.to_learning_record()
                decision_timestamp = self._log_decision(**learning_record)
                decision.brain_insights.append(
                    f"Logged for learning: {decision_timestamp}"
                )
            except Exception as e:
                self.logger.error(f"Failed to log decision for learning: {e}")

        return decision

    def _calculate_signal_probability(
        self, signal_data: dict[str, Any], parameters: dict[str, Any]
    ) -> float | None:
        """Calculate signal probability based on current data and rules."""
        try:
            rsi = signal_data.get("rsi", 50.0)

            rsi_oversold = parameters.get("rsi_oversold", 30.0)
            rsi_overbought = parameters.get("rsi_overbought", 70.0)

            # Simple probability calculation
            if rsi < rsi_oversold:
                probability = 0.7  # Bullish probability when oversold
            elif rsi > rsi_overbought:
                probability = 0.3  # Bearish probability when overbought
            else:
                # Neutral zone
                probability = 0.5

            # Adjust based on regime strength
            regime_strength = signal_data.get("regime_strength", 0.5)
            probability = probability * regime_strength + 0.5 * (1 - regime_strength)

            return max(0.1, min(0.9, probability))  # Clamp to reasonable range

        except Exception as e:
            self.logger.error(f"Failed to calculate signal probability: {e}")
            return None

    def _determine_action(
        self,
        ticker: str,
        probability: float | None,
        features: dict[str, Any],
        parameters: dict[str, Any],
    ) -> tuple[str, float, float, list[str]]:
        """Determine trading action based on probability and rules."""
        if probability is None:
            return "hold", 0.0, 0.0, ["Insufficient data for decision"]

        reasoning = []

        # Base position size (could be made configurable)
        base_quantity = 100.0

        if probability > 0.65:
            action = "buy"
            quantity = base_quantity * (probability - 0.5) * 2  # Scale with confidence
            confidence = probability
            reasoning.append(f"Strong bullish signal (p={probability:.3f})")
        elif probability < 0.35:
            action = "sell"
            quantity = base_quantity * (0.5 - probability) * 2  # Scale with confidence
            confidence = 1.0 - probability
            reasoning.append(f"Strong bearish signal (p={probability:.3f})")
        else:
            action = "hold"
            quantity = 0.0
            confidence = 0.5
            reasoning.append(f"Neutral signal (p={probability:.3f})")

        # Adjust for regime
        regime_strength = features.get("regime_strength", 0.5)
        if regime_strength < 0.3:
            quantity *= 0.5  # Reduce size in uncertain regimes
            reasoning.append("Reduced size due to regime uncertainty")

        return action, quantity, confidence, reasoning

    def _calculate_risk_levels(
        self,
        market_data: dict[str, Any],
        features: dict[str, Any],
        parameters: dict[str, Any],
    ) -> tuple[float | None, float | None, float]:
        """Calculate stop loss, take profit, and risk score."""
        try:
            current_price = market_data.get("price", 100.0)
            atr = features.get("atr", 1.0)
            atr_multiplier = parameters.get("atr_stop_multiplier", 2.0)

            # ATR-based stop loss
            stop_distance = atr * atr_multiplier
            stop_loss = current_price - stop_distance

            # Take profit at 2x stop distance
            take_profit = current_price + (stop_distance * 2)

            # Risk score based on volatility and regime uncertainty
            volatility_risk = min(atr / current_price * 100, 1.0)  # Normalize to 0-1
            regime_risk = 1.0 - features.get("regime_strength", 0.5)
            risk_score = (volatility_risk + regime_risk) / 2

            return stop_loss, take_profit, risk_score

        except Exception as e:
            self.logger.error(f"Failed to calculate risk levels: {e}")
            return None, None, 0.5

    def update_decision_outcome(
        self,
        decision: IntegratedDecision,
        exit_price: float,
        realized_pnl: float,
        fees: float = 0.0,
        exit_reason: str = "unknown",
    ):
        """Update decision outcome for learning."""
        if not self._learning_available:
            return

        try:
            self._update_outcome(
                decision_timestamp=decision.timestamp,
                ticker=decision.ticker,
                exit_price=exit_price,
                realized_pnl=realized_pnl,
                fees_paid=fees,
                exit_reason=exit_reason,
            )
            self.logger.info(f"Updated outcome for decision {decision.timestamp}")
        except Exception as e:
            self.logger.error(f"Failed to update decision outcome: {e}")

    def get_system_health(self) -> dict[str, Any]:
        """Get integrated system health status."""
        health = {
            "timestamp": time.time(),
            "overall_status": "healthy",
            "components": {
                "brain_intelligence": {
                    "status": "active" if self._brain_available else "offline",
                    "available": self._brain_available,
                },
                "learning_system": {
                    "status": "active" if self._learning_available else "offline",
                    "available": self._learning_available,
                },
                "calibration_system": {
                    "status": "active" if self._calibration_available else "offline",
                    "available": self._calibration_available,
                },
            },
            "integration_score": 0,
        }

        # Calculate integration score
        active_systems = sum(
            [
                self._brain_available,
                self._learning_available,
                self._calibration_available,
            ]
        )
        health["integration_score"] = (active_systems / 3.0) * 100

        if health["integration_score"] < 50:
            health["overall_status"] = "degraded"
        elif health["integration_score"] < 80:
            health["overall_status"] = "partial"

        return health


# Global integration hub instance
_integration_hub: ZiggyIntegrationHub | None = None


def get_integration_hub() -> ZiggyIntegrationHub:
    """Get the global integration hub instance."""
    global _integration_hub
    if _integration_hub is None:
        _integration_hub = ZiggyIntegrationHub()
    return _integration_hub


# Convenience functions for easy integration
def make_intelligent_decision(
    ticker: str, market_data: dict[str, Any], signal_data: dict[str, Any]
) -> IntegratedDecision:
    """Make an intelligent trading decision using all integrated systems."""
    hub = get_integration_hub()
    return hub.make_integrated_decision(ticker, market_data, signal_data)


def enhance_data_with_intelligence(
    data: dict[str, Any], source: str, symbols: list[str] | None = None
) -> dict[str, Any]:
    """Enhance any data with brain intelligence."""
    hub = get_integration_hub()
    return hub.enhance_with_brain_intelligence(data, source, symbols)


def get_integrated_system_health() -> dict[str, Any]:
    """Get health status of all integrated systems."""
    hub = get_integration_hub()
    return hub.get_system_health()


if __name__ == "__main__":
    # Example usage
    hub = ZiggyIntegrationHub()

    # Test market context
    context = hub.get_current_market_context()
    print(f"Market context: {context}")

    # Test decision making
    decision = hub.make_integrated_decision(
        ticker="AAPL",
        market_data={"price": 150.0, "volume": 1000000},
        signal_data={"rsi": 25.0, "atr": 2.5, "volume_ratio": 1.2},
    )
    print(
        f"Decision: {decision.action} {decision.quantity} shares (confidence: {decision.confidence:.3f})"
    )

    # Test system health
    health = hub.get_system_health()
    print(
        f"System health: {health['overall_status']} (score: {health['integration_score']:.1f}%)"
    )
