'use client';

import React, { useState, useEffect } from 'react';
import { RequireAuth } from '@/routes/RequireAuth';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { QuoteCard } from '@/components/market/QuoteCard';
import { PageLayout, ThemedButton, ThemedCard, StatusIndicator } from '@/components/layout/PageLayout';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { CardSkeleton } from '@/components/ui/Loading';
import { formatCurrency, formatPercentage, getPriceColor } from '@/utils';
import { useLiveData } from '@/hooks/useLiveData';
import { Activity } from 'lucide-react';
import apiClient from '@/services/api';
import { guardRealData } from '@/lib/guardRealData';
import type { Quote } from '@/types/api';

// Symbol name mappings
const symbolNames: Record<string, string> = {
  'SPY': 'S&P 500 ETF',
  'QQQ': 'NASDAQ-100 ETF', 
  'IWM': 'Russell 2000 ETF',
  'DIA': 'Dow Jones ETF',
  'AAPL': 'Apple Inc.',
  'TSLA': 'Tesla Inc.',
  'NVDA': 'NVIDIA Corp.',
  'MSFT': 'Microsoft Corp.',
  'GOOGL': 'Alphabet Inc.',
  'AMZN': 'Amazon.com Inc.'
};

interface MarketSummaryProps {
  title: string;
  data: Array<{ name: string; change_percent: number; leaders: string[] }>;
}

function MarketSummary({ title, data }: MarketSummaryProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {data.map((item, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <div>
                <div className="font-medium">{item.name}</div>
                <div className="text-sm text-gray-500">
                  Leaders: {item.leaders.join(', ')}
                </div>
              </div>
              <div className={`text-right ${getPriceColor(item.change_percent)}`}>
                <div className="font-bold">
                  {item.change_percent >= 0 ? '+' : ''}{formatPercentage(item.change_percent)}
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

interface MarketOverviewProps {
  indices: Quote[];
}

function MarketOverview({ indices }: MarketOverviewProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Market Overview</span>
          <span className="text-sm font-normal text-gray-500">
            {new Date().toLocaleTimeString()} ET
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {indices.map(quote => (
            <div key={quote.symbol} className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <div className="font-semibold text-sm text-gray-600 dark:text-gray-400">{symbolNames[quote.symbol] || quote.symbol}</div>
              <div className="text-xl font-bold mt-1">{formatCurrency(quote.price)}</div>
              <div className={`text-sm mt-1 ${getPriceColor(quote.change)}`}>
                {quote.change >= 0 ? '+' : ''}{formatCurrency(quote.change)} ({formatPercentage(quote.change_percent)})
              </div>
              <div className="text-xs text-gray-500 mt-2">
                Vol: {(quote.volume / 1000000).toFixed(1)}M
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

interface WatchlistProps {
  symbols: Quote[];
  onAddSymbol?: () => void;
}

function Watchlist({ symbols, onAddSymbol }: WatchlistProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>My Watchlist</span>
          <Button onClick={onAddSymbol} variant="ghost" size="sm">
            + Add Symbol
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {symbols.map(quote => (
            <div key={quote.symbol} className="flex items-center justify-between p-3 hover:bg-gray-50 dark:hover:bg-gray-800 rounded-lg cursor-pointer">
              <div>
                <div className="font-semibold">{quote.symbol}</div>
                <div className="text-sm text-gray-500">{symbolNames[quote.symbol] || quote.symbol}</div>
              </div>
              <div className="text-right">
                <div className="font-bold">{formatCurrency(quote.price)}</div>
                <div className={`text-sm ${getPriceColor(quote.change)}`}>
                  {quote.change >= 0 ? '+' : ''}{formatPercentage(quote.change_percent)}
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export default function MarketPage() {
  const [refreshing, setRefreshing] = useState(false);
  const [sectorsData, setSectorsData] = useState<Array<{name: string; change_percent: number; leaders: string[]}>>([]);
  const [sectorsLoading, setSectorsLoading] = useState(true);

  // Major market symbols to track
  const marketSymbols = ['SPY', 'QQQ', 'IWM', 'DIA', 'AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA', 'AMZN'];
  
  // Load sectors data
  const loadSectorsData = async () => {
    try {
      setSectorsLoading(true);
      const sectors = await apiClient.getMarketSectors();
      setSectorsData(sectors);
    } catch (error) {
      console.error('Failed to load sectors data:', error);
      // Fallback to basic sector structure
      setSectorsData([
        { name: 'Technology', change_percent: 0, leaders: ['AAPL', 'MSFT', 'NVDA'] },
        { name: 'Energy', change_percent: 0, leaders: ['XOM', 'CVX'] },
        { name: 'Healthcare', change_percent: 0, leaders: ['JNJ', 'PFE'] },
        { name: 'Financials', change_percent: 0, leaders: ['JPM', 'BAC'] }
      ]);
    } finally {
      setSectorsLoading(false);
    }
  };

  useEffect(() => {
    loadSectorsData();
  }, []);
  
  // Get live market data
  const {
    getQuote,
    isConnected: liveDataConnected,
    lastUpdate
  } = useLiveData({
    symbols: marketSymbols,
    autoConnect: true,
    maxNewsItems: 10
  });

  useEffect(() => {
    // Auto-refresh connection every 30 seconds if disconnected
    const interval = setInterval(() => {
      if (!liveDataConnected) {
        console.log('Attempting to reconnect live data...');
      }
    }, 30000);

    return () => clearInterval(interval);
  }, [liveDataConnected]);

  // Generate live market data from WebSocket quotes
  const generateLiveMarketData = () => {
    const indices = ['SPY', 'QQQ', 'IWM', 'DIA'].map(symbol => {
      const quote = getQuote(symbol);
      return quote || {
        symbol,
        price: 0,
        change: 0,
        change_percent: 0,
        volume: 0,
        high: 0,
        low: 0,
        open: 0,
        close: 0,
        timestamp: new Date().toISOString()
      };
    });

    const topMovers = ['AAPL', 'TSLA', 'NVDA', 'MSFT', 'GOOGL', 'AMZN'].map(symbol => {
      const quote = getQuote(symbol);
      return quote || {
        symbol,
        price: 0,
        change: 0,
        change_percent: 0,
        volume: 0,
        high: 0,
        low: 0,
        open: 0,
        close: 0,
        timestamp: new Date().toISOString()
      };
    });

    return { indices, topMovers };
  };

  const liveMarketData = generateLiveMarketData();

  if (process.env.NODE_ENV === 'development') {
    guardRealData('MarketOverview', [
      ...liveMarketData.indices.map(q => q.price),
      ...liveMarketData.topMovers.map(q => q.price)
    ]);
  }

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadSectorsData(); // Refresh sectors data
    setRefreshing(false);
  };

  // Get top 4 symbols for watchlist from live data
  const watchlistSymbols = liveMarketData.topMovers.slice(0, 4);

  return (
    <RequireAuth>
      <ErrorBoundary 
        fallback={
          <PageLayout
            theme="market"
            title="Market Overview"
            subtitle="Real-time market data and analysis"
          >
            <CardSkeleton showHeader contentLines={4} className="mb-6" />
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 space-y-6">
                <CardSkeleton showHeader contentLines={3} />
                <CardSkeleton showHeader contentLines={3} />
              </div>
              <div className="space-y-6">
                <CardSkeleton showHeader contentLines={2} />
              </div>
            </div>
          </PageLayout>
        }
      >
        <PageLayout
          theme="market"
          title="Market Overview"
          subtitle="Real-time market data and analysis"
          actions={
            <div className="flex items-center space-x-4">
              {liveDataConnected ? (
                <StatusIndicator status="success" theme="market" label="Live Data Active" />
              ) : (
                <StatusIndicator status="warning" theme="market" label="Connecting..." />
              )}
              <ThemedButton 
                theme="market" 
                variant="secondary" 
                size="sm"
                onClick={handleRefresh}
                disabled={refreshing}
              >
                {refreshing ? '🔄' : '↻'} Refresh Data
              </ThemedButton>
            </div>
          }
        >
        {/* Live Data Connection Status */}
        {liveDataConnected && (
          <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Activity className="w-5 h-5 text-green-600" />
                <span className="text-green-700 font-medium">Live Market Data Connected</span>
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              </div>
              {lastUpdate?.quotes && (
                <span className="text-sm text-green-600">
                  Updated: {new Date(lastUpdate.quotes).toLocaleTimeString()}
                </span>
              )}
            </div>
          </div>
        )}

        {/* Market Overview - using live data */}
        <MarketOverview indices={liveMarketData.indices} />

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Top Movers */}
          <div className="lg:col-span-2 space-y-6">
            <ThemedCard variant="elevated">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <span>🚀</span>
                  <span>Top Movers</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {liveMarketData.topMovers.map(quote => (
                    <div key={quote.symbol} className="relative">
                      <QuoteCard quote={quote} showDetails />
                      {getQuote(quote.symbol) && (
                        <div className="absolute top-2 right-2 bg-green-500 text-white text-xs px-2 py-1 rounded-full">
                          LIVE
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </ThemedCard>

          {/* Sector Performance */}
          {sectorsLoading ? (
            <ThemedCard variant="elevated" className="animate-pulse">
              <CardHeader>
                <CardTitle>Sector Performance</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {[...Array(6)].map((_, i) => (
                    <div key={i} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <div className="space-y-2">
                        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-20"></div>
                        <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-32"></div>
                      </div>
                      <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-12"></div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </ThemedCard>
          ) : (
            <MarketSummary title="Sector Performance" data={sectorsData} />
          )}
        </div>

        {/* Right Column - Watchlist */}
        <div className="space-y-6">
          <Watchlist 
            symbols={watchlistSymbols} 
            onAddSymbol={() => alert('Add Symbol functionality would open a modal here')}
          />
        </div>
        </div>
        </PageLayout>
      </ErrorBoundary>
    </RequireAuth>
  );
}