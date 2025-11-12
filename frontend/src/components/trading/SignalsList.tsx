import React, { useMemo } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { formatCurrency, formatPercentage, timeAgo } from '@/utils';
import { useKeyboardNavigation, useScreenReader } from '@/hooks/useAccessibility';
import { InlineTooltip } from '@/components/ui/Tooltip';
import type { TradingSignal } from '@/types/api';

interface SignalCardProps {
  signal: TradingSignal;
}

// Memoized signal type colors mapping
const SIGNAL_TYPE_COLORS = {
  BUY: 'text-green-600 bg-green-100 dark:bg-green-900 dark:text-green-300',
  SELL: 'text-red-600 bg-red-100 dark:bg-red-900 dark:text-red-300',
  HOLD: 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900 dark:text-yellow-300',
} as const;

// Memoized Signal Reasoning Component
const SignalReasoning = React.memo(({ reasoning }: { reasoning: string }) => (
  <div className="mt-3 p-2 bg-gray-50 dark:bg-gray-800 rounded text-sm">
    <span className="text-gray-500">Reasoning:</span>
    <p className="mt-1 text-gray-700 dark:text-gray-300">{reasoning}</p>
  </div>
));

SignalReasoning.displayName = 'SignalReasoning';

// Memoized Signal Metrics Component
const SignalMetrics = React.memo(({ signal }: { signal: TradingSignal }) => {
  const metrics = useMemo(() => {
    const items = [
      { 
        label: 'Confidence', 
        value: formatPercentage(signal.confidence), 
        color: '',
        ariaLabel: `Confidence level: ${formatPercentage(signal.confidence)}`,
        tooltip: 'How confident the AI is in this recommendation. Higher is better. Above 70% is considered strong.'
      }
    ];
    
    if (signal.price_target) {
      items.push({
        label: 'Target',
        value: formatCurrency(signal.price_target),
        color: 'text-green-600',
        ariaLabel: `Price target: ${formatCurrency(signal.price_target)}`,
        tooltip: 'The price level the AI expects the stock to reach. This is where you might consider taking profit.'
      });
    }
    
    if (signal.stop_loss) {
      items.push({
        label: 'Stop Loss',
        value: formatCurrency(signal.stop_loss),
        color: 'text-red-600',
        ariaLabel: `Stop loss: ${formatCurrency(signal.stop_loss)}`,
        tooltip: 'A safety price level. If the stock drops to this price, consider selling to limit losses.'
      });
    }
    
    return items;
  }, [signal.confidence, signal.price_target, signal.stop_loss]);

  return (
    <dl className="space-y-2" role="group" aria-label="Signal metrics">
      {metrics.map(({ label, value, color, ariaLabel, tooltip }) => (
        <div key={label} className="flex justify-between text-sm">
          <dt className="text-gray-500 flex items-center">
            {label}:
            {tooltip && <InlineTooltip content={tooltip} />}
          </dt>
          <dd className={`font-medium ${color}`} aria-label={ariaLabel}>
            {value}
          </dd>
        </div>
      ))}
    </dl>
  );
});

SignalMetrics.displayName = 'SignalMetrics';

export const SignalCard = React.memo(({ signal }: SignalCardProps) => {
  const signalTypeColor = useMemo(() => 
    SIGNAL_TYPE_COLORS[signal.signal_type], 
    [signal.signal_type]
  );

  const strengthColor = useMemo(() => {
    if (signal.strength >= 80) return 'text-green-600';
    if (signal.strength >= 60) return 'text-yellow-600';
    return 'text-red-600';
  }, [signal.strength]);

  const formattedTimestamp = useMemo(() => 
    timeAgo(signal.timestamp), 
    [signal.timestamp]
  );

  // Screen reader friendly description
  const signalDescription = useMemo(() => {
    let description = `Trading signal for ${signal.symbol}: ${signal.signal_type} with ${signal.strength}% strength and ${formatPercentage(signal.confidence)} confidence.`;
    if (signal.price_target) {
      description += ` Price target: ${formatCurrency(signal.price_target)}.`;
    }
    if (signal.stop_loss) {
      description += ` Stop loss: ${formatCurrency(signal.stop_loss)}.`;
    }
    description += ` Generated ${formattedTimestamp}.`;
    return description;
  }, [signal, formattedTimestamp]);

  return (
    <Card 
      className="hover:shadow-md transition-shadow focus-within:ring-2 focus-within:ring-blue-500"
      role="article"
      aria-label={signalDescription}
      tabIndex={0}
    >
      <CardHeader className="pb-2">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <CardTitle className="text-base sm:text-lg truncate">
            {signal.symbol}
            <span className="sr-only">trading signal</span>
          </CardTitle>
          <div className="flex items-center space-x-2 flex-shrink-0">
            <span 
              className={`px-2 py-1 rounded-full text-xs font-medium ${signalTypeColor}`}
              aria-label={`Signal type: ${signal.signal_type}`}
            >
              {signal.signal_type}
            </span>
            <span 
              className={`text-xs sm:text-sm font-medium ${strengthColor}`}
              aria-label={`Signal strength: ${signal.strength} percent`}
            >
              {signal.strength}%
            </span>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="px-3 sm:px-6">
        <div className="space-y-2" role="group" aria-label="Signal details">
          <SignalMetrics signal={signal} />
          
          {signal.reasoning && <SignalReasoning reasoning={signal.reasoning} />}
          
          <div className="mt-3 text-xs text-gray-400">
            <time dateTime={signal.timestamp} aria-label={`Signal generated ${formattedTimestamp}`}>
              {formattedTimestamp}
            </time>
          </div>
        </div>
      </CardContent>
    </Card>
  );
});

SignalCard.displayName = 'SignalCard';

interface SignalsListProps {
  signals: TradingSignal[];
  loading?: boolean;
  error?: string | null;
}

// Memoized Loading Component
const LoadingSpinner = React.memo(() => (
  <div className="flex items-center justify-center h-32" role="status" aria-label="Loading trading signals">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    <span className="sr-only">Loading trading signals...</span>
  </div>
));

LoadingSpinner.displayName = 'LoadingSpinner';

// Memoized Error Component
const ErrorMessage = React.memo(({ error }: { error: string }) => (
  <div className="text-center py-8" role="alert" aria-live="assertive">
    <div className="text-red-600 mb-2">Failed to load signals</div>
    <div className="text-sm text-gray-500">{error}</div>
  </div>
));

ErrorMessage.displayName = 'ErrorMessage';

// Memoized Empty State Component
const EmptyState = React.memo(() => (
  <div className="text-center py-8 text-gray-500" role="status" aria-live="polite">
    <p>No trading signals available</p>
    <span className="sr-only">The trading signals feed is empty</span>
  </div>
));

EmptyState.displayName = 'EmptyState';

export const SignalsList = React.memo(({ signals, loading, error }: SignalsListProps) => {
  const signalCountText = useMemo(() => 
    `${signals.length} signal${signals.length !== 1 ? 's' : ''}`,
    [signals.length]
  );

  const { listRef } = useKeyboardNavigation(signals);

  const { announce } = useScreenReader();

  // Announce signal count changes
  React.useEffect(() => {
    if (signals.length > 0) {
      announce(`${signalCountText} loaded`);
    }
  }, [signals.length, signalCountText, announce]);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;
  if (signals.length === 0) return <EmptyState />;

  return (
    <section className="space-y-6" aria-labelledby="signals-heading">
      <header className="flex items-center justify-between p-4 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950 dark:to-purple-950 rounded-xl border border-blue-200 dark:border-blue-800">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
            <span className="text-2xl">🎯</span>
          </div>
          <div>
            <h2 id="signals-heading" className="text-xl font-bold text-fg">
              Trading Signals
            </h2>
            <div className="text-sm text-fg-muted font-medium" aria-live="polite">
              {signalCountText} active
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2 text-xs font-medium text-green-600 dark:text-green-400">
          <span className="status-dot status-dot-success"></span>
          <span>Live Analysis</span>
        </div>
      </header>
      
      <div 
        ref={listRef}
        className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3 sm:gap-4"
        role="feed"
        aria-label="Trading signals feed"
        aria-describedby="signals-help"
      >
        {signals.map((signal, index) => (
          <SignalCard key={`${signal.symbol}-${signal.timestamp}-${index}`} signal={signal} />
        ))}
      </div>
      
      <div id="signals-help" className="sr-only">
        Use arrow keys to navigate between trading signals. Press Tab to focus on individual signal cards.
      </div>
    </section>
  );
});

SignalsList.displayName = 'SignalsList';