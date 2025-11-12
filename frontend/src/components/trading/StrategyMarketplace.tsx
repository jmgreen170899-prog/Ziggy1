'use client';

import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

interface MarketplaceBotListing {
  id: string;
  name: string;
  description: string;
  author: string;
  category: 'momentum' | 'mean_reversion' | 'arbitrage' | 'ai_signals' | 'multi_strategy';
  forwardTest: {
    duration: string;
    totalReturn: number;
    totalReturnNetFees: number;
    sharpeRatio: number;
    maxDrawdown: number;
    calmarRatio: number;
    winRate: number;
    totalTrades: number;
    avgTrade: number;
    avgTradeNetFees: number;
    feesTotal: number;
    worstDrawdownPeriod: string;
  };
  riskMetrics: {
    volatility: number;
    beta: number;
    correlationSPY: number;
    var95: number;
    maxLeverage: number;
  };
  safetyScore: number; // 0-100, ZiggyAI's safety evaluation
  transparencyScore: number; // 0-100, based on explainability
  reviews: {
    total: number;
    avgRating: number;
    clarityRating: number;
    riskDisclosureRating: number;
    supportRating: number;
  };
  pricing: {
    subscriptionFee?: number;
    performanceFee?: number;
    oneTimeFee?: number;
    freeTrialDays?: number;
  };
  requirements: {
    minCapital: number;
    tradingExperience: 'beginner' | 'intermediate' | 'advanced';
    timeCommitment: string;
    monitoringRequired: boolean;
  };
  features: string[];
  risks: string[];
  lastUpdated: Date;
  installs: number;
  paperTestRequired: boolean;
}

interface StrategyMarketplaceProps {
  onInstallBot?: (botId: string) => void;
  onViewDetails?: (botId: string) => void;
  userExperience?: 'beginner' | 'intermediate' | 'advanced';
}

// Mock marketplace bots with focus on safety and transparency
const mockMarketplaceBots: MarketplaceBotListing[] = [
  {
    id: 'bot_1',
    name: 'ZiggyMomentum Pro',
    description: 'AI-powered momentum strategy with dynamic risk management and Coach Mode integration',
    author: 'ZiggyAI Team',
    category: 'ai_signals',
    forwardTest: {
      duration: '6 months',
      totalReturn: 28.4,
      totalReturnNetFees: 25.1,
      sharpeRatio: 1.62,
      maxDrawdown: -7.8,
      calmarRatio: 3.21,
      winRate: 71.2,
      totalTrades: 89,
      avgTrade: 3.2,
      avgTradeNetFees: 2.8,
      feesTotal: 2847.50,
      worstDrawdownPeriod: 'March 2024 (Tech selloff)'
    },
    riskMetrics: {
      volatility: 15.2,
      beta: 1.08,
      correlationSPY: 0.72,
      var95: -2.1,
      maxLeverage: 1.0
    },
    safetyScore: 92,
    transparencyScore: 96,
    reviews: {
      total: 127,
      avgRating: 4.7,
      clarityRating: 4.8,
      riskDisclosureRating: 4.9,
      supportRating: 4.6
    },
    pricing: {
      subscriptionFee: 29.00,
      freeTrialDays: 14
    },
    requirements: {
      minCapital: 10000,
      tradingExperience: 'intermediate',
      timeCommitment: '15 min/day monitoring',
      monitoringRequired: true
    },
    features: [
      'AI signal generation',
      'Automatic position sizing',
      'Coach Mode integration',
      'Real-time risk monitoring',
      'Net-of-fees optimization'
    ],
    risks: [
      'Market regime changes may reduce performance',
      'Requires active monitoring during high volatility',
      'Technology sector concentration (max 35%)'
    ],
    lastUpdated: new Date(Date.now() - 86400000),
    installs: 342,
    paperTestRequired: true
  },
  {
    id: 'bot_2',
    name: 'Defensive Value Shield',
    description: 'Conservative value investing with downside protection and dividend focus',
    author: 'SafeTrading Co.',
    category: 'mean_reversion',
    forwardTest: {
      duration: '12 months',
      totalReturn: 14.2,
      totalReturnNetFees: 12.8,
      sharpeRatio: 1.89,
      maxDrawdown: -4.1,
      calmarRatio: 3.12,
      winRate: 68.4,
      totalTrades: 45,
      avgTrade: 2.1,
      avgTradeNetFees: 1.8,
      feesTotal: 1234.00,
      worstDrawdownPeriod: 'August 2024 (Rate concerns)'
    },
    riskMetrics: {
      volatility: 8.7,
      beta: 0.65,
      correlationSPY: 0.58,
      var95: -1.2,
      maxLeverage: 1.0
    },
    safetyScore: 98,
    transparencyScore: 94,
    reviews: {
      total: 89,
      avgRating: 4.8,
      clarityRating: 4.7,
      riskDisclosureRating: 5.0,
      supportRating: 4.6
    },
    pricing: {
      subscriptionFee: 19.00,
      freeTrialDays: 30
    },
    requirements: {
      minCapital: 25000,
      tradingExperience: 'beginner',
      timeCommitment: '5 min/week review',
      monitoringRequired: false
    },
    features: [
      'Dividend-focused selection',
      'Automatic rebalancing',
      'Low-volatility bias',
      'ESG screening available',
      'Tax-loss harvesting'
    ],
    risks: [
      'May underperform in strong bull markets',
      'Interest rate sensitivity on utilities',
      'Limited growth exposure'
    ],
    lastUpdated: new Date(Date.now() - 172800000),
    installs: 567,
    paperTestRequired: false
  },
  {
    id: 'bot_3',
    name: 'Crypto Arbitrage Hunter',
    description: 'Cross-exchange arbitrage opportunities with automated execution',
    author: 'CryptoEdge Labs',
    category: 'arbitrage',
    forwardTest: {
      duration: '4 months',
      totalReturn: 22.8,
      totalReturnNetFees: 18.9,
      sharpeRatio: 2.34,
      maxDrawdown: -3.2,
      calmarRatio: 5.91,
      winRate: 84.7,
      totalTrades: 234,
      avgTrade: 0.8,
      avgTradeNetFees: 0.6,
      feesTotal: 3456.78,
      worstDrawdownPeriod: 'October 2024 (Exchange outage)'
    },
    riskMetrics: {
      volatility: 12.4,
      beta: 0.15,
      correlationSPY: 0.23,
      var95: -1.8,
      maxLeverage: 2.0
    },
    safetyScore: 85,
    transparencyScore: 91,
    reviews: {
      total: 67,
      avgRating: 4.4,
      clarityRating: 4.3,
      riskDisclosureRating: 4.7,
      supportRating: 4.2
    },
    pricing: {
      subscriptionFee: 49.00,
      performanceFee: 15.0,
      freeTrialDays: 7
    },
    requirements: {
      minCapital: 5000,
      tradingExperience: 'advanced',
      timeCommitment: 'Fully automated',
      monitoringRequired: true
    },
    features: [
      'Cross-exchange monitoring',
      'Automated execution',
      'Real-time P&L tracking',
      'Multiple crypto pairs',
      'API key management'
    ],
    risks: [
      'Exchange connectivity risks',
      'Regulatory changes',
      'High-frequency trading competition',
      'Withdrawal/deposit timing risks'
    ],
    lastUpdated: new Date(Date.now() - 3600000),
    installs: 123,
    paperTestRequired: true
  }
];

export function StrategyMarketplace({ onInstallBot, onViewDetails, userExperience = 'intermediate' }: StrategyMarketplaceProps) {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'safety' | 'return' | 'sharpe' | 'reviews'>('safety');
  const [showAdvancedOnly, setShowAdvancedOnly] = useState(false);

  const categories = [
    { key: 'all', name: 'All Strategies', icon: '📊' },
    { key: 'ai_signals', name: 'AI Signals', icon: '🤖' },
    { key: 'momentum', name: 'Momentum', icon: '📈' },
    { key: 'mean_reversion', name: 'Mean Reversion', icon: '🔄' },
    { key: 'arbitrage', name: 'Arbitrage', icon: '⚡' },
    { key: 'multi_strategy', name: 'Multi-Strategy', icon: '🎯' }
  ];

  const filteredBots = mockMarketplaceBots
    .filter(bot => {
      if (selectedCategory !== 'all' && bot.category !== selectedCategory) return false;
      if (!showAdvancedOnly && bot.requirements.tradingExperience === 'advanced' && userExperience !== 'advanced') return false;
      return true;
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'safety':
          return b.safetyScore - a.safetyScore;
        case 'return':
          return b.forwardTest.totalReturnNetFees - a.forwardTest.totalReturnNetFees;
        case 'sharpe':
          return b.forwardTest.sharpeRatio - a.forwardTest.sharpeRatio;
        case 'reviews':
          return b.reviews.avgRating - a.reviews.avgRating;
        default:
          return 0;
      }
    });

  const getSafetyColor = (score: number) => {
    if (score >= 90) return 'text-green-600 dark:text-green-400';
    if (score >= 75) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  const getExperienceColor = (level: string) => {
    switch (level) {
      case 'beginner': return 'text-green-600 bg-green-100 dark:bg-green-900/30';
      case 'intermediate': return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/30';
      case 'advanced': return 'text-red-600 bg-red-100 dark:bg-red-900/30';
      default: return 'text-gray-600 bg-gray-100 dark:bg-gray-900/30';
    }
  };

  return (
    <Card className="bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 border-purple-200 dark:border-purple-800">
      <CardHeader className="bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-t-lg">
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-white/20 rounded-lg flex items-center justify-center">
              <span className="text-lg">🏪</span>
            </div>
            <div>
              <span className="text-xl font-bold">Strategy Marketplace</span>
              <div className="text-purple-100 text-sm">
                Curated • Safety-First • Transparent Performance
              </div>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <div className="text-xs text-purple-100 bg-white/10 px-3 py-1 rounded-full">
              {filteredBots.length} strategies available
            </div>
            <Button className="bg-white/20 hover:bg-white/30 text-white border-white/30 text-sm px-3 py-1">
              📤 Submit Strategy
            </Button>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Filters and Controls */}
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex flex-wrap gap-2">
              {categories.map(category => (
                <Button
                  key={category.key}
                  onClick={() => setSelectedCategory(category.key)}
                  size="sm"
                  variant={selectedCategory === category.key ? 'primary' : 'ghost'}
                  className="text-sm"
                >
                  {category.icon} {category.name}
                </Button>
              ))}
            </div>
            
            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-2">
                <span className="text-sm text-purple-700 dark:text-purple-300">Sort by:</span>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as 'safety' | 'return' | 'sharpe' | 'reviews')}
                  className="text-sm border border-purple-200 dark:border-purple-700 rounded px-2 py-1 bg-white dark:bg-gray-900"
                >
                  <option value="safety">Safety Score</option>
                  <option value="return">Net Returns</option>
                  <option value="sharpe">Sharpe Ratio</option>
                  <option value="reviews">User Rating</option>
                </select>
              </div>
              
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="advanced"
                  checked={showAdvancedOnly}
                  onChange={(e) => setShowAdvancedOnly(e.target.checked)}
                  className="rounded"
                />
                <label htmlFor="advanced" className="text-sm text-purple-700 dark:text-purple-300">
                  Show Advanced
                </label>
              </div>
            </div>
          </div>

          {/* Bot Listings */}
          <div className="space-y-4">
            {filteredBots.map((bot) => (
              <div
                key={bot.id}
                className="bg-white dark:bg-gray-900 rounded-lg border border-purple-200 dark:border-purple-800 p-6 hover:shadow-lg transition-shadow"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="text-xl font-semibold">{bot.name}</h3>
                      <span className={`text-xs px-2 py-1 rounded-full ${getExperienceColor(bot.requirements.tradingExperience)}`}>
                        {bot.requirements.tradingExperience}
                      </span>
                      {bot.paperTestRequired && (
                        <span className="text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 px-2 py-1 rounded-full">
                          📝 Paper Test Required
                        </span>
                      )}
                    </div>
                    <p className="text-gray-600 dark:text-gray-400 mb-2">{bot.description}</p>
                    <div className="text-sm text-gray-500">
                      By {bot.author} • {bot.installs} installs • Updated {bot.lastUpdated.toLocaleDateString()}
                    </div>
                  </div>
                  
                  <div className="text-right ml-6">
                    <div className={`text-2xl font-bold mb-1 ${getSafetyColor(bot.safetyScore)}`}>
                      {bot.safetyScore}/100
                    </div>
                    <div className="text-xs text-gray-500">Safety Score</div>
                  </div>
                </div>

                {/* Performance Metrics */}
                <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-4 text-sm">
                  <div className="bg-purple-50 dark:bg-purple-900/20 p-3 rounded-lg">
                    <div className="text-purple-700 dark:text-purple-300">Net Return</div>
                    <div className="font-semibold text-lg text-green-600 dark:text-green-400">
                      +{bot.forwardTest.totalReturnNetFees}%
                    </div>
                    <div className="text-xs text-gray-500">
                      ({bot.forwardTest.duration} forward test)
                    </div>
                  </div>
                  
                  <div className="bg-purple-50 dark:bg-purple-900/20 p-3 rounded-lg">
                    <div className="text-purple-700 dark:text-purple-300">Sharpe Ratio</div>
                    <div className="font-semibold text-lg">{bot.forwardTest.sharpeRatio}</div>
                    <div className="text-xs text-gray-500">Risk-adj. return</div>
                  </div>
                  
                  <div className="bg-purple-50 dark:bg-purple-900/20 p-3 rounded-lg">
                    <div className="text-purple-700 dark:text-purple-300">Max Drawdown</div>
                    <div className="font-semibold text-lg text-red-600 dark:text-red-400">
                      {bot.forwardTest.maxDrawdown}%
                    </div>
                    <div className="text-xs text-gray-500">Worst period</div>
                  </div>
                  
                  <div className="bg-purple-50 dark:bg-purple-900/20 p-3 rounded-lg">
                    <div className="text-purple-700 dark:text-purple-300">Win Rate</div>
                    <div className="font-semibold text-lg">{bot.forwardTest.winRate}%</div>
                    <div className="text-xs text-gray-500">
                      {bot.forwardTest.totalTrades} trades
                    </div>
                  </div>
                  
                  <div className="bg-purple-50 dark:bg-purple-900/20 p-3 rounded-lg">
                    <div className="text-purple-700 dark:text-purple-300">User Rating</div>
                    <div className="font-semibold text-lg text-yellow-600 dark:text-yellow-400">
                      ⭐ {bot.reviews.avgRating}/5
                    </div>
                    <div className="text-xs text-gray-500">
                      {bot.reviews.total} reviews
                    </div>
                  </div>
                </div>

                {/* Fee Impact Transparency */}
                <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-3 mb-4">
                  <div className="text-sm font-medium text-yellow-800 dark:text-yellow-200 mb-2">
                    💰 Fee Impact Analysis
                  </div>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="text-yellow-700 dark:text-yellow-300">Gross Return:</span>
                      <span className="ml-2 font-medium">+{bot.forwardTest.totalReturn}%</span>
                    </div>
                    <div>
                      <span className="text-yellow-700 dark:text-yellow-300">Total Fees:</span>
                      <span className="ml-2 font-medium text-red-600">${bot.forwardTest.feesTotal.toLocaleString()}</span>
                    </div>
                    <div>
                      <span className="text-yellow-700 dark:text-yellow-300">Fee Impact:</span>
                      <span className="ml-2 font-medium text-red-600">
                        -{(bot.forwardTest.totalReturn - bot.forwardTest.totalReturnNetFees).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                </div>

                {/* Key Features and Risks */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
                  <div>
                    <div className="text-sm font-medium mb-2 text-green-700 dark:text-green-300">✅ Key Features</div>
                    <div className="space-y-1">
                      {bot.features.map((feature, idx) => (
                        <div key={idx} className="text-sm text-gray-600 dark:text-gray-400">
                          • {feature}
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <div>
                    <div className="text-sm font-medium mb-2 text-red-700 dark:text-red-300">⚠️ Key Risks</div>
                    <div className="space-y-1">
                      {bot.risks.map((risk, idx) => (
                        <div key={idx} className="text-sm text-gray-600 dark:text-gray-400">
                          • {risk}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Pricing and Actions */}
                <div className="flex items-center justify-between pt-4 border-t border-purple-200 dark:border-purple-700">
                  <div className="flex items-center space-x-4">
                    <div className="text-sm">
                      <span className="text-gray-500">Pricing:</span>
                      <span className="ml-2 font-medium">
                        {bot.pricing.subscriptionFee ? `$${bot.pricing.subscriptionFee}/month` : 'Performance fee only'}
                        {bot.pricing.performanceFee && ` + ${bot.pricing.performanceFee}% performance`}
                      </span>
                    </div>
                    {bot.pricing.freeTrialDays && (
                      <span className="text-xs bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200 px-2 py-1 rounded-full">
                        {bot.pricing.freeTrialDays}-day free trial
                      </span>
                    )}
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <Button
                      onClick={() => onViewDetails?.(bot.id)}
                      size="sm"
                      variant="ghost"
                      className="text-sm"
                    >
                      📊 View Details
                    </Button>
                    <Button
                      onClick={() => onInstallBot?.(bot.id)}
                      size="sm"
                      className="bg-purple-600 text-white hover:bg-purple-700"
                    >
                      {bot.pricing.freeTrialDays ? '🆓 Try Free' : '💳 Subscribe'}
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Marketplace Guidelines */}
          <div className="bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-lg p-4">
            <h4 className="font-semibold mb-3 flex items-center space-x-2 text-emerald-800 dark:text-emerald-200">
              <span>🛡️</span>
              <span>ZiggyAI Marketplace Safety Standards</span>
            </h4>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-emerald-700 dark:text-emerald-300">Verification:</span>
                <span className="ml-2 font-medium">6+ month forward testing required</span>
              </div>
              <div>
                <span className="text-emerald-700 dark:text-emerald-300">Transparency:</span>
                <span className="ml-2 font-medium">Full fee disclosure mandatory</span>
              </div>
              <div>
                <span className="text-emerald-700 dark:text-emerald-300">Safety First:</span>
                <span className="ml-2 font-medium">Risk controls always active</span>
              </div>
              <div>
                <span className="text-emerald-700 dark:text-emerald-300">Reviews:</span>
                <span className="ml-2 font-medium">Verified user feedback only</span>
              </div>
            </div>
            <div className="mt-3 text-xs text-emerald-600 dark:text-emerald-400">
              📋 All strategies undergo bias correction, survivorship analysis, and Coach Mode compatibility testing before approval.
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export type { MarketplaceBotListing, StrategyMarketplaceProps };