"""
Multi-armed bandit allocator for ZiggyAI paper trading lab.

This module implements Thompson Sampling and UCB1 algorithms to route
trading flow across theories based on performance metrics.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from app.core.logging import get_logger


logger = get_logger("ziggy.bandit_allocator")


class BanditAlgorithm(Enum):
    """Bandit algorithm types."""

    THOMPSON_SAMPLING = "thompson_sampling"
    UCB1 = "ucb1"
    EPSILON_GREEDY = "epsilon_greedy"


@dataclass
class TheoryArm:
    """Bandit arm representing a trading theory."""

    theory_id: str

    # Thompson Sampling (Beta distribution)
    alpha: float = 1.0  # Success count + 1
    beta: float = 1.0  # Failure count + 1

    # UCB1
    total_reward: float = 0.0
    num_selections: int = 0

    # Performance tracking
    total_trades: int = 0
    winning_trades: int = 0
    total_pnl_bps: float = 0.0
    total_fees_bps: float = 0.0

    # Exponential decay tracking
    recent_alpha: float = 1.0
    recent_beta: float = 1.0
    recent_reward: float = 0.0
    recent_selections: int = 0

    # Metadata
    last_update: datetime | None = None
    last_allocation: float = 0.0


@dataclass
class AllocationResult:
    """Result of bandit allocation."""

    allocations: dict[str, float]  # theory_id -> allocation weight
    selected_theory: str
    confidence: float
    algorithm_state: dict[str, Any]


class BanditAllocator:
    """
    Multi-armed bandit for theory allocation.

    Features:
    - Thompson Sampling with Beta priors
    - UCB1 with confidence bounds
    - Exponential decay for concept drift
    - Performance-based reward calculation
    - Cold-start handling
    """

    def __init__(
        self,
        algorithm: BanditAlgorithm = BanditAlgorithm.THOMPSON_SAMPLING,
        decay_factor: float = 0.995,
        min_allocation: float = 0.05,
        ucb_c: float = 1.0,
        epsilon: float = 0.1,
        performance_window_mins: int = 60,
        random_seed: int | None = None,
    ):
        self.algorithm = algorithm
        self.decay_factor = decay_factor
        self.min_allocation = min_allocation
        self.ucb_c = ucb_c
        self.epsilon = epsilon
        self.performance_window_mins = performance_window_mins

        self.rng = random.Random(random_seed)
        self.arms: dict[str, TheoryArm] = {}
        self.total_selections = 0

        logger.info(
            "BanditAllocator initialized",
            extra={
                "algorithm": algorithm.value,
                "decay_factor": decay_factor,
                "min_allocation": min_allocation,
            },
        )

    def add_theory(self, theory_id: str) -> None:
        """Add a new theory arm."""
        if theory_id not in self.arms:
            self.arms[theory_id] = TheoryArm(theory_id=theory_id)
            logger.info("Added theory arm", extra={"theory_id": theory_id})

    def allocate(self, available_theories: list[str]) -> AllocationResult:
        """
        Allocate resources across theories using bandit algorithm.

        Args:
            available_theories: List of theory IDs to consider

        Returns:
            AllocationResult with allocations and selected theory
        """
        # Ensure all theories are registered
        for theory_id in available_theories:
            self.add_theory(theory_id)

        # Apply decay to all arms
        self._apply_decay()

        # Calculate allocations based on algorithm
        if self.algorithm == BanditAlgorithm.THOMPSON_SAMPLING:
            result = self._thompson_sampling_allocation(available_theories)
        elif self.algorithm == BanditAlgorithm.UCB1:
            result = self._ucb1_allocation(available_theories)
        else:  # EPSILON_GREEDY
            result = self._epsilon_greedy_allocation(available_theories)

        # Update allocation tracking
        for theory_id, allocation in result.allocations.items():
            if theory_id in self.arms:
                self.arms[theory_id].last_allocation = allocation

        self.total_selections += 1

        return result

    def update_performance(
        self,
        theory_id: str,
        pnl_bps: float,
        fees_bps: float,
        was_winner: bool,
        timestamp: datetime | None = None,
    ) -> None:
        """
        Update theory performance metrics.

        Args:
            theory_id: Theory ID
            pnl_bps: PnL in basis points
            fees_bps: Fees in basis points
            was_winner: True if trade was profitable
            timestamp: Trade timestamp (defaults to now)
        """
        if theory_id not in self.arms:
            self.add_theory(theory_id)

        arm = self.arms[theory_id]
        timestamp = timestamp or datetime.utcnow()

        # Calculate net PnL
        net_pnl_bps = pnl_bps - fees_bps

        # Update basic stats
        arm.total_trades += 1
        arm.total_pnl_bps += net_pnl_bps
        arm.total_fees_bps += fees_bps
        arm.last_update = timestamp

        if was_winner:
            arm.winning_trades += 1

        # Update bandit-specific metrics
        if self.algorithm == BanditAlgorithm.THOMPSON_SAMPLING:
            # Convert PnL to success/failure for Beta distribution
            if net_pnl_bps > 0:
                arm.alpha += 1
                arm.recent_alpha += 1
            else:
                arm.beta += 1
                arm.recent_beta += 1

        elif self.algorithm == BanditAlgorithm.UCB1:
            # Normalize reward to [0, 1] range
            # Map PnL bps to reward (e.g., +100 bps = 1.0, -100 bps = 0.0)
            reward = max(0.0, min(1.0, (net_pnl_bps + 100) / 200))
            arm.total_reward += reward
            arm.recent_reward += reward
            arm.num_selections += 1
            arm.recent_selections += 1

        logger.debug(
            "Updated theory performance",
            extra={
                "theory_id": theory_id,
                "net_pnl_bps": net_pnl_bps,
                "was_winner": was_winner,
                "total_trades": arm.total_trades,
            },
        )

    def get_allocations(self, available_theories: list[str]) -> dict[str, float]:
        """Get current allocation weights without selection."""
        result = self.allocate(available_theories)
        return result.allocations

    def get_performance_summary(self) -> dict[str, dict[str, Any]]:
        """Get performance summary for all theories."""
        summary = {}

        for theory_id, arm in self.arms.items():
            win_rate = arm.winning_trades / arm.total_trades if arm.total_trades > 0 else 0.0
            avg_pnl_bps = arm.total_pnl_bps / arm.total_trades if arm.total_trades > 0 else 0.0

            # Calculate Sharpe-like ratio (avg return / volatility proxy)
            # Using fees as a volatility proxy for simplicity
            sharpe_proxy = 0.0
            if arm.total_trades > 1 and arm.total_fees_bps > 0:
                sharpe_proxy = avg_pnl_bps / (arm.total_fees_bps / arm.total_trades)

            summary[theory_id] = {
                "total_trades": arm.total_trades,
                "win_rate": win_rate,
                "avg_pnl_bps": avg_pnl_bps,
                "total_pnl_bps": arm.total_pnl_bps,
                "total_fees_bps": arm.total_fees_bps,
                "sharpe_proxy": sharpe_proxy,
                "last_allocation": arm.last_allocation,
                "last_update": arm.last_update.isoformat() if arm.last_update else None,
                # Algorithm-specific metrics
                "alpha": arm.alpha,
                "beta": arm.beta,
                "ucb_reward": arm.total_reward,
                "ucb_selections": arm.num_selections,
            }

        return summary

    def reset_theory(self, theory_id: str) -> bool:
        """Reset a theory's performance metrics."""
        if theory_id in self.arms:
            arm = self.arms[theory_id]
            arm.alpha = 1.0
            arm.beta = 1.0
            arm.total_reward = 0.0
            arm.num_selections = 0
            arm.total_trades = 0
            arm.winning_trades = 0
            arm.total_pnl_bps = 0.0
            arm.total_fees_bps = 0.0
            arm.recent_alpha = 1.0
            arm.recent_beta = 1.0
            arm.recent_reward = 0.0
            arm.recent_selections = 0
            logger.info("Reset theory metrics", extra={"theory_id": theory_id})
            return True
        return False

    # --- Durability API ---
    def get_state(self) -> dict[str, Any]:
        """Return serializable state of bandit arms and allocator parameters."""
        arms_payload = {}
        for tid, arm in self.arms.items():
            arms_payload[tid] = {
                "alpha": arm.alpha,
                "beta": arm.beta,
                "total_reward": arm.total_reward,
                "num_selections": arm.num_selections,
                "total_trades": arm.total_trades,
                "winning_trades": arm.winning_trades,
                "total_pnl_bps": arm.total_pnl_bps,
                "total_fees_bps": arm.total_fees_bps,
                "recent_alpha": arm.recent_alpha,
                "recent_beta": arm.recent_beta,
                "recent_reward": arm.recent_reward,
                "recent_selections": arm.recent_selections,
                "last_allocation": arm.last_allocation,
            }
        return {
            "algorithm": self.algorithm.value,
            "params": {
                "decay_factor": self.decay_factor,
                "min_allocation": self.min_allocation,
                "ucb_c": self.ucb_c,
                "epsilon": self.epsilon,
            },
            "arms": arms_payload,
        }

    def set_state(self, state: dict[str, Any]) -> None:
        """Restore bandit arms from payload."""
        payload = state.get("arms") or {}
        if not isinstance(payload, dict):
            return
        for tid, data in payload.items():
            self.add_theory(tid)
            arm = self.arms[tid]
            arm.alpha = float(data.get("alpha", arm.alpha))
            arm.beta = float(data.get("beta", arm.beta))
            arm.total_reward = float(data.get("total_reward", arm.total_reward))
            arm.num_selections = int(data.get("num_selections", arm.num_selections))
            arm.total_trades = int(data.get("total_trades", arm.total_trades))
            arm.winning_trades = int(data.get("winning_trades", arm.winning_trades))
            arm.total_pnl_bps = float(data.get("total_pnl_bps", arm.total_pnl_bps))
            arm.total_fees_bps = float(data.get("total_fees_bps", arm.total_fees_bps))
            arm.recent_alpha = float(data.get("recent_alpha", arm.recent_alpha))
            arm.recent_beta = float(data.get("recent_beta", arm.recent_beta))
            arm.recent_reward = float(data.get("recent_reward", arm.recent_reward))
            arm.recent_selections = int(data.get("recent_selections", arm.recent_selections))
            arm.last_allocation = float(data.get("last_allocation", arm.last_allocation))

    def _apply_decay(self) -> None:
        """Apply exponential decay to recent performance metrics."""
        for arm in self.arms.values():
            arm.recent_alpha = max(1.0, arm.recent_alpha * self.decay_factor)
            arm.recent_beta = max(1.0, arm.recent_beta * self.decay_factor)
            arm.recent_reward *= self.decay_factor
            arm.recent_selections = int(arm.recent_selections * self.decay_factor)

    def _thompson_sampling_allocation(self, theories: list[str]) -> AllocationResult:
        """Thompson Sampling allocation using Beta distributions."""
        samples = {}

        # Sample from each theory's Beta distribution
        for theory_id in theories:
            arm = self.arms[theory_id]
            # Use recent metrics for concept drift adaptation
            sample = self.rng.betavariate(arm.recent_alpha, arm.recent_beta)
            samples[theory_id] = sample

        # Select theory with highest sample
        selected_theory = max(samples.keys(), key=lambda k: samples[k])

        # Calculate allocation weights based on samples
        total_sample = sum(samples.values())
        allocations = {}

        for theory_id in theories:
            base_allocation = (
                samples[theory_id] / total_sample if total_sample > 0 else 1.0 / len(theories)
            )
            # Ensure minimum allocation
            allocations[theory_id] = max(self.min_allocation, base_allocation)

        # Renormalize
        total_allocation = sum(allocations.values())
        allocations = {k: v / total_allocation for k, v in allocations.items()}

        return AllocationResult(
            allocations=allocations,
            selected_theory=selected_theory,
            confidence=samples[selected_theory],
            algorithm_state={
                "samples": samples,
                "beta_parameters": {
                    theory_id: {
                        "alpha": self.arms[theory_id].recent_alpha,
                        "beta": self.arms[theory_id].recent_beta,
                    }
                    for theory_id in theories
                },
            },
        )

    def _ucb1_allocation(self, theories: list[str]) -> AllocationResult:
        """UCB1 allocation with confidence bounds."""
        ucb_values = {}

        for theory_id in theories:
            arm = self.arms[theory_id]

            if arm.recent_selections == 0:
                # Infinite confidence for unselected arms
                ucb_values[theory_id] = float("inf")
            else:
                avg_reward = arm.recent_reward / arm.recent_selections
                confidence_bound = math.sqrt(
                    (2 * math.log(self.total_selections)) / arm.recent_selections
                )
                ucb_values[theory_id] = avg_reward + self.ucb_c * confidence_bound

        # Select theory with highest UCB value
        selected_theory = max(ucb_values.keys(), key=lambda k: ucb_values[k])

        # Convert UCB values to allocation weights
        # Use softmax transformation for smooth allocation
        max_ucb = max(ucb_values.values())
        if max_ucb == float("inf"):
            # Handle infinite values
            exp_values = {
                theory_id: 1.0 if ucb == float("inf") else 0.1
                for theory_id, ucb in ucb_values.items()
            }
        else:
            exp_values = {
                theory_id: math.exp((ucb - max_ucb) / 2.0)  # Temperature = 2.0
                for theory_id, ucb in ucb_values.items()
            }

        total_exp = sum(exp_values.values())
        allocations = {
            theory_id: max(self.min_allocation, exp_val / total_exp)
            for theory_id, exp_val in exp_values.items()
        }

        # Renormalize
        total_allocation = sum(allocations.values())
        allocations = {k: v / total_allocation for k, v in allocations.items()}

        return AllocationResult(
            allocations=allocations,
            selected_theory=selected_theory,
            confidence=ucb_values[selected_theory],
            algorithm_state={
                "ucb_values": ucb_values,
                "avg_rewards": {
                    theory_id: (
                        self.arms[theory_id].recent_reward / self.arms[theory_id].recent_selections
                        if self.arms[theory_id].recent_selections > 0
                        else 0.0
                    )
                    for theory_id in theories
                },
            },
        )

    def _epsilon_greedy_allocation(self, theories: list[str]) -> AllocationResult:
        """Epsilon-greedy allocation."""
        # Calculate average rewards
        avg_rewards = {}
        for theory_id in theories:
            arm = self.arms[theory_id]
            if arm.recent_selections > 0:
                avg_rewards[theory_id] = arm.recent_reward / arm.recent_selections
            else:
                avg_rewards[theory_id] = 0.0

        # Epsilon-greedy selection
        if self.rng.random() < self.epsilon:
            # Explore: random selection
            selected_theory = self.rng.choice(theories)
        else:
            # Exploit: select best theory
            selected_theory = max(avg_rewards.keys(), key=lambda k: avg_rewards[k])

        # Allocation: heavy weight to selected theory, remainder distributed
        allocations = {}
        main_allocation = 1.0 - (len(theories) - 1) * self.min_allocation

        for theory_id in theories:
            if theory_id == selected_theory:
                allocations[theory_id] = main_allocation
            else:
                allocations[theory_id] = self.min_allocation

        return AllocationResult(
            allocations=allocations,
            selected_theory=selected_theory,
            confidence=avg_rewards[selected_theory],
            algorithm_state={
                "avg_rewards": avg_rewards,
                "epsilon": self.epsilon,
                "was_exploration": self.rng.random() < self.epsilon,
            },
        )
