import type { TradingPlan } from './types';

// Mock trading plans data for ZiggyClean AI Trading Platform
export const mockTradingPlans: TradingPlan[] = [
  {
    id: 'plan_001',
    symbol: 'NVDA',
    predictionId: 'pred_001',
    entry: 875.00,
    stop: 825.00,
    target: 950.00,
    atr: 28.50,
    riskAmount: 5000.00,
    rMultiple: 1.5,
    size: 100, // shares
    accountRiskPct: 2.0,
    status: 'approved',
    createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
    approvedAt: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(), // 1 hour ago
    notes: 'High-conviction AI play with strong technical setup. Risk 2% of account on breakout above $870.'
  },
  {
    id: 'plan_002',
    symbol: 'TSLA',
    predictionId: 'pred_002',
    entry: 195.00,
    stop: 205.00,
    target: 175.00,
    atr: 12.80,
    riskAmount: 2500.00,
    rMultiple: 2.0,
    size: 250, // shares (short position)
    accountRiskPct: 1.0,
    status: 'draft',
    createdAt: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(), // 1 hour ago
    notes: 'Short setup on production concerns. Wait for confirmed break below $195 support.'
  },
  {
    id: 'plan_003',
    symbol: 'MSFT',
    predictionId: 'pred_004',
    entry: 312.00,
    stop: 300.00,
    target: 335.00,
    atr: 8.40,
    riskAmount: 3600.00,
    rMultiple: 1.9,
    size: 300, // shares
    accountRiskPct: 1.5,
    status: 'executed',
    createdAt: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(), // 3 hours ago
    approvedAt: new Date(Date.now() - 2.5 * 60 * 60 * 1000).toISOString(),
    executedAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
    notes: 'Cloud growth thesis playing out. Entered on breakout with strong volume.'
  },
  {
    id: 'plan_004',
    symbol: 'AAPL',
    predictionId: 'pred_003',
    entry: 155.00,
    stop: 150.00,
    target: 162.00,
    atr: 3.20,
    riskAmount: 1500.00,
    rMultiple: 1.4,
    size: 300, // shares
    accountRiskPct: 0.6,
    status: 'cancelled',
    createdAt: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(), // 4 hours ago
    notes: 'Cancelled due to weak setup and neutral signal. Better opportunities elsewhere.'
  },
  {
    id: 'plan_005',
    symbol: 'GOOGL',
    predictionId: 'pred_005',
    entry: 2955.00,
    stop: 2880.00,
    target: 3100.00,
    atr: 45.20,
    riskAmount: 4500.00,
    rMultiple: 1.9,
    size: 60, // shares
    accountRiskPct: 1.8,
    status: 'approved',
    createdAt: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(), // 5 hours ago
    approvedAt: new Date(Date.now() - 30 * 60 * 1000).toISOString(), // 30 minutes ago
    notes: 'Value play with AI upside. Strong fundamentals with attractive entry point.'
  },
  {
    id: 'plan_006',
    symbol: 'AMD',
    predictionId: 'pred_006',
    entry: 118.00,
    stop: 125.00,
    target: 105.00,
    atr: 6.80,
    riskAmount: 2100.00,
    rMultiple: 1.9,
    size: 300, // shares (short position)
    accountRiskPct: 0.8,
    status: 'draft',
    createdAt: new Date(Date.now() - 30 * 60 * 1000).toISOString(), // 30 minutes ago
    notes: 'Short on competitive pressure. Conservative size due to sector volatility.'
  },
  {
    id: 'plan_007',
    symbol: 'SPY',
    predictionId: 'pred_007',
    entry: 435.00,
    stop: 428.00,
    target: 448.00,
    atr: 4.20,
    riskAmount: 3500.00,
    rMultiple: 1.9,
    size: 500, // shares
    accountRiskPct: 1.4,
    status: 'draft',
    createdAt: new Date(Date.now() - 15 * 60 * 1000).toISOString(), // 15 minutes ago
    notes: 'Market hedge position. Bullish on broad market strength.'
  }
];

// Helper functions for plan management
export function getPlansByStatus(status: TradingPlan['status']): TradingPlan[] {
  return mockTradingPlans.filter(plan => plan.status === status);
}

export function getPlansBySymbol(symbol: string): TradingPlan[] {
  return mockTradingPlans.filter(plan => plan.symbol === symbol);
}

export function getPlansByPrediction(predictionId: string): TradingPlan[] {
  return mockTradingPlans.filter(plan => plan.predictionId === predictionId);
}

export function getActivePlans(): TradingPlan[] {
  return mockTradingPlans.filter(plan => 
    plan.status === 'approved' || plan.status === 'executed'
  );
}

export function getPendingPlans(): TradingPlan[] {
  return mockTradingPlans.filter(plan => plan.status === 'draft');
}

export function calculatePlanMetrics(plan: TradingPlan) {
  const riskAmount = plan.riskAmount;
  const potentialProfit = (plan.target - plan.entry) * plan.size;
  const potentialLoss = (plan.entry - plan.stop) * plan.size;
  
  return {
    riskAmount,
    potentialProfit: Math.abs(potentialProfit),
    potentialLoss: Math.abs(potentialLoss),
    riskRewardRatio: Math.abs(potentialProfit / potentialLoss),
    breakeven: plan.entry,
    maxRisk: riskAmount,
    accountRiskPct: plan.accountRiskPct
  };
}

export function getTotalPortfolioRisk(): number {
  return getActivePlans().reduce((total, plan) => total + plan.riskAmount, 0);
}

export function getTotalAccountRisk(): number {
  return getActivePlans().reduce((total, plan) => total + plan.accountRiskPct, 0);
}