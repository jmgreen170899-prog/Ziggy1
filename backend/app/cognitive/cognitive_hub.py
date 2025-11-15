"""
Cognitive Hub - Central Integration Point for Advanced Cognitive Systems

Orchestrates all cognitive enhancements:
- Meta-learning for strategy evolution
- Counterfactual reasoning for opportunity learning
- Episodic memory for case-based reasoning
- Integration with existing ZiggyAI brain and learning systems
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from .counterfactual import (
    ActionType,
    CounterfactualEngine,
    Outcome,
    TradingDecision,
)
from .episodic_memory import EpisodicMemory, MarketEpisode
from .meta_learner import MetaLearner


logger = logging.getLogger(__name__)


class CognitiveHub:
    """
    Central hub for all cognitive enhancement systems.

    Provides unified interface to:
    - Meta-learning (learning how to learn)
    - Counterfactual reasoning (learning from alternatives)
    - Episodic memory (case-based reasoning)
    """

    def __init__(
        self,
        data_dir: Path | None = None,
        enable_meta_learning: bool = True,
        enable_counterfactual: bool = True,
        enable_episodic_memory: bool = True,
    ):
        """
        Initialize cognitive hub.

        Args:
            data_dir: Base directory for cognitive data
            enable_meta_learning: Enable meta-learning system
            enable_counterfactual: Enable counterfactual reasoning
            enable_episodic_memory: Enable episodic memory
        """
        self.data_dir = data_dir or Path("data/cognitive")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize subsystems
        self.meta_learner: MetaLearner | None = None
        self.counterfactual_engine: CounterfactualEngine | None = None
        self.episodic_memory: EpisodicMemory | None = None

        if enable_meta_learning:
            self.meta_learner = MetaLearner(
                strategies_dir=self.data_dir / "meta_learning"
            )
            logger.info("Meta-learning system: ACTIVE")

        if enable_counterfactual:
            self.counterfactual_engine = CounterfactualEngine(
                enable_shadow_portfolios=True
            )
            logger.info("Counterfactual reasoning: ACTIVE")

        if enable_episodic_memory:
            self.episodic_memory = EpisodicMemory(
                memory_dir=self.data_dir / "episodic_memory"
            )
            logger.info("Episodic memory: ACTIVE")

        logger.info("CognitiveHub initialized successfully")

    def enhance_decision(
        self,
        ticker: str,
        proposed_action: str,
        market_context: dict[str, Any],
        confidence: float,
    ) -> dict[str, Any]:
        """
        Enhance a trading decision with cognitive intelligence.

        Uses all active cognitive systems to:
        1. Select best learning strategy (meta-learning)
        2. Recall similar past episodes (episodic memory)
        3. Consider alternative actions (counterfactual preview)

        Args:
            ticker: Stock symbol
            proposed_action: Proposed trading action
            market_context: Current market state and features
            confidence: Initial confidence in decision

        Returns:
            Enhanced decision with cognitive insights
        """
        enhanced = {
            "ticker": ticker,
            "proposed_action": proposed_action,
            "original_confidence": confidence,
            "cognitive_insights": [],
        }

        # Get regime from context
        regime = market_context.get("regime", "unknown")

        # Meta-learning: Select best learning strategy for current regime
        if self.meta_learner:
            strategy = self.meta_learner.select_strategy(regime)
            enhanced["meta_learning"] = {
                "selected_strategy": strategy.name,
                "strategy_type": strategy.strategy_type.value,
                "strategy_accuracy": strategy.accuracy,
                "regime_accuracy": strategy.get_regime_accuracy(regime),
            }
            enhanced["cognitive_insights"].append(
                f"Using {strategy.name} strategy (accuracy: {strategy.accuracy:.2%})"
            )

        # Episodic memory: Find similar past situations
        if self.episodic_memory:
            similar_episodes = self.episodic_memory.recall_similar_episodes(
                market_context, k=3
            )

            if similar_episodes:
                # Calculate success rate of similar episodes
                successful = sum(1 for ep in similar_episodes if ep.was_successful)
                success_rate = successful / len(similar_episodes)

                enhanced["episodic_memory"] = {
                    "similar_episodes_found": len(similar_episodes),
                    "historical_success_rate": success_rate,
                    "lessons": [],
                }

                # Get lessons from similar episodes
                lessons = self.episodic_memory.get_lessons_from_similar_episodes(
                    market_context
                )
                enhanced["episodic_memory"]["lessons"] = lessons

                for lesson in lessons[:2]:  # Top 2 lessons
                    enhanced["cognitive_insights"].append(
                        f"Historical lesson: {lesson}"
                    )

                # Adjust confidence based on historical success
                confidence_adjustment = (success_rate - 0.5) * 0.2
                enhanced["confidence_adjustment"] = confidence_adjustment
                enhanced["adjusted_confidence"] = confidence + confidence_adjustment
            else:
                enhanced["episodic_memory"] = {
                    "similar_episodes_found": 0,
                    "note": "Novel situation - no historical precedent",
                }
                enhanced["cognitive_insights"].append(
                    "Warning: Novel market situation with no historical precedent"
                )

        # Add timestamp
        enhanced["timestamp"] = datetime.utcnow().isoformat()

        return enhanced

    def record_decision_outcome(
        self,
        ticker: str,
        action: str,
        entry_price: float,
        quantity: float,
        market_context: dict[str, Any],
        confidence: float,
        reasoning: list[str],
        outcome_pnl: float,
        outcome_pnl_percent: float,
        holding_period_hours: float,
        current_prices: dict[str, float],
    ) -> None:
        """
        Record a completed decision and its outcome across all cognitive systems.

        Args:
            ticker: Stock symbol
            action: Action taken
            entry_price: Entry price
            quantity: Position size
            market_context: Market context at decision time
            confidence: Decision confidence
            reasoning: Decision reasoning
            outcome_pnl: Realized profit/loss
            outcome_pnl_percent: P&L percentage
            holding_period_hours: How long position was held
            current_prices: Current market prices for counterfactual analysis
        """
        timestamp = datetime.utcnow().isoformat()
        regime = market_context.get("regime", "unknown")

        # Create decision object
        try:
            action_type = ActionType[action.upper()]
        except KeyError:
            action_type = ActionType.HOLD

        decision = TradingDecision(
            timestamp=timestamp,
            ticker=ticker,
            action=action_type,
            quantity=quantity,
            entry_price=entry_price,
            market_regime=regime,
            confidence=confidence,
            reasoning=reasoning,
        )

        # Create outcome object
        outcome = Outcome(
            decision_id=f"{ticker}_{timestamp}",
            exit_timestamp=datetime.utcnow().isoformat(),
            exit_price=current_prices.get(ticker, entry_price),
            pnl=outcome_pnl,
            pnl_percent=outcome_pnl_percent,
            holding_period_hours=holding_period_hours,
        )

        # Update meta-learner
        if self.meta_learner:
            current_strategy = self.meta_learner.state.current_strategy
            was_correct = outcome_pnl > 0
            self.meta_learner.update_strategy_performance(
                current_strategy, was_correct, outcome_pnl, regime
            )

        # Perform counterfactual analysis
        if self.counterfactual_engine:
            self.counterfactual_engine.analyze_decision(
                decision, outcome, current_prices
            )

        # Store episode in memory
        if self.episodic_memory:
            episode = MarketEpisode(
                episode_id=f"{ticker}_{timestamp}",
                timestamp=timestamp,
                ticker=ticker,
                price=entry_price,
                volume=market_context.get("volume", 0.0),
                volatility=market_context.get("volatility", 0.5),
                regime=regime,
                rsi=market_context.get("rsi"),
                macd=market_context.get("macd"),
                news_sentiment=market_context.get("news_sentiment", 0.0),
                social_sentiment=market_context.get("social_sentiment", 0.0),
                analyst_sentiment=market_context.get("analyst_sentiment", "neutral"),
                decision_action=action,
                decision_confidence=confidence,
                decision_reasoning=reasoning,
                outcome_pnl=outcome_pnl,
                outcome_pnl_percent=outcome_pnl_percent,
                holding_period_hours=holding_period_hours,
                was_successful=outcome_pnl > 0,
            )

            self.episodic_memory.store_episode(episode)

    def get_system_status(self) -> dict[str, Any]:
        """Get status of all cognitive systems."""
        status = {
            "cognitive_hub": "active",
            "timestamp": datetime.utcnow().isoformat(),
            "subsystems": {},
        }

        if self.meta_learner:
            status["subsystems"]["meta_learning"] = self.meta_learner.get_status()

        if self.counterfactual_engine:
            status["subsystems"][
                "counterfactual"
            ] = self.counterfactual_engine.get_aggregate_insights()

            if self.counterfactual_engine.enable_shadow_portfolios:
                status["subsystems"]["shadow_portfolios"] = (
                    self.counterfactual_engine.get_shadow_portfolio_performance({})
                )

        if self.episodic_memory:
            status["subsystems"]["episodic_memory"] = self.episodic_memory.get_stats()

        return status
