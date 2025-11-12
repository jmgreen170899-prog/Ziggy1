// Mock Service Adapter for ZiggyClean Frontend
// Provides environment-based switching between mock data and real API calls

import { mockPredictions } from './predictions';
import { mockTradingPlans } from './plans';
import { mockEvidence } from './evidence';
import { mockAgentQueue } from './agentQueue';
import type { 
  Prediction, 
  TradingPlan, 
  Evidence, 
  AgentAction,
  ScenarioResult,
  CalendarEvent,
  ModelMetrics,
  MacroContext
} from './types';

// Environment configuration
export const isDevelopmentMode = process.env.NODE_ENV === 'development';
export const isBackendAvailable = process.env.NEXT_PUBLIC_BACKEND_AVAILABLE === 'true';
export const useMocks = isDevelopmentMode && !isBackendAvailable;

// Helper function to simulate API delay
export const simulateApiDelay = (ms: number = 300) => 
  new Promise(resolve => setTimeout(resolve, ms));

// Mock Service Adapter Class
class MockServiceAdapter {
  
  // Predictions API
  async getPredictions(): Promise<Prediction[]> {
    if (useMocks) {
      await simulateApiDelay();
      return mockPredictions;
    }
    throw new Error('Real API not implemented');
  }

  async getPredictionById(id: string): Promise<Prediction | null> {
    if (useMocks) {
      await simulateApiDelay();
      return mockPredictions.find(p => p.id === id) || null;
    }
    throw new Error('Real API not implemented');
  }

  async getPredictionsBySymbol(symbol: string): Promise<Prediction[]> {
    if (useMocks) {
      await simulateApiDelay();
      return mockPredictions.filter(p => p.symbol === symbol);
    }
    throw new Error('Real API not implemented');
  }

  async createPrediction(prediction: Omit<Prediction, 'id' | 'createdAt'>): Promise<Prediction> {
    if (useMocks) {
      await simulateApiDelay();
      const newPrediction: Prediction = {
        ...prediction,
        id: `pred_${Date.now()}`,
        createdAt: new Date().toISOString()
      };
      mockPredictions.unshift(newPrediction);
      return newPrediction;
    }
    throw new Error('Real API not implemented');
  }

  // Trading Plans API
  async getTradingPlans(): Promise<TradingPlan[]> {
    if (useMocks) {
      await simulateApiDelay();
      return mockTradingPlans;
    }
    throw new Error('Real API not implemented');
  }

  async getTradingPlanById(id: string): Promise<TradingPlan | null> {
    if (useMocks) {
      await simulateApiDelay();
      return mockTradingPlans.find(p => p.id === id) || null;
    }
    throw new Error('Real API not implemented');
  }

  async createTradingPlan(plan: Omit<TradingPlan, 'id' | 'createdAt'>): Promise<TradingPlan> {
    if (useMocks) {
      await simulateApiDelay();
      const newPlan: TradingPlan = {
        ...plan,
        id: `plan_${Date.now()}`,
        createdAt: new Date().toISOString()
      };
      mockTradingPlans.unshift(newPlan);
      return newPlan;
    }
    throw new Error('Real API not implemented');
  }

  async updateTradingPlan(id: string, updates: Partial<TradingPlan>): Promise<TradingPlan | null> {
    if (useMocks) {
      await simulateApiDelay();
      const planIndex = mockTradingPlans.findIndex(p => p.id === id);
      if (planIndex === -1) return null;
      
      mockTradingPlans[planIndex] = { ...mockTradingPlans[planIndex], ...updates };
      return mockTradingPlans[planIndex];
    }
    throw new Error('Real API not implemented');
  }

  // Evidence API
  async getEvidence(): Promise<Evidence[]> {
    if (useMocks) {
      await simulateApiDelay();
      return mockEvidence;
    }
    throw new Error('Real API not implemented');
  }

  async getEvidenceByPrediction(predictionId: string): Promise<Evidence | null> {
    if (useMocks) {
      await simulateApiDelay();
      return mockEvidence.find(e => e.predictionId === predictionId) || null;
    }
    throw new Error('Real API not implemented');
  }

  // Agent Queue API
  async getAgentQueue(): Promise<AgentAction[]> {
    if (useMocks) {
      await simulateApiDelay();
      return mockAgentQueue;
    }
    throw new Error('Real API not implemented');
  }

  async createAgentAction(action: Omit<AgentAction, 'id' | 'createdAt'>): Promise<AgentAction> {
    if (useMocks) {
      await simulateApiDelay();
      const newAction: AgentAction = {
        ...action,
        id: `agent_${Date.now()}`,
        createdAt: new Date().toISOString()
      };
      mockAgentQueue.unshift(newAction);
      return newAction;
    }
    throw new Error('Real API not implemented');
  }

  async updateAgentAction(id: string, updates: Partial<AgentAction>): Promise<AgentAction | null> {
    if (useMocks) {
      await simulateApiDelay();
      const actionIndex = mockAgentQueue.findIndex(a => a.id === id);
      if (actionIndex === -1) return null;
      
      mockAgentQueue[actionIndex] = { ...mockAgentQueue[actionIndex], ...updates };
      return mockAgentQueue[actionIndex];
    }
    throw new Error('Real API not implemented');
  }

  // Scenario Simulation API
  async runScenario(params: {
    symbol: string;
    basePrice: number;
    volatility: number;
    timeDecay: number;
    priceRange: { min: number; max: number };
  }): Promise<ScenarioResult> {
    if (useMocks) {
      await simulateApiDelay(800); // Longer delay for simulation
      
      const { symbol, basePrice } = params;
      
      // TODO: Use volatility, timeDecay, and priceRange for more sophisticated modeling
      
      // Generate mock scenario results
      const scenarios = [];
      for (let i = -10; i <= 10; i++) {
        const priceChange = i * 2; // -20% to +20% in 2% increments
        const price = basePrice * (1 + priceChange / 100);
        
        // Simple probability distribution (normal-ish)
        const probability = Math.exp(-Math.pow(priceChange / 8, 2)) * 15;
        
        // Mock P&L calculation (assuming 100 shares)
        const pnl = (price - basePrice) * 100;
        
        scenarios.push({
          priceChange,
          probability: Math.max(0.1, probability),
          pnl,
          timeframe: '1d'
        });
      }
      
      // Calculate statistics
      const weightedPnL = scenarios.reduce((sum, s) => sum + (s.pnl * s.probability / 100), 0);
      const pnlValues = scenarios.map(s => s.pnl);
      const positiveProb = scenarios
        .filter(s => s.pnl > 0)
        .reduce((sum, s) => sum + s.probability, 0);
      
      return {
        id: `scenario_${Date.now()}`,
        symbol,
        basePrice,
        scenarios,
        statistics: {
          expectedValue: weightedPnL,
          worstCase: Math.min(...pnlValues),
          bestCase: Math.max(...pnlValues),
          breakeven: basePrice,
          probabilityOfProfit: positiveProb,
          maxDrawdown: Math.min(...pnlValues) / (basePrice * 100)
        },
        params
      };
    }
    throw new Error('Real API not implemented');
  }

  // Calendar Events API
  async getCalendarEvents(): Promise<CalendarEvent[]> {
    if (useMocks) {
      await simulateApiDelay();
      return [
        {
          id: 'cal_001',
          type: 'prediction_expiry',
          title: 'NVDA Prediction Expires',
          description: 'Bullish prediction for NVDA expires in 2 days',
          symbol: 'NVDA',
          date: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString(),
          time: '16:00',
          importance: 'high',
          status: 'upcoming',
          impact: 'bullish'
        },
        {
          id: 'cal_002',
          type: 'model_refresh',
          title: 'AI Model Retrain',
          description: 'Scheduled model retraining for all timeframes',
          date: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(),
          time: '02:00',
          importance: 'medium',
          status: 'upcoming'
        },
        {
          id: 'cal_003',
          type: 'earnings',
          title: 'TSLA Earnings Report',
          symbol: 'TSLA',
          date: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString(),
          time: '16:30',
          importance: 'high',
          status: 'upcoming',
          impact: 'neutral'
        }
      ];
    }
    throw new Error('Real API not implemented');
  }

  // Model Metrics API
  async getModelMetrics(): Promise<ModelMetrics[]> {
    if (useMocks) {
      await simulateApiDelay();
      return [
        {
          id: 'model_001',
          modelName: 'AI Signals Generator',
          timeframe: '1d',
          metrics: {
            accuracy: 78.5,
            precision: 82.1,
            recall: 74.8,
            f1Score: 78.3,
            sharpeRatio: 1.85,
            winRate: 68.2,
            avgReturn: 4.2,
            maxDrawdown: -8.5
          },
          drift: {
            detected: false,
            severity: 'low',
            recommendation: 'Model performance stable. Continue monitoring.'
          },
          performance: {
            last7Days: 85.2,
            last30Days: 78.5,
            last90Days: 76.8,
            ytd: 74.2
          },
          status: 'healthy',
          lastUpdated: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
          nextUpdate: new Date(Date.now() + 22 * 60 * 60 * 1000).toISOString()
        }
      ];
    }
    throw new Error('Real API not implemented');
  }

  // Macro Context API
  async getMacroContext(): Promise<MacroContext> {
    if (useMocks) {
      await simulateApiDelay();
      return {
        id: 'macro_001',
        regime: {
          current: 'risk_on',
          confidence: 72,
          duration: '23 days',
          nextChange: 'Nov 15, 2025'
        },
        indicators: {
          vix: { value: 18.5, trend: 'down', signal: 'normal' },
          yield10y: { value: 4.25, trend: 'up' },
          dxy: { value: 102.8, trend: 'down' },
          commodities: { value: 485.2, trend: 'up' }
        },
        guards: [
          {
            name: 'VIX Spike Guard',
            active: false,
            type: 'volatility',
            threshold: 25,
            current: 18.5
          },
          {
            name: 'Correlation Breakdown',
            active: false,
            type: 'correlation',
            threshold: 0.8,
            current: 0.65
          }
        ],
        outlook: {
          bullish: 65,
          bearish: 20,
          neutral: 15,
          timeframe: '1m'
        }
      };
    }
    throw new Error('Real API not implemented');
  }
}

// Export singleton instance
export const mockService = new MockServiceAdapter();

// Generic API call wrapper for easy switching
export async function apiCall<T>(
  mockFn: () => Promise<T>,
  realApiFn?: () => Promise<T>
): Promise<T> {
  if (useMocks) {
    return mockFn();
  }
  
  if (realApiFn) {
    return realApiFn();
  }
  
  throw new Error('Real API function not provided');
}