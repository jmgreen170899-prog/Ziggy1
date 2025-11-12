"""
Counterfactual Reasoning Engine for ZiggyAI

Enables learning from the road not taken by:
1. Simulating alternative decisions in parallel shadow portfolios
2. Comparing actual outcomes to counterfactual alternatives
3. Learning from opportunity costs and missed chances
4. Minimizing regret through better decision calibration
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Possible trading actions."""

    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    CLOSE_LONG = "close_long"
    CLOSE_SHORT = "close_short"


@dataclass
class TradingDecision:
    """A trading decision with full context."""

    timestamp: str
    ticker: str
    action: ActionType
    quantity: float
    entry_price: float

    # Decision context
    market_regime: str
    confidence: float
    reasoning: list[str]

    # Risk parameters
    stop_loss: float | None = None
    take_profit: float | None = None
    risk_score: float = 0.5

    # Strategy info
    strategy_name: str = "default"
    signal_name: str = "unknown"


@dataclass
class Outcome:
    """Outcome of a trading decision."""

    decision_id: str
    exit_timestamp: str
    exit_price: float
    pnl: float
    pnl_percent: float
    holding_period_hours: float

    # Risk metrics
    max_adverse_excursion: float = 0.0
    max_favorable_excursion: float = 0.0

    # Success flags
    hit_stop_loss: bool = False
    hit_take_profit: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "decision_id": self.decision_id,
            "exit_timestamp": self.exit_timestamp,
            "exit_price": self.exit_price,
            "pnl": self.pnl,
            "pnl_percent": self.pnl_percent,
            "holding_period_hours": self.holding_period_hours,
            "max_adverse_excursion": self.max_adverse_excursion,
            "max_favorable_excursion": self.max_favorable_excursion,
            "hit_stop_loss": self.hit_stop_loss,
            "hit_take_profit": self.hit_take_profit,
        }


@dataclass
class CounterfactualScenario:
    """A counterfactual alternative decision."""

    alternative_action: ActionType
    alternative_quantity: float
    simulated_outcome: Outcome | None = None

    # Comparison metrics
    opportunity_cost: float = 0.0
    regret_score: float = 0.0

    # Why this alternative wasn't chosen
    decision_factors: list[str] = field(default_factory=list)


@dataclass
class CounterfactualAnalysis:
    """Complete analysis comparing actual to counterfactual outcomes."""

    decision_id: str
    actual_decision: TradingDecision
    actual_outcome: Outcome

    # All alternative scenarios
    counterfactuals: list[CounterfactualScenario] = field(default_factory=list)

    # Analysis results
    best_alternative: ActionType | None = None
    worst_alternative: ActionType | None = None
    total_opportunity_cost: float = 0.0
    regret_score: float = 0.0

    # Learning insights
    should_have_acted_differently: bool = False
    key_lessons: list[str] = field(default_factory=list)

    analyzed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class ShadowPortfolio:
    """
    Shadow portfolio that simulates an alternative trading strategy.

    Maintains parallel trading history to compare against actual decisions.
    """

    def __init__(self, name: str, strategy_description: str, initial_cash: float = 100000.0):
        """
        Initialize shadow portfolio.

        Args:
            name: Portfolio identifier
            strategy_description: What alternative strategy this represents
            initial_cash: Starting capital
        """
        self.name = name
        self.strategy_description = strategy_description
        self.cash = initial_cash
        self.initial_cash = initial_cash

        # Positions and trade history
        self.positions: dict[str, dict[str, float]] = {}
        self.trade_history: list[dict[str, Any]] = []

        # Performance metrics
        self.total_pnl = 0.0
        self.win_count = 0
        self.loss_count = 0
        self.total_trades = 0

    def execute_trade(
        self, ticker: str, action: ActionType, quantity: float, price: float, timestamp: str
    ) -> bool:
        """
        Execute trade in shadow portfolio.

        Returns:
            True if trade successful, False if insufficient funds/shares
        """
        if action == ActionType.BUY:
            cost = quantity * price
            if cost > self.cash:
                return False

            self.cash -= cost
            if ticker not in self.positions:
                self.positions[ticker] = {"quantity": 0, "cost_basis": 0}

            # Update position
            old_qty = self.positions[ticker]["quantity"]
            old_basis = self.positions[ticker]["cost_basis"]
            new_qty = old_qty + quantity
            new_basis = ((old_qty * old_basis) + (quantity * price)) / new_qty

            self.positions[ticker]["quantity"] = new_qty
            self.positions[ticker]["cost_basis"] = new_basis

        elif action == ActionType.SELL or action == ActionType.CLOSE_LONG:
            if ticker not in self.positions or self.positions[ticker]["quantity"] < quantity:
                return False

            # Calculate profit
            cost_basis = self.positions[ticker]["cost_basis"]
            pnl = (price - cost_basis) * quantity
            self.total_pnl += pnl

            # Update position
            self.positions[ticker]["quantity"] -= quantity
            self.cash += quantity * price

            # Track win/loss
            if pnl > 0:
                self.win_count += 1
            else:
                self.loss_count += 1

        # Record trade
        self.trade_history.append(
            {
                "timestamp": timestamp,
                "ticker": ticker,
                "action": action.value,
                "quantity": quantity,
                "price": price,
                "cash_after": self.cash,
            }
        )

        self.total_trades += 1
        return True

    def get_portfolio_value(self, current_prices: dict[str, float]) -> float:
        """Calculate total portfolio value with current prices."""
        position_value = sum(
            pos["quantity"] * current_prices.get(ticker, pos["cost_basis"])
            for ticker, pos in self.positions.items()
        )
        return self.cash + position_value

    def get_return_percent(self, current_prices: dict[str, float]) -> float:
        """Calculate total return percentage."""
        current_value = self.get_portfolio_value(current_prices)
        return ((current_value - self.initial_cash) / self.initial_cash) * 100


class CounterfactualEngine:
    """
    Counterfactual reasoning engine for learning from alternatives.

    Maintains shadow portfolios for different trading strategies and
    continuously compares actual decisions to counterfactual alternatives.
    """

    def __init__(self, enable_shadow_portfolios: bool = True, track_all_alternatives: bool = True):
        """
        Initialize counterfactual engine.

        Args:
            enable_shadow_portfolios: Whether to maintain shadow portfolios
            track_all_alternatives: Whether to track all possible alternatives
        """
        self.enable_shadow_portfolios = enable_shadow_portfolios
        self.track_all_alternatives = track_all_alternatives

        # Shadow portfolios for different strategies
        self.shadow_portfolios: dict[str, ShadowPortfolio] = {}

        # Initialize default shadow strategies
        if enable_shadow_portfolios:
            self._initialize_shadow_portfolios()

        # Counterfactual analysis history
        self.analyses: list[CounterfactualAnalysis] = []

        # Learning metrics
        self.total_regret = 0.0
        self.total_opportunity_cost = 0.0
        self.decisions_analyzed = 0

        logger.info("CounterfactualEngine initialized")

    def _initialize_shadow_portfolios(self) -> None:
        """Create shadow portfolios for alternative strategies."""
        shadow_strategies = [
            ("always_buy", "Always buy on signals, never hold"),
            ("always_hold", "Never trade, always hold cash"),
            ("opposite_action", "Do opposite of actual decision"),
            ("half_size", "Same decisions but half position size"),
            ("double_size", "Same decisions but double position size"),
        ]

        for name, description in shadow_strategies:
            self.shadow_portfolios[name] = ShadowPortfolio(
                name=name, strategy_description=description
            )

    def analyze_decision(
        self, decision: TradingDecision, actual_outcome: Outcome, current_prices: dict[str, float]
    ) -> CounterfactualAnalysis:
        """
        Perform counterfactual analysis on a completed decision.

        Args:
            decision: The actual decision that was made
            actual_outcome: The actual outcome that occurred
            current_prices: Current market prices for portfolio valuation

        Returns:
            Complete counterfactual analysis
        """
        decision_id = f"{decision.ticker}_{decision.timestamp}"

        # Generate counterfactual scenarios
        counterfactuals = self._generate_counterfactuals(decision, actual_outcome, current_prices)

        # Find best and worst alternatives
        best_alternative = None
        worst_alternative = None
        best_pnl = -float("inf")
        worst_pnl = float("inf")

        total_opportunity_cost = 0.0

        for cf in counterfactuals:
            if cf.simulated_outcome:
                pnl = cf.simulated_outcome.pnl

                if pnl > best_pnl:
                    best_pnl = pnl
                    best_alternative = cf.alternative_action

                if pnl < worst_pnl:
                    worst_pnl = pnl
                    worst_alternative = cf.alternative_action

                # Calculate opportunity cost (positive if we missed gains)
                opportunity_cost = pnl - actual_outcome.pnl
                cf.opportunity_cost = opportunity_cost
                total_opportunity_cost += max(0, opportunity_cost)

                # Calculate regret (how much better best alternative was)
                cf.regret_score = max(0, best_pnl - actual_outcome.pnl)

        # Overall regret is how much better best alternative was
        regret_score = max(0, best_pnl - actual_outcome.pnl)

        # Determine if we should have acted differently
        should_have_acted_differently = regret_score > abs(actual_outcome.pnl) * 0.5

        # Extract key lessons
        key_lessons = self._extract_lessons(
            decision, actual_outcome, counterfactuals, should_have_acted_differently
        )

        # Create analysis
        analysis = CounterfactualAnalysis(
            decision_id=decision_id,
            actual_decision=decision,
            actual_outcome=actual_outcome,
            counterfactuals=counterfactuals,
            best_alternative=best_alternative,
            worst_alternative=worst_alternative,
            total_opportunity_cost=total_opportunity_cost,
            regret_score=regret_score,
            should_have_acted_differently=should_have_acted_differently,
            key_lessons=key_lessons,
        )

        # Update metrics
        self.total_regret += regret_score
        self.total_opportunity_cost += total_opportunity_cost
        self.decisions_analyzed += 1

        # Store analysis
        self.analyses.append(analysis)

        # Update shadow portfolios
        if self.enable_shadow_portfolios:
            self._update_shadow_portfolios(decision, current_prices)

        logger.debug(
            f"Counterfactual analysis: {decision_id}, "
            f"regret: ${regret_score:.2f}, "
            f"best_alternative: {best_alternative}"
        )

        return analysis

    def _generate_counterfactuals(
        self, decision: TradingDecision, actual_outcome: Outcome, current_prices: dict[str, float]
    ) -> list[CounterfactualScenario]:
        """Generate all counterfactual alternative scenarios."""
        counterfactuals = []

        # Define all possible alternative actions
        alternatives = []

        if decision.action == ActionType.BUY:
            alternatives = [
                (ActionType.HOLD, 0),
                (ActionType.BUY, decision.quantity * 0.5),  # Half size
                (ActionType.BUY, decision.quantity * 2.0),  # Double size
            ]
        elif decision.action == ActionType.SELL:
            alternatives = [
                (ActionType.HOLD, 0),
                (ActionType.SELL, decision.quantity * 0.5),
                (ActionType.SELL, decision.quantity * 2.0),
            ]
        elif decision.action == ActionType.HOLD:
            alternatives = [
                (ActionType.BUY, decision.quantity if decision.quantity > 0 else 100),
                (ActionType.SELL, decision.quantity if decision.quantity > 0 else 100),
            ]

        # Simulate each alternative
        for alt_action, alt_quantity in alternatives:
            simulated_outcome = self._simulate_outcome(
                decision, alt_action, alt_quantity, current_prices
            )

            counterfactuals.append(
                CounterfactualScenario(
                    alternative_action=alt_action,
                    alternative_quantity=alt_quantity,
                    simulated_outcome=simulated_outcome,
                    decision_factors=[
                        f"Confidence was {decision.confidence:.2f}",
                        f"Market regime was {decision.market_regime}",
                    ],
                )
            )

        return counterfactuals

    def _simulate_outcome(
        self,
        original_decision: TradingDecision,
        alt_action: ActionType,
        alt_quantity: float,
        current_prices: dict[str, float],
    ) -> Outcome | None:
        """
        Simulate what outcome would have been with alternative action.

        This is a simplified simulation. In production, this would use
        actual market data and more sophisticated modeling.
        """
        if alt_action == ActionType.HOLD or alt_quantity == 0:
            # Holding has zero PnL
            return Outcome(
                decision_id=f"{original_decision.ticker}_counterfactual",
                exit_timestamp=datetime.utcnow().isoformat(),
                exit_price=original_decision.entry_price,
                pnl=0.0,
                pnl_percent=0.0,
                holding_period_hours=0.0,
            )

        # Get current price for ticker
        current_price = current_prices.get(
            original_decision.ticker,
            original_decision.entry_price * 1.01,  # Assume 1% move if no data
        )

        # Calculate counterfactual PnL
        if alt_action in [ActionType.BUY, ActionType.CLOSE_SHORT]:
            price_change = current_price - original_decision.entry_price
        else:  # SELL or CLOSE_LONG
            price_change = original_decision.entry_price - current_price

        pnl = price_change * alt_quantity
        pnl_percent = (price_change / original_decision.entry_price) * 100

        return Outcome(
            decision_id=f"{original_decision.ticker}_counterfactual",
            exit_timestamp=datetime.utcnow().isoformat(),
            exit_price=current_price,
            pnl=pnl,
            pnl_percent=pnl_percent,
            holding_period_hours=1.0,  # Simplified
        )

    def _extract_lessons(
        self,
        decision: TradingDecision,
        actual_outcome: Outcome,
        counterfactuals: list[CounterfactualScenario],
        should_have_acted_differently: bool,
    ) -> list[str]:
        """Extract key learning lessons from counterfactual analysis."""
        lessons = []

        if should_have_acted_differently:
            # Find what we should have done
            best_cf = max(
                (cf for cf in counterfactuals if cf.simulated_outcome),
                key=lambda cf: cf.simulated_outcome.pnl if cf.simulated_outcome else -float("inf"),
                default=None,
            )

            if best_cf:
                lessons.append(
                    f"Should have {best_cf.alternative_action.value} instead of "
                    f"{decision.action.value} - would have saved "
                    f"${best_cf.opportunity_cost:.2f}"
                )

        # Lesson about position sizing
        half_size_cf = next(
            (cf for cf in counterfactuals if cf.alternative_quantity < decision.quantity), None
        )
        if half_size_cf and half_size_cf.simulated_outcome:
            if actual_outcome.pnl < 0 and half_size_cf.simulated_outcome.pnl > actual_outcome.pnl:
                lessons.append("Smaller position size would have reduced loss")

        # Lesson about regime
        if actual_outcome.pnl < 0:
            lessons.append(f"Strategy may not be optimal for {decision.market_regime} regime")

        return lessons

    def _update_shadow_portfolios(
        self, decision: TradingDecision, current_prices: dict[str, float]
    ) -> None:
        """Update all shadow portfolios with alternative decisions."""
        timestamp = decision.timestamp
        ticker = decision.ticker
        price = decision.entry_price

        for name, portfolio in self.shadow_portfolios.items():
            if name == "always_buy" and decision.action != ActionType.HOLD:
                portfolio.execute_trade(ticker, ActionType.BUY, decision.quantity, price, timestamp)

            elif name == "always_hold":
                # Do nothing
                pass

            elif name == "opposite_action":
                opposite_actions = {
                    ActionType.BUY: ActionType.SELL,
                    ActionType.SELL: ActionType.BUY,
                    ActionType.HOLD: ActionType.BUY,
                }
                opposite = opposite_actions.get(decision.action, ActionType.HOLD)
                if opposite != ActionType.HOLD:
                    portfolio.execute_trade(ticker, opposite, decision.quantity, price, timestamp)

            elif name == "half_size" and decision.action != ActionType.HOLD:
                portfolio.execute_trade(
                    ticker, decision.action, decision.quantity * 0.5, price, timestamp
                )

            elif name == "double_size" and decision.action != ActionType.HOLD:
                portfolio.execute_trade(
                    ticker, decision.action, decision.quantity * 2.0, price, timestamp
                )

    def get_shadow_portfolio_performance(
        self, current_prices: dict[str, float]
    ) -> dict[str, dict[str, Any]]:
        """Get performance metrics for all shadow portfolios."""
        performance = {}

        for name, portfolio in self.shadow_portfolios.items():
            total_return = portfolio.get_return_percent(current_prices)
            win_rate = (
                portfolio.win_count / (portfolio.win_count + portfolio.loss_count)
                if portfolio.total_trades > 0
                else 0.0
            )

            performance[name] = {
                "strategy": portfolio.strategy_description,
                "total_trades": portfolio.total_trades,
                "total_return_percent": total_return,
                "total_pnl": portfolio.total_pnl,
                "win_rate": win_rate,
                "cash": portfolio.cash,
                "portfolio_value": portfolio.get_portfolio_value(current_prices),
            }

        return performance

    def get_aggregate_insights(self) -> dict[str, Any]:
        """Get aggregate insights from all counterfactual analyses."""
        if not self.analyses:
            return {
                "decisions_analyzed": 0,
                "total_regret": 0.0,
                "avg_regret": 0.0,
                "total_opportunity_cost": 0.0,
            }

        # Count how often we should have acted differently
        should_have_acted_differently_count = sum(
            1 for a in self.analyses if a.should_have_acted_differently
        )

        # Find most common lessons
        all_lessons = []
        for analysis in self.analyses:
            all_lessons.extend(analysis.key_lessons)

        # Most common alternative actions
        alternative_actions = {}
        for analysis in self.analyses:
            if analysis.best_alternative:
                key = analysis.best_alternative.value
                alternative_actions[key] = alternative_actions.get(key, 0) + 1

        return {
            "decisions_analyzed": self.decisions_analyzed,
            "total_regret": self.total_regret,
            "avg_regret": self.total_regret / self.decisions_analyzed,
            "total_opportunity_cost": self.total_opportunity_cost,
            "avg_opportunity_cost": self.total_opportunity_cost / self.decisions_analyzed,
            "should_have_acted_differently_percent": (
                should_have_acted_differently_count / self.decisions_analyzed * 100
            ),
            "most_common_lessons": list(set(all_lessons))[:5],
            "best_alternative_actions": alternative_actions,
        }
