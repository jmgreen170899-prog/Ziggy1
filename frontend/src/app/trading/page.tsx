'use client';

import React, { useState, useEffect } from 'react';
import { RequireAuth } from '@/routes/RequireAuth';
import { PageLayout } from '@/components/layout/PageLayout';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { SignalCard } from '@/components/trading/SignalsList';
import { AIScanner } from '@/components/trading/AIScanner';
import { StrategyLab } from '@/components/trading/StrategyLab';
import { PatternEngine } from '@/components/trading/PatternEngine';
import { StrategyMarketplace } from '@/components/trading/StrategyMarketplace';
import { FeeEstimator } from '@/components/trading/FeeEstimator';
import { formatCurrency, formatPercentage, timeAgo, getPriceColor } from '@/utils';
import { apiClient } from '@/services/api';
import type { TradingSignal, Portfolio } from '@/types/api';

// Extended TradingSignal interface for internal use
interface ExtendedTradingSignal extends TradingSignal {
  id: string;
}

// Trade order interface
interface TradeOrder {
  id: string;
  symbol: string;
  type: 'BUY' | 'SELL';
  quantity: number;
  entry_price: number;
  exit_price?: number | null;
  pnl?: number;
  pnl_percent?: number;
  status: 'open' | 'closed';
  opened_at: string;
  closed_at?: string | null;
}

interface PortfolioSummaryProps {
  portfolio: Portfolio;
}

function PortfolioSummary({ portfolio }: PortfolioSummaryProps) {
  // Calculate total value and daily change from portfolio positions
  const totalValue = portfolio.total_value;
  const dailyPnL = portfolio.daily_pnl;
  const dailyPnLPercent = portfolio.daily_pnl_percent;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Portfolio Summary</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="text-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <div className="text-2xl font-bold">{formatCurrency(totalValue)}</div>
            <div className="text-sm text-gray-500">Total Value</div>
          </div>
          <div className="text-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <div className={`text-2xl font-bold ${getPriceColor(dailyPnL)}`}>
              {dailyPnL >= 0 ? '+' : ''}{formatCurrency(dailyPnL)}
            </div>
            <div className={`text-sm ${getPriceColor(dailyPnL)}`}>
              {formatPercentage(dailyPnLPercent)} Today
            </div>
          </div>
        </div>
        
        <div className="space-y-2">
          <h4 className="font-medium text-sm text-gray-600 dark:text-gray-400 mb-3">Current Positions</h4>
          {portfolio.positions.map(position => (
            <div key={position.symbol} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <div>
                <div className="font-semibold">{position.symbol}</div>
                <div className="text-sm text-gray-500">{position.quantity} shares</div>
              </div>
              <div className="text-right">
                <div className="font-bold">{formatCurrency(position.market_value)}</div>
                <div className={`text-sm ${getPriceColor(position.pnl)}`}>
                  {position.pnl >= 0 ? '+' : ''}{formatCurrency(position.pnl)}
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

interface RecentTradesProps {
  trades: TradeOrder[];
}

function RecentTrades({ trades }: RecentTradesProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>
          Recent Trades
          <span className="text-sm font-normal text-gray-500 ml-2">
            {trades.length} recent
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {trades.map((trade: TradeOrder) => (
            <div key={trade.id} className="border-b border-gray-100 dark:border-gray-700 pb-3 last:border-b-0">
              <div className="flex justify-between items-start">
                <div>
                  <div className="font-semibold text-sm">
                    {trade.type} {trade.symbol}
                  </div>
                  <div className="text-xs text-gray-500">
                    {trade.quantity} shares @ {formatCurrency(trade.entry_price)}
                  </div>
                  <div className="text-xs text-gray-500">
                    {timeAgo(trade.opened_at)}
                  </div>
                </div>
                <div className="text-right">
                  <div className={`text-sm font-medium ${getPriceColor(trade.pnl || 0)}`}>
                    {trade.pnl && trade.pnl >= 0 ? '+' : ''}{formatCurrency(trade.pnl || 0)}
                  </div>
                  <div className="text-xs text-gray-500">
                    {trade.status === 'open' ? 'Open' : 'Closed'}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function TradingControls({
  onNewSignal,
  onViewHistory,
  onManageRisk
}: {
  onNewSignal: () => void;
  onViewHistory: () => void;
  onManageRisk: () => void;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Quick Actions</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <Button onClick={onNewSignal} className="w-full" variant="primary">
            🎯 Generate New Signal
          </Button>
          <Button onClick={onViewHistory} className="w-full" variant="ghost">
            📊 View Trade History
          </Button>
          <Button onClick={onManageRisk} className="w-full" variant="ghost">
            🛡️ Manage Risk Settings
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

interface ActiveSignalsProps {
  signals: ExtendedTradingSignal[];
  onExecute?: (id: string) => void;
  onDismiss?: (id: string) => void;
}

function ActiveSignals({ signals, onExecute, onDismiss }: ActiveSignalsProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>
          🎯 Active AI Signals
          <span className="text-sm font-normal text-gray-500">
            {signals.length} active
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {signals.map(signal => (
            <div key={signal.id} className="relative">
              <SignalCard signal={signal} />
              <div className="flex gap-2 mt-3">
                <Button
                  onClick={() => onExecute?.(signal.id)}
                  size="sm"
                  className="flex-1"
                >
                  Execute Trade
                </Button>
                <Button
                  onClick={() => onDismiss?.(signal.id)}
                  size="sm"
                  variant="ghost"
                  className="flex-1"
                >
                  Dismiss
                </Button>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export default function TradingPage() {
  const [activeTab, setActiveTab] = useState<'overview' | 'signals' | 'scanner' | 'lab' | 'patterns' | 'marketplace'>('overview');
  const [tradingSignals, setTradingSignals] = useState<ExtendedTradingSignal[]>([]);
  const [recentTrades, setRecentTrades] = useState<TradeOrder[]>([]);
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [selectedSymbol, setSelectedSymbol] = useState<string>(''); // Used by AIScanner component

  useEffect(() => {
    const fetchTradingData = async () => {
      try {
        if (!refreshing) setLoading(true);
        
        // Fetch all trading data in parallel
        const [signalsData, tradesData, portfolioData] = await Promise.all([
          apiClient.getTradingSignals(),
          apiClient.getTradeOrders(),
          apiClient.getPortfolio()
        ]);

        // Add IDs to signals for consistency with the existing interface
        const signalsWithIds = signalsData.map((signal, index) => ({
          ...signal,
          id: `signal_${signal.symbol}_${index}`
        }));

        setTradingSignals(signalsWithIds);
        setRecentTrades(tradesData);
        setPortfolio(portfolioData);
      } catch (error) {
        console.error('Error fetching trading data:', error);
        // Keep existing state on error - graceful degradation
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    };

    fetchTradingData();
    
    // Refresh data every 30 seconds
    const interval = setInterval(fetchTradingData, 30000);
    return () => clearInterval(interval);
  }, [refreshing]);

  const handleRefresh = async () => {
    setRefreshing(true);
    // The useEffect will handle the actual refresh
  };

  const handleExecuteTrade = (signalId: string) => {
    console.log('Executing signal:', signalId);
    // This would open an order ticket with fee estimation
  };

  const handleDismissSignal = (signalId: string) => {
    console.log('Dismissing signal:', signalId);
  };

  const tabs = [
    { id: 'overview' as const, name: '📊 Portfolio Overview', icon: '📊' },
    { id: 'signals' as const, name: '🎯 AI Signals', icon: '🎯' },
    { id: 'scanner' as const, name: '🔍 Market Scanner', icon: '🔍' },
    { id: 'lab' as const, name: '⚗️ Strategy Lab', icon: '⚗️' },
    { id: 'patterns' as const, name: '🔬 Pattern Engine', icon: '🔬' },
    { id: 'marketplace' as const, name: '🏪 Marketplace', icon: '🏪' }
  ];

  if (loading) {
    return (
      <RequireAuth>
        <PageLayout title="Trading">
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600 dark:text-gray-400">Loading trading data...</p>
            </div>
          </div>
        </PageLayout>
      </RequireAuth>
    );
  }

  return (
    <RequireAuth>
      <PageLayout
        title="Advanced Trading Platform"
        subtitle="AI-Powered • Transparent Fees • Safety-First • Net-of-Fees Analysis"
        theme="trading"
        actions={
          <div className="flex items-center space-x-3">
            <Button
              onClick={handleRefresh}
              disabled={refreshing}
              variant="ghost"
              className="text-sm"
            >
              {refreshing ? '🔄' : '↻'} Refresh
            </Button>
            <Button
              variant="ghost"
              className="text-sm"
            >
              📝 Paper Mode
            </Button>
            <Button
              variant="ghost"
              className="text-sm"
            >
              ⚙️ Settings
            </Button>
          </div>
        }
      >
        {/* Tab Navigation */}
        <div className="mb-6">
          <div className="flex flex-wrap gap-2">
            {tabs.map((tab) => (
              <Button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                variant={activeTab === tab.id ? 'primary' : 'ghost'}
                className="text-sm"
              >
                {tab.icon} {tab.name}
              </Button>
            ))}
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && portfolio && (
          <div className="space-y-6">
            {/* Portfolio Summary */}
            <PortfolioSummary portfolio={portfolio} />
            
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <ActiveSignals
                  signals={tradingSignals}
                  onExecute={handleExecuteTrade}
                  onDismiss={handleDismissSignal}
                />
              </div>
              <div className="space-y-6">
                <TradingControls
                  onNewSignal={() => setActiveTab('signals')}
                  onViewHistory={() => console.log('View history')}
                  onManageRisk={() => console.log('Manage risk')}
                />
                <RecentTrades trades={recentTrades} />
              </div>
            </div>

            {/* Fee Estimator Demo */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <FeeEstimator
                symbol="AAPL"
                quantity={100}
                price={178.50}
                side="BUY"
                venue="IBKR"
                showBreakdown={true}
              />
              <Card>
                <CardHeader>
                  <CardTitle>💡 ZiggyAI Coach Insights</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3 text-sm">
                    <div className="p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                      <div className="font-medium text-green-800 dark:text-green-200">🎯 Coach Mode Active</div>
                      <div className="text-green-700 dark:text-green-300">
                        Based on your trading pattern, consider reducing position sizes during high volatility periods.
                      </div>
                    </div>
                    <div className="p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                      <div className="font-medium text-blue-800 dark:text-blue-200">💰 Fee Optimization</div>
                      <div className="text-blue-700 dark:text-blue-300">
                        Your trading frequency suggests PnL share model could save $1,200 annually.
                      </div>
                    </div>
                    <div className="p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
                      <div className="font-medium text-yellow-800 dark:text-yellow-200">⚠️ Risk Notice</div>
                      <div className="text-yellow-700 dark:text-yellow-300">
                        Portfolio concentration in tech sector at 38%. Consider diversification.
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        )}

        {activeTab === 'signals' && (
          <div className="space-y-6">
            <ActiveSignals
              signals={tradingSignals}
              onExecute={handleExecuteTrade}
              onDismiss={handleDismissSignal}
            />
          </div>
        )}

        {activeTab === 'scanner' && (
          <div className="space-y-6">
            <AIScanner
              onSelectSymbol={setSelectedSymbol}
              autoRefresh={true}
              refreshInterval={30}
            />
          </div>
        )}

        {activeTab === 'lab' && (
          <div className="space-y-6">
            <StrategyLab
              onDeployStrategy={(id) => console.log('Deploying strategy:', id)}
            />
          </div>
        )}

        {activeTab === 'patterns' && (
          <div className="space-y-6">
            <PatternEngine
              onPatternSelect={(pattern) => console.log('Selected pattern:', pattern)}
              onTrendSelect={(trend) => console.log('Selected trend:', trend)}
              autoRefresh={true}
            />
          </div>
        )}

        {activeTab === 'marketplace' && (
          <div className="space-y-6">
            <StrategyMarketplace
              onInstallBot={(id) => console.log('Installing bot:', id)}
              onViewDetails={(id) => console.log('Viewing bot details:', id)}
              userExperience="intermediate"
            />
          </div>
        )}
      </PageLayout>
    </RequireAuth>
  );
}