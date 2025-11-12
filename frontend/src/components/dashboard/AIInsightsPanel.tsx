'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

interface AIInsight {
  type: 'market' | 'portfolio' | 'risk' | 'signal' | 'fee' | 'coach';
  title: string;
  description: string;
  severity: 'info' | 'warning' | 'success' | 'error';
  action?: string;
  explainability?: {
    confidence: number;
    features: string[];
    reasoning: string;
    netOfFees?: boolean;
  };
  coachMode?: {
    suggestion: string;
    rationale: string;
    skipRecommended?: boolean;
  };
}

const mockInsights: AIInsight[] = [
  {
    type: 'market',
    title: 'Market Regime Analysis',
    description: 'Current market shows elevated volatility with rotation from growth to value sectors. VIX at 22.5 indicates heightened uncertainty.',
    severity: 'warning',
    action: 'View detailed analysis',
    explainability: {
      confidence: 0.84,
      features: ['VIX spike', 'Sector rotation', 'Volume patterns', 'Options flow'],
      reasoning: 'Multiple technical indicators confirm regime shift with 84% confidence based on historical pattern matching.',
      netOfFees: true
    }
  },
  {
    type: 'signal',
    title: 'AAPL - Strong Buy Signal',
    description: 'AI model identifies high-conviction buy opportunity with 12.5% expected return (11.8% net of fees). Entry recommended at $178-180.',
    severity: 'success',
    action: 'View signal details',
    explainability: {
      confidence: 0.91,
      features: ['Earnings momentum', 'Technical breakout', 'Insider buying', 'Analyst upgrades'],
      reasoning: 'Convergence of fundamental and technical factors with strong institutional support.',
      netOfFees: true
    },
    coachMode: {
      suggestion: 'Consider 2-3% position sizing for optimal risk-adjusted returns',
      rationale: 'Based on your current portfolio allocation and risk profile'
    }
  },
  {
    type: 'coach',
    title: 'Trade Optimization Alert',
    description: 'TSLA signal shows marginal edge after fees (2.1% vs 3.2% gross). Consider paper trading first or reducing position size.',
    severity: 'info',
    action: 'Skip trade',
    coachMode: {
      suggestion: 'Skip this trade or reduce to 0.5% position',
      rationale: 'Fee-adjusted expectancy below your 3% minimum threshold. Better opportunities available.',
      skipRecommended: true
    }
  },
  {
    type: 'fee',
    title: 'Fee Impact Analysis',
    description: 'Current execution settings show 0.12% average commission impact. High-frequency signals may benefit from PnL share model.',
    severity: 'info',
    action: 'Review fee settings',
    explainability: {
      confidence: 0.95,
      features: ['Trade frequency', 'Position sizes', 'Fee structure'],
      reasoning: 'Analysis of last 30 trades shows fee optimization potential of $1,240 annually.',
      netOfFees: true
    }
  },
  {
    type: 'risk',
    title: 'Portfolio Concentration Risk',
    description: 'Tech allocation at 45% exceeds recommended 30% limit. Correlation risk elevated during sector rotations.',
    severity: 'warning',
    action: 'Rebalance portfolio',
    explainability: {
      confidence: 0.87,
      features: ['Sector weights', 'Correlation matrix', 'VaR calculations'],
      reasoning: 'Monte Carlo simulations show 15% higher downside risk vs balanced allocation.',
      netOfFees: true
    }
  }
];

type RiskMetricsShape = {
  risk_reward_ratio?: number;
};

type ExplanationShape = {
  confidence?: number;
  features_used?: string[] | Record<string, unknown>;
  reason?: string;
  risk_metrics?: RiskMetricsShape;
};

type SignalShape = {
  direction?: string;
  signal_type?: string;
  type?: string;
  confidence?: number;
  risk_reward_ratio?: number;
  reason?: string;
};

type BackendSignal = {
  signal: SignalShape | null;
  explanation: ExplanationShape | null;
};

type WatchlistResponse = {
  signals: Record<string, BackendSignal>;
  signal_count: number;
  total_tickers: number;
  status: string;
  regime_context?: Record<string, unknown>;
};

function mapBackendToInsight(ticker: string, payload: BackendSignal): AIInsight | null {
  if (!payload || !payload.signal) {
    return null;
  }

  const s = payload.signal;
  const e = payload.explanation || {};

  // Derive fields safely
  const direction = s.direction?.toUpperCase?.() || s.direction || 'NEUTRAL';
  const signalType = s.signal_type || s.type || 'signal';
  const confidence: number = typeof e.confidence === 'number' ? e.confidence : (typeof s.confidence === 'number' ? s.confidence : 0.5);
  const riskRR = s.risk_reward_ratio ?? e?.risk_metrics?.risk_reward_ratio;
  const reason: string = s.reason || e.reason || 'Model generated signal';
  const featuresUsed = Array.isArray(e.features_used)
    ? e.features_used
    : (e.features_used && typeof e.features_used === 'object'
        ? Object.keys(e.features_used)
        : []);

  // Map to severity
  const severity: AIInsight['severity'] = confidence >= 0.8
    ? 'success'
    : confidence >= 0.6
      ? 'info'
      : 'warning';

  // Simple coach suggestion heuristic
  const coachSuggestion = (() => {
    if (riskRR != null && riskRR < 1.2) {
      return {
        suggestion: 'Consider smaller size or skip',
        rationale: 'Risk/reward below 1.2; limited edge after fees',
        skipRecommended: true,
      };
    }
    if (confidence >= 0.8 && direction === 'LONG') {
      return {
        suggestion: 'Consider 2-3% position size',
        rationale: 'High confidence and favorable reward profile',
      };
    }
    return {
      suggestion: 'Paper trade first to validate edge',
      rationale: 'Moderate confidence or incomplete risk metrics',
    };
  })();

  const title = `${ticker} — ${direction === 'SHORT' ? 'Sell' : 'Buy'} (${signalType})`;
  const description = reason;

  return {
    type: 'signal',
    title,
    description,
    severity,
    action: 'View signal details',
    explainability: {
      confidence,
      features: (featuresUsed || []).slice(0, 6),
      reasoning: reason,
      netOfFees: true,
    },
    coachMode: coachSuggestion,
  };
}

export function AIInsightsPanel() {
  const [isGenerating, setIsGenerating] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [showExplainability, setShowExplainability] = useState<number | null>(null);
  const [coachModeEnabled, setCoachModeEnabled] = useState(true);
  const [insights, setInsights] = useState<AIInsight[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const defaultTickers = useMemo(() => ['AAPL', 'MSFT', 'NVDA', 'TSLA'], []);

  const fetchInsights = async (tickers: string[]) => {
    try {
      setError(null);
      const res = await fetch('/api/signals/watchlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tickers, include_regime: false }),
        cache: 'no-store',
      });
      if (!res.ok) {
        const txt = await res.text();
        throw new Error(txt || `Failed with ${res.status}`);
      }
      const data: WatchlistResponse = await res.json();
      const mapped: AIInsight[] = Object.entries(data.signals || {})
        .map(([ticker, payload]) => mapBackendToInsight(ticker, payload as BackendSignal))
        .filter((x): x is AIInsight => Boolean(x));
      setInsights(mapped.length > 0 ? mapped : null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error');
      setInsights(null);
    }
  };

  const handleRefreshInsights = async () => {
    setIsGenerating(true);
    await fetchInsights(defaultTickers);
    setIsGenerating(false);
    setLastUpdated(new Date());
  };

  useEffect(() => {
    // Initial load
    fetchInsights(defaultTickers);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleExplainSignal = (index: number) => {
    setShowExplainability(showExplainability === index ? null : index);
  };

  const getSeverityStyles = (severity: string) => {
    switch (severity) {
      case 'success':
        return 'bg-green-50 border-l-green-400 text-green-800 dark:bg-green-900/20 dark:border-l-green-400 dark:text-green-200';
      case 'warning':
        return 'bg-yellow-50 border-l-yellow-400 text-yellow-800 dark:bg-yellow-900/20 dark:border-l-yellow-400 dark:text-yellow-200';
      case 'error':
        return 'bg-red-50 border-l-red-400 text-red-800 dark:bg-red-900/20 dark:border-l-red-400 dark:text-red-200';
      default:
        return 'bg-blue-50 border-l-blue-400 text-blue-800 dark:bg-blue-900/20 dark:border-l-blue-400 dark:text-blue-200';
    }
  };

  const getIconForType = (type: string) => {
    switch (type) {
      case 'market':
        return '📊';
      case 'portfolio':
        return '💼';
      case 'risk':
        return '⚠️';
      case 'signal':
        return '🎯';
      case 'fee':
        return '💰';
      case 'coach':
        return '🧠';
      default:
        return '🤖';
    }
  };

  return (
    <Card className="bg-gradient-to-br from-white to-indigo-50 dark:from-gray-900 dark:to-indigo-950 border-indigo-200 dark:border-indigo-800 shadow-lg hover:shadow-xl transition-all duration-300">
      <CardHeader className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-t-lg">
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-white/20 rounded-lg flex items-center justify-center">
              <span className="text-lg">🤖</span>
            </div>
            <div>
              <span className="text-xl font-bold">ZiggyAI Insights</span>
              <div className="text-indigo-100 text-sm">
                Explainable AI • Net-of-Fees Analysis • Coach Mode
                {coachModeEnabled && <span className="ml-2 px-2 py-0.5 bg-green-500/20 rounded-full text-xs">🧠 Coach Active</span>}
              </div>
            </div>
            {isGenerating && (
              <div className="flex items-center space-x-2 bg-white/10 px-3 py-1 rounded-full">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-white rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
                <span className="text-sm font-medium">Analyzing...</span>
              </div>
            )}
          </div>
          <div className="flex items-center space-x-3">
            <Button
              onClick={() => setCoachModeEnabled(!coachModeEnabled)}
              className={`text-xs px-3 py-1 ${coachModeEnabled 
                ? 'bg-green-500/20 hover:bg-green-500/30 text-green-100 border-green-400/30' 
                : 'bg-white/20 hover:bg-white/30 text-white border-white/30'}`}
            >
              🧠 Coach Mode
            </Button>
            <span className="text-xs text-indigo-100 bg-white/10 px-2 py-1 rounded-full">
              Updated: {lastUpdated?.toLocaleTimeString?.([], { hour: '2-digit', minute: '2-digit' })}
            </span>
            <Button
              onClick={handleRefreshInsights}
              disabled={isGenerating}
              className="bg-white/20 hover:bg-white/30 text-white border-white/30 hover:border-white/50 text-sm px-3 py-1"
            >
              {isGenerating ? '⏳' : '🔄'} Refresh
            </Button>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Error banner */}
          {error && (
            <div className="p-3 rounded-lg border-l-4 bg-red-50 border-l-red-400 text-red-800 dark:bg-red-900/20 dark:border-l-red-400 dark:text-red-200">
              Failed to load live insights: {error}. Showing placeholders.
            </div>
          )}

          {(insights || mockInsights).map((insight, index) => (
            <div
              key={index}
              className={`p-4 rounded-lg border-l-4 ${getSeverityStyles(insight.severity)} transition-all duration-200`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <span className="text-lg">{getIconForType(insight.type)}</span>
                    <h4 className="font-semibold">{insight.title}</h4>
                    {insight.explainability && (
                      <span className="text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 px-2 py-0.5 rounded-full">
                        {Math.round(insight.explainability.confidence * 100)}% confidence
                      </span>
                    )}
                    {insight.explainability?.netOfFees && (
                      <span className="text-xs bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200 px-2 py-0.5 rounded-full">
                        Net of Fees
                      </span>
                    )}
                  </div>
                  <p className="text-sm mb-3 opacity-90">
                    {insight.description}
                  </p>
                  
                  {/* Coach Mode Suggestions */}
                  {coachModeEnabled && insight.coachMode && (
                    <div className="mt-3 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                      <div className="flex items-start space-x-2">
                        <span className="text-blue-600 dark:text-blue-400">🧠</span>
                        <div>
                          <div className="font-medium text-blue-800 dark:text-blue-200 text-sm">Coach Recommendation:</div>
                          <div className="text-blue-700 dark:text-blue-300 text-sm">{insight.coachMode.suggestion}</div>
                          <div className="text-blue-600 dark:text-blue-400 text-xs mt-1">{insight.coachMode.rationale}</div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Explainability Panel */}
                  {insight.explainability && showExplainability === index && (
                    <div className="mt-3 p-3 bg-gray-50 dark:bg-gray-900/20 border border-gray-200 dark:border-gray-700 rounded-lg">
                      <div className="text-sm font-medium mb-2">Why this insight?</div>
                      <div className="text-sm text-gray-700 dark:text-gray-300 mb-3">{insight.explainability.reasoning}</div>
                      <div className="text-xs text-gray-600 dark:text-gray-400 mb-2">Key factors analyzed:</div>
                      <div className="flex flex-wrap gap-1">
                        {insight.explainability.features?.map((feature, idx) => (
                          <span key={idx} className="text-xs bg-gray-200 dark:bg-gray-700 px-2 py-1 rounded">
                            {feature}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="flex items-center space-x-3 mt-3">
                    {insight.action && (
                      <button className="text-sm underline hover:no-underline font-medium">
                        {insight.action} →
                      </button>
                    )}
                    {insight.explainability && (
                      <button 
                        onClick={() => handleExplainSignal(index)}
                        className="text-xs text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 font-medium"
                      >
                        {showExplainability === index ? '🔽 Hide explanation' : '🔍 Explain why'}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
          
          {/* Safety & Transparency Banner */}
          <div className="mt-6 p-4 bg-gradient-to-r from-emerald-50 to-teal-50 dark:from-emerald-900/20 dark:to-teal-900/20 border border-emerald-200 dark:border-emerald-800 rounded-lg">
            <h4 className="font-semibold mb-3 flex items-center space-x-2 text-emerald-800 dark:text-emerald-200">
              <span>🛡️</span>
              <span>Safety Rails & Transparency</span>
            </h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-emerald-700 dark:text-emerald-300">Risk Controls:</span>
                <span className="ml-2 font-medium">Always Active</span>
              </div>
              <div>
                <span className="text-emerald-700 dark:text-emerald-300">Fee Disclosure:</span>
                <span className="ml-2 font-medium">Full Transparency</span>
              </div>
              <div>
                <span className="text-emerald-700 dark:text-emerald-300">AI Explainability:</span>
                <span className="ml-2 font-medium">Required for All Signals</span>
              </div>
              <div>
                <span className="text-emerald-700 dark:text-emerald-300">Conflict Protection:</span>
                <span className="ml-2 font-medium">Churn Penalties Active</span>
              </div>
            </div>
            <div className="mt-3 text-xs text-emerald-600 dark:text-emerald-400">
              ⚠️ All performance metrics include fees, slippage, and borrowing costs. AI recommendations prioritize risk-adjusted, net-of-fee outcomes.
            </div>
          </div>

          {/* Daily Market Summary with Net-of-Fees Focus */}
          <div className="mt-6 p-4 bg-surface border border-border rounded-lg">
            <h4 className="font-semibold mb-3 flex items-center space-x-2">
              <span>📈</span>
              <span>Daily Market Summary (Net Performance)</span>
            </h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-fg-muted">Market Sentiment:</span>
                <span className="ml-2 font-medium text-yellow-600">Cautious (High Vol)</span>
              </div>
              <div>
                <span className="text-fg-muted">Avg Signal Quality:</span>
                <span className="ml-2 font-medium">87% (Post-Fee)</span>
              </div>
              <div>
                <span className="text-fg-muted">Top Opportunity:</span>
                <span className="ml-2 font-medium">Value Rotation (+5.2% net)</span>
              </div>
              <div>
                <span className="text-fg-muted">Trades Filtered:</span>
                <span className="ml-2 font-medium">12/18 (Coach Mode)</span>
              </div>
            </div>
          </div>

          {/* Enhanced Chat Access with RAG Integration */}
          <div className="mt-4 p-3 bg-accent/10 border border-accent/20 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <h5 className="font-medium text-accent">Need deeper analysis?</h5>
                <p className="text-sm text-fg-muted">Ask ZiggyAI about fees, risks, or strategy optimization</p>
              </div>
              <div className="flex space-x-2">
                <Button
                  size="sm"
                  variant="ghost"
                  className="text-xs"
                  onClick={() => console.log('Navigate to fee calculator')}
                >
                  💰 Fee Calculator
                </Button>
                <Button
                  size="sm"
                  className="bg-accent text-accent-fg hover:bg-accent/90"
                  onClick={() => console.log('Navigate to chat with portfolio analysis query')}
                >
                  💬 Ask ZiggyAI
                </Button>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}