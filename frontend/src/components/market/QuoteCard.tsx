import React, { useMemo, useCallback } from 'react';
import { Card, CardContent } from '@/components/ui/Card';
import { formatCurrency, formatPercentage, getPriceColor } from '@/utils';
import { InlineTooltip } from '@/components/ui/Tooltip';
import type { Quote } from '@/types/api';

interface QuoteCardProps {
  quote: Quote;
  showDetails?: boolean;
  onRemove?: (symbol: string) => void;
}

// Memoized Quote Details Component
const QuoteDetails = React.memo(({ quote }: { quote: Quote }) => {
  const details = useMemo(() => [
    { 
      label: 'High', 
      value: formatCurrency(quote.high),
      tooltip: 'Highest price reached today'
    },
    { 
      label: 'Low', 
      value: formatCurrency(quote.low),
      tooltip: 'Lowest price reached today'
    },
    { 
      label: 'Open', 
      value: formatCurrency(quote.open),
      tooltip: 'Price when the market opened today'
    },
    { 
      label: 'Volume', 
      value: quote.volume.toLocaleString(),
      tooltip: 'Total number of shares traded today. Higher volume means more trading activity.'
    }
  ], [quote.high, quote.low, quote.open, quote.volume]);

  return (
    <div className="mt-4 grid grid-cols-2 gap-2 text-sm">
      {details.map(({ label, value, tooltip }) => (
        <div key={label}>
          <span className="text-fg-muted inline-flex items-center">
            {label}:
            <InlineTooltip content={tooltip} />
          </span>
          <span className="ml-2 font-medium font-mono text-fg">{value}</span>
        </div>
      ))}
    </div>
  );
});

QuoteDetails.displayName = 'QuoteDetails';

export const QuoteCard = React.memo(({ quote, showDetails = false, onRemove }: QuoteCardProps) => {
  const changeColor = useMemo(() => getPriceColor(quote.change), [quote.change]);
  const isPositive = useMemo(() => quote.change >= 0, [quote.change]);
  
  const formattedPrice = useMemo(() => formatCurrency(quote.price), [quote.price]);
  const formattedChange = useMemo(() => formatCurrency(quote.change), [quote.change]);
  const formattedChangePercent = useMemo(() => formatPercentage(quote.change_percent), [quote.change_percent]);
  
  const formattedTimestamp = useMemo(() => 
    new Date(quote.timestamp).toLocaleTimeString(), 
    [quote.timestamp]
  );

  const handleRemove = useCallback(() => {
    onRemove?.(quote.symbol);
  }, [onRemove, quote.symbol]);

  return (
    <Card className="hover:shadow-md transition-shadow cursor-pointer relative" role="article">
      <CardContent className="p-3 sm:p-4">
        <div className="flex items-start justify-between">
          <div className="min-w-0 flex-1">
            <h3 
              className="font-semibold text-base sm:text-lg truncate"
              id={`quote-symbol-${quote.symbol}`}
            >
              {quote.symbol}
            </h3>
            <div 
              className="text-xl sm:text-2xl font-bold font-mono truncate"
              aria-labelledby={`quote-symbol-${quote.symbol}`}
              aria-describedby={`quote-change-${quote.symbol}`}
            >
              {formattedPrice}
            </div>
          </div>
          
          <div className="text-right ml-2 flex-shrink-0">
            <div 
              className={`text-xs sm:text-sm font-medium font-mono ${changeColor} truncate`}
              id={`quote-change-${quote.symbol}`}
              aria-label={`Price change: ${isPositive ? 'up' : 'down'} ${formattedChange}`}
            >
              {isPositive ? '+' : ''}{formattedChange}
            </div>
            <div 
              className={`text-xs sm:text-sm font-mono ${changeColor} truncate`}
              aria-label={`Percentage change: ${isPositive ? 'up' : 'down'} ${formattedChangePercent}`}
            >
              {formattedChangePercent}
            </div>
          </div>
        </div>

        {showDetails && <QuoteDetails quote={quote} />}

        <div 
          className="mt-3 pt-2 border-t border-border flex items-center justify-between text-xs"
          aria-label={`Last updated: ${formattedTimestamp}`}
        >
          <span className="text-fg-muted flex items-center gap-1">
            <span className="status-dot status-dot-success"></span>
            Live
          </span>
          <span className="text-fg-muted font-medium font-mono">{formattedTimestamp}</span>
        </div>
      </CardContent>
      
      {onRemove && (
        <button
          onClick={handleRemove}
          className="absolute top-1 right-1 sm:top-2 sm:right-2 w-6 h-6 sm:w-auto sm:h-auto text-gray-400 hover:text-red-600 transition-colors z-10 flex items-center justify-center focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-1 rounded"
          aria-label={`Remove ${quote.symbol} from watchlist`}
          type="button"
        >
          <span aria-hidden="true">×</span>
        </button>
      )}
    </Card>
  );
});

QuoteCard.displayName = 'QuoteCard';

interface WatchlistProps {
  quotes: Quote[];
  onAddSymbol?: (symbol: string) => void;
  onRemoveSymbol?: (symbol: string) => void;
}

export const Watchlist = React.memo(({ quotes, onAddSymbol, onRemoveSymbol }: WatchlistProps) => {
  const handleAddSymbol = useCallback(() => {
    onAddSymbol?.('');
  }, [onAddSymbol]);

  const handleRemoveSymbol = useCallback((symbol: string) => {
    onRemoveSymbol?.(symbol);
  }, [onRemoveSymbol]);

  return (
    <section className="space-y-3" aria-labelledby="watchlist-heading">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <h2 id="watchlist-heading" className="text-lg sm:text-xl font-semibold">
          Watchlist
        </h2>
        <button 
          onClick={handleAddSymbol}
          className="text-blue-600 hover:text-blue-700 text-sm font-medium self-start sm:self-auto px-3 py-1 border border-blue-200 rounded-md hover:bg-blue-50 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1"
          type="button"
          aria-describedby="add-symbol-description"
        >
          + Add Symbol
          <span id="add-symbol-description" className="sr-only">
            Add a new stock symbol to your watchlist
          </span>
        </button>
      </div>
      
      <div 
        className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3 sm:gap-4"
        role="list"
        aria-label={`Watchlist with ${quotes.length} stocks`}
      >
        {quotes.map((quote) => (
          <div key={quote.symbol} role="listitem">
            <QuoteCard 
              quote={quote} 
              onRemove={onRemoveSymbol ? handleRemoveSymbol : undefined}
            />
          </div>
        ))}
      </div>
      {quotes.length === 0 && (
        <p className="text-gray-500 text-sm text-center py-8" role="status">
          No stocks in your watchlist. Click &ldquo;Add Symbol&rdquo; to get started.
        </p>
      )}
    </section>
  );
});

Watchlist.displayName = 'Watchlist';