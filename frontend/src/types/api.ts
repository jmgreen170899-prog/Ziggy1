// Core API Types matching backend structure

// RAG and Query Types
export interface RAGQueryRequest {
  query: string;
  context?: string;
  max_tokens?: number;
}

export interface RAGQueryResponse {
  response: string;
  sources?: string[];
  confidence?: number;
}

// Agent Types
export interface AgentRequest {
  message: string;
  agent_type?: string;
  context?: Record<string, unknown>;
}

export interface AgentResponse {
  response: string;
  actions?: string[];
  suggestions?: string[];
}

// Market Data Types
export interface Quote {
  symbol: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  high: number;
  low: number;
  open: number;
  close: number;
  timestamp: string;
}

export interface ChartData {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface RiskMetrics {
  var_95: number;
  var_99: number;
  expected_shortfall: number;
  beta: number;
  volatility: number;
  sharpe_ratio: number;
}

// Trading Types
export interface TradingSignal {
  symbol: string;
  signal_type: 'BUY' | 'SELL' | 'HOLD';
  strength: number;
  price_target?: number;
  stop_loss?: number;
  confidence: number;
  timestamp: string;
  reasoning?: string;
}

export interface PortfolioPosition {
  symbol: string;
  quantity: number;
  avg_price: number;
  current_price: number;
  market_value: number;
  pnl: number;
  pnl_percent: number;
}

export interface Portfolio {
  total_value: number;
  cash_balance: number;
  positions: PortfolioPosition[];
  daily_pnl: number;
  daily_pnl_percent: number;
}

// News Types
export interface NewsItem {
  id: string;
  title: string;
  summary: string;
  content: string;
  url: string;
  published_date: string;
  source: string;
  sentiment?: 'positive' | 'negative' | 'neutral';
  sentiment_score?: number;
  symbols?: string[];
}

// Backend News Response Types
export interface BackendNewsItem {
  id: string;
  title: string;
  summary: string;
  url: string;
  published: string;
  date: string;
  source: string;
  label: string;
  score: number;
  symbols: string[];
  tickers: string[];
  site?: string;
  favicon?: string;
  source_id?: string;
}

export interface BackendNewsResponse {
  asof: number;
  count: number;
  items: BackendNewsItem[];
}

// Crypto Types
export interface CryptoPrice {
  symbol: string;
  name: string;
  price: number;
  change_24h: number;
  change_percent_24h: number;
  volume_24h: number;
  market_cap: number;
  rank: number;
}

// Alert Types
export interface Alert {
  id: string;
  type: 'price' | 'volume' | 'news' | 'technical';
  symbol: string;
  condition: string;
  target_value: number;
  current_value: number;
  is_active: boolean;
  created_at: string;
  triggered_at?: string;
  message?: string;
}

// Backend Alert Response Types
export interface BackendAlert {
  id: string;
  type: string;
  symbol: string;
  condition: string;
  target_value: number;
  current_value: number;
  is_active: boolean;
  created_at: string;
  triggered_at?: string;
  message: string;
}

export interface BackendAlertResponse {
  symbols: {
    items: BackendAlert[];
    count: number;
    production: boolean;
    asof: number;
  };
  market_context?: {
    enhanced_by: string;
    symbols_analyzed: number;
    timestamp: string;
  };
}

// Learning Types
export interface Feedback {
  action: string;
  rating: number;
  comment?: string;
  timestamp: string;
}

export interface AdaptationMetrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  last_updated: string;
}

// WebSocket Types
export interface WebSocketMessage {
  type: 'quote' | 'news' | 'alert' | 'signal';
  data: Quote | NewsItem | Alert | TradingSignal;
  timestamp: string;
}

// API Response wrapper
export interface APIResponse<T> {
  data: T;
  success: boolean;
  message?: string;
  timestamp: string;
}

// Chat Types
export interface ChatMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: string;
  sources?: string[];
  confidence?: number;
  isLoading?: boolean;
}

export interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  currentModel?: string;
}

export interface OllamaChatRequest {
  message: string;
  context?: string;
  model?: string;
  temperature?: number;
  stream?: boolean;
}

export interface OllamaChatResponse {
  response: string;
  model: string;
  sources?: string[];
  confidence?: number;
  context?: string;
}

// Privacy-Preserving Trade Data Pipeline for ZiggyAI Brain
export interface AnonymizedTradeData {
  // NO PERSONAL IDENTIFIERS - Only aggregated data patterns
  symbol: string;
  trade_type: 'buy' | 'sell';
  quantity_tier: 'small' | 'medium' | 'large' | 'institutional'; // Bucketed, not exact
  price_tier: 'below_avg' | 'avg' | 'above_avg'; // Relative to market
  time_bucket: string; // Rounded to hour/day for privacy
  strategy_type?: 'momentum' | 'mean_reversion' | 'breakout' | 'fundamental' | 'ai_signal';
  holding_period_tier: 'intraday' | 'short_term' | 'medium_term' | 'long_term';
  market_conditions: {
    volatility_tier: 'low' | 'medium' | 'high';
    volume_tier: 'low' | 'medium' | 'high';
    trend: 'up' | 'down' | 'sideways';
  };
  outcome_tier?: 'loss' | 'breakeven' | 'small_gain' | 'large_gain'; // Added later for learning
  // Hash-based session ID (changes regularly, no persistence to user account)
  session_hash: string;
}

export interface TradeDataSubmission {
  trades: AnonymizedTradeData[];
  market_context: {
    session_start: string;
    market_state: 'pre_market' | 'open' | 'close' | 'after_hours';
    major_events?: string[]; // Earnings, news, etc.
  };
  // Privacy commitment
  privacy_level: 'anonymized' | 'aggregated_only';
  // No user identifiers - data flows to ZiggyAI brain anonymously
}

export interface ZiggyBrainLearning {
  pattern_insights: {
    successful_patterns: string[];
    risk_patterns: string[];
    market_timing_insights: string[];
  };
  model_improvements: {
    prediction_accuracy_delta: number;
    risk_assessment_improvements: string[];
    new_signal_types: string[];
  };
  collective_intelligence: {
    crowd_sentiment_shifts: string[];
    emerging_strategies: string[];
    risk_warnings: string[];
  };
}

export interface TradeDataPrivacySettings {
  anonymization_level: 'full' | 'partial' | 'opt_out';
  data_retention_days: number;
  share_outcomes: boolean; // Whether to share trade outcomes for learning
  share_strategies: boolean; // Whether to share strategy patterns
  geographic_region?: string; // For regulatory compliance only
}