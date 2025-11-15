"""
Episodic Memory System for ZiggyAI

Human-like memory that recalls similar historical market episodes:
1. Stores rich contextual market situations (episodes)
2. Retrieves similar past scenarios using semantic similarity
3. Learns from analogous situations
4. Builds temporal understanding of market patterns
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np


logger = logging.getLogger(__name__)


@dataclass
class MarketEpisode:
    """
    A complete market episode with context and outcome.

    Captures:
    - Market state (prices, volatility, regime)
    - News/sentiment context
    - Decision made and reasoning
    - Outcome and lessons learned
    """

    episode_id: str
    timestamp: str
    ticker: str

    # Market state
    price: float
    volume: float
    volatility: float
    regime: str

    # Technical context
    rsi: float | None = None
    macd: float | None = None
    moving_avg_50: float | None = None
    moving_avg_200: float | None = None

    # Sentiment context
    news_sentiment: float = 0.0  # -1 to 1
    social_sentiment: float = 0.0
    analyst_sentiment: str = "neutral"

    # Decision details
    decision_action: str = "hold"
    decision_confidence: float = 0.5
    decision_reasoning: list[str] = field(default_factory=list)

    # Outcome
    outcome_pnl: float | None = None
    outcome_pnl_percent: float | None = None
    holding_period_hours: float | None = None
    was_successful: bool | None = None

    # Lessons learned
    lessons: list[str] = field(default_factory=list)

    def to_embedding_features(self) -> dict[str, float]:
        """
        Convert episode to features for similarity calculation.

        Returns flat dictionary of numeric features for embedding.
        """
        # Convert regime to numeric
        regime_map = {
            "Panic": -2.0,
            "RiskOff": -1.0,
            "Chop": 0.0,
            "RiskOn": 1.0,
            "Melt": 2.0,
        }

        # Convert sentiment to numeric
        sentiment_map = {
            "very_negative": -2.0,
            "negative": -1.0,
            "neutral": 0.0,
            "positive": 1.0,
            "very_positive": 2.0,
        }

        return {
            "volatility": self.volatility,
            "regime": regime_map.get(self.regime, 0.0),
            "rsi": self.rsi or 50.0,
            "macd": self.macd or 0.0,
            "news_sentiment": self.news_sentiment,
            "social_sentiment": self.social_sentiment,
            "analyst_sentiment": sentiment_map.get(self.analyst_sentiment, 0.0),
            "confidence": self.decision_confidence,
        }


class EpisodicMemory:
    """
    Episodic memory system for case-based reasoning.

    Stores and retrieves similar historical market situations
    to inform current decisions.
    """

    def __init__(self, memory_dir: Path | None = None, max_episodes: int = 10000):
        """
        Initialize episodic memory.

        Args:
            memory_dir: Directory to store episodes
            max_episodes: Maximum number of episodes to keep
        """
        self.memory_dir = memory_dir or Path("data/episodic_memory")
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        self.max_episodes = max_episodes
        self.episodes: list[MarketEpisode] = []

        # Load existing episodes
        self._load_episodes()

        logger.info(f"EpisodicMemory initialized with {len(self.episodes)} episodes")

    def store_episode(self, episode: MarketEpisode) -> None:
        """Store a new market episode in memory."""
        self.episodes.append(episode)

        # Prune old episodes if exceeding max
        if len(self.episodes) > self.max_episodes:
            # Keep most recent episodes
            self.episodes = self.episodes[-self.max_episodes :]

        # Persist to disk periodically (every 10 episodes)
        if len(self.episodes) % 10 == 0:
            self._save_episodes()

    def recall_similar_episodes(
        self, current_context: dict[str, Any], k: int = 5, min_similarity: float = 0.7
    ) -> list[MarketEpisode]:
        """
        Find k most similar past episodes to current context.

        Args:
            current_context: Current market state features
            k: Number of similar episodes to return
            min_similarity: Minimum similarity threshold (0-1)

        Returns:
            List of similar historical episodes
        """
        if not self.episodes:
            return []

        # Convert current context to feature vector
        current_features = self._extract_features(current_context)

        # Calculate similarity to all episodes
        similarities = []
        for episode in self.episodes:
            episode_features = episode.to_embedding_features()
            similarity = self._calculate_similarity(current_features, episode_features)

            if similarity >= min_similarity:
                similarities.append((similarity, episode))

        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x[0], reverse=True)
        return [episode for _, episode in similarities[:k]]

    def _extract_features(self, context: dict[str, Any]) -> dict[str, float]:
        """Extract numeric features from context."""
        # Map regime string to numeric value
        regime_map = {
            "Panic": -2.0,
            "RiskOff": -1.0,
            "Chop": 0.0,
            "RiskOn": 1.0,
            "Melt": 2.0,
        }

        return {
            "volatility": float(context.get("volatility", 0.5)),
            "regime": regime_map.get(context.get("regime", "Chop"), 0.0),
            "rsi": float(context.get("rsi", 50.0)),
            "macd": float(context.get("macd", 0.0)),
            "news_sentiment": float(context.get("news_sentiment", 0.0)),
            "social_sentiment": float(context.get("social_sentiment", 0.0)),
            "analyst_sentiment": float(context.get("analyst_sentiment", 0.0)),
            "confidence": float(context.get("confidence", 0.5)),
        }

    def _calculate_similarity(
        self, features1: dict[str, float], features2: dict[str, float]
    ) -> float:
        """
        Calculate cosine similarity between two feature vectors.

        Returns value between 0 (no similarity) and 1 (identical).
        """
        # Get common keys
        keys = set(features1.keys()) & set(features2.keys())

        if not keys:
            return 0.0

        # Build vectors
        vec1 = np.array([features1[k] for k in keys])
        vec2 = np.array([features2[k] for k in keys])

        # Normalize
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        # Cosine similarity
        similarity = np.dot(vec1, vec2) / (norm1 * norm2)

        # Convert from [-1, 1] to [0, 1]
        return (similarity + 1) / 2

    def get_lessons_from_similar_episodes(
        self, current_context: dict[str, Any], k: int = 3
    ) -> list[str]:
        """
        Get lessons learned from similar past episodes.

        Args:
            current_context: Current market context
            k: Number of similar episodes to consider

        Returns:
            List of relevant lessons
        """
        similar_episodes = self.recall_similar_episodes(current_context, k=k)

        all_lessons = []
        for episode in similar_episodes:
            all_lessons.extend(episode.lessons)

        # Return unique lessons
        return list(set(all_lessons))

    def _save_episodes(self) -> None:
        """Persist episodes to disk."""
        try:
            filepath = self.memory_dir / "episodes.jsonl"

            with open(filepath, "w") as f:
                for episode in self.episodes:
                    episode_dict = {
                        "episode_id": episode.episode_id,
                        "timestamp": episode.timestamp,
                        "ticker": episode.ticker,
                        "price": episode.price,
                        "volume": episode.volume,
                        "volatility": episode.volatility,
                        "regime": episode.regime,
                        "rsi": episode.rsi,
                        "macd": episode.macd,
                        "moving_avg_50": episode.moving_avg_50,
                        "moving_avg_200": episode.moving_avg_200,
                        "news_sentiment": episode.news_sentiment,
                        "social_sentiment": episode.social_sentiment,
                        "analyst_sentiment": episode.analyst_sentiment,
                        "decision_action": episode.decision_action,
                        "decision_confidence": episode.decision_confidence,
                        "decision_reasoning": episode.decision_reasoning,
                        "outcome_pnl": episode.outcome_pnl,
                        "outcome_pnl_percent": episode.outcome_pnl_percent,
                        "holding_period_hours": episode.holding_period_hours,
                        "was_successful": episode.was_successful,
                        "lessons": episode.lessons,
                    }
                    f.write(json.dumps(episode_dict) + "\n")

            logger.debug(f"Saved {len(self.episodes)} episodes to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save episodes: {e}")

    def _load_episodes(self) -> None:
        """Load episodes from disk."""
        filepath = self.memory_dir / "episodes.jsonl"

        if not filepath.exists():
            return

        try:
            with open(filepath) as f:
                for line in f:
                    data = json.loads(line.strip())
                    episode = MarketEpisode(**data)
                    self.episodes.append(episode)

            logger.info(f"Loaded {len(self.episodes)} episodes from {filepath}")
        except Exception as e:
            logger.error(f"Failed to load episodes: {e}")

    def get_stats(self) -> dict[str, Any]:
        """Get memory statistics."""
        if not self.episodes:
            return {"total_episodes": 0, "regimes": {}, "success_rate": 0.0}

        # Count episodes by regime
        regime_counts = {}
        successful_episodes = 0
        total_with_outcome = 0

        for episode in self.episodes:
            regime_counts[episode.regime] = regime_counts.get(episode.regime, 0) + 1

            if episode.was_successful is not None:
                total_with_outcome += 1
                if episode.was_successful:
                    successful_episodes += 1

        success_rate = (
            successful_episodes / total_with_outcome if total_with_outcome > 0 else 0.0
        )

        return {
            "total_episodes": len(self.episodes),
            "regimes": regime_counts,
            "success_rate": success_rate,
            "episodes_with_outcomes": total_with_outcome,
        }
