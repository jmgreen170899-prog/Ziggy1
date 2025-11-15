// Core Predictive AI Types for ZiggyClean Frontend

// Prediction Types
export interface Prediction {
  id: string;
  symbol: string;
  timeframe: "5m" | "15m" | "1h" | "4h" | "1d" | "1w";
  signal: "bullish" | "bearish" | "neutral";
  confidence: number; // 0-100
  expectedMovePct: number;
  rationale: string[];
  quality: number; // 0-100 model quality score
  createdAt: string;
  expiresAt: string;
  evidence: {
    technicalWeight: number; // 0-100
    fundamentalWeight: number; // 0-100
    sentimentWeight: number; // 0-100
    macroWeight: number; // 0-100
  };
  riskReward: {
    probability: number; // 0-100
    expectedReturn: number; // Expected % return
    maxDrawdown: number; // Max % drawdown
    sharpeRatio: number;
  };
}

// Trading Plan Types
export interface TradingPlan {
  id: string;
  symbol: string;
  predictionId: string;
  entry: number;
  stop: number;
  target: number;
  atr: number; // Average True Range
  riskAmount: number; // Dollar risk amount
  rMultiple: number; // Risk-reward multiple
  size: number; // Position size
  accountRiskPct: number; // % of account at risk
  status: "draft" | "approved" | "executed" | "cancelled";
  createdAt: string;
  approvedAt?: string;
  executedAt?: string;
  notes?: string;
}

// Evidence and Supporting Data
export interface Evidence {
  predictionId: string;
  sentiment: {
    score: number; // -1 to 1
    label: "bearish" | "neutral" | "bullish";
    sources: number; // Number of sources analyzed
    confidence: number; // 0-100
  };
  headlines: Array<{
    title: string;
    source: string;
    date: string;
    url: string;
    sentiment: number; // -1 to 1
    relevance: number; // 0-100
    impact: "low" | "medium" | "high";
  }>;
  indicators: {
    rsi: { value: number; signal: "oversold" | "neutral" | "overbought" };
    macd: {
      value: number;
      signal: number;
      histogram: number;
      trend: "bullish" | "bearish";
    };
    sma50: number;
    sma200: number;
    volume_ratio: number; // Current vs average volume
    atr: number;
    volatility: number;
  };
  history: {
    similarSetups: Array<{
      date: string;
      outcome: "win" | "loss";
      movePercent: number;
      similarity: number; // 0-100
      timeframe: string;
    }>;
    successRate: number; // 0-100
    avgReturn: number; // Average % return
    avgHoldTime: string; // Average holding period
  };
  patterns: {
    chartPattern?: string;
    supportLevel?: number;
    resistanceLevel?: number;
    trendDirection: "up" | "down" | "sideways";
    strength: number; // 0-100
  };
}

// AI Agent Action Queue
export interface AgentAction {
  id: string;
  type: "monitor" | "alert" | "plan" | "execute" | "research" | "analyze";
  symbol: string;
  priority: "low" | "medium" | "high" | "urgent";
  payload: Record<string, unknown>;
  status:
    | "pending"
    | "in_progress"
    | "completed"
    | "failed"
    | "requires_approval";
  eta?: string;
  progress?: number; // 0-100
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
  result?: string;
  error?: string;
  requiresApproval: boolean;
  approvedBy?: string;
  approvedAt?: string;
}

// Scenario Simulation
export interface ScenarioResult {
  id: string;
  symbol: string;
  basePrice: number;
  scenarios: Array<{
    priceChange: number; // % change
    probability: number; // 0-100
    pnl: number; // Dollar P&L
    timeframe: string;
  }>;
  statistics: {
    expectedValue: number;
    worstCase: number;
    bestCase: number;
    breakeven: number;
    probabilityOfProfit: number;
    maxDrawdown: number;
  };
  params: {
    volatility: number;
    timeDecay: number;
    priceRange: { min: number; max: number };
  };
}

// Calendar and Scheduling
export interface CalendarEvent {
  id: string;
  type:
    | "prediction_expiry"
    | "model_refresh"
    | "macro_guard"
    | "earnings"
    | "fed_meeting";
  title: string;
  description?: string;
  symbol?: string;
  date: string;
  time?: string;
  importance: "low" | "medium" | "high";
  status: "upcoming" | "active" | "completed";
  impact?: "bullish" | "bearish" | "neutral";
}

// Model Quality and Monitoring
export interface ModelMetrics {
  id: string;
  modelName: string;
  timeframe: string;
  metrics: {
    accuracy: number; // 0-100
    precision: number; // 0-100
    recall: number; // 0-100
    f1Score: number; // 0-100
    sharpeRatio: number;
    winRate: number; // 0-100
    avgReturn: number;
    maxDrawdown: number;
  };
  drift: {
    detected: boolean;
    severity: "low" | "medium" | "high";
    lastDetected?: string;
    recommendation: string;
  };
  performance: {
    last7Days: number; // 0-100
    last30Days: number; // 0-100
    last90Days: number; // 0-100
    ytd: number; // 0-100
  };
  status: "healthy" | "warning" | "critical";
  lastUpdated: string;
  nextUpdate: string;
}

// Portfolio Risk Analytics
export interface RiskAnalytics {
  portfolioId: string;
  totalRisk: number; // Total portfolio risk %
  concentration: {
    sectors: Array<{ name: string; allocation: number; risk: number }>;
    positions: Array<{ symbol: string; allocation: number; risk: number }>;
  };
  metrics: {
    var95: number; // Value at Risk 95%
    var99: number; // Value at Risk 99%
    expectedShortfall: number;
    beta: number;
    correlation: number;
    sharpeRatio: number;
  };
  alerts: Array<{
    type: "concentration" | "var_breach" | "correlation_spike";
    severity: "low" | "medium" | "high";
    message: string;
    date: string;
  }>;
  recommendations: string[];
}

// Macro Economic Context
export interface MacroContext {
  id: string;
  regime: {
    current: "risk_on" | "risk_off" | "transitional";
    confidence: number; // 0-100
    duration: string; // How long in current regime
    nextChange?: string; // Predicted regime change
  };
  indicators: {
    vix: {
      value: number;
      trend: "up" | "down";
      signal: "low" | "normal" | "high";
    };
    yield10y: { value: number; trend: "up" | "down" };
    dxy: { value: number; trend: "up" | "down" };
    commodities: { value: number; trend: "up" | "down" };
  };
  guards: Array<{
    name: string;
    active: boolean;
    type: "volatility" | "liquidity" | "correlation" | "sentiment";
    threshold: number;
    current: number;
    triggered?: string;
  }>;
  outlook: {
    bullish: number; // 0-100
    bearish: number; // 0-100
    neutral: number; // 0-100
    timeframe: "1w" | "1m" | "3m" | "6m";
  };
}

// Enhanced News Analysis
export interface NewsAnalysis {
  id: string;
  symbol?: string;
  timeframe: string;
  sentiment: {
    overall: number; // -1 to 1
    trend: "improving" | "deteriorating" | "stable";
    velocity: number; // Rate of change
    sources: {
      mainstream: number;
      social: number;
      analyst: number;
      insider: number;
    };
  };
  topics: Array<{
    name: string;
    relevance: number; // 0-100
    sentiment: number; // -1 to 1
    frequency: number; // Mention frequency
  }>;
  impact: {
    short_term: "bullish" | "bearish" | "neutral";
    medium_term: "bullish" | "bearish" | "neutral";
    long_term: "bullish" | "bearish" | "neutral";
    confidence: number; // 0-100
  };
  signals: Array<{
    type: "momentum" | "reversal" | "continuation";
    strength: number; // 0-100
    timeframe: string;
  }>;
}

// Market Regime Detection
export interface MarketRegime {
  id: string;
  name: string;
  description: string;
  current: boolean;
  probability: number; // 0-100
  characteristics: {
    volatility: "low" | "medium" | "high";
    correlation: "low" | "medium" | "high";
    momentum: "strong" | "weak" | "neutral";
    trend: "bull" | "bear" | "sideways";
  };
  duration: {
    typical: string;
    current?: string;
    remaining?: string;
  };
  strategies: Array<{
    name: string;
    performance: number; // Expected performance in this regime
    allocation: number; // Recommended allocation %
  }>;
  indicators: Array<{
    name: string;
    value: number;
    threshold: number;
    status: "bullish" | "bearish" | "neutral";
  }>;
}
