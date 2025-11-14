import React from 'react';
import { JourneyContainer } from '../demo/JourneyContainer';
import { useJourney } from '@/utils/journeyManager';
import { useDemoData } from '@/utils/demoIntegration';

/**
 * Trader Journey Component
 * Guides users through the trader workflow
 */
export const TraderJourney: React.FC = () => {
  const journey = useJourney('trader');
  const { data: marketData } = useDemoData('market', { ticker: 'AAPL' });
  const { data: signalsData } = useDemoData('signals');
  const { data: portfolioData } = useDemoData('portfolio');

  const renderStep = () => {
    const { currentStep } = journey;

    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Step 1: Select a Ticker
              </h2>
              <p className="text-gray-600 dark:text-gray-300 mb-4">
                Choose a stock symbol to begin your analysis. Popular choices include AAPL, MSFT, NVDA, and TSLA.
              </p>
            </div>

            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-6">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
                Search for a ticker
              </label>
              <input
                type="text"
                placeholder="e.g., AAPL, MSFT, NVDA..."
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
                defaultValue="AAPL"
              />

              <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-2">
                {['AAPL', 'MSFT', 'NVDA', 'TSLA'].map((ticker) => (
                  <button
                    key={ticker}
                    className="px-4 py-2 bg-white dark:bg-gray-600 border border-gray-300 dark:border-gray-500 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-500 text-sm font-medium"
                  >
                    {ticker}
                  </button>
                ))}
              </div>
            </div>

            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
              <p className="text-sm text-blue-800 dark:text-blue-200">
                💡 <strong>Tip:</strong> In demo mode, data is pre-loaded for popular tickers. Try AAPL to see live charts and signals.
              </p>
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Step 2: View Live Chart
              </h2>
              <p className="text-gray-600 dark:text-gray-300 mb-4">
                Analyze real-time price movements with technical indicators and volume data.
              </p>
            </div>

            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-bold text-gray-900 dark:text-white">AAPL</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Apple Inc.</p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                    ${marketData?.price || '178.50'}
                  </p>
                  <p className="text-sm text-green-600 dark:text-green-400">
                    +2.35 (+1.33%)
                  </p>
                </div>
              </div>

              <div className="h-64 bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-600 flex items-center justify-center">
                <p className="text-gray-400">📈 Chart visualization area</p>
              </div>

              <div className="mt-4 flex gap-2">
                <button className="px-3 py-1 text-xs bg-blue-600 text-white rounded">1D</button>
                <button className="px-3 py-1 text-xs bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-200 rounded">5D</button>
                <button className="px-3 py-1 text-xs bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-200 rounded">1M</button>
                <button className="px-3 py-1 text-xs bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-200 rounded">3M</button>
                <button className="px-3 py-1 text-xs bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-200 rounded">1Y</button>
              </div>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Step 3: Analyze Market Brain Signals
              </h2>
              <p className="text-gray-600 dark:text-gray-300 mb-4">
                Review AI-generated trading signals and technical indicators.
              </p>
            </div>

            <div className="grid gap-4">
              {signalsData?.signals?.slice(0, 3).map((signal: any, idx: number) => (
                <div key={idx} className="bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-semibold text-gray-900 dark:text-white">{signal.type}</h4>
                      <p className="text-sm text-gray-500 dark:text-gray-400">{signal.description}</p>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                      signal.strength === 'strong' 
                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                        : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                    }`}>
                      {signal.strength}
                    </span>
                  </div>
                </div>
              )) || (
                <div className="bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                  <p className="text-gray-500">Loading signals...</p>
                </div>
              )}
            </div>
          </div>
        );

      case 4:
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Step 4: Execute Paper Trade
              </h2>
              <p className="text-gray-600 dark:text-gray-300 mb-4">
                Place a simulated trade to test your strategy without risking real money.
              </p>
            </div>

            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-6">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
                    Action
                  </label>
                  <div className="flex gap-2">
                    <button className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg font-medium">
                      Buy
                    </button>
                    <button className="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-200 rounded-lg font-medium">
                      Sell
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
                    Quantity
                  </label>
                  <input
                    type="number"
                    defaultValue="10"
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-800 dark:text-white"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
                    Order Type
                  </label>
                  <select className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-800 dark:text-white">
                    <option>Market Order</option>
                    <option>Limit Order</option>
                    <option>Stop Loss</option>
                  </select>
                </div>

                <button className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700">
                  Place Paper Trade
                </button>
              </div>
            </div>

            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
              <p className="text-sm text-green-800 dark:text-green-200">
                ✅ <strong>Safe Mode:</strong> This is a paper trade. No real money will be used.
              </p>
            </div>
          </div>
        );

      case 5:
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Step 5: Monitor Portfolio
              </h2>
              <p className="text-gray-600 dark:text-gray-300 mb-4">
                Track your paper trading positions and performance metrics.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="bg-white dark:bg-gray-700 rounded-lg p-4 border border-gray-200 dark:border-gray-600">
                <p className="text-sm text-gray-500 dark:text-gray-400">Total Value</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  ${portfolioData?.total_value || '10,785.50'}
                </p>
              </div>
              <div className="bg-white dark:bg-gray-700 rounded-lg p-4 border border-gray-200 dark:border-gray-600">
                <p className="text-sm text-gray-500 dark:text-gray-400">Day P&L</p>
                <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                  +$235.50
                </p>
              </div>
              <div className="bg-white dark:bg-gray-700 rounded-lg p-4 border border-gray-200 dark:border-gray-600">
                <p className="text-sm text-gray-500 dark:text-gray-400">Total Return</p>
                <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                  +7.86%
                </p>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600">
              <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-600">
                <h3 className="font-semibold text-gray-900 dark:text-white">Open Positions</h3>
              </div>
              <div className="divide-y divide-gray-200 dark:divide-gray-600">
                {portfolioData?.positions?.map((position: any, idx: number) => (
                  <div key={idx} className="px-4 py-3 flex items-center justify-between">
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">{position.symbol}</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">{position.quantity} shares</p>
                    </div>
                    <div className="text-right">
                      <p className="font-medium text-gray-900 dark:text-white">${position.current_value}</p>
                      <p className={`text-sm ${position.pnl > 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {position.pnl > 0 ? '+' : ''}{position.pnl}%
                      </p>
                    </div>
                  </div>
                )) || (
                  <div className="px-4 py-3">
                    <p className="text-gray-500">No positions yet</p>
                  </div>
                )}
              </div>
            </div>

            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
              <p className="text-sm text-blue-800 dark:text-blue-200">
                🎉 <strong>Journey Complete!</strong> You've successfully navigated the trader workflow. Feel free to explore more or start a new journey.
              </p>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <JourneyContainer
      title={journey.config.title}
      currentStep={journey.currentStep}
      totalSteps={journey.totalSteps}
      onNext={journey.goNext}
      onPrevious={journey.goPrevious}
      onExit={() => window.location.href = '/'}
    >
      {renderStep()}
    </JourneyContainer>
  );
};
