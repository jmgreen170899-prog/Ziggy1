/**
 * API Types Index
 * 
 * Re-exports all generated API types for easy importing
 */

export * from './generated';

// Re-export the original api.ts types for backward compatibility
export type {
  Quote,
  ChartData,
  RiskMetrics,
  TradingSignal,
  PortfolioPosition,
  Portfolio,
  NewsItem,
  CryptoPrice,
  Alert,
  Feedback,
  AdaptationMetrics,
  AnonymizedTradeData,
  TradeDataSubmission,
  ZiggyBrainLearning,
  TradeDataPrivacySettings,
} from '../api';
