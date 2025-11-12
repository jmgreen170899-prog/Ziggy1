/**
 * Live Quotes Widget - Real-time market data for main dashboard
 * Shows key market indicators with live updates
 */
'use client';

import React from 'react';
import { TrendingUp, TrendingDown, Activity } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { useLiveData } from '@/hooks/useLiveData';
import { cn } from '@/utils';
import LiveDataStatus from './LiveDataStatus';

const DEFAULT_SYMBOLS = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'NVDA', 'TSLA'];

interface LiveQuotesWidgetProps {
  symbols?: string[];
  maxQuotes?: number;
  showStatus?: boolean;
  className?: string;
}

export function LiveQuotesWidget({ 
  symbols = DEFAULT_SYMBOLS,
  maxQuotes = 6,
  showStatus = true,
  className 
}: LiveQuotesWidgetProps) {
  const { getQuote, isConnected, lastUpdate } = useLiveData({
    symbols: symbols.slice(0, maxQuotes),
    autoConnect: true,
  });

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(price);
  };

  const formatPercent = (percent: number) => {
    return `${percent >= 0 ? '+' : ''}${percent.toFixed(2)}%`;
  };

  const symbolsToShow = symbols.slice(0, maxQuotes);

  return (
    <Card className={cn("w-full card-elevated", className)}>
      <CardHeader className="pb-3 border-b border-border">
        <CardTitle className="flex items-center justify-between text-lg">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
              <Activity className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <div className="font-bold">Live Market Data</div>
              {isConnected && (
                <div className="flex items-center space-x-1.5 text-xs font-medium text-green-600 dark:text-green-400 mt-0.5">
                  <div className="status-dot status-dot-success"></div>
                  <span>STREAMING LIVE</span>
                </div>
              )}
            </div>
          </div>
          {showStatus && (
            <LiveDataStatus compact showLabel={false} />
          )}
        </CardTitle>
        {lastUpdate?.quotes && (
          <p className="text-xs text-fg-muted mt-2" aria-live="polite">
            📡 Last update: {new Date(lastUpdate.quotes).toLocaleTimeString()}
          </p>
        )}
      </CardHeader>
      
      <CardContent className="pt-4">
        {!isConnected ? (
          <div className="text-center py-12 text-fg-muted">
            <div className="mb-4">
              <Activity className="w-12 h-12 mx-auto animate-spin text-blue-500" />
            </div>
            <p className="text-lg font-medium">Connecting to live data stream...</p>
            <p className="text-sm mt-1">Establishing WebSocket connection</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {symbolsToShow.map(symbol => {
              const quote = getQuote(symbol);
              
              return (
                <div
                  key={symbol}
                  className="metric-card group cursor-pointer"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-mono font-bold text-base text-fg group-hover:text-accent transition-colors">
                      {symbol}
                    </span>
                    {quote && (
                      <div className={cn(
                        "flex items-center gap-1 font-semibold",
                        quote.change >= 0 ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"
                      )}>
                        {quote.change >= 0 ? (
                          <TrendingUp className="w-4 h-4" />
                        ) : (
                          <TrendingDown className="w-4 h-4" />
                        )}
                        <span className="text-sm font-bold">
                          {formatPercent(quote.change_percent)}
                        </span>
                      </div>
                    )}
                  </div>
                  
                  {quote ? (
                    <>
                      <div className="text-2xl font-bold mb-2 text-fg">
                        {formatPrice(quote.price)}
                      </div>
                      <div className="flex items-center justify-between pt-2 border-t border-border">
                        <div className="text-xs text-fg-muted">
                          <div className="font-medium">Volume</div>
                          <div className="text-fg font-semibold">{(quote.volume / 1000000).toFixed(1)}M</div>
                        </div>
                        <div className="text-right">
                          <div className="text-xs text-fg-muted font-medium">Change</div>
                          <div className={cn(
                            "font-bold text-sm",
                            quote.change >= 0 ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"
                          )}>
                            {quote.change >= 0 ? '+' : ''}{formatPrice(quote.change)}
                          </div>
                        </div>
                      </div>
                    </>
                  ) : (
                    <div className="space-y-3">
                      <div className="h-8 skeleton rounded"></div>
                      <div className="h-4 skeleton rounded w-3/4"></div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
        
        {lastUpdate?.quotes && (
          <div className="mt-3 pt-3 border-t text-xs text-gray-500 flex items-center justify-between">
            <span>Last updated: {lastUpdate.quotes.toLocaleTimeString()}</span>
            <a
              href="/live"
              className="text-blue-600 hover:text-blue-800 font-medium"
              aria-label="View Live Dashboard"
            >
              View Live Dashboard →
            </a>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default LiveQuotesWidget;