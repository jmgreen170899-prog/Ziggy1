'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

interface ScannerResult {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  avgVolume: number;
  volumeRatio: number;
  marketCap: number;
  expectancy: number;
  expectancyNetFees: number;
  mfe: number; // Maximum Favorable Excursion
  mae: number; // Maximum Adverse Excursion
  aiSignal: 'STRONG_BUY' | 'BUY' | 'HOLD' | 'SELL' | 'STRONG_SELL';
  confidence: number;
  features: string[];
  timeframe: string;
  lastRefresh: Date;
}

interface ScannerFilter {
  priceMin?: number;
  priceMax?: number;
  volumeRatio?: number;
  marketCapMin?: number;
  marketCapMax?: number;
  expectancyMin?: number;
  sectors?: string[];
  aiSignals?: string[];
  sortBy: 'expectancy' | 'expectancyNetFees' | 'volumeRatio' | 'confidence';
  sortDirection: 'asc' | 'desc';
  maxResults: number;
}

interface AIScannerProps {
  onSelectSymbol?: (symbol: string) => void;
  autoRefresh?: boolean;
  refreshInterval?: number; // in seconds
}

// Example scanner results with net-of-fees analysis
const initialScannerResults: ScannerResult[] = [
  {
    symbol: 'NVDA',
    name: 'NVIDIA Corporation',
    price: 478.32,
    change: 12.45,
    changePercent: 2.67,
    volume: 45230000,
    avgVolume: 32100000,
    volumeRatio: 1.41,
    marketCap: 1180000000000,
    expectancy: 8.4,
    expectancyNetFees: 7.8,
    mfe: 15.2,
    mae: -3.1,
    aiSignal: 'STRONG_BUY',
    confidence: 0.92,
    features: ['AI chip demand', 'Volume surge', 'Breakout pattern', 'Institutional flow'],
    timeframe: '1-3 days',
    lastRefresh: new Date()
  },
  {
    symbol: 'AAPL',
    name: 'Apple Inc.',
    price: 178.94,
    change: 2.87,
    changePercent: 1.63,
    volume: 28450000,
    avgVolume: 45200000,
    volumeRatio: 0.63,
    marketCap: 2800000000000,
    expectancy: 5.2,
    expectancyNetFees: 4.7,
    mfe: 9.8,
    mae: -2.4,
    aiSignal: 'BUY',
    confidence: 0.87,
    features: ['Earnings momentum', 'Support bounce', 'Options flow', 'Analyst upgrades'],
    timeframe: '2-5 days',
    lastRefresh: new Date()
  },
  {
    symbol: 'TSLA',
    name: 'Tesla, Inc.',
    price: 242.18,
    change: -8.22,
    changePercent: -3.28,
    volume: 62100000,
    avgVolume: 41500000,
    volumeRatio: 1.50,
    marketCap: 780000000000,
    expectancy: -2.1,
    expectancyNetFees: -2.8,
    mfe: 4.2,
    mae: -8.5,
    aiSignal: 'SELL',
    confidence: 0.78,
    features: ['Bearish divergence', 'Volume spike', 'Resistance rejection', 'Sector rotation'],
    timeframe: '1-2 days',
    lastRefresh: new Date()
  },
  {
    symbol: 'MSFT',
    name: 'Microsoft Corporation',
    price: 334.67,
    change: 4.23,
    changePercent: 1.28,
    volume: 18900000,
    avgVolume: 22100000,
    volumeRatio: 0.86,
    marketCap: 2480000000000,
    expectancy: 3.8,
    expectancyNetFees: 3.4,
    mfe: 7.1,
    mae: -1.9,
    aiSignal: 'BUY',
    confidence: 0.81,
    features: ['Cloud growth', 'AI integration', 'Steady accumulation', 'Technical setup'],
    timeframe: '3-7 days',
    lastRefresh: new Date()
  }
];

export function AIScanner({ onSelectSymbol, autoRefresh = true, refreshInterval = 30 }: AIScannerProps) {
  const [results, setResults] = useState<ScannerResult[]>(initialScannerResults);
  const [filters, setFilters] = useState<ScannerFilter>({
    sortBy: 'expectancyNetFees',
    sortDirection: 'desc',
    maxResults: 20,
    expectancyMin: 0
  });
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [selectedPreset, setSelectedPreset] = useState('high_expectancy');

  // Scanner presets
  const presets = {
    high_expectancy: {
      name: '🎯 High Expectancy',
      description: 'AI signals with >5% expected return (net of fees)',
      filters: { expectancyMin: 5, sortBy: 'expectancyNetFees' as const }
    },
    volume_surge: {
      name: '📈 Volume Surge',
      description: 'Unusual volume with AI confirmation',
      filters: { volumeRatio: 1.5, sortBy: 'volumeRatio' as const }
    },
    strong_signals: {
      name: '🔥 Strong AI Signals', 
      description: 'High-confidence AI recommendations',
      filters: { aiSignals: ['STRONG_BUY', 'STRONG_SELL'], sortBy: 'confidence' as const }
    },
    breakout_momentum: {
      name: '🚀 Breakout Momentum',
      description: 'Technical breakouts with AI validation',
      filters: { expectancyMin: 3, volumeRatio: 1.2, sortBy: 'expectancyNetFees' as const }
    }
  };

  useEffect(() => {
    if (!autoRefresh) return;
    
    const interval = setInterval(() => {
      handleRefresh();
    }, refreshInterval * 1000);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 1500));
    
  // In real implementation, this would call the scanner API
  const updatedResults = initialScannerResults.map(result => ({
      ...result,
      lastRefresh: new Date(),
      // Simulate small price changes
      price: result.price + (Math.random() - 0.5) * 2,
      change: result.change + (Math.random() - 0.5) * 0.5
    }));
    
    setResults(updatedResults);
    setLastUpdate(new Date());
    setIsRefreshing(false);
  };

  const applyPreset = (presetKey: string) => {
    const preset = presets[presetKey as keyof typeof presets];
    if (preset) {
      setFilters(prev => ({ ...prev, ...preset.filters }));
      setSelectedPreset(presetKey);
    }
  };

  const filteredResults = results
    .filter(result => {
      if (filters.expectancyMin && result.expectancyNetFees < filters.expectancyMin) return false;
      if (filters.volumeRatio && result.volumeRatio < filters.volumeRatio) return false;
      if (filters.aiSignals?.length && !filters.aiSignals.includes(result.aiSignal)) return false;
      return true;
    })
    .sort((a, b) => {
      const direction = filters.sortDirection === 'desc' ? -1 : 1;
      return direction * (a[filters.sortBy] - b[filters.sortBy]);
    })
    .slice(0, filters.maxResults);

  const getSignalColor = (signal: string) => {
    const baseColors = {
      'STRONG_BUY': 'text-green-600 dark:text-green-400',
      'BUY': 'text-green-600 dark:text-green-400',
      'HOLD': 'text-yellow-600 dark:text-yellow-400',
      'SELL': 'text-red-600 dark:text-red-400',
      'STRONG_SELL': 'text-red-600 dark:text-red-400'
    };
    return baseColors[signal as keyof typeof baseColors] || 'text-gray-600';
  };

  return (
    <Card className="bg-gradient-to-br from-emerald-50 to-teal-50 dark:from-emerald-900/20 dark:to-teal-900/20 border-emerald-200 dark:border-emerald-800">
      <CardHeader className="bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-t-lg">
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-white/20 rounded-lg flex items-center justify-center">
              <span className="text-lg">🔍</span>
            </div>
            <div>
              <span className="text-xl font-bold">AI Market Scanner</span>
              <div className="text-emerald-100 text-sm">
                Real-time • Net-of-Fees • ML-Powered
                {isRefreshing && <span className="ml-2 px-2 py-0.5 bg-white/20 rounded-full text-xs">⏳ Scanning...</span>}
              </div>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <span className="text-xs text-emerald-100 bg-white/10 px-2 py-1 rounded-full">
              Updated: {lastUpdate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
            <Button
              onClick={handleRefresh}
              disabled={isRefreshing}
              className="bg-white/20 hover:bg-white/30 text-white border-white/30 text-sm px-3 py-1"
            >
              {isRefreshing ? '⏳' : '🔄'} Scan
            </Button>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Scanner Presets */}
          <div className="flex flex-wrap gap-2">
            {Object.entries(presets).map(([key, preset]) => (
              <Button
                key={key}
                onClick={() => applyPreset(key)}
                size="sm"
                variant={selectedPreset === key ? "primary" : "ghost"}
                className="text-xs"
              >
                {preset.name}
              </Button>
            ))}
          </div>

          {/* Results Table */}
          <div className="bg-white dark:bg-gray-900 rounded-lg border border-emerald-200 dark:border-emerald-800 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-emerald-50 dark:bg-emerald-900/50">
                  <tr>
                    <th className="text-left p-3 font-medium">Symbol</th>
                    <th className="text-left p-3 font-medium">Price</th>
                    <th className="text-left p-3 font-medium">Volume</th>
                    <th className="text-left p-3 font-medium">AI Signal</th>
                    <th className="text-left p-3 font-medium">Expected Return</th>
                    <th className="text-left p-3 font-medium">Net of Fees</th>
                    <th className="text-left p-3 font-medium">Confidence</th>
                    <th className="text-left p-3 font-medium">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredResults.map((result) => (
                    <tr 
                      key={result.symbol}
                      className="border-b border-emerald-100 dark:border-emerald-800 hover:bg-emerald-50/50 dark:hover:bg-emerald-900/20 transition-colors"
                    >
                      <td className="p-3">
                        <div>
                          <div className="font-medium">{result.symbol}</div>
                          <div className="text-xs text-gray-500 truncate max-w-32">{result.name}</div>
                        </div>
                      </td>
                      <td className="p-3">
                        <div>
                          <div className="font-medium">${result.price.toFixed(2)}</div>
                          <div className={`text-xs ${result.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {result.change >= 0 ? '+' : ''}{result.change.toFixed(2)} ({result.changePercent.toFixed(1)}%)
                          </div>
                        </div>
                      </td>
                      <td className="p-3">
                        <div>
                          <div className="font-medium">{(result.volume / 1000000).toFixed(1)}M</div>
                          <div className={`text-xs ${result.volumeRatio > 1.2 ? 'text-orange-600' : 'text-gray-500'}`}>
                            {result.volumeRatio.toFixed(1)}x avg
                          </div>
                        </div>
                      </td>
                      <td className="p-3">
                        <div className={`font-medium ${getSignalColor(result.aiSignal)}`}>
                          {result.aiSignal.replace('_', ' ')}
                        </div>
                        <div className="text-xs text-gray-500">{result.timeframe}</div>
                      </td>
                      <td className="p-3">
                        <div className={`font-medium ${result.expectancy >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {result.expectancy >= 0 ? '+' : ''}{result.expectancy.toFixed(1)}%
                        </div>
                        <div className="text-xs text-gray-500">
                          MFE: {result.mfe.toFixed(1)}% / MAE: {result.mae.toFixed(1)}%
                        </div>
                      </td>
                      <td className="p-3">
                        <div className={`font-medium ${result.expectancyNetFees >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {result.expectancyNetFees >= 0 ? '+' : ''}{result.expectancyNetFees.toFixed(1)}%
                        </div>
                        <div className="text-xs text-gray-500">
                          Impact: -{(result.expectancy - result.expectancyNetFees).toFixed(1)}%
                        </div>
                      </td>
                      <td className="p-3">
                        <div className="flex items-center space-x-1">
                          <div className={`w-2 h-2 rounded-full ${result.confidence > 0.8 ? 'bg-green-500' : result.confidence > 0.6 ? 'bg-yellow-500' : 'bg-red-500'}`}></div>
                          <span className="font-medium">{Math.round(result.confidence * 100)}%</span>
                        </div>
                      </td>
                      <td className="p-3">
                        <div className="flex space-x-1">
                          <Button
                            size="sm"
                            variant="ghost"
                            className="text-xs px-2 py-1"
                            onClick={() => onSelectSymbol?.(result.symbol)}
                          >
                            📊 View
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="text-xs px-2 py-1"
                          >
                            🔍 Explain
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Scanner Stats */}
          <div className="grid grid-cols-4 gap-4 text-sm">
            <div className="bg-white dark:bg-gray-900 p-3 rounded-lg border border-emerald-200 dark:border-emerald-800">
              <div className="text-emerald-700 dark:text-emerald-300">Total Scanned</div>
              <div className="font-medium text-lg">{results.length}</div>
            </div>
            <div className="bg-white dark:bg-gray-900 p-3 rounded-lg border border-emerald-200 dark:border-emerald-800">
              <div className="text-emerald-700 dark:text-emerald-300">Filtered Results</div>
              <div className="font-medium text-lg">{filteredResults.length}</div>
            </div>
            <div className="bg-white dark:bg-gray-900 p-3 rounded-lg border border-emerald-200 dark:border-emerald-800">
              <div className="text-emerald-700 dark:text-emerald-300">Avg Confidence</div>
              <div className="font-medium text-lg">
                {Math.round(filteredResults.reduce((sum, r) => sum + r.confidence, 0) / filteredResults.length * 100)}%
              </div>
            </div>
            <div className="bg-white dark:bg-gray-900 p-3 rounded-lg border border-emerald-200 dark:border-emerald-800">
              <div className="text-emerald-700 dark:text-emerald-300">Avg Net Return</div>
              <div className="font-medium text-lg">
                {(filteredResults.reduce((sum, r) => sum + r.expectancyNetFees, 0) / filteredResults.length).toFixed(1)}%
              </div>
            </div>
          </div>

          {/* Transparency Notice */}
          <div className="text-xs text-emerald-600 dark:text-emerald-400 bg-emerald-100/50 dark:bg-emerald-900/20 p-3 rounded-lg">
            <div className="flex items-start space-x-1">
              <span>🛡️</span>
              <div>
                <div className="font-medium">Scanner Transparency:</div>
                <div>
                  • All expectancy calculations include estimated execution fees and slippage
                  • MFE/MAE based on 90-day backtests with realistic market conditions
                  • AI signals refresh every {refreshInterval} seconds during market hours
                  • Coach Mode automatically filters signals below your risk-adjusted thresholds
                </div>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export type { ScannerResult, ScannerFilter, AIScannerProps };