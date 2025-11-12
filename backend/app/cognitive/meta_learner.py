"""
Meta-Learning System for ZiggyAI

Enables the AI to learn HOW to learn by:
1. Maintaining a portfolio of learning strategies
2. Tracking which strategies work best in different market regimes
3. Evolving new learning strategies through genetic programming
4. Automatically selecting optimal learning approach for current conditions
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np


logger = logging.getLogger(__name__)


class LearningStrategyType(Enum):
    """Types of learning strategies."""

    MOMENTUM = "momentum"  # Fast adaptation to recent patterns
    CONTRARIAN = "contrarian"  # Learn from reversals and overreactions
    BALANCED = "balanced"  # Mix of momentum and mean reversion
    VOLATILITY_ADAPTIVE = "volatility_adaptive"  # Adjust learning rate by volatility
    REGIME_SPECIFIC = "regime_specific"  # Different rules per regime
    ENSEMBLE = "ensemble"  # Combine multiple sub-strategies


@dataclass
class LearningStrategy:
    """A learning strategy with its configuration and performance metrics."""

    name: str
    strategy_type: LearningStrategyType
    parameters: dict[str, Any]

    # Performance tracking
    total_predictions: int = 0
    correct_predictions: int = 0
    total_profit: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0

    # Regime-specific performance
    regime_performance: dict[str, dict[str, float]] = field(default_factory=dict)

    # Genetic programming metadata
    generation: int = 0
    parent_strategies: list[str] = field(default_factory=list)
    mutations: list[str] = field(default_factory=list)

    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def update_performance(self, correct: bool, profit: float, regime: str) -> None:
        """Update strategy performance metrics."""
        self.total_predictions += 1
        if correct:
            self.correct_predictions += 1
        self.total_profit += profit
        self.last_updated = datetime.utcnow().isoformat()

        # Update regime-specific performance
        if regime not in self.regime_performance:
            self.regime_performance[regime] = {
                "predictions": 0,
                "correct": 0,
                "profit": 0.0,
                "accuracy": 0.0,
            }

        self.regime_performance[regime]["predictions"] += 1
        if correct:
            self.regime_performance[regime]["correct"] += 1
        self.regime_performance[regime]["profit"] += profit

        # Update accuracy
        if self.regime_performance[regime]["predictions"] > 0:
            self.regime_performance[regime]["accuracy"] = (
                self.regime_performance[regime]["correct"]
                / self.regime_performance[regime]["predictions"]
            )

    @property
    def accuracy(self) -> float:
        """Overall accuracy of this strategy."""
        if self.total_predictions == 0:
            return 0.0
        return self.correct_predictions / self.total_predictions

    def get_regime_accuracy(self, regime: str) -> float:
        """Get accuracy for specific market regime."""
        if regime not in self.regime_performance:
            return 0.0
        return self.regime_performance[regime].get("accuracy", 0.0)


@dataclass
class MetaLearningState:
    """State of the meta-learning system."""

    current_strategy: str
    regime: str
    strategies_evaluated: int = 0
    strategy_switches: int = 0
    total_profit: float = 0.0

    # Track strategy performance over time
    strategy_timeline: list[dict[str, Any]] = field(default_factory=list)
    regime_history: list[dict[str, Any]] = field(default_factory=list)

    last_evolution: str | None = None
    next_evolution_due: str | None = None


class MetaLearner:
    """
    Meta-learning system that learns how to learn.

    Core capabilities:
    1. Strategy Portfolio Management: Maintains diverse learning strategies
    2. Performance Tracking: Monitors which strategies work in which regimes
    3. Automatic Selection: Chooses best strategy for current conditions
    4. Strategy Evolution: Creates new strategies via genetic programming
    5. Adaptive Optimization: Continuously improves strategy portfolio
    """

    def __init__(
        self,
        strategies_dir: Path | None = None,
        evolution_frequency: int = 100,  # Evolve after N trades
        min_strategy_samples: int = 20,  # Min samples before strategy evaluation
    ):
        """
        Initialize meta-learner.

        Args:
            strategies_dir: Directory to save/load strategies
            evolution_frequency: How often to evolve new strategies
            min_strategy_samples: Minimum predictions before evaluating strategy
        """
        self.strategies_dir = strategies_dir or Path("data/meta_learning")
        self.strategies_dir.mkdir(parents=True, exist_ok=True)

        self.evolution_frequency = evolution_frequency
        self.min_strategy_samples = min_strategy_samples

        # Strategy portfolio
        self.strategies: dict[str, LearningStrategy] = {}
        self.state = MetaLearningState(current_strategy="balanced_default", regime="unknown")

        # Initialize with default strategies
        self._initialize_default_strategies()

        # Load any saved strategies
        self._load_strategies()

        logger.info(f"MetaLearner initialized with {len(self.strategies)} strategies")

    def _initialize_default_strategies(self) -> None:
        """Create initial set of learning strategies."""
        default_strategies = [
            LearningStrategy(
                name="momentum_aggressive",
                strategy_type=LearningStrategyType.MOMENTUM,
                parameters={
                    "learning_rate": 0.1,
                    "momentum_decay": 0.9,
                    "lookback_period": 5,
                    "confidence_threshold": 0.6,
                },
            ),
            LearningStrategy(
                name="contrarian_conservative",
                strategy_type=LearningStrategyType.CONTRARIAN,
                parameters={
                    "learning_rate": 0.01,
                    "reversal_threshold": 2.0,
                    "lookback_period": 20,
                    "confidence_threshold": 0.75,
                },
            ),
            LearningStrategy(
                name="balanced_default",
                strategy_type=LearningStrategyType.BALANCED,
                parameters={
                    "learning_rate": 0.05,
                    "momentum_weight": 0.5,
                    "mean_reversion_weight": 0.5,
                    "lookback_period": 10,
                    "confidence_threshold": 0.65,
                },
            ),
            LearningStrategy(
                name="volatility_adaptive",
                strategy_type=LearningStrategyType.VOLATILITY_ADAPTIVE,
                parameters={
                    "base_learning_rate": 0.05,
                    "volatility_scaling": True,
                    "high_vol_multiplier": 0.5,
                    "low_vol_multiplier": 1.5,
                    "confidence_threshold": 0.7,
                },
            ),
        ]

        for strategy in default_strategies:
            self.strategies[strategy.name] = strategy

    def select_strategy(self, regime: str) -> LearningStrategy:
        """
        Select best learning strategy for current market regime.

        Args:
            regime: Current market regime (e.g., "Panic", "RiskOn", "Chop")

        Returns:
            Best learning strategy for this regime
        """
        # Update regime
        self.state.regime = regime
        self.state.regime_history.append(
            {"regime": regime, "timestamp": datetime.utcnow().isoformat()}
        )

        # Find best strategy for this regime
        best_strategy = None
        best_score = -float("inf")

        for strategy in self.strategies.values():
            # Skip strategies with insufficient data
            regime_data = strategy.regime_performance.get(regime, {})
            if regime_data.get("predictions", 0) < self.min_strategy_samples:
                # Use overall accuracy as fallback
                score = strategy.accuracy
            else:
                # Use regime-specific accuracy
                score = regime_data.get("accuracy", 0.0)

            # Add exploration bonus for less-tried strategies
            exploration_bonus = 0.1 * np.sqrt(
                self.min_strategy_samples / max(regime_data.get("predictions", 1), 1)
            )
            total_score = score + exploration_bonus

            if total_score > best_score:
                best_score = total_score
                best_strategy = strategy

        # Default to balanced if no strategy selected
        if best_strategy is None:
            best_strategy = self.strategies.get(
                "balanced_default", list(self.strategies.values())[0]
            )

        # Track strategy switch
        if self.state.current_strategy != best_strategy.name:
            self.state.strategy_switches += 1
            logger.info(
                f"Strategy switch: {self.state.current_strategy} -> "
                f"{best_strategy.name} (regime: {regime}, score: {best_score:.3f})"
            )

        self.state.current_strategy = best_strategy.name
        return best_strategy

    def update_strategy_performance(
        self, strategy_name: str, correct: bool, profit: float, regime: str
    ) -> None:
        """
        Update performance metrics for a strategy.

        Args:
            strategy_name: Name of strategy to update
            correct: Whether prediction was correct
            profit: Profit/loss from this prediction
            regime: Market regime when prediction was made
        """
        if strategy_name not in self.strategies:
            logger.warning(f"Unknown strategy: {strategy_name}")
            return

        strategy = self.strategies[strategy_name]
        strategy.update_performance(correct, profit, regime)

        self.state.strategies_evaluated += 1
        self.state.total_profit += profit

        # Record in timeline
        self.state.strategy_timeline.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "strategy": strategy_name,
                "regime": regime,
                "correct": correct,
                "profit": profit,
                "accuracy": strategy.accuracy,
            }
        )

        # Check if evolution is due
        if (
            self.state.strategies_evaluated % self.evolution_frequency == 0
            and self.state.strategies_evaluated > 0
        ):
            self._evolve_strategies()

    def _evolve_strategies(self) -> None:
        """
        Evolve new learning strategies using genetic programming.

        Process:
        1. Select top-performing strategies as parents
        2. Combine their best characteristics
        3. Add random mutations for exploration
        4. Add new strategy to portfolio
        """
        logger.info("Evolving new strategies...")

        # Get top 2 performing strategies
        sorted_strategies = sorted(self.strategies.values(), key=lambda s: s.accuracy, reverse=True)

        if len(sorted_strategies) < 2:
            logger.warning("Not enough strategies for evolution")
            return

        parent1 = sorted_strategies[0]
        parent2 = sorted_strategies[1]

        # Create new strategy by combining parents
        new_strategy = self._crossover_strategies(parent1, parent2)

        # Add mutations
        new_strategy = self._mutate_strategy(new_strategy)

        # Add to portfolio
        self.strategies[new_strategy.name] = new_strategy

        self.state.last_evolution = datetime.utcnow().isoformat()

        logger.info(
            f"Evolved new strategy: {new_strategy.name} from parents "
            f"{parent1.name} (acc: {parent1.accuracy:.3f}) and "
            f"{parent2.name} (acc: {parent2.accuracy:.3f})"
        )

        # Prune worst strategies if portfolio too large
        if len(self.strategies) > 10:
            self._prune_strategies()

    def _crossover_strategies(
        self, parent1: LearningStrategy, parent2: LearningStrategy
    ) -> LearningStrategy:
        """Combine two strategies to create offspring."""
        # Mix parameters from both parents
        new_params = {}
        for key in parent1.parameters:
            if key in parent2.parameters:
                # Average numeric parameters
                if isinstance(parent1.parameters[key], (int, float)):
                    new_params[key] = (parent1.parameters[key] + parent2.parameters[key]) / 2
                else:
                    # Randomly choose for non-numeric
                    new_params[key] = (
                        parent1.parameters[key]
                        if np.random.random() > 0.5
                        else parent2.parameters[key]
                    )

        # Determine strategy type based on parents
        strategy_type = (
            parent1.strategy_type if parent1.accuracy > parent2.accuracy else parent2.strategy_type
        )

        # Generate name
        generation = max(parent1.generation, parent2.generation) + 1
        name = f"evolved_gen{generation}_{datetime.utcnow().timestamp():.0f}"

        return LearningStrategy(
            name=name,
            strategy_type=strategy_type,
            parameters=new_params,
            generation=generation,
            parent_strategies=[parent1.name, parent2.name],
        )

    def _mutate_strategy(self, strategy: LearningStrategy) -> LearningStrategy:
        """Add random mutations to strategy parameters."""
        mutation_rate = 0.2  # 20% chance to mutate each parameter
        mutations = []

        for key, value in strategy.parameters.items():
            if np.random.random() < mutation_rate:
                if isinstance(value, float):
                    # Add gaussian noise
                    mutation_factor = np.random.normal(1.0, 0.2)
                    strategy.parameters[key] = value * mutation_factor
                    mutations.append(f"{key}_mutated")
                elif isinstance(value, int):
                    # Add/subtract small integer
                    delta = np.random.randint(-2, 3)
                    strategy.parameters[key] = max(1, value + delta)
                    mutations.append(f"{key}_mutated")

        strategy.mutations = mutations
        return strategy

    def _prune_strategies(self, keep_top: int = 8) -> None:
        """Remove worst-performing strategies to maintain portfolio size."""
        sorted_strategies = sorted(self.strategies.values(), key=lambda s: s.accuracy, reverse=True)

        # Always keep default strategies and top performers
        protected_names = {
            "momentum_aggressive",
            "contrarian_conservative",
            "balanced_default",
            "volatility_adaptive",
        }

        to_keep = set(protected_names)
        for strategy in sorted_strategies[:keep_top]:
            to_keep.add(strategy.name)

        # Remove strategies not in keep set
        to_remove = [name for name in self.strategies.keys() if name not in to_keep]

        for name in to_remove:
            del self.strategies[name]
            logger.info(f"Pruned strategy: {name}")

    def _save_strategies(self) -> None:
        """Save strategies to disk."""
        try:
            strategies_data = {
                name: {
                    "name": s.name,
                    "strategy_type": s.strategy_type.value,
                    "parameters": s.parameters,
                    "total_predictions": s.total_predictions,
                    "correct_predictions": s.correct_predictions,
                    "total_profit": s.total_profit,
                    "sharpe_ratio": s.sharpe_ratio,
                    "max_drawdown": s.max_drawdown,
                    "regime_performance": s.regime_performance,
                    "generation": s.generation,
                    "parent_strategies": s.parent_strategies,
                    "mutations": s.mutations,
                    "created_at": s.created_at,
                    "last_updated": s.last_updated,
                }
                for name, s in self.strategies.items()
            }

            filepath = self.strategies_dir / "strategies.json"
            with open(filepath, "w") as f:
                json.dump(strategies_data, f, indent=2)

            logger.debug(f"Saved {len(strategies_data)} strategies to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save strategies: {e}")

    def _load_strategies(self) -> None:
        """Load strategies from disk."""
        filepath = self.strategies_dir / "strategies.json"
        if not filepath.exists():
            logger.debug("No saved strategies found")
            return

        try:
            with open(filepath) as f:
                strategies_data = json.load(f)

            for name, data in strategies_data.items():
                # Skip if already loaded (default strategies)
                if name in self.strategies:
                    continue

                strategy = LearningStrategy(
                    name=data["name"],
                    strategy_type=LearningStrategyType(data["strategy_type"]),
                    parameters=data["parameters"],
                    total_predictions=data.get("total_predictions", 0),
                    correct_predictions=data.get("correct_predictions", 0),
                    total_profit=data.get("total_profit", 0.0),
                    sharpe_ratio=data.get("sharpe_ratio", 0.0),
                    max_drawdown=data.get("max_drawdown", 0.0),
                    regime_performance=data.get("regime_performance", {}),
                    generation=data.get("generation", 0),
                    parent_strategies=data.get("parent_strategies", []),
                    mutations=data.get("mutations", []),
                    created_at=data.get("created_at", datetime.utcnow().isoformat()),
                    last_updated=data.get("last_updated", datetime.utcnow().isoformat()),
                )
                self.strategies[name] = strategy

            logger.info(f"Loaded {len(strategies_data)} strategies from {filepath}")
        except Exception as e:
            logger.error(f"Failed to load strategies: {e}")

    def get_status(self) -> dict[str, Any]:
        """Get current meta-learning status."""
        return {
            "current_strategy": self.state.current_strategy,
            "current_regime": self.state.regime,
            "total_strategies": len(self.strategies),
            "strategies_evaluated": self.state.strategies_evaluated,
            "strategy_switches": self.state.strategy_switches,
            "total_profit": self.state.total_profit,
            "last_evolution": self.state.last_evolution,
            "strategies": {
                name: {
                    "type": s.strategy_type.value,
                    "accuracy": s.accuracy,
                    "total_predictions": s.total_predictions,
                    "total_profit": s.total_profit,
                    "generation": s.generation,
                }
                for name, s in self.strategies.items()
            },
        }

    def __del__(self):
        """Save strategies on cleanup."""
        try:
            self._save_strategies()
        except:
            pass
