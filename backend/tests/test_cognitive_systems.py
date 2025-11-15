"""
Tests for cognitive enhancement systems.

Tests:
- Meta-learning strategy selection and evolution
- Counterfactual reasoning and opportunity cost analysis
- Episodic memory recall and similarity matching
- Cognitive hub integration
"""

import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from app.cognitive.cognitive_hub import CognitiveHub
from app.cognitive.counterfactual import (
    ActionType,
    CounterfactualEngine,
    Outcome,
    TradingDecision,
)
from app.cognitive.episodic_memory import EpisodicMemory, MarketEpisode
from app.cognitive.meta_learner import MetaLearner


class TestMetaLearner:
    """Tests for meta-learning system."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def meta_learner(self, temp_dir):
        """Create meta-learner instance."""
        return MetaLearner(strategies_dir=temp_dir, evolution_frequency=10)

    def test_initialization(self, meta_learner):
        """Test meta-learner initializes with default strategies."""
        assert len(meta_learner.strategies) >= 4
        assert "balanced_default" in meta_learner.strategies
        assert "momentum_aggressive" in meta_learner.strategies

    def test_strategy_selection(self, meta_learner):
        """Test strategy selection for different regimes."""
        strategy = meta_learner.select_strategy("RiskOn")
        assert strategy is not None
        assert strategy.name in meta_learner.strategies

    def test_performance_update(self, meta_learner):
        """Test updating strategy performance."""
        strategy_name = "balanced_default"
        initial_predictions = meta_learner.strategies[strategy_name].total_predictions

        meta_learner.update_strategy_performance(
            strategy_name, correct=True, profit=100.0, regime="RiskOn"
        )

        assert (
            meta_learner.strategies[strategy_name].total_predictions
            == initial_predictions + 1
        )
        assert meta_learner.strategies[strategy_name].total_profit == 100.0

    def test_strategy_evolution(self, meta_learner):
        """Test strategy evolution through genetic programming."""
        # Update strategies enough times to trigger evolution
        for i in range(10):
            meta_learner.update_strategy_performance(
                "balanced_default",
                correct=i % 2 == 0,
                profit=float(i * 10),
                regime="RiskOn",
            )

        # Should have evolved at least one new strategy
        evolved_strategies = [
            s for s in meta_learner.strategies.values() if s.generation > 0
        ]
        assert len(evolved_strategies) > 0

    def test_regime_specific_accuracy(self, meta_learner):
        """Test tracking regime-specific performance."""
        # Add performance for specific regime
        for i in range(5):
            meta_learner.update_strategy_performance(
                "balanced_default", correct=True, profit=10.0, regime="Panic"
            )

        strategy = meta_learner.strategies["balanced_default"]
        panic_accuracy = strategy.get_regime_accuracy("Panic")
        assert panic_accuracy == 1.0  # All correct


class TestCounterfactualEngine:
    """Tests for counterfactual reasoning engine."""

    @pytest.fixture
    def engine(self):
        """Create counterfactual engine."""
        return CounterfactualEngine(enable_shadow_portfolios=True)

    @pytest.fixture
    def sample_decision(self):
        """Create sample trading decision."""
        return TradingDecision(
            timestamp=datetime.utcnow().isoformat(),
            ticker="AAPL",
            action=ActionType.BUY,
            quantity=100,
            entry_price=150.0,
            market_regime="RiskOn",
            confidence=0.75,
            reasoning=["Strong momentum", "Positive news"],
        )

    @pytest.fixture
    def sample_outcome(self):
        """Create sample outcome."""
        return Outcome(
            decision_id="AAPL_test",
            exit_timestamp=datetime.utcnow().isoformat(),
            exit_price=155.0,
            pnl=500.0,
            pnl_percent=3.33,
            holding_period_hours=24.0,
        )

    def test_initialization(self, engine):
        """Test engine initializes with shadow portfolios."""
        assert len(engine.shadow_portfolios) > 0
        assert "always_buy" in engine.shadow_portfolios
        assert "opposite_action" in engine.shadow_portfolios

    def test_counterfactual_analysis(self, engine, sample_decision, sample_outcome):
        """Test counterfactual analysis of a decision."""
        current_prices = {"AAPL": 155.0}

        analysis = engine.analyze_decision(
            sample_decision, sample_outcome, current_prices
        )

        assert analysis is not None
        assert len(analysis.counterfactuals) > 0
        assert analysis.best_alternative is not None
        assert analysis.regret_score >= 0

    def test_opportunity_cost_calculation(
        self, engine, sample_decision, sample_outcome
    ):
        """Test opportunity cost calculation."""
        current_prices = {"AAPL": 160.0}  # Price went up more

        analysis = engine.analyze_decision(
            sample_decision, sample_outcome, current_prices
        )

        # Should identify opportunities if price moved favorably
        assert analysis.total_opportunity_cost >= 0

    def test_shadow_portfolio_tracking(self, engine, sample_decision):
        """Test shadow portfolios track alternative strategies."""
        current_prices = {"AAPL": 155.0}

        # Execute decision in shadow portfolios
        engine._update_shadow_portfolios(sample_decision, current_prices)

        # Check portfolios updated
        for portfolio in engine.shadow_portfolios.values():
            assert portfolio.total_trades >= 0  # At least initialized

    def test_aggregate_insights(self, engine, sample_decision, sample_outcome):
        """Test aggregate insights from multiple analyses."""
        current_prices = {"AAPL": 155.0}

        # Analyze multiple decisions
        for i in range(3):
            engine.analyze_decision(sample_decision, sample_outcome, current_prices)

        insights = engine.get_aggregate_insights()
        assert insights["decisions_analyzed"] == 3
        assert "avg_regret" in insights


class TestEpisodicMemory:
    """Tests for episodic memory system."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def memory(self, temp_dir):
        """Create episodic memory."""
        return EpisodicMemory(memory_dir=temp_dir)

    @pytest.fixture
    def sample_episode(self):
        """Create sample market episode."""
        return MarketEpisode(
            episode_id="test_1",
            timestamp=datetime.utcnow().isoformat(),
            ticker="AAPL",
            price=150.0,
            volume=1000000,
            volatility=0.3,
            regime="RiskOn",
            rsi=65.0,
            macd=2.5,
            news_sentiment=0.7,
            social_sentiment=0.6,
            analyst_sentiment="positive",
            decision_action="buy",
            decision_confidence=0.8,
            decision_reasoning=["Strong momentum"],
            outcome_pnl=500.0,
            outcome_pnl_percent=3.33,
            holding_period_hours=24.0,
            was_successful=True,
            lessons=["Buy on momentum in RiskOn regime"],
        )

    def test_store_episode(self, memory, sample_episode):
        """Test storing episodes in memory."""
        initial_count = len(memory.episodes)
        memory.store_episode(sample_episode)
        assert len(memory.episodes) == initial_count + 1

    def test_recall_similar_episodes(self, memory, sample_episode):
        """Test recalling similar episodes."""
        # Store sample episode
        memory.store_episode(sample_episode)

        # Create similar context
        context = {
            "volatility": 0.35,
            "regime": "RiskOn",
            "rsi": 68.0,
            "macd": 2.8,
            "news_sentiment": 0.75,
            "social_sentiment": 0.65,
            "analyst_sentiment": 0.8,
            "confidence": 0.82,
        }

        # Recall similar
        similar = memory.recall_similar_episodes(context, k=1, min_similarity=0.5)

        assert len(similar) > 0
        assert similar[0].ticker == "AAPL"

    def test_similarity_calculation(self, memory):
        """Test feature similarity calculation."""
        features1 = {"volatility": 0.3, "regime": 1.0, "rsi": 65.0}
        features2 = {"volatility": 0.35, "regime": 1.0, "rsi": 68.0}

        similarity = memory._calculate_similarity(features1, features2)
        assert 0.0 <= similarity <= 1.0
        assert similarity > 0.8  # Should be very similar

    def test_lessons_retrieval(self, memory, sample_episode):
        """Test retrieving lessons from similar episodes."""
        memory.store_episode(sample_episode)

        context = {
            "volatility": 0.3,
            "regime": "RiskOn",
            "rsi": 65.0,
            "confidence": 0.8,
        }

        lessons = memory.get_lessons_from_similar_episodes(context, k=1)
        assert len(lessons) > 0
        assert "Buy on momentum in RiskOn regime" in lessons

    def test_memory_persistence(self, temp_dir):
        """Test saving and loading episodes."""
        # Create memory and store episode
        memory1 = EpisodicMemory(memory_dir=temp_dir)
        episode = MarketEpisode(
            episode_id="persist_test",
            timestamp=datetime.utcnow().isoformat(),
            ticker="AAPL",
            price=150.0,
            volume=1000000,
            volatility=0.3,
            regime="RiskOn",
        )
        memory1.store_episode(episode)
        memory1._save_episodes()

        # Create new memory instance and load
        memory2 = EpisodicMemory(memory_dir=temp_dir)
        assert len(memory2.episodes) > 0


class TestCognitiveHub:
    """Tests for cognitive hub integration."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def hub(self, temp_dir):
        """Create cognitive hub."""
        return CognitiveHub(
            data_dir=temp_dir,
            enable_meta_learning=True,
            enable_counterfactual=True,
            enable_episodic_memory=True,
        )

    def test_hub_initialization(self, hub):
        """Test hub initializes all subsystems."""
        assert hub.meta_learner is not None
        assert hub.counterfactual_engine is not None
        assert hub.episodic_memory is not None

    def test_decision_enhancement(self, hub):
        """Test enhancing decisions with cognitive intelligence."""
        market_context = {
            "regime": "RiskOn",
            "volatility": 0.3,
            "rsi": 65.0,
            "macd": 2.5,
            "news_sentiment": 0.7,
            "confidence": 0.8,
        }

        enhanced = hub.enhance_decision(
            ticker="AAPL",
            proposed_action="buy",
            market_context=market_context,
            confidence=0.75,
        )

        assert "ticker" in enhanced
        assert "meta_learning" in enhanced
        assert "cognitive_insights" in enhanced
        assert len(enhanced["cognitive_insights"]) > 0

    def test_outcome_recording(self, hub):
        """Test recording decision outcomes."""
        market_context = {"regime": "RiskOn", "volatility": 0.3, "volume": 1000000}

        # Should not raise exception
        hub.record_decision_outcome(
            ticker="AAPL",
            action="BUY",
            entry_price=150.0,
            quantity=100,
            market_context=market_context,
            confidence=0.75,
            reasoning=["Strong momentum"],
            outcome_pnl=500.0,
            outcome_pnl_percent=3.33,
            holding_period_hours=24.0,
            current_prices={"AAPL": 155.0},
        )

        # Check systems were updated
        assert hub.meta_learner.state.strategies_evaluated > 0
        assert len(hub.episodic_memory.episodes) > 0

    def test_system_status(self, hub):
        """Test getting system status."""
        status = hub.get_system_status()

        assert "cognitive_hub" in status
        assert "subsystems" in status
        assert "meta_learning" in status["subsystems"]
        assert "counterfactual" in status["subsystems"]
        assert "episodic_memory" in status["subsystems"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
