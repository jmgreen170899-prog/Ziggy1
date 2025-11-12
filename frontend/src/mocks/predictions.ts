import type { Prediction } from './types';

// Mock predictions data for ZiggyClean AI Trading Platform
export const mockPredictions: Prediction[] = [
  {
    id: 'pred_001',
    symbol: 'NVDA',
    timeframe: '1d',
    signal: 'bullish',
    confidence: 87,
    expectedMovePct: 8.5,
    rationale: [
      'Strong earnings beat with 94% revenue growth driven by AI demand',
      'Technical breakout above $850 resistance with volume confirmation',
      'RSI showing bullish divergence after oversold bounce',
      'Institutional accumulation pattern detected in options flow',
      'Sector rotation favoring AI/semiconductor plays continues'
    ],
    quality: 92,
    createdAt: new Date().toISOString(),
    expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 days
    evidence: {
      technicalWeight: 35,
      fundamentalWeight: 40,
      sentimentWeight: 15,
      macroWeight: 10
    },
    riskReward: {
      probability: 72,
      expectedReturn: 8.5,
      maxDrawdown: -3.2,
      sharpeRatio: 2.1
    }
  },
  {
    id: 'pred_002',
    symbol: 'TSLA',
    timeframe: '4h',
    signal: 'bearish',
    confidence: 79,
    expectedMovePct: -5.8,
    rationale: [
      'Shanghai production bottlenecks impacting Q4 delivery targets',
      'Technical rejection at $200 resistance forming lower high',
      'Negative sentiment from supply chain disruption news',
      'EV competition intensifying with new model launches',
      'Macro headwinds from rising interest rates affecting growth stocks'
    ],
    quality: 85,
    createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
    expiresAt: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString(), // 2 days
    evidence: {
      technicalWeight: 30,
      fundamentalWeight: 35,
      sentimentWeight: 25,
      macroWeight: 10
    },
    riskReward: {
      probability: 68,
      expectedReturn: -5.8,
      maxDrawdown: -8.2,
      sharpeRatio: 1.8
    }
  },
  {
    id: 'pred_003',
    symbol: 'AAPL',
    timeframe: '1h',
    signal: 'neutral',
    confidence: 71,
    expectedMovePct: 1.2,
    rationale: [
      'Mixed signals from iPhone 16 AI features announcement',
      'Trading in consolidation range between $150-$158',
      'Earnings momentum positive but priced in',
      'Services growth steady but not accelerating',
      'Waiting for clear directional catalyst'
    ],
    quality: 78,
    createdAt: new Date(Date.now() - 30 * 60 * 1000).toISOString(), // 30 minutes ago
    expiresAt: new Date(Date.now() + 4 * 60 * 60 * 1000).toISOString(), // 4 hours
    evidence: {
      technicalWeight: 40,
      fundamentalWeight: 30,
      sentimentWeight: 20,
      macroWeight: 10
    },
    riskReward: {
      probability: 55,
      expectedReturn: 1.2,
      maxDrawdown: -2.1,
      sharpeRatio: 0.9
    }
  },
  {
    id: 'pred_004',
    symbol: 'MSFT',
    timeframe: '1d',
    signal: 'bullish',
    confidence: 83,
    expectedMovePct: 6.2,
    rationale: [
      'Azure cloud growth accelerating with 29% QoQ growth',
      'AI integration across Office suite driving enterprise adoption',
      'Strong technical setup with break above $310 resistance',
      'Relative strength vs SPY indicating institutional interest',
      'Management guidance raised for cloud segment'
    ],
    quality: 89,
    createdAt: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(), // 4 hours ago
    expiresAt: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString(), // 5 days
    evidence: {
      technicalWeight: 25,
      fundamentalWeight: 45,
      sentimentWeight: 20,
      macroWeight: 10
    },
    riskReward: {
      probability: 75,
      expectedReturn: 6.2,
      maxDrawdown: -2.8,
      sharpeRatio: 2.3
    }
  },
  {
    id: 'pred_005',
    symbol: 'GOOGL',
    timeframe: '1d',
    signal: 'bullish',
    confidence: 76,
    expectedMovePct: 4.8,
    rationale: [
      'Search revenue stabilizing after AI concerns overdone',
      'YouTube advertising showing resilience vs competitors',
      'Cloud division margin expansion ahead of expectations',
      'Bard AI integration creating new revenue opportunities',
      'Valuation attractive vs growth tech peers'
    ],
    quality: 82,
    createdAt: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(), // 6 hours ago
    expiresAt: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(), // 3 days
    evidence: {
      technicalWeight: 30,
      fundamentalWeight: 40,
      sentimentWeight: 20,
      macroWeight: 10
    },
    riskReward: {
      probability: 69,
      expectedReturn: 4.8,
      maxDrawdown: -3.5,
      sharpeRatio: 1.7
    }
  },
  {
    id: 'pred_006',
    symbol: 'AMD',
    timeframe: '4h',
    signal: 'bearish',
    confidence: 74,
    expectedMovePct: -4.2,
    rationale: [
      'Intel competition intensifying with new CPU releases',
      'Data center market share pressure from NVIDIA AI chips',
      'Technical weakness with break below $120 support',
      'Analyst downgrades citing margin compression concerns',
      'Semiconductor cycle showing signs of maturation'
    ],
    quality: 80,
    createdAt: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(), // 1 hour ago
    expiresAt: new Date(Date.now() + 18 * 60 * 60 * 1000).toISOString(), // 18 hours
    evidence: {
      technicalWeight: 35,
      fundamentalWeight: 30,
      sentimentWeight: 25,
      macroWeight: 10
    },
    riskReward: {
      probability: 66,
      expectedReturn: -4.2,
      maxDrawdown: -6.8,
      sharpeRatio: 1.5
    }
  }
];

// Helper function to get predictions by symbol
export function getPredictionsBySymbol(symbol: string): Prediction[] {
  return mockPredictions.filter(pred => pred.symbol === symbol);
}

// Helper function to get predictions by timeframe
export function getPredictionsByTimeframe(timeframe: string): Prediction[] {
  return mockPredictions.filter(pred => pred.timeframe === timeframe);
}

// Helper function to get high-confidence predictions
export function getHighConfidencePredictions(minConfidence: number = 80): Prediction[] {
  return mockPredictions.filter(pred => pred.confidence >= minConfidence);
}

// Helper function to get active predictions (not expired)
export function getActivePredictions(): Prediction[] {
  const now = new Date();
  return mockPredictions.filter(pred => new Date(pred.expiresAt) > now);
}

// Helper function to get predictions by signal type
export function getPredictionsBySignal(signal: 'bullish' | 'bearish' | 'neutral'): Prediction[] {
  return mockPredictions.filter(pred => pred.signal === signal);
}