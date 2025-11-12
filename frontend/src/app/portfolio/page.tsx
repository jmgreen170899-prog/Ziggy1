'use client';

import React, { useState, useEffect } from 'react';
import { RequireAuth } from '@/routes/RequireAuth';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { EmptyState } from '@/components/ui/EmptyState';
import { PageLayout, ThemedButton, ThemedCard } from '@/components/layout/PageLayout';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { CardSkeleton } from '@/components/ui/Loading';
import { formatCurrency, formatPercentage, getPriceColor, formatDateTime } from '@/utils';
import { useLiveData } from '@/hooks/useLiveData';
import { usePortfolio } from '@/hooks';
import { Activity } from 'lucide-react';
import type { Portfolio, PortfolioPosition } from '@/types/api';
import apiClient from '@/services/api';
import { guardRealData } from '@/lib/guardRealData';

// Removed dev portfolio sample; rely on real data only.

interface PortfolioSummaryProps {
  portfolio: Portfolio;
}

function PortfolioSummary({ portfolio }: PortfolioSummaryProps) {
  const totalPnl = portfolio.positions.reduce((sum, pos) => sum + pos.pnl, 0);
  const totalCost = portfolio.total_value - totalPnl;
  const overallReturn = (totalPnl / totalCost) * 100;

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <ThemedCard>
        <CardContent className="p-6 text-center">
          <div className="text-3xl font-bold">{formatCurrency(portfolio.total_value)}</div>
          <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">Total Portfolio Value</div>
        </CardContent>
      </ThemedCard>
      
      <ThemedCard>
        <CardContent className="p-6 text-center">
          <div className={`text-3xl font-bold ${getPriceColor(portfolio.daily_pnl)}`}>
            {portfolio.daily_pnl >= 0 ? '+' : ''}{formatCurrency(portfolio.daily_pnl)}
          </div>
          <div className={`text-sm mt-1 ${getPriceColor(portfolio.daily_pnl)}`}>
            {formatPercentage(portfolio.daily_pnl_percent)} Today
          </div>
        </CardContent>
      </ThemedCard>
      
      <ThemedCard>
        <CardContent className="p-6 text-center">
          <div className={`text-3xl font-bold ${getPriceColor(totalPnl)}`}>
            {totalPnl >= 0 ? '+' : ''}{formatCurrency(totalPnl)}
          </div>
          <div className={`text-sm mt-1 ${getPriceColor(totalPnl)}`}>
            {formatPercentage(overallReturn)} Total Return
          </div>
        </CardContent>
      </ThemedCard>
      
      <ThemedCard>
        <CardContent className="p-6 text-center">
          <div className="text-3xl font-bold">{formatCurrency(portfolio.cash_balance)}</div>
          <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">Available Cash</div>
        </CardContent>
      </ThemedCard>
    </div>
  );
}

interface PositionCardProps {
  position: PortfolioPosition;
  onManage?: (symbol: string) => void;
}

function PositionCard({ position, onManage }: PositionCardProps) {
  const costBasis = position.quantity * position.avg_price;

  return (
    <Card className="card-elevated group">
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-2xl font-bold text-fg group-hover:text-accent transition-colors">
              {position.symbol}
            </h3>
            <div className="text-sm text-fg-muted font-medium mt-1">
              {position.quantity} shares
            </div>
          </div>
          
          <div className="text-right">
            <div className="text-3xl font-bold text-fg">{formatCurrency(position.market_value)}</div>
            <div className={`text-base font-bold mt-1 ${getPriceColor(position.pnl)}`}>
              {position.pnl >= 0 ? '+' : ''}{formatCurrency(position.pnl)} ({formatPercentage(position.pnl_percent)})
            </div>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-6 mb-6 pb-6 border-b border-border">
          <div>
            <div className="text-xs text-fg-muted font-medium uppercase tracking-wide mb-1">Avg Cost</div>
            <div className="font-bold text-lg text-fg">{formatCurrency(position.avg_price)}</div>
          </div>
          <div>
            <div className="text-xs text-fg-muted font-medium uppercase tracking-wide mb-1">Current Price</div>
            <div className="font-bold text-lg text-fg">{formatCurrency(position.current_price)}</div>
          </div>
          <div>
            <div className="text-xs text-fg-muted font-medium uppercase tracking-wide mb-1">Cost Basis</div>
            <div className="font-bold text-lg text-fg">{formatCurrency(costBasis)}</div>
          </div>
        </div>

        <div className="flex gap-3">
          <Button onClick={() => onManage?.(position.symbol)} variant="primary" size="sm" className="flex-1">
            Manage Position
          </Button>
          <Button variant="secondary" size="sm" className="flex-1">
            View Chart
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

interface AllocationChartProps {
  positions: PortfolioPosition[];
}

function AllocationChart({ positions }: AllocationChartProps) {
  const totalValue = positions.reduce((sum, pos) => sum + pos.market_value, 0);
  const sortedPositions = [...positions].sort((a, b) => b.market_value - a.market_value);
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Portfolio Allocation</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {sortedPositions.map((position, index) => {
            const percentage = (position.market_value / totalValue) * 100;
            const colors = [
              'bg-blue-500', 'bg-green-500', 'bg-yellow-500', 'bg-red-500', 
              'bg-purple-500', 'bg-pink-500', 'bg-indigo-500'
            ];
            const color = colors[index % colors.length];
            
            return (
              <div key={position.symbol}>
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="font-medium">{position.symbol}</span>
                  <span>{percentage.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full ${color}`}
                    style={{ width: `${percentage}%` }}
                  ></div>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

interface PerformanceMetricsProps {
  positions: PortfolioPosition[];
}

function PerformanceMetrics({ positions }: PerformanceMetricsProps) {
  const gainers = positions.filter(pos => pos.pnl > 0);
  const losers = positions.filter(pos => pos.pnl < 0);
  const bestPerformer = positions.reduce((best, current) => 
    current.pnl_percent > best.pnl_percent ? current : best
  );
  const worstPerformer = positions.reduce((worst, current) => 
    current.pnl_percent < worst.pnl_percent ? current : worst
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>Performance Metrics</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
            <div className="text-2xl font-bold text-green-600">{gainers.length}</div>
            <div className="text-sm text-green-700 dark:text-green-400">Gainers</div>
          </div>
          
          <div className="p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
            <div className="text-2xl font-bold text-red-600">{losers.length}</div>
            <div className="text-sm text-red-700 dark:text-red-400">Losers</div>
          </div>
          
          <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <div className="font-bold text-blue-600">{bestPerformer.symbol}</div>
            <div className="text-sm text-blue-700 dark:text-blue-400">Best: +{formatPercentage(bestPerformer.pnl_percent)}</div>
          </div>
          
          <div className="p-3 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
            <div className="font-bold text-orange-600">{worstPerformer.symbol}</div>
            <div className="text-sm text-orange-700 dark:text-orange-400">Worst: {formatPercentage(worstPerformer.pnl_percent)}</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

interface RecentActivityProps {
  activities: Array<{
    id: string;
    type: 'buy' | 'sell' | 'dividend';
    symbol: string;
    quantity?: number;
    price?: number;
    amount: number;
    date: string;
  }>;
}

function RecentActivity({ activities }: RecentActivityProps) {
  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'buy': return '🟢';
      case 'sell': return '🔴';
      case 'dividend': return '💰';
      default: return '📊';
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3 max-h-64 overflow-y-auto">
          {activities.map(activity => (
            <div key={activity.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <div className="flex items-center gap-3">
                <span className="text-lg">{getActivityIcon(activity.type)}</span>
                <div>
                  <div className="font-medium text-sm">
                    {activity.type.toUpperCase()} {activity.symbol}
                    {activity.quantity && ` (${activity.quantity} shares)`}
                  </div>
                  <div className="text-xs text-gray-500">
                    {formatDateTime(activity.date)}
                    {activity.price && ` @ ${formatCurrency(activity.price)}`}
                  </div>
                </div>
              </div>
              <div className={`font-medium text-sm ${activity.type === 'sell' || activity.type === 'dividend' ? 'text-green-600' : 'text-red-600'}`}>
                {activity.type === 'sell' || activity.type === 'dividend' ? '+' : '-'}{formatCurrency(Math.abs(activity.amount))}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export default function PortfolioPage() {
  const [viewMode, setViewMode] = useState<'overview' | 'positions' | 'analytics'>('overview');
  const [refreshing, setRefreshing] = useState(false);
  const [recentTrades, setRecentTrades] = useState<Array<{ id: string; type: 'buy' | 'sell' | 'dividend'; symbol: string; quantity?: number; price?: number; amount: number; date: string }>>([]);

  // Get real portfolio data from WebSocket
  const {
    portfolio,
    loading: portfolioLoading,
    error: portfolioError,
    fetchPortfolio,
    retry: retryPortfolio
  } = usePortfolio();

  // Get live market data for portfolio symbols
  const portfolioSymbols = portfolio?.positions?.map(pos => pos.symbol) || ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA'];
  const {
    getQuote,
    isConnected: liveDataConnected,
    lastUpdate
  } = useLiveData({
    symbols: portfolioSymbols,
    autoConnect: true,
    maxNewsItems: 5
  });

  useEffect(() => {
    fetchPortfolio();
  }, [fetchPortfolio]);

  // Load recent trades from backend orders
  useEffect(() => {
    const loadTrades = async () => {
      try {
        const orders = await apiClient.getTradeOrders();
        const mapped = orders.slice(0, 10).map(o => ({
          id: o.id,
          type: (o.type.toLowerCase() as 'buy' | 'sell'),
          symbol: o.symbol,
          quantity: o.quantity,
          price: o.entry_price,
          amount: (o.type === 'SELL' ? 1 : -1) * (o.quantity * o.entry_price),
          date: o.opened_at
        }));
        setRecentTrades(mapped);
      } catch {
        // keep empty on failure
      }
    };
    loadTrades();
  }, []);

  // Enhanced portfolio data with live prices
  const enhancedPortfolio = portfolio ? {
    ...portfolio,
    positions: portfolio.positions?.map(position => {
      const liveQuote = getQuote(position.symbol);
      return {
        ...position,
        current_price: liveQuote?.price || position.current_price,
        // Recalculate with live price
        market_value: (liveQuote?.price || position.current_price) * position.quantity,
        pnl: ((liveQuote?.price || position.current_price) - position.avg_price) * position.quantity,
        pnl_percent: (((liveQuote?.price || position.current_price) / position.avg_price) - 1) * 100,
        is_live: !!liveQuote
      };
    }) || []
  } : null;

  if (process.env.NODE_ENV === 'development' && enhancedPortfolio) {
    guardRealData('PortfolioSummary', [
      enhancedPortfolio.total_value,
      enhancedPortfolio.daily_pnl,
      ...enhancedPortfolio.positions.slice(0, 5).map(p => p.market_value)
    ]);
  }

  const handleRefresh = async () => {
    setRefreshing(true);
    await new Promise(resolve => setTimeout(resolve, 1000));
    setRefreshing(false);
  };

  const handleManagePosition = (symbol: string) => {
    alert(`Manage ${symbol} position - This would open position management modal`);
  };

  const recentActivities = recentTrades;

  return (
    <RequireAuth>
      <ErrorBoundary 
        fallback={
          <PageLayout 
            title="Portfolio Overview" 
            subtitle="Track your investments and portfolio performance"
            breadcrumbs={['Portfolio']}
          >
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 space-y-6">
                <CardSkeleton showHeader contentLines={4} />
                <CardSkeleton showHeader contentLines={6} />
              </div>
              <div className="space-y-6">
                <CardSkeleton showHeader contentLines={3} />
                <CardSkeleton showHeader contentLines={4} />
              </div>
            </div>
          </PageLayout>
        }
      >
        <PageLayout 
          title="Portfolio Overview" 
          subtitle="Track your investments and portfolio performance"
          breadcrumbs={['Portfolio']}
          rightContent={
            <div className="flex items-center gap-3">
              <div className="flex rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
                <ThemedButton
                  variant={viewMode === 'overview' ? 'primary' : 'outline'}
                onClick={() => setViewMode('overview')}
                size="sm"
              >
                📊 Overview
              </ThemedButton>
              <ThemedButton
                variant={viewMode === 'positions' ? 'primary' : 'outline'}
                onClick={() => setViewMode('positions')}
                size="sm"
              >
                💼 Positions
              </ThemedButton>
              <ThemedButton
                variant={viewMode === 'analytics' ? 'primary' : 'outline'}
                onClick={() => setViewMode('analytics')}
                size="sm"
              >
                📈 Analytics
              </ThemedButton>
            </div>
            <ThemedButton 
              onClick={handleRefresh}
              disabled={refreshing}
              variant="outline"
              size="sm"
            >
              {refreshing ? '🔄' : '↻'} Refresh
            </ThemedButton>
          </div>
        }
      >
        <div className="space-y-6">
          {/* Live Data Connection Status */}
          {liveDataConnected && (
            <div className="flex items-center justify-between bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <Activity className="w-5 h-5 text-green-600" />
                <span className="text-green-700 font-medium">Live Portfolio Data Active</span>
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              </div>
              {lastUpdate?.portfolio && (
                <span className="text-sm text-green-600">
                  Updated: {new Date(lastUpdate.portfolio).toLocaleTimeString()}
                </span>
              )}
            </div>
          )}

          {/* Portfolio Summary - using real data */}
          {enhancedPortfolio ? (
            <PortfolioSummary portfolio={enhancedPortfolio} />
          ) : portfolioLoading ? (
            <div className="text-center py-8">
              <Activity className="w-8 h-8 mx-auto mb-2 animate-spin text-blue-500" />
              <p>Loading portfolio data...</p>
            </div>
          ) : portfolioError ? (
            <div className="text-center py-8 text-red-500">
              <p>Error loading portfolio: {portfolioError}</p>
              <Button onClick={retryPortfolio} className="mt-2">Retry</Button>
            </div>
          ) : (
            <EmptyState
              icon={<span role="img" aria-label="portfolio">💼</span>}
              title="No portfolio data yet"
              description="Connect to the backend or add symbols to start tracking positions."
              actionText="Refresh"
              onAction={retryPortfolio}
            />
          )}

          {/* Main Content based on view mode */}
          {viewMode === 'overview' && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 space-y-6">
                <ThemedCard>
                  <CardHeader>
                    <CardTitle>Top Holdings</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {(enhancedPortfolio?.positions || []).sort((a,b) => b.market_value - a.market_value).slice(0,4).map(position => (
                        <PositionCard 
                          key={position.symbol} 
                          position={position}
                          onManage={handleManagePosition}
                        />
                      ))}
                    </div>
                  </CardContent>
                </ThemedCard>
              </div>

              <div className="space-y-6">
                {enhancedPortfolio && (
                  <>
                    <AllocationChart positions={enhancedPortfolio.positions} />
                    {recentActivities.length > 0 && <RecentActivity activities={recentActivities} />}
                  </>
                )}
              </div>
            </div>
          )}

          {viewMode === 'positions' && enhancedPortfolio && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {enhancedPortfolio.positions.map(position => (
                <div key={position.symbol} className="relative">
                  <PositionCard 
                    position={position}
                    onManage={handleManagePosition}
                  />
                  {position.is_live && (
                    <div className="absolute top-2 right-2 bg-green-500 text-white text-xs px-2 py-1 rounded-full">
                      LIVE
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {viewMode === 'analytics' && enhancedPortfolio && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <AllocationChart positions={enhancedPortfolio.positions} />
              <PerformanceMetrics positions={enhancedPortfolio.positions} />
              <div className="lg:col-span-2">
                {recentActivities.length > 0 && <RecentActivity activities={recentActivities} />}
              </div>
            </div>
          )}
        </div>
      </PageLayout>
      </ErrorBoundary>
    </RequireAuth>
  );
}