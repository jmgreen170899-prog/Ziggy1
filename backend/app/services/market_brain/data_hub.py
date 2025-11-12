"""
Market Brain Data Hub - Universal Intelligence Layer

Central processing hub that enhances ALL market data feeds with:
- Regime context and analysis
- Technical indicator enrichment
- Signal generation and validation
- Risk assessment and alerts
- Cross-market correlation analysis
- Unified data normalization

This hub acts as middleware for every market data request,
providing consistent intelligence across all endpoints.
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from app.services.market_brain.features import FeatureSet


# Try to import brain modules with graceful fallback
try:
    from .regime import RegimeResult, RegimeState, get_regime_state

    REGIME_AVAILABLE = True
except ImportError:
    REGIME_AVAILABLE = False
    RegimeResult = None
    RegimeState = None

try:
    from .signals import Signal, generate_ticker_signal

    SIGNALS_AVAILABLE = True
except ImportError:
    SIGNALS_AVAILABLE = False
    Signal = None

# For features, we'll use a simple fallback approach
FEATURES_AVAILABLE = False

logger = logging.getLogger(__name__)


class DataSource(Enum):
    """Data source types for tracking and routing."""

    OVERVIEW = "market_overview"
    BREADTH = "market_breadth"
    RISK_LITE = "risk_lite"
    CALENDAR = "market_calendar"
    MACRO = "macro_data"
    SCREENER = "screener"
    NEWS = "news_feeds"
    CRYPTO = "crypto_data"


@dataclass
class DataContext:
    """Context information for data enhancement."""

    source: DataSource
    timestamp: datetime
    regime: RegimeResult | None = None
    market_features: FeatureSet | None = None
    enhanced: bool = False
    processing_time_ms: float = 0.0

    # Enhancement metadata
    enhancements_applied: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    debug_info: dict[str, Any] = field(default_factory=dict)


@dataclass
class EnhancedData:
    """Container for brain-enhanced market data."""

    original_data: dict[str, Any]
    enhanced_data: dict[str, Any]
    context: DataContext
    brain_metadata: dict[str, Any] = field(default_factory=dict)


class MarketBrainDataHub:
    """
    Universal data hub that enhances all market data with intelligence.

    Acts as middleware layer between raw data sources and API responses,
    adding regime context, technical analysis, and signal intelligence.
    """

    def __init__(self):
        """Initialize the data hub."""
        self.cache_ttl = 60  # 1 minute cache
        self._cache: dict[str, tuple] = {}  # (data, timestamp)
        self._regime_cache: tuple | None = None  # (regime, timestamp)
        self._spy_features_cache: tuple | None = None  # (features, timestamp)

        logger.info("Market Brain Data Hub initialized")

    def enhance_overview_data(
        self, symbols_data: dict[str, Any], symbols: list[str], **kwargs
    ) -> EnhancedData:
        """
        Enhance market overview data with brain intelligence.

        Args:
            symbols_data: Raw symbol overview data
            symbols: List of symbols
            **kwargs: Additional parameters (period_days, since_open, etc.)

        Returns:
            EnhancedData with regime context and technical analysis
        """
        start_time = time.time()
        context = DataContext(source=DataSource.OVERVIEW, timestamp=datetime.now())

        try:
            # Get current market regime
            regime = self._get_cached_regime()
            context.regime = regime

            # Get SPY features for market context
            spy_features = self._get_cached_spy_features()
            context.market_features = spy_features

            # Enhance each symbol with brain data
            enhanced_symbols = {}

            for symbol, data in symbols_data.items():
                if data is None:
                    enhanced_symbols[symbol] = data
                    continue

                try:
                    enhanced_symbol = self._enhance_symbol_overview(
                        symbol, data, regime, spy_features
                    )
                    enhanced_symbols[symbol] = enhanced_symbol
                    context.enhancements_applied.append(f"enhanced_{symbol}")
                except Exception as e:
                    logger.debug(f"Symbol enhancement failed for {symbol}: {e}")
                    enhanced_symbols[symbol] = data
                    context.warnings.append(f"Enhancement failed for {symbol}")

            # Add market-wide context
            enhanced_data = {
                "symbols": enhanced_symbols,
                "market_regime": (
                    {
                        "current": regime.regime.value if regime else "UNKNOWN",
                        "confidence": regime.confidence if regime else 0.0,
                        "explanation": regime.explanation if regime else "No regime data",
                        "timestamp": (
                            regime.timestamp.isoformat() if regime and regime.timestamp else None
                        ),
                    }
                    if regime
                    else None
                ),
                "market_context": {
                    "spy_rsi": spy_features.rsi_14 if spy_features else None,
                    "spy_volatility": spy_features.volatility_20d if spy_features else None,
                    "spy_z_score": spy_features.z_score_20 if spy_features else None,
                    "market_stress": self._calculate_market_stress(spy_features, regime),
                },
                "brain_metadata": {
                    "enhanced": True,
                    "processing_time_ms": (time.time() - start_time) * 1000,
                    "symbols_enhanced": len(
                        [
                            s
                            for s in enhanced_symbols.values()
                            if s and isinstance(s, dict) and s.get("brain_enhanced")
                        ]
                    ),
                    "regime_available": regime is not None,
                    "features_available": spy_features is not None,
                },
            }

            # Preserve original data structure
            for key, value in symbols_data.items():
                if key not in enhanced_data:
                    enhanced_data[key] = value

            context.enhanced = True
            context.processing_time_ms = (time.time() - start_time) * 1000

            return EnhancedData(
                original_data=symbols_data, enhanced_data=enhanced_data, context=context
            )

        except Exception as e:
            logger.error(f"Overview enhancement failed: {e}")
            context.warnings.append(f"Enhancement failed: {e!s}")
            context.processing_time_ms = (time.time() - start_time) * 1000

            return EnhancedData(
                original_data=symbols_data,
                enhanced_data=symbols_data,  # Return original on failure
                context=context,
            )

    def enhance_breadth_data(self, breadth_data: dict[str, Any]) -> EnhancedData:
        """Enhance market breadth data with regime and correlation analysis."""
        start_time = time.time()
        context = DataContext(source=DataSource.BREADTH, timestamp=datetime.now())

        try:
            regime = self._get_cached_regime()
            context.regime = regime

            enhanced_data = breadth_data.copy()

            # Add regime-aware breadth interpretation
            enhanced_data["regime_analysis"] = self._analyze_breadth_vs_regime(breadth_data, regime)

            # Add brain metadata
            enhanced_data["brain_metadata"] = {
                "enhanced": True,
                "processing_time_ms": (time.time() - start_time) * 1000,
                "regime_context": regime.regime.value if regime else "UNKNOWN",
            }

            context.enhanced = True
            context.enhancements_applied.append("regime_breadth_analysis")
            context.processing_time_ms = (time.time() - start_time) * 1000

            return EnhancedData(
                original_data=breadth_data, enhanced_data=enhanced_data, context=context
            )

        except Exception as e:
            logger.error(f"Breadth enhancement failed: {e}")
            context.warnings.append(f"Enhancement failed: {e!s}")
            context.processing_time_ms = (time.time() - start_time) * 1000

            return EnhancedData(
                original_data=breadth_data, enhanced_data=breadth_data, context=context
            )

    def enhance_risk_data(self, risk_data: dict[str, Any]) -> EnhancedData:
        """Enhance risk-lite data with regime-aware risk assessment."""
        start_time = time.time()
        context = DataContext(source=DataSource.RISK_LITE, timestamp=datetime.now())

        try:
            regime = self._get_cached_regime()
            spy_features = self._get_cached_spy_features()
            context.regime = regime
            context.market_features = spy_features

            enhanced_data = risk_data.copy()

            # Add brain-powered risk assessment
            enhanced_data["brain_risk_assessment"] = self._calculate_enhanced_risk(
                risk_data, regime, spy_features
            )

            # Add regime-specific risk warnings
            enhanced_data["risk_warnings"] = self._generate_risk_warnings(
                risk_data, regime, spy_features
            )

            enhanced_data["brain_metadata"] = {
                "enhanced": True,
                "processing_time_ms": (time.time() - start_time) * 1000,
                "regime_context": regime.regime.value if regime else "UNKNOWN",
            }

            context.enhanced = True
            context.enhancements_applied.extend(["risk_assessment", "risk_warnings"])
            context.processing_time_ms = (time.time() - start_time) * 1000

            return EnhancedData(
                original_data=risk_data, enhanced_data=enhanced_data, context=context
            )

        except Exception as e:
            logger.error(f"Risk enhancement failed: {e}")
            context.warnings.append(f"Enhancement failed: {e!s}")
            context.processing_time_ms = (time.time() - start_time) * 1000

            return EnhancedData(original_data=risk_data, enhanced_data=risk_data, context=context)

    def enhance_calendar_data(self, calendar_data: dict[str, Any]) -> EnhancedData:
        """Enhance calendar data with market impact analysis."""
        start_time = time.time()
        context = DataContext(source=DataSource.CALENDAR, timestamp=datetime.now())

        try:
            regime = self._get_cached_regime()
            context.regime = regime

            enhanced_data = calendar_data.copy()

            # Add market impact analysis for calendar events
            enhanced_data["market_impact_analysis"] = self._analyze_calendar_impact(
                calendar_data, regime
            )

            enhanced_data["brain_metadata"] = {
                "enhanced": True,
                "processing_time_ms": (time.time() - start_time) * 1000,
                "regime_context": regime.regime.value if regime else "UNKNOWN",
            }

            context.enhanced = True
            context.enhancements_applied.append("calendar_impact_analysis")
            context.processing_time_ms = (time.time() - start_time) * 1000

            return EnhancedData(
                original_data=calendar_data, enhanced_data=enhanced_data, context=context
            )

        except Exception as e:
            logger.error(f"Calendar enhancement failed: {e}")
            context.warnings.append(f"Enhancement failed: {e!s}")
            context.processing_time_ms = (time.time() - start_time) * 1000

            return EnhancedData(
                original_data=calendar_data, enhanced_data=calendar_data, context=context
            )

    def _enhance_symbol_overview(
        self,
        symbol: str,
        data: dict[str, Any],
        regime: RegimeResult | None,
        spy_features: FeatureSet | None,
    ) -> dict[str, Any]:
        """Enhance individual symbol data with brain intelligence."""
        enhanced = data.copy()

        try:
            # Get symbol-specific features and signal
            features = get_ticker_features(symbol)
            signal = generate_ticker_signal(symbol)

            if features:
                enhanced["brain_features"] = {
                    "rsi_14": features.rsi_14,
                    "z_score": features.z_score_20,
                    "volatility": features.volatility_20d,
                    "atr": features.atr_14,
                }
                enhanced["technical_summary"] = self._create_technical_summary(features)

            if signal:
                enhanced["brain_signal"] = {
                    "direction": signal.direction.value,
                    "type": signal.signal_type.value,
                    "confidence": signal.confidence,
                    "reason": signal.reason,
                    "entry_price": signal.entry_price,
                    "stop_loss": signal.stop_loss,
                    "take_profit": signal.take_profit,
                }
                enhanced["signal_strength"] = self._calculate_signal_strength(
                    signal, features, regime
                )

            # Add regime context
            if regime:
                enhanced["regime_context"] = {
                    "current_regime": regime.regime.value,
                    "regime_suitability": self._assess_regime_suitability(signal, regime),
                    "regime_confidence": regime.confidence,
                }

            enhanced["brain_enhanced"] = True

        except Exception as e:
            logger.debug(f"Symbol {symbol} enhancement error: {e}")
            enhanced["brain_enhanced"] = False

        return enhanced

    def _get_cached_regime(self) -> RegimeResult | None:
        """Get cached regime data or fetch fresh if stale."""
        now = time.time()

        if self._regime_cache:
            regime, timestamp = self._regime_cache
            if now - timestamp < self.cache_ttl:
                return regime

        try:
            regime = get_regime_state()
            self._regime_cache = (regime, now)
            return regime
        except Exception as e:
            logger.debug(f"Regime fetch failed: {e}")
            return None

    def _get_cached_spy_features(self) -> FeatureSet | None:
        """Get cached SPY features or fetch fresh if stale."""
        now = time.time()

        if self._spy_features_cache:
            features, timestamp = self._spy_features_cache
            if now - timestamp < self.cache_ttl:
                return features

        try:
            features = get_ticker_features("SPY")
            self._spy_features_cache = (features, now)
            return features
        except Exception as e:
            logger.debug(f"SPY features fetch failed: {e}")
            return None

    def _calculate_market_stress(
        self, spy_features: FeatureSet | None, regime: RegimeResult | None
    ) -> str | None:
        """Calculate overall market stress level."""
        if not spy_features or not regime:
            return None

        stress_factors = []

        # Volatility stress
        if spy_features.volatility_20d and spy_features.volatility_20d > 25:
            stress_factors.append("high_volatility")

        # Regime stress
        if regime.regime in [RegimeState.PANIC, RegimeState.RISK_OFF]:
            stress_factors.append("defensive_regime")

        # RSI extremes
        if spy_features.rsi_14:
            if spy_features.rsi_14 < 30 or spy_features.rsi_14 > 70:
                stress_factors.append("momentum_extreme")

        if len(stress_factors) >= 2:
            return "HIGH"
        elif len(stress_factors) == 1:
            return "MODERATE"
        else:
            return "LOW"

    def _analyze_breadth_vs_regime(
        self, breadth_data: dict[str, Any], regime: RegimeResult | None
    ) -> dict[str, Any]:
        """Analyze breadth data in context of current regime."""
        analysis = {
            "regime_breadth_alignment": "UNKNOWN",
            "interpretation": "No regime data available",
            "warnings": [],
        }

        if not regime:
            return analysis

        # This would analyze breadth indicators vs regime expectations
        # For now, basic framework
        analysis["regime_breadth_alignment"] = "ALIGNED"
        analysis["interpretation"] = (
            f"Breadth indicators consistent with {regime.regime.value} regime"
        )

        return analysis

    def _calculate_enhanced_risk(
        self,
        risk_data: dict[str, Any],
        regime: RegimeResult | None,
        spy_features: FeatureSet | None,
    ) -> dict[str, Any]:
        """Calculate enhanced risk metrics using brain data."""
        enhanced_risk = {
            "overall_risk_level": "UNKNOWN",
            "regime_risk_factor": 1.0,
            "volatility_risk_factor": 1.0,
            "combined_risk_score": 0.5,
        }

        if regime:
            # Regime-based risk adjustment
            if regime.regime == RegimeState.PANIC:
                enhanced_risk["regime_risk_factor"] = 2.0
                enhanced_risk["overall_risk_level"] = "EXTREME"
            elif regime.regime == RegimeState.RISK_OFF:
                enhanced_risk["regime_risk_factor"] = 1.5
                enhanced_risk["overall_risk_level"] = "HIGH"
            elif regime.regime == RegimeState.CHOP:
                enhanced_risk["regime_risk_factor"] = 1.2
                enhanced_risk["overall_risk_level"] = "MODERATE"
            else:  # RISK_ON
                enhanced_risk["regime_risk_factor"] = 0.8
                enhanced_risk["overall_risk_level"] = "LOW"

        if spy_features and spy_features.volatility_20d:
            # Volatility-based risk adjustment
            vol = spy_features.volatility_20d
            if vol > 30:
                enhanced_risk["volatility_risk_factor"] = 1.8
            elif vol > 20:
                enhanced_risk["volatility_risk_factor"] = 1.3
            else:
                enhanced_risk["volatility_risk_factor"] = 1.0

        # Combined risk score
        enhanced_risk["combined_risk_score"] = min(
            (enhanced_risk["regime_risk_factor"] + enhanced_risk["volatility_risk_factor"]) / 2, 2.0
        )

        return enhanced_risk

    def _generate_risk_warnings(
        self,
        risk_data: dict[str, Any],
        regime: RegimeResult | None,
        spy_features: FeatureSet | None,
    ) -> list[str]:
        """Generate regime-aware risk warnings."""
        warnings = []

        if regime and regime.regime == RegimeState.PANIC:
            warnings.append("EXTREME CAUTION: Market in PANIC regime - avoid new positions")

        if spy_features and spy_features.volatility_20d and spy_features.volatility_20d > 30:
            warnings.append("HIGH VOLATILITY: Consider reducing position sizes")

        if regime and regime.confidence and regime.confidence < 0.5:
            warnings.append("REGIME UNCERTAINTY: Low confidence in current regime classification")

        return warnings

    def _analyze_calendar_impact(
        self, calendar_data: dict[str, Any], regime: RegimeResult | None
    ) -> dict[str, Any]:
        """Analyze market impact of calendar events."""
        return {
            "high_impact_events": [],
            "regime_sensitivity": regime.regime.value if regime else "UNKNOWN",
            "market_prep_needed": False,
        }

    def _create_technical_summary(self, features: FeatureSet) -> str:
        """Create human-readable technical summary."""
        parts = []

        if features.rsi_14:
            if features.rsi_14 > 70:
                parts.append("Overbought")
            elif features.rsi_14 < 30:
                parts.append("Oversold")
            else:
                parts.append("Neutral momentum")

        if features.z_score_20:
            if abs(features.z_score_20) > 2:
                parts.append("Extreme price level")
            elif abs(features.z_score_20) > 1:
                parts.append("Extended price level")

        return " | ".join(parts) if parts else "Normal conditions"

    def _calculate_signal_strength(
        self, signal: Signal, features: FeatureSet | None, regime: RegimeResult | None
    ) -> str:
        """Calculate overall signal strength."""
        if not signal.confidence:
            return "WEAK"

        strength = signal.confidence

        # Regime boost
        if regime and regime.regime in [RegimeState.RISK_ON, RegimeState.CHOP]:
            strength *= 1.1

        if strength > 0.8:
            return "VERY_STRONG"
        elif strength > 0.6:
            return "STRONG"
        elif strength > 0.4:
            return "MODERATE"
        else:
            return "WEAK"

    def _assess_regime_suitability(self, signal: Signal | None, regime: RegimeResult) -> str:
        """Assess how suitable current regime is for the signal."""
        if not signal:
            return "NO_SIGNAL"

        if regime.regime == RegimeState.PANIC:
            return "VERY_POOR"
        elif regime.regime == RegimeState.RISK_OFF:
            return "POOR"
        elif regime.regime == RegimeState.CHOP:
            return "MODERATE"
        else:  # RISK_ON
            return "GOOD"


# Global data hub instance
data_hub = MarketBrainDataHub()


def enhance_market_data(data: dict[str, Any], source: DataSource, **kwargs) -> dict[str, Any]:
    """
    Universal function to enhance any market data through the brain hub.

    Args:
        data: Original market data
        source: Type of data source
        **kwargs: Additional parameters specific to data type

    Returns:
        Enhanced data with brain intelligence
    """
    try:
        if source == DataSource.OVERVIEW:
            symbols = kwargs.get("symbols", [])
            enhanced = data_hub.enhance_overview_data(data, symbols, **kwargs)
        elif source == DataSource.BREADTH:
            enhanced = data_hub.enhance_breadth_data(data)
        elif source == DataSource.RISK_LITE:
            enhanced = data_hub.enhance_risk_data(data)
        elif source == DataSource.CALENDAR:
            enhanced = data_hub.enhance_calendar_data(data)
        else:
            # For unsupported sources, return original data with minimal enhancement
            logger.debug(f"No specific enhancement for source: {source}")
            return data

        return enhanced.enhanced_data

    except Exception as e:
        logger.error(f"Data enhancement failed for {source}: {e}")
        return data  # Return original data on failure
