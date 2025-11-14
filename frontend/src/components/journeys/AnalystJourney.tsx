import React, { useState } from 'react';
import { JourneyContainer } from '../demo/JourneyContainer';
import { useJourney } from '@/utils/journeyManager';
import { useDemoData } from '@/utils/demoIntegration';

/**
 * Analyst Journey Component
 * Guides users through the market screening and analysis workflow
 */
export const AnalystJourney: React.FC = () => {
  const journey = useJourney('analyst');
  const { data: screenerData } = useDemoData('screener', { preset: 'momentum' });
  const [selectedPreset, setSelectedPreset] = useState('momentum');

  const renderStep = () => {
    const { currentStep } = journey;

    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Step 1: Open Market Screener
              </h2>
              <p className="text-gray-600 dark:text-gray-300 mb-4">
                Access the powerful market screening tool to discover trading opportunities across thousands of symbols.
              </p>
            </div>

            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-6">
              <div className="text-center py-12">
                <div className="inline-flex items-center justify-center w-20 h-20 bg-blue-100 dark:bg-blue-900 rounded-full mb-4">
                  <span className="text-4xl">🔍</span>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  Market Screener
                </h3>
                <p className="text-gray-600 dark:text-gray-300 mb-6">
                  Scan the entire market for opportunities based on technical and fundamental criteria
                </p>
                <button className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700">
                  Launch Screener
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                <h4 className="font-semibold text-gray-900 dark:text-white mb-2">Real-Time Scanning</h4>
                <p className="text-sm text-gray-600 dark:text-gray-300">
                  Scan thousands of symbols in seconds
                </p>
              </div>
              <div className="bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                <h4 className="font-semibold text-gray-900 dark:text-white mb-2">Custom Filters</h4>
                <p className="text-sm text-gray-600 dark:text-gray-300">
                  Build your own screening criteria
                </p>
              </div>
              <div className="bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                <h4 className="font-semibold text-gray-900 dark:text-white mb-2">Save Presets</h4>
                <p className="text-sm text-gray-600 dark:text-gray-300">
                  Reuse your favorite strategies
                </p>
              </div>
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Step 2: Choose Screening Strategy
              </h2>
              <p className="text-gray-600 dark:text-gray-300 mb-4">
                Select a pre-built strategy or create your own custom criteria.
              </p>
            </div>

            <div className="grid gap-4">
              <button
                onClick={() => setSelectedPreset('momentum')}
                className={`p-6 rounded-lg border-2 text-left transition-all ${
                  selectedPreset === 'momentum'
                    ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                      📈 Momentum Strategy
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-300 mb-3">
                      Find stocks with strong upward price momentum and increasing volume
                    </p>
                    <div className="flex flex-wrap gap-2">
                      <span className="px-2 py-1 bg-gray-100 dark:bg-gray-600 rounded text-xs">RSI &gt; 60</span>
                      <span className="px-2 py-1 bg-gray-100 dark:bg-gray-600 rounded text-xs">Volume +50%</span>
                      <span className="px-2 py-1 bg-gray-100 dark:bg-gray-600 rounded text-xs">20 SMA Cross</span>
                    </div>
                  </div>
                  {selectedPreset === 'momentum' && (
                    <div className="ml-4 flex-shrink-0">
                      <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center">
                        <span className="text-white text-sm">✓</span>
                      </div>
                    </div>
                  )}
                </div>
              </button>

              <button
                onClick={() => setSelectedPreset('mean_reversion')}
                className={`p-6 rounded-lg border-2 text-left transition-all ${
                  selectedPreset === 'mean_reversion'
                    ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                      ↩️ Mean Reversion Strategy
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-300 mb-3">
                      Identify oversold stocks likely to bounce back to their mean
                    </p>
                    <div className="flex flex-wrap gap-2">
                      <span className="px-2 py-1 bg-gray-100 dark:bg-gray-600 rounded text-xs">RSI &lt; 30</span>
                      <span className="px-2 py-1 bg-gray-100 dark:bg-gray-600 rounded text-xs">Bollinger Band</span>
                      <span className="px-2 py-1 bg-gray-100 dark:bg-gray-600 rounded text-xs">Support Level</span>
                    </div>
                  </div>
                  {selectedPreset === 'mean_reversion' && (
                    <div className="ml-4 flex-shrink-0">
                      <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center">
                        <span className="text-white text-sm">✓</span>
                      </div>
                    </div>
                  )}
                </div>
              </button>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Step 3: Run Market Scan
              </h2>
              <p className="text-gray-600 dark:text-gray-300 mb-4">
                Execute the screening query across the market to find matching opportunities.
              </p>
            </div>

            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-white">
                    {selectedPreset === 'momentum' ? 'Momentum Strategy' : 'Mean Reversion Strategy'}
                  </h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Scanning 5,000+ symbols...
                  </p>
                </div>
                <button className="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700">
                  Start Scan
                </button>
              </div>

              {/* Progress simulation */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600 dark:text-gray-300">Progress</span>
                  <span className="text-gray-600 dark:text-gray-300">100%</span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                  <div className="bg-blue-600 h-2 rounded-full w-full"></div>
                </div>
              </div>

              <div className="mt-4 grid grid-cols-3 gap-4 text-center">
                <div>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">5,247</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Scanned</p>
                </div>
                <div>
                  <p className="text-2xl font-bold text-green-600 dark:text-green-400">42</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Matches</p>
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">2.3s</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Duration</p>
                </div>
              </div>
            </div>

            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
              <p className="text-sm text-green-800 dark:text-green-200">
                ✅ <strong>Scan Complete!</strong> Found 42 symbols matching your criteria.
              </p>
            </div>
          </div>
        );

      case 4:
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Step 4: Review Results
              </h2>
              <p className="text-gray-600 dark:text-gray-300 mb-4">
                Analyze the screener results sorted by strength and potential.
              </p>
            </div>

            <div className="bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg overflow-hidden">
              <div className="px-4 py-3 bg-gray-50 dark:bg-gray-600 border-b border-gray-200 dark:border-gray-500 flex items-center justify-between">
                <h3 className="font-semibold text-gray-900 dark:text-white">
                  Top Results ({screenerData?.results?.length || 42} symbols)
                </h3>
                <div className="flex gap-2">
                  <button className="px-3 py-1 text-xs bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-500 rounded">
                    Export
                  </button>
                  <button className="px-3 py-1 text-xs bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-500 rounded">
                    Filter
                  </button>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 dark:bg-gray-600">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-300">Symbol</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-300">Price</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-300">Change</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-300">Volume</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-300">Score</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 dark:divide-gray-600">
                    {screenerData?.results?.slice(0, 5).map((result: any, idx: number) => (
                      <tr key={idx} className="hover:bg-gray-50 dark:hover:bg-gray-600">
                        <td className="px-4 py-3">
                          <span className="font-medium text-gray-900 dark:text-white">{result.symbol}</span>
                        </td>
                        <td className="px-4 py-3 text-gray-700 dark:text-gray-200">${result.price}</td>
                        <td className="px-4 py-3">
                          <span className={result.change > 0 ? 'text-green-600' : 'text-red-600'}>
                            {result.change > 0 ? '+' : ''}{result.change}%
                          </span>
                        </td>
                        <td className="px-4 py-3 text-gray-700 dark:text-gray-200">{result.volume}M</td>
                        <td className="px-4 py-3">
                          <span className="px-2 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 rounded text-xs font-medium">
                            {result.score}
                          </span>
                        </td>
                      </tr>
                    )) || (
                      <tr>
                        <td colSpan={5} className="px-4 py-3 text-center text-gray-500">
                          Loading results...
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        );

      case 5:
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Step 5: Drill Down into Details
              </h2>
              <p className="text-gray-600 dark:text-gray-300 mb-4">
                Explore detailed analysis for any symbol from your screener results.
              </p>
            </div>

            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-2xl font-bold text-gray-900 dark:text-white">NVDA</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">NVIDIA Corporation</p>
                </div>
                <div className="text-right">
                  <p className="text-3xl font-bold text-green-600 dark:text-green-400">$485.20</p>
                  <p className="text-sm text-green-600 dark:text-green-400">+8.45 (+1.77%)</p>
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-white dark:bg-gray-600 rounded-lg p-3">
                  <p className="text-xs text-gray-500 dark:text-gray-400">RSI (14)</p>
                  <p className="text-lg font-semibold text-gray-900 dark:text-white">68.5</p>
                </div>
                <div className="bg-white dark:bg-gray-600 rounded-lg p-3">
                  <p className="text-xs text-gray-500 dark:text-gray-400">Volume</p>
                  <p className="text-lg font-semibold text-gray-900 dark:text-white">45.2M</p>
                </div>
                <div className="bg-white dark:bg-gray-600 rounded-lg p-3">
                  <p className="text-xs text-gray-500 dark:text-gray-400">Avg Volume</p>
                  <p className="text-lg font-semibold text-gray-900 dark:text-white">32.1M</p>
                </div>
                <div className="bg-white dark:bg-gray-600 rounded-lg p-3">
                  <p className="text-xs text-gray-500 dark:text-gray-400">Market Cap</p>
                  <p className="text-lg font-semibold text-gray-900 dark:text-white">$1.2T</p>
                </div>
              </div>

              <div className="flex gap-3">
                <button className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700">
                  View Full Analysis
                </button>
                <button className="flex-1 px-4 py-2 bg-white dark:bg-gray-600 border border-gray-300 dark:border-gray-500 text-gray-700 dark:text-gray-200 rounded-lg font-medium hover:bg-gray-50 dark:hover:bg-gray-500">
                  Add to Watchlist
                </button>
              </div>
            </div>

            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
              <p className="text-sm text-blue-800 dark:text-blue-200">
                🎉 <strong>Journey Complete!</strong> You've successfully used the screener to discover opportunities. Explore more symbols or try a different strategy.
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
