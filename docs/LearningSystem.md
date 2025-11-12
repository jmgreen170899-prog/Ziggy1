# Ziggy AI - Strict Learning & Adaptation System

## Overview

Ziggy's strict learning system implements a conservative, auditable learning pipeline that adapts RULE PARAMETERS (not black-box weights) using collected trade/market data. All adaptations must pass strict, pre-declared gates using out-of-sample evaluation before being promoted to "active" status.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   STRICT LEARNING PIPELINE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│  │ Data Logger │───▶│ Evaluation  │───▶│ Calibration │        │
│  │             │    │             │    │             │        │
│  │ • Decisions │    │ • Metrics   │    │ • Isotonic  │        │
│  │ • Outcomes  │    │ • Brier     │    │ • Platt     │        │
│  │ • Features  │    │ • Sharpe    │    │ • Curves    │        │
│  │ • Context   │    │ • Drawdown  │    │ • Reports   │        │
│  └─────────────┘    └─────────────┘    └─────────────┘        │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                 STRICT LEARNER                         │   │
│  │                                                         │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │   │
│  │  │   GENERATE   │  │   VALIDATE   │  │    GATES     │  │   │
│  │  │              │  │              │  │              │  │   │
│  │  │ • Parameter  │  │ • Train/Val/ │  │ • Min Trades │  │   │
│  │  │   Variations │  │   Test Split │  │ • Sharpe +   │  │   │
│  │  │ • Grid       │  │ • Calibrate  │  │ • Brier ↓    │  │   │
│  │  │   Search     │  │ • Evaluate   │  │ • Drawdown   │  │   │
│  │  │ • Rules      │  │ • Compare    │  │ • Hit Rate   │  │   │
│  │  │   Versioning │  │ • Bootstrap  │  │ • PSI Drift  │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  API LAYER                              │   │
│  │                                                         │   │
│  │  • /learning/status      • /learning/run               │   │
│  │  • /learning/rules/*     • /learning/results/*         │   │
│  │  • /learning/gates       • /learning/calibration/*     │   │
│  │  • /learning/evaluate/*  • /learning/health            │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Data Logger (`app/services/data_log.py`)

**Purpose**: Capture every live trading decision with complete context for later analysis.

**Features**:
- Append-only storage with monthly rotation
- Parquet format with CSV fallback
- Full decision context: features, parameters, regime, probabilities
- Outcome tracking: PnL, fees, slippage, exit reasons
- Chronological integrity for time-series analysis

**Data Structure**:
```python
@dataclass
class TradingDecisionRecord:
    timestamp: float
    ticker: str
    regime: str
    features_used: Dict[str, float]
    signal_name: str
    params_used: Dict[str, Any]
    predicted_prob: Optional[float]
    position_qty: float
    entry_price: float
    stop_price: Optional[float]
    take_profit: Optional[float]
    
    # Outcomes (filled after completion)
    outcome_after_1h: Optional[float]
    outcome_after_4h: Optional[float] 
    outcome_after_24h: Optional[float]
    exit_price: Optional[float]
    fees_paid: Optional[float]
    slippage: Optional[float]
    exit_reason: Optional[str]
    realized_pnl: Optional[float]
    
    # Versioning
    rule_version: str
    signal_version: str
```

### 2. Evaluation Engine (`app/services/evaluation.py`)

**Purpose**: Calculate comprehensive performance metrics with statistical significance.

**Metrics Calculated**:
- **Performance**: Hit rate, expectancy, total PnL, Sharpe ratio, Sortino ratio
- **Risk**: Maximum drawdown, Calmar ratio, drawdown duration
- **Calibration**: Brier score, calibration slope/intercept, reliability diagrams
- **Stability**: Population Stability Index (PSI) for feature drift
- **Statistical**: Bootstrap confidence intervals, significance tests

**Key Functions**:
- `evaluate_trading_performance()`: Comprehensive metric calculation
- `compare_runs()`: Statistical comparison between baseline and candidate
- `bootstrap_confidence_interval()`: Statistical significance testing

### 3. Calibration System (`app/services/calibration.py`)

**Purpose**: Ensure predicted probabilities match actual outcomes.

**Methods**:
- **Isotonic Regression**: Non-parametric, monotonic calibration
- **Platt Scaling**: Sigmoid-based parametric calibration

**Features**:
- Train/test validation splits
- Reliability diagram generation
- Calibration curve analysis
- Model persistence and loading

**Quality Metrics**:
- Calibration slope (ideal: 1.0)
- Calibration intercept (ideal: 0.0)
- Mean squared error from perfect calibration
- Brier score improvement

### 4. Strict Learner (`app/services/learner.py`)

**Purpose**: Optimize rule parameters with rigorous validation gates.

**Rule Parameters**:
- RSI thresholds (oversold/overbought)
- ATR stop multipliers
- Regime strength thresholds
- Signal-specific parameters

**Learning Pipeline**:
1. **Data Split**: Chronological 60% train / 20% validation / 20% test
2. **Candidate Generation**: Small parameter variations around current values
3. **Validation**: Fit calibration on train, select best on validation
4. **Testing**: Evaluate top candidate on held-out test set
5. **Gate Checking**: All strict gates must pass for promotion

**Strict Validation Gates**:
```python
@dataclass
class StrictGates:
    min_trades: int = 200                    # Minimum sample size
    min_sharpe_improvement_abs: float = 0.20  # Absolute Sharpe improvement
    min_sharpe_improvement_rel: float = 0.15  # Relative Sharpe improvement
    max_brier_score_improvement: float = 0.02 # Calibration improvement
    calibration_slope_range: tuple = (0.8, 1.2)  # Calibration quality
    max_drawdown_deterioration_rel: float = 0.10  # Risk control
    hit_rate_significance_p: float = 0.05     # Statistical significance
    max_psi_threshold: float = 0.25          # Feature drift control
    max_daily_turnover_cap: float = 50.0     # Trading frequency cap
```

### 5. API Layer (`app/api/routes_learning.py`)

**Endpoints**:

#### System Status
- `GET /learning/status` - Overall system health and readiness
- `GET /learning/health` - Detailed health diagnostics

#### Data Management
- `GET /learning/data/summary?days=90` - Available learning data summary

#### Rule Management
- `GET /learning/rules/current` - Active rule set
- `GET /learning/rules/history` - Rule version history

#### Learning Operations
- `POST /learning/run` - Execute learning iteration (background)
- `GET /learning/results/latest` - Most recent learning results
- `GET /learning/results/history?limit=20` - Learning history

#### Configuration
- `GET /learning/gates` - Current validation gates
- `PUT /learning/gates` - Update validation gates

#### Calibration
- `GET /learning/calibration/status` - Calibration model status
- `POST /learning/calibration/build?days=90` - Build calibration model

#### Evaluation
- `GET /learning/evaluate/current?days=30` - Current performance metrics

## Usage Examples

### 1. Basic Learning Workflow

```python
from app.services.learner import StrictLearner, create_default_rule_set

# Initialize learner
learner = StrictLearner(data_window_days=180)

# Get current rules
current_rules = create_default_rule_set()

# Run learning iteration
result = learner.learn_iteration(current_rules)

print(f"Result: {result.recommendation}")
print(f"Passed gates: {result.passed_gates}")
print(f"Gate results: {result.gate_results}")
```

### 2. Data Logging Integration

```python
from app.services.data_log import log_trading_decision, update_trading_outcome

# Log a trading decision
timestamp = log_trading_decision(
    ticker="AAPL",
    regime="bull", 
    features={"rsi": 30.5, "atr": 2.1},
    signal_name="momentum_breakout",
    params={"rsi_threshold": 30, "atr_multiplier": 2.0},
    position_qty=100,
    entry_price=150.25,
    predicted_prob=0.65
)

# Later, update with outcome
update_trading_outcome(
    decision_timestamp=timestamp,
    ticker="AAPL",
    exit_price=154.80,
    realized_pnl=455.0,
    fees_paid=2.0,
    exit_reason="take_profit"
)
```

### 3. API Usage

```bash
# Check system status
curl http://localhost:8000/learning/status

# Get current rules
curl http://localhost:8000/learning/rules/current

# Run learning iteration
curl -X POST http://localhost:8000/learning/run

# Check latest results
curl http://localhost:8000/learning/results/latest
```

## Data Storage Structure

```
data/
├── logs/                    # Trading decision logs
│   ├── 2025-01/
│   │   └── trading_decisions.parquet
│   ├── 2025-02/
│   │   └── trading_decisions.parquet
│   └── ...
├── rules/                   # Rule versions
│   ├── v1.0_default.json
│   ├── v1.1_optimized.json
│   └── ...
├── learning/               # Learning results
│   ├── learning_20250118_143022_v1.1.json
│   └── ...
└── models/                 # Calibration models
    └── calibrator.pkl
```

## Safety Features

### 1. Conservative Gates
All improvements must pass **ALL** validation gates simultaneously:
- Statistical significance required
- Minimum sample size enforced
- Risk deterioration limits
- Feature drift monitoring
- Calibration quality checks

### 2. Out-of-Sample Testing
- Strict chronological splits (no look-ahead bias)
- Final evaluation on held-out test set
- Bootstrap confidence intervals

### 3. Versioning & Rollback
- Full rule version history
- Parent-child relationships tracked
- Easy rollback to previous versions
- Audit trail for all changes

### 4. Interpretability
- Only rule parameters optimized (no black boxes)
- Clear parameter ranges and meanings
- Full explanation of changes
- Human-readable reports

## Monitoring & Alerts

The system continuously monitors:
- Data freshness and quality
- Trading frequency within limits
- Feature drift detection
- Calibration model staleness
- Learning iteration frequency

Health status is exposed via `/learning/health` endpoint with actionable recommendations.

## Integration Points

### With Existing Ziggy Systems:
1. **Signal Generation**: Parameters feed into signal calculations
2. **Risk Management**: Stop-loss and position sizing rules
3. **Regime Detection**: Regime-specific parameter sets
4. **Market Brain**: Enhanced with learning insights

### External Integration:
1. **Trading Platforms**: Real-time parameter updates
2. **Monitoring Systems**: Health and performance metrics
3. **Notification Systems**: Learning results and alerts
4. **UI Dashboard**: Visual learning progress and controls

## Best Practices

1. **Regular Learning**: Run iterations weekly or after significant market events
2. **Gate Tuning**: Adjust validation gates based on market conditions
3. **Data Quality**: Ensure complete outcome tracking for all decisions
4. **Calibration**: Rebuild calibration models monthly or after regime changes
5. **Monitoring**: Set up alerts for system health degradation

## Troubleshooting

Common issues and solutions:

1. **Insufficient Data**: Wait for more trading activity
2. **All Gates Failing**: Relax gates or improve base strategy
3. **Feature Drift**: Investigate market regime changes
4. **Poor Calibration**: Increase calibration training data
5. **High Turnover**: Adjust frequency caps or strategy parameters

## Future Enhancements

1. **Multi-Asset Learning**: Asset-specific parameter sets
2. **Regime-Aware Learning**: Different parameters per market regime
3. **Ensemble Methods**: Multiple calibration models
4. **Real-Time Adaptation**: Faster learning cycles
5. **Advanced Gates**: More sophisticated validation criteria