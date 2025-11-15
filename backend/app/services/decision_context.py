# backend/app/services/decision_context.py
"""
Enhanced Decision Context System for Ziggy's Brain

Enriches trading decisions with:
1. Historical outcome tracking for confidence calibration
2. Similar past decision recall from memory
3. Dynamic confidence adjustment based on recent performance
4. Regime-specific calibration
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np

from .calibration import ProbabilityCalibrator
from .decision_log import get_decision_logger


logger = logging.getLogger(__name__)


@dataclass
class HistoricalPerformance:
    """Performance metrics for a signal type in a specific regime."""

    signal_type: str
    regime: str
    total_signals: int
    successful_signals: int
    win_rate: float
    avg_confidence: float
    brier_score: float  # Lower is better
    last_updated: datetime


@dataclass
class DecisionContext:
    """
    Enhanced context for a trading decision.
    Includes historical performance and similar past decisions.
    """

    # Current decision info
    ticker: str
    signal_type: str
    regime: str
    raw_confidence: float

    # Historical context
    historical_performance: HistoricalPerformance | None
    calibrated_confidence: float
    confidence_adjustment: float  # How much calibration changed confidence

    # Similar past decisions
    similar_decisions: list[dict[str, Any]]
    similar_decisions_summary: dict[str, Any]

    # Decision quality indicators
    expected_accuracy: float  # Based on historical performance
    reliability_score: float  # How reliable the calibration is (based on sample size)
    lessons_learned: list[str]  # Key insights from similar past decisions


class DecisionContextEnricher:
    """
    Enriches trading decisions with historical context and calibration.

    This system improves decision-making by:
    1. Learning from past outcomes to calibrate confidence scores
    2. Providing context from similar historical decisions
    3. Adjusting confidence based on regime-specific performance
    """

    def __init__(
        self,
        data_dir: str = "./data/decisions",
        calibrators_dir: str = "./data/calibrators",
    ):
        self.data_dir = Path(data_dir)
        self.calibrators_dir = Path(calibrators_dir)
        self.calibrators_dir.mkdir(parents=True, exist_ok=True)

        self.decision_logger = get_decision_logger()

        # Cache for calibrators by (signal_type, regime)
        self._calibrator_cache: dict[tuple[str, str], ProbabilityCalibrator] = {}

        # Performance tracking cache (refreshed periodically)
        self._performance_cache: dict[tuple[str, str], HistoricalPerformance] = {}
        self._cache_last_updated = datetime.now(UTC)
        self._cache_ttl = timedelta(hours=1)

    def enrich_decision(
        self,
        ticker: str,
        signal_type: str,
        regime: str,
        raw_confidence: float,
        features: dict[str, Any] | None = None,
    ) -> DecisionContext:
        """
        Enrich a trading decision with historical context and calibration.

        Args:
            ticker: Stock symbol
            signal_type: Type of signal (e.g., "MeanReversion", "Momentum")
            regime: Current market regime
            raw_confidence: Original confidence score from signal generator
            features: Optional feature dictionary for similarity matching

        Returns:
            DecisionContext with calibrated confidence and historical insights
        """
        try:
            # Refresh performance cache if needed
            self._refresh_cache_if_needed()

            # Get historical performance for this signal type and regime
            historical_perf = self._get_historical_performance(signal_type, regime)

            # Apply calibration
            calibrated_conf = self._apply_calibration(
                signal_type, regime, raw_confidence, historical_perf
            )

            # Find similar past decisions
            similar_decisions = self._find_similar_decisions(
                ticker, signal_type, regime, features, limit=5
            )

            # Summarize similar decisions
            summary = self._summarize_similar_decisions(similar_decisions)

            # Extract lessons learned
            lessons = self._extract_lessons(similar_decisions, historical_perf)

            # Calculate reliability score
            reliability = self._calculate_reliability_score(historical_perf)

            # Calculate expected accuracy
            expected_accuracy = (
                historical_perf.win_rate if historical_perf else raw_confidence
            )

            return DecisionContext(
                ticker=ticker,
                signal_type=signal_type,
                regime=regime,
                raw_confidence=raw_confidence,
                historical_performance=historical_perf,
                calibrated_confidence=calibrated_conf,
                confidence_adjustment=calibrated_conf - raw_confidence,
                similar_decisions=similar_decisions,
                similar_decisions_summary=summary,
                expected_accuracy=expected_accuracy,
                reliability_score=reliability,
                lessons_learned=lessons,
            )

        except Exception as e:
            logger.error(f"Error enriching decision context: {e}")
            # Return basic context on error
            return DecisionContext(
                ticker=ticker,
                signal_type=signal_type,
                regime=regime,
                raw_confidence=raw_confidence,
                historical_performance=None,
                calibrated_confidence=raw_confidence,
                confidence_adjustment=0.0,
                similar_decisions=[],
                similar_decisions_summary={},
                expected_accuracy=raw_confidence,
                reliability_score=0.5,
                lessons_learned=[],
            )

    def _refresh_cache_if_needed(self):
        """Refresh performance cache if TTL expired."""
        now = datetime.now(UTC)
        if now - self._cache_last_updated > self._cache_ttl:
            logger.info("Refreshing decision context performance cache")
            self._performance_cache.clear()
            self._cache_last_updated = now

    def _get_historical_performance(
        self, signal_type: str, regime: str
    ) -> HistoricalPerformance | None:
        """Get historical performance for signal type and regime."""
        cache_key = (signal_type, regime)

        # Check cache
        if cache_key in self._performance_cache:
            return self._performance_cache[cache_key]

        # Query decision log for this signal type and regime
        try:
            # Get decisions from last 90 days
            since = (datetime.now(UTC) - timedelta(days=90)).isoformat()
            result = self.decision_logger.query_events(
                filters={
                    "signal_name": signal_type,
                    "regime": regime,
                    "has_outcome": True,
                },
                since=since,
                limit=1000,
            )

            events = result["items"]

            if len(events) < 10:  # Need minimum sample size
                return None

            # Calculate performance metrics
            total = len(events)
            successful = sum(
                1 for e in events if e.get("outcome", {}).get("hit", False)
            )
            win_rate = successful / total if total > 0 else 0.0

            # Calculate average confidence
            confidences = [
                e.get("confidence", 0.5) for e in events if e.get("confidence")
            ]
            avg_confidence = np.mean(confidences) if confidences else 0.5

            # Calculate Brier score
            brier_score = self._calculate_brier_score(events)

            performance = HistoricalPerformance(
                signal_type=signal_type,
                regime=regime,
                total_signals=total,
                successful_signals=successful,
                win_rate=win_rate,
                avg_confidence=avg_confidence,
                brier_score=brier_score,
                last_updated=datetime.now(UTC),
            )

            # Cache it
            self._performance_cache[cache_key] = performance
            return performance

        except Exception as e:
            logger.error(f"Error getting historical performance: {e}")
            return None

    def _calculate_brier_score(self, events: list[dict[str, Any]]) -> float:
        """Calculate Brier score from events."""
        try:
            scores = []
            for event in events:
                confidence = event.get("confidence")
                hit = event.get("outcome", {}).get("hit", False)
                if confidence is not None:
                    # Brier score: (forecast - outcome)^2
                    scores.append((confidence - (1.0 if hit else 0.0)) ** 2)

            return float(np.mean(scores)) if scores else 1.0
        except Exception:
            return 1.0

    def _apply_calibration(
        self,
        signal_type: str,
        regime: str,
        raw_confidence: float,
        historical_perf: HistoricalPerformance | None,
    ) -> float:
        """Apply calibration to confidence score."""
        # If no historical data, return raw confidence
        if historical_perf is None:
            return raw_confidence

        # Check if we have enough data for calibration
        if historical_perf.total_signals < 30:
            # Use simple adjustment based on win rate
            adjustment = (
                historical_perf.win_rate - historical_perf.avg_confidence
            ) * 0.5
            calibrated = raw_confidence + adjustment
            return np.clip(calibrated, 0.01, 0.99)

        # Try to load or build calibrator
        cache_key = (signal_type, regime)
        if cache_key not in self._calibrator_cache:
            calibrator_path = (
                self.calibrators_dir / f"calibrator_{signal_type}_{regime}.pkl"
            )

            calibrator = ProbabilityCalibrator(method="isotonic", min_samples=30)

            # Try to load existing calibrator
            if calibrator_path.exists() and calibrator.load(str(calibrator_path)):
                self._calibrator_cache[cache_key] = calibrator
            else:
                # Build new calibrator from recent data
                calibrator = self._build_calibrator(signal_type, regime)
                if calibrator:
                    calibrator.save(str(calibrator_path))
                    self._calibrator_cache[cache_key] = calibrator

        # Apply calibration
        calibrator = self._calibrator_cache.get(cache_key)
        if calibrator and calibrator.is_fitted:
            calibrated = calibrator.predict(np.array([raw_confidence]))[0]
            return np.clip(calibrated, 0.01, 0.99)
        else:
            # Fallback to simple adjustment
            adjustment = (
                historical_perf.win_rate - historical_perf.avg_confidence
            ) * 0.5
            calibrated = raw_confidence + adjustment
            return np.clip(calibrated, 0.01, 0.99)

    def _build_calibrator(
        self, signal_type: str, regime: str
    ) -> ProbabilityCalibrator | None:
        """Build calibrator from historical data."""
        try:
            # Get historical events
            since = (datetime.now(UTC) - timedelta(days=180)).isoformat()
            result = self.decision_logger.query_events(
                filters={
                    "signal_name": signal_type,
                    "regime": regime,
                    "has_outcome": True,
                },
                since=since,
                limit=2000,
            )

            events = result["items"]
            if len(events) < 30:
                return None

            # Extract probabilities and outcomes
            probabilities = []
            outcomes = []
            for event in events:
                confidence = event.get("confidence")
                hit = event.get("outcome", {}).get("hit", False)
                if confidence is not None:
                    probabilities.append(confidence)
                    outcomes.append(1.0 if hit else 0.0)

            if len(probabilities) < 30:
                return None

            # Fit calibrator
            calibrator = ProbabilityCalibrator(method="isotonic", min_samples=30)
            probs_array = np.array(probabilities)
            outcomes_array = np.array(outcomes)

            if calibrator.fit(probs_array, outcomes_array):
                logger.info(
                    f"Built calibrator for {signal_type}/{regime} with {len(probabilities)} samples"
                )
                return calibrator
            else:
                return None

        except Exception as e:
            logger.error(f"Error building calibrator: {e}")
            return None

    def _find_similar_decisions(
        self,
        ticker: str,
        signal_type: str,
        regime: str,
        features: dict[str, Any] | None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Find similar past decisions."""
        try:
            # Query recent decisions with same signal type and regime
            since = (datetime.now(UTC) - timedelta(days=60)).isoformat()
            result = self.decision_logger.query_events(
                filters={
                    "signal_name": signal_type,
                    "regime": regime,
                    "has_outcome": True,
                },
                since=since,
                limit=limit * 2,  # Get more to filter
            )

            events = result["items"]

            # Prioritize same ticker, then by recency
            same_ticker = [e for e in events if e.get("ticker") == ticker]
            other_ticker = [e for e in events if e.get("ticker") != ticker]

            # Combine and limit
            similar = (same_ticker + other_ticker)[:limit]

            return similar

        except Exception as e:
            logger.error(f"Error finding similar decisions: {e}")
            return []

    def _summarize_similar_decisions(
        self, similar_decisions: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Summarize similar past decisions."""
        if not similar_decisions:
            return {}

        try:
            total = len(similar_decisions)
            successful = sum(
                1 for d in similar_decisions if d.get("outcome", {}).get("hit", False)
            )
            win_rate = successful / total if total > 0 else 0.0

            # Average PnL if available
            pnls = [
                d.get("outcome", {}).get("pnl", 0)
                for d in similar_decisions
                if d.get("outcome", {}).get("pnl") is not None
            ]
            avg_pnl = np.mean(pnls) if pnls else None

            return {
                "total_similar": total,
                "win_rate": win_rate,
                "avg_pnl": avg_pnl,
                "time_range": "last 60 days",
            }
        except Exception:
            return {}

    def _extract_lessons(
        self,
        similar_decisions: list[dict[str, Any]],
        historical_perf: HistoricalPerformance | None,
    ) -> list[str]:
        """Extract key lessons from similar decisions."""
        lessons = []

        try:
            if historical_perf:
                # Lesson about overall performance
                if historical_perf.win_rate > 0.65:
                    lessons.append(
                        f"Strong track record: {historical_perf.win_rate:.1%} win rate "
                        f"over {historical_perf.total_signals} signals"
                    )
                elif historical_perf.win_rate < 0.45:
                    lessons.append(
                        f"Caution: Below-average performance ({historical_perf.win_rate:.1%}) "
                        f"in this regime"
                    )

                # Lesson about calibration
                if abs(historical_perf.brier_score - 0.25) < 0.05:
                    lessons.append("Well-calibrated predictions in this regime")
                elif historical_perf.brier_score > 0.3:
                    lessons.append(
                        "Predictions tend to be overconfident - adjusted downward"
                    )

            # Lessons from recent similar decisions
            if similar_decisions:
                summary = self._summarize_similar_decisions(similar_decisions)
                recent_win_rate = summary.get("win_rate", 0)

                if recent_win_rate > 0.70:
                    lessons.append("Recent similar trades performing well")
                elif recent_win_rate < 0.40:
                    lessons.append("Recent similar trades underperforming")

        except Exception as e:
            logger.error(f"Error extracting lessons: {e}")

        return lessons[:3]  # Limit to top 3 lessons

    def _calculate_reliability_score(
        self, historical_perf: HistoricalPerformance | None
    ) -> float:
        """
        Calculate reliability score based on sample size and consistency.

        Returns value between 0 and 1, where 1 is most reliable.
        """
        if historical_perf is None:
            return 0.3  # Low reliability without data

        # Base reliability on sample size
        sample_score = min(historical_perf.total_signals / 100.0, 1.0)

        # Adjust for Brier score (lower is better, perfect is 0)
        # Typical Brier scores range from 0.15 (good) to 0.35 (poor)
        brier_score = max(0.0, 1.0 - (historical_perf.brier_score / 0.35))

        # Combined score
        reliability = 0.6 * sample_score + 0.4 * brier_score

        return np.clip(reliability, 0.0, 1.0)

    def get_performance_summary(self) -> dict[str, Any]:
        """Get summary of all tracked performance."""
        self._refresh_cache_if_needed()

        summary = {
            "total_tracked_combinations": len(self._performance_cache),
            "cache_last_updated": self._cache_last_updated.isoformat(),
            "performance_by_signal": {},
        }

        for (signal_type, regime), perf in self._performance_cache.items():
            if signal_type not in summary["performance_by_signal"]:
                summary["performance_by_signal"][signal_type] = {}

            summary["performance_by_signal"][signal_type][regime] = {
                "win_rate": perf.win_rate,
                "total_signals": perf.total_signals,
                "brier_score": perf.brier_score,
            }

        return summary


# Global instance
_context_enricher: DecisionContextEnricher | None = None


def get_decision_context_enricher() -> DecisionContextEnricher:
    """Get global decision context enricher instance."""
    global _context_enricher
    if _context_enricher is None:
        _context_enricher = DecisionContextEnricher()
    return _context_enricher


def enrich_decision(
    ticker: str,
    signal_type: str,
    regime: str,
    raw_confidence: float,
    features: dict[str, Any] | None = None,
) -> DecisionContext:
    """Convenience function to enrich a decision."""
    enricher = get_decision_context_enricher()
    return enricher.enrich_decision(
        ticker, signal_type, regime, raw_confidence, features
    )
