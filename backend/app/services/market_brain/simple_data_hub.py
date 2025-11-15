"""
Simple Market Brain Data Hub - Universal Intelligence Layer

This is a simplified version that works without complex dependencies.
Provides brain enhancement for all market data feeds with graceful fallbacks.
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


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
    LEARNING = "learning_system"  # New: Learning system integration
    SIGNALS = "trading_signals"  # New: Trading signals integration


@dataclass
class DataContext:
    """Context information for data enhancement."""

    source: DataSource
    timestamp: datetime
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


class SimpleMarketBrainDataHub:
    """
    Simplified universal data hub that enhances all market data with basic intelligence.

    This version provides core functionality without complex brain module dependencies.
    """

    def __init__(self):
        """Initialize the data hub."""
        self.cache_ttl = 60  # 1 minute cache
        self._cache: dict[str, tuple] = {}  # (data, timestamp)

        logger.info("Simple Market Brain Data Hub initialized")

    def enhance_overview_data(
        self, symbols_data: dict[str, Any], symbols: list[str], **kwargs
    ) -> EnhancedData:
        """
        Enhance market overview data with basic intelligence.
        """
        start_time = time.time()
        context = DataContext(source=DataSource.OVERVIEW, timestamp=datetime.now())

        try:
            # Basic enhancement - add metadata and market analysis
            enhanced_data = {
                "symbols": symbols_data,
                "market_context": {
                    "enhanced_by": "SimpleMarketBrain",
                    "symbols_analyzed": len(symbols),
                    "timestamp": datetime.now().isoformat(),
                },
                "brain_metadata": {
                    "enhanced": True,
                    "processing_time_ms": 0,  # Will be updated below
                    "enhancement_level": "basic",
                    "available_modules": self._get_available_modules(),
                },
            }

            # Add basic market regime simulation (placeholder)
            enhanced_data["market_regime"] = {
                "current": "NORMAL",  # Placeholder regime
                "confidence": 0.5,
                "explanation": "Basic market analysis - no advanced regime detection available",
                "timestamp": datetime.now().isoformat(),
            }

            # Preserve any original data structure
            for key, value in kwargs.items():
                if key not in enhanced_data:
                    enhanced_data[key] = value

            context.enhanced = True
            context.enhancements_applied.append("basic_overview_enhancement")
            context.processing_time_ms = (time.time() - start_time) * 1000

            # Update metadata with actual processing time
            enhanced_data["brain_metadata"][
                "processing_time_ms"
            ] = context.processing_time_ms

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
        """Enhance market breadth data with basic analysis."""
        start_time = time.time()
        context = DataContext(source=DataSource.BREADTH, timestamp=datetime.now())

        try:
            enhanced_data = breadth_data.copy()

            # Add basic breadth analysis
            enhanced_data["brain_analysis"] = {
                "market_health": self._analyze_breadth_health(breadth_data),
                "breadth_score": self._calculate_breadth_score(breadth_data),
            }

            enhanced_data["brain_metadata"] = {
                "enhanced": True,
                "processing_time_ms": (time.time() - start_time) * 1000,
                "enhancement_type": "breadth_analysis",
            }

            context.enhanced = True
            context.enhancements_applied.append("basic_breadth_analysis")
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
        """Enhance risk data with basic assessment."""
        start_time = time.time()
        context = DataContext(source=DataSource.RISK_LITE, timestamp=datetime.now())

        try:
            enhanced_data = risk_data.copy()

            # Add basic risk assessment
            enhanced_data["brain_risk_assessment"] = {
                "risk_level": self._assess_risk_level(risk_data),
                "risk_warnings": self._generate_basic_risk_warnings(risk_data),
            }

            enhanced_data["brain_metadata"] = {
                "enhanced": True,
                "processing_time_ms": (time.time() - start_time) * 1000,
                "enhancement_type": "risk_assessment",
            }

            context.enhanced = True
            context.enhancements_applied.append("basic_risk_assessment")
            context.processing_time_ms = (time.time() - start_time) * 1000

            return EnhancedData(
                original_data=risk_data, enhanced_data=enhanced_data, context=context
            )

        except Exception as e:
            logger.error(f"Risk enhancement failed: {e}")
            context.warnings.append(f"Enhancement failed: {e!s}")
            context.processing_time_ms = (time.time() - start_time) * 1000

            return EnhancedData(
                original_data=risk_data, enhanced_data=risk_data, context=context
            )

    def enhance_calendar_data(self, calendar_data: dict[str, Any]) -> EnhancedData:
        """Enhance calendar data with basic impact analysis."""
        start_time = time.time()
        context = DataContext(source=DataSource.CALENDAR, timestamp=datetime.now())

        try:
            enhanced_data = calendar_data.copy()

            # Add basic market impact analysis
            enhanced_data["brain_impact_analysis"] = {
                "high_impact_events": self._identify_high_impact_events(calendar_data),
                "market_preparation_needed": False,  # Basic placeholder
            }

            enhanced_data["brain_metadata"] = {
                "enhanced": True,
                "processing_time_ms": (time.time() - start_time) * 1000,
                "enhancement_type": "calendar_analysis",
            }

            context.enhanced = True
            context.enhancements_applied.append("basic_calendar_analysis")
            context.processing_time_ms = (time.time() - start_time) * 1000

            return EnhancedData(
                original_data=calendar_data,
                enhanced_data=enhanced_data,
                context=context,
            )

        except Exception as e:
            logger.error(f"Calendar enhancement failed: {e}")
            context.warnings.append(f"Enhancement failed: {e!s}")
            context.processing_time_ms = (time.time() - start_time) * 1000

            return EnhancedData(
                original_data=calendar_data,
                enhanced_data=calendar_data,
                context=context,
            )

    def _get_available_modules(self) -> list[str]:
        """Get list of available brain modules."""
        modules = ["basic_enhancement"]

        # Test for advanced modules
        try:
            from . import regime

            modules.append("regime_detection")
        except ImportError:
            pass

        try:
            from . import signals

            modules.append("signal_generation")
        except ImportError:
            pass

        try:
            from . import features

            modules.append("feature_computation")
        except ImportError:
            pass

        return modules

    def _analyze_breadth_health(self, breadth_data: dict[str, Any]) -> str:
        """Analyze overall market breadth health."""
        try:
            ad_data = breadth_data.get("ad", {})
            adv = ad_data.get("adv", 0)
            dec = ad_data.get("dec", 0)

            if adv + dec == 0:
                return "UNKNOWN"

            ratio = adv / (adv + dec)

            if ratio > 0.7:
                return "STRONG"
            elif ratio > 0.55:
                return "HEALTHY"
            elif ratio > 0.45:
                return "NEUTRAL"
            elif ratio > 0.3:
                return "WEAK"
            else:
                return "POOR"

        except Exception:
            return "UNKNOWN"

    def _calculate_breadth_score(self, breadth_data: dict[str, Any]) -> float | None:
        """Calculate a simple breadth score."""
        try:
            ad_data = breadth_data.get("ad", {})
            adv = ad_data.get("adv", 0)
            dec = ad_data.get("dec", 0)

            if adv + dec == 0:
                return None

            return adv / (adv + dec)

        except Exception:
            return None

    def _assess_risk_level(self, risk_data: dict[str, Any]) -> str:
        """Assess basic risk level from CPC/CPCE data."""
        try:
            cpc_data = risk_data.get("cpc", {})
            z_score = cpc_data.get("z20", 0)

            if abs(z_score) > 2:
                return "EXTREME"
            elif abs(z_score) > 1.5:
                return "HIGH"
            elif abs(z_score) > 1:
                return "MODERATE"
            else:
                return "LOW"

        except Exception:
            return "UNKNOWN"

    def _generate_basic_risk_warnings(self, risk_data: dict[str, Any]) -> list[str]:
        """Generate basic risk warnings."""
        warnings = []

        try:
            cpc_data = risk_data.get("cpc", {})
            z_score = cpc_data.get("z20", 0)

            if z_score > 2:
                warnings.append(
                    "Extremely high put/call ratio - potential oversold condition"
                )
            elif z_score < -2:
                warnings.append(
                    "Extremely low put/call ratio - potential overbought condition"
                )
            elif abs(z_score) > 1.5:
                warnings.append("Elevated put/call ratio - monitor for trend changes")

        except Exception:
            pass

        return warnings

    def _identify_high_impact_events(self, calendar_data: dict[str, Any]) -> list[str]:
        """Identify high-impact events from calendar data."""
        high_impact = []

        try:
            events = calendar_data.get("events", [])

            for event in events[:5]:  # Check first 5 events
                if isinstance(event, dict):
                    event_name = event.get("event", "")
                    if any(
                        keyword in event_name.lower()
                        for keyword in [
                            "cpi",
                            "fomc",
                            "fed",
                            "gdp",
                            "employment",
                            "earnings",
                        ]
                    ):
                        high_impact.append(event_name)

        except Exception:
            pass

        return high_impact


# Global data hub instance
simple_data_hub = SimpleMarketBrainDataHub()


def enhance_market_data(
    data: dict[str, Any], source: DataSource, **kwargs
) -> dict[str, Any]:
    """
    Universal function to enhance any market data through the simple brain hub.

    Args:
        data: Original market data
        source: Type of data source
        **kwargs: Additional parameters specific to data type

    Returns:
        Enhanced data with brain intelligence
    """
    try:
        if source == DataSource.OVERVIEW:
            # Handle both data formats - direct symbols dict or nested structure
            symbols_data = data.get("symbols", data) if "symbols" in data else data
            symbols = kwargs.get("symbols", list(symbols_data.keys()))
            enhanced = simple_data_hub.enhance_overview_data(symbols_data, symbols)
        elif source == DataSource.BREADTH:
            enhanced = simple_data_hub.enhance_breadth_data(data)
        elif source == DataSource.RISK_LITE:
            enhanced = simple_data_hub.enhance_risk_data(data)
        elif source == DataSource.CALENDAR:
            enhanced = simple_data_hub.enhance_calendar_data(data)
        else:
            # For unsupported sources, return original data with minimal enhancement
            logger.debug(f"No specific enhancement for source: {source}")
            return data

        return enhanced.enhanced_data

    except Exception as e:
        logger.error(f"Data enhancement failed for {source}: {e}")
        return data  # Return original data on failure
