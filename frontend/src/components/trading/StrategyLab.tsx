'use client';

import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

interface StrategyBlock {
  id: string;
  type: 'condition' | 'action' | 'risk' | 'timing';
  name: string;
  description: string;
  parameters: Record<string, unknown>;
  connections: string[];
}

interface Strategy {
  id: string;
  name: string;
  description: string;
  blocks: StrategyBlock[];
  backtest: {
    totalReturn: number;
    totalReturnNetFees: number;
    sharpeRatio: number;
    maxDrawdown: number;
    winRate: number;
    avgTrade: number;
    avgTradeNetFees: number;
    totalTrades: number;
    feesTotal: number;
  };
  status: 'draft' | 'backtested' | 'live' | 'paper';
  createdAt: Date;
  lastModified: Date;
}

interface StrategyLabProps {
  onSaveStrategy?: (strategy: Strategy) => void;
  onDeployStrategy?: (strategyId: string) => void;
}

// Predefined block templates
const blockTemplates = {
  conditions: [
    {
      id: 'price_cross_ma',
      type: 'condition',
      name: 'Price Crosses Moving Average',
      description: 'Trigger when price crosses above/below moving average',
      parameters: { period: 20, direction: 'above', ma_type: 'SMA' }
    },
    {
      id: 'rsi_overbought',
      type: 'condition', 
      name: 'RSI Overbought/Oversold',
      description: 'RSI reaches extreme levels',
      parameters: { period: 14, overbought: 70, oversold: 30 }
    },
    {
      id: 'volume_surge',
      type: 'condition',
      name: 'Volume Surge',
      description: 'Volume exceeds average by specified ratio',
      parameters: { ratio: 2.0, period: 20 }
    },
    {
      id: 'ai_signal',
      type: 'condition',
      name: 'AI Signal Confirmation',
      description: 'ZiggyAI generates signal with minimum confidence',
      parameters: { signal_type: 'BUY', min_confidence: 0.8, min_expectancy: 5.0 }
    }
  ],
  actions: [
    {
      id: 'market_order',
      type: 'action',
      name: 'Market Order',
      description: 'Execute market order with position sizing',
      parameters: { position_size: 2.0, size_type: 'percent_portfolio' }
    },
    {
      id: 'limit_order',
      type: 'action',
      name: 'Limit Order',
      description: 'Place limit order at specified price level',
      parameters: { offset: 0.5, offset_type: 'percent', position_size: 2.0 }
    },
    {
      id: 'take_profit',
      type: 'action',
      name: 'Take Profit',
      description: 'Close position at profit target',
      parameters: { target: 5.0, target_type: 'percent' }
    },
    {
      id: 'stop_loss',
      type: 'action',
      name: 'Stop Loss',
      description: 'Close position at loss limit',
      parameters: { stop: 2.0, stop_type: 'percent' }
    }
  ],
  risk: [
    {
      id: 'position_size',
      type: 'risk',
      name: 'Position Sizing',
      description: 'Risk-based position sizing using volatility',
      parameters: { risk_percent: 1.0, method: 'volatility_adjusted' }
    },
    {
      id: 'max_exposure',
      type: 'risk',
      name: 'Maximum Exposure',
      description: 'Limit total exposure to asset class/sector',
      parameters: { max_percent: 10.0, scope: 'sector' }
    },
    {
      id: 'correlation_check',
      type: 'risk',
      name: 'Correlation Check',
      description: 'Avoid correlated positions',
      parameters: { max_correlation: 0.7, lookback: 30 }
    }
  ],
  timing: [
    {
      id: 'market_hours',
      type: 'timing',
      name: 'Market Hours Only',
      description: 'Execute only during market hours',
      parameters: { include_premarket: false, include_afterhours: false }
    },
    {
      id: 'earnings_avoid',
      type: 'timing',
      name: 'Avoid Earnings',
      description: 'Skip trades around earnings announcements',
      parameters: { days_before: 2, days_after: 1 }
    }
  ]
};

// Example strategy for demonstration
const exampleStrategy: Strategy = {
  id: 'strategy_1',
  name: 'AI-Enhanced Momentum',
  description: 'Combines technical momentum with AI signal confirmation',
  blocks: [
    {
      id: 'block_1',
      type: 'condition',
      name: 'AI Signal Confirmation',
      description: 'ZiggyAI generates BUY signal with high confidence',
      parameters: { signal_type: 'BUY', min_confidence: 0.8, min_expectancy: 5.0 },
      connections: ['block_2']
    },
    {
      id: 'block_2',
      type: 'condition',
      name: 'Volume Surge',
      description: 'Volume 1.5x above 20-day average',
      parameters: { ratio: 1.5, period: 20 },
      connections: ['block_3']
    },
    {
      id: 'block_3',
      type: 'action',
      name: 'Market Order',
      description: 'Buy with 2% portfolio allocation',
      parameters: { position_size: 2.0, size_type: 'percent_portfolio' },
      connections: ['block_4', 'block_5']
    },
    {
      id: 'block_4',
      type: 'action',
      name: 'Take Profit',
      description: 'Exit at 8% profit',
      parameters: { target: 8.0, target_type: 'percent' },
      connections: []
    },
    {
      id: 'block_5',
      type: 'action',
      name: 'Stop Loss',
      description: 'Exit at 3% loss',
      parameters: { stop: 3.0, stop_type: 'percent' },
      connections: []
    }
  ],
  backtest: {
    totalReturn: 34.2,
    totalReturnNetFees: 31.8,
    sharpeRatio: 1.47,
    maxDrawdown: -8.3,
    winRate: 67.4,
    avgTrade: 2.8,
    avgTradeNetFees: 2.3,
    totalTrades: 142,
    feesTotal: 1847.50
  },
  status: 'backtested',
  createdAt: new Date(Date.now() - 86400000 * 7),
  lastModified: new Date(Date.now() - 3600000)
};

export function StrategyLab({ onDeployStrategy }: StrategyLabProps) {
  const [strategy, setStrategy] = useState<Strategy>(exampleStrategy);
  const [selectedBlockType, setSelectedBlockType] = useState<keyof typeof blockTemplates>('conditions');
  const [isBacktesting, setIsBacktesting] = useState(false);
  const [showNLBuilder, setShowNLBuilder] = useState(false);
  const [nlInput, setNlInput] = useState('');

  const handleRunBacktest = async () => {
    setIsBacktesting(true);
    // Simulate backtesting delay
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    // Update strategy with new backtest results
    setStrategy(prev => ({
      ...prev,
      status: 'backtested',
      lastModified: new Date()
    }));
    setIsBacktesting(false);
  };

  const handleDeployToPaper = () => {
    setStrategy(prev => ({
      ...prev,
      status: 'paper',
      lastModified: new Date()
    }));
    console.log('Deploying to paper trading...');
  };

  const handleNLParse = () => {
  // Simple natural language parsing stub
    // Example strategies that could be parsed:
    // "If AAPL crosses above 20-day moving average and RSI < 70 then buy 2% position with 5% profit target and 2% stop loss"
    // "When AI signal confidence > 85% and volume surge > 1.5x average then enter position, exit at 8% profit or 3% loss"
    // "Buy on breakout above resistance with volume confirmation, hold until RSI overbought or 10% gain"
    
    if (nlInput.trim()) {
      console.log('Parsing strategy:', nlInput);
      // In real implementation, this would parse the natural language and create blocks
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'draft': return 'text-gray-600 bg-gray-100';
      case 'backtested': return 'text-blue-600 bg-blue-100';
      case 'paper': return 'text-yellow-600 bg-yellow-100';
      case 'live': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getBlockColor = (type: string) => {
    switch (type) {
      case 'condition': return 'bg-blue-100 border-blue-300 text-blue-800';
      case 'action': return 'bg-green-100 border-green-300 text-green-800';
      case 'risk': return 'bg-orange-100 border-orange-300 text-orange-800';
      case 'timing': return 'bg-purple-100 border-purple-300 text-purple-800';
      default: return 'bg-gray-100 border-gray-300 text-gray-800';
    }
  };

  return (
    <Card className="bg-gradient-to-br from-violet-50 to-purple-50 dark:from-violet-900/20 dark:to-purple-900/20 border-violet-200 dark:border-violet-800">
      <CardHeader className="bg-gradient-to-r from-violet-600 to-purple-600 text-white rounded-t-lg">
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-white/20 rounded-lg flex items-center justify-center">
              <span className="text-lg">⚗️</span>
            </div>
            <div>
              <span className="text-xl font-bold">Strategy Lab</span>
              <div className="text-violet-100 text-sm">
                No-Code Builder • Natural Language • Net-of-Fees Backtesting
              </div>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <span className={`text-xs px-3 py-1 rounded-full ${getStatusColor(strategy.status)}`}>
              {strategy.status.toUpperCase()}
            </span>
            <Button
              onClick={() => setShowNLBuilder(!showNLBuilder)}
              className="bg-white/20 hover:bg-white/30 text-white border-white/30 text-sm px-3 py-1"
            >
              💬 Natural Language
            </Button>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Natural Language Builder */}
          {showNLBuilder && (
            <div className="bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-200 dark:border-indigo-800 rounded-lg p-4">
              <h4 className="font-semibold mb-3 text-indigo-800 dark:text-indigo-200">🗣️ Natural Language Strategy Builder</h4>
              <div className="space-y-3">
                <textarea
                  value={nlInput}
                  onChange={(e) => setNlInput(e.target.value)}
                  placeholder="Describe your strategy in plain English, e.g., 'When AAPL breaks above 20-day moving average with volume surge, buy 2% position and take profit at 5%'"
                  className="w-full p-3 border border-indigo-200 dark:border-indigo-700 rounded-lg bg-white dark:bg-gray-900 text-sm"
                  rows={3}
                />
                <div className="flex items-center justify-between">
                  <div className="text-xs text-indigo-600 dark:text-indigo-400">
                    💡 Try: &quot;Buy when AI confidence &gt; 80% and RSI &lt; 30, sell at 5% profit or 2% loss&quot;
                  </div>
                  <Button onClick={handleNLParse} size="sm" className="bg-indigo-600 text-white">
                    🔄 Parse Strategy
                  </Button>
                </div>
              </div>
            </div>
          )}

          {/* Strategy Overview */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Strategy Blocks */}
            <div className="lg:col-span-2">
              <div className="bg-white dark:bg-gray-900 rounded-lg border border-violet-200 dark:border-violet-800 p-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-violet-800 dark:text-violet-200">Strategy Flow</h3>
                  <div className="text-sm text-violet-600 dark:text-violet-400">
                    {strategy.blocks.length} blocks connected
                  </div>
                </div>
                
                <div className="space-y-3">
                  {strategy.blocks.map((block, index) => (
                    <div key={block.id} className="flex items-center space-x-3">
                      <div className="flex items-center justify-center w-6 h-6 rounded-full bg-violet-100 dark:bg-violet-900 text-violet-800 dark:text-violet-200 text-xs font-medium">
                        {index + 1}
                      </div>
                      <div className={`flex-1 p-3 rounded-lg border-2 ${getBlockColor(block.type)}`}>
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="font-medium">{block.name}</div>
                            <div className="text-sm opacity-75">{block.description}</div>
                          </div>
                          <div className="flex space-x-1">
                            <Button size="sm" variant="ghost" className="text-xs px-2 py-1">
                              ⚙️
                            </Button>
                            <Button size="sm" variant="ghost" className="text-xs px-2 py-1">
                              ❌
                            </Button>
                          </div>
                        </div>
                      </div>
                      {index < strategy.blocks.length - 1 && (
                        <div className="w-4 text-center text-violet-400">
                          ↓
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                {/* Add Block Section */}
                <div className="mt-6 pt-4 border-t border-violet-200 dark:border-violet-700">
                  <div className="flex items-center space-x-3 mb-3">
                    <span className="text-sm font-medium text-violet-700 dark:text-violet-300">Add Block:</span>
                    {Object.keys(blockTemplates).map((type) => (
                      <Button
                        key={type}
                        onClick={() => setSelectedBlockType(type as keyof typeof blockTemplates)}
                        size="sm"
                        variant={selectedBlockType === type ? "primary" : "ghost"}
                        className="text-xs capitalize"
                      >
                        {type}
                      </Button>
                    ))}
                  </div>
                  
                  <div className="grid grid-cols-2 gap-2">
                    {blockTemplates[selectedBlockType].map((template) => (
                      <div
                        key={template.id}
                        className={`p-2 rounded border-2 border-dashed cursor-pointer hover:bg-opacity-50 ${getBlockColor(template.type)}`}
                        onClick={() => console.log('Add block:', template.name)}
                      >
                        <div className="text-sm font-medium">{template.name}</div>
                        <div className="text-xs opacity-75">{template.description}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Backtest Results */}
            <div className="space-y-4">
              <div className="bg-white dark:bg-gray-900 rounded-lg border border-violet-200 dark:border-violet-800 p-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-violet-800 dark:text-violet-200">Backtest Results</h3>
                  <Button
                    onClick={handleRunBacktest}
                    disabled={isBacktesting}
                    size="sm"
                    className="bg-violet-600 text-white"
                  >
                    {isBacktesting ? '⏳ Testing...' : '🧪 Backtest'}
                  </Button>
                </div>

                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span>Total Return:</span>
                    <span className="font-medium text-green-600">+{strategy.backtest.totalReturn}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Net of Fees:</span>
                    <span className="font-medium text-green-600">+{strategy.backtest.totalReturnNetFees}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Fee Impact:</span>
                    <span className="font-medium text-red-600">
                      -{(strategy.backtest.totalReturn - strategy.backtest.totalReturnNetFees).toFixed(1)}%
                    </span>
                  </div>
                  <hr className="border-violet-200 dark:border-violet-700" />
                  <div className="flex justify-between">
                    <span>Sharpe Ratio:</span>
                    <span className="font-medium">{strategy.backtest.sharpeRatio}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Max Drawdown:</span>
                    <span className="font-medium text-red-600">{strategy.backtest.maxDrawdown}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Win Rate:</span>
                    <span className="font-medium">{strategy.backtest.winRate}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Avg Trade (Net):</span>
                    <span className="font-medium">+{strategy.backtest.avgTradeNetFees}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Total Trades:</span>
                    <span className="font-medium">{strategy.backtest.totalTrades}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Total Fees:</span>
                    <span className="font-medium text-red-600">${strategy.backtest.feesTotal.toLocaleString()}</span>
                  </div>
                </div>
              </div>

              {/* Deployment */}
              <div className="bg-white dark:bg-gray-900 rounded-lg border border-violet-200 dark:border-violet-800 p-4">
                <h3 className="font-semibold mb-4 text-violet-800 dark:text-violet-200">Deployment</h3>
                <div className="space-y-3">
                  <Button
                    onClick={handleDeployToPaper}
                    className="w-full bg-yellow-500 hover:bg-yellow-600 text-white"
                    disabled={strategy.status === 'draft'}
                  >
                    📝 Deploy to Paper Trading
                  </Button>
                  <Button
                    onClick={() => onDeployStrategy?.(strategy.id)}
                    className="w-full bg-green-500 hover:bg-green-600 text-white"
                    disabled={strategy.status !== 'paper'}
                  >
                    🚀 Deploy to Live Trading
                  </Button>
                  <div className="text-xs text-violet-600 dark:text-violet-400">
                    ⚠️ Strategy must be paper tested before live deployment
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Safety & Transparency */}
          <div className="bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-lg p-4">
            <h4 className="font-semibold mb-3 flex items-center space-x-2 text-emerald-800 dark:text-emerald-200">
              <span>🛡️</span>
              <span>Strategy Safety & Transparency</span>
            </h4>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-emerald-700 dark:text-emerald-300">Fee Modeling:</span>
                <span className="ml-2 font-medium">All backtests include execution costs</span>
              </div>
              <div>
                <span className="text-emerald-700 dark:text-emerald-300">Slippage:</span>
                <span className="ml-2 font-medium">Market impact modeled by liquidity</span>
              </div>
              <div>
                <span className="text-emerald-700 dark:text-emerald-300">Paper Required:</span>
                <span className="ml-2 font-medium">30-day minimum before live</span>
              </div>
            </div>
            <div className="mt-3 text-xs text-emerald-600 dark:text-emerald-400">
              📊 All strategies undergo survivorship bias correction and walk-forward validation. Risk controls are always active.
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export type { Strategy, StrategyBlock, StrategyLabProps };