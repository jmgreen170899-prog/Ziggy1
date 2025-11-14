import React, { useState } from 'react';
import { JourneyContainer } from '../demo/JourneyContainer';
import { useJourney } from '@/utils/journeyManager';
import { useDemoData } from '@/utils/demoIntegration';

/**
 * Research Journey Component
 * Guides users through the AI-powered research and cognitive workflow
 */
export const ResearchJourney: React.FC = () => {
  const journey = useJourney('research');
  const { data: cognitiveData } = useDemoData('cognitive');
  const [question, setQuestion] = useState('');

  const renderStep = () => {
    const { currentStep } = journey;

    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Step 1: Open AI Research Assistant
              </h2>
              <p className="text-gray-600 dark:text-gray-300 mb-4">
                Access ZiggyAI's powerful research assistant for market insights and decision support.
              </p>
            </div>

            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-6">
              <div className="text-center py-12">
                <div className="inline-flex items-center justify-center w-20 h-20 bg-purple-100 dark:bg-purple-900 rounded-full mb-4">
                  <span className="text-4xl">🤖</span>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  AI Research Assistant
                </h3>
                <p className="text-gray-600 dark:text-gray-300 mb-6">
                  Get instant insights, analysis, and recommendations powered by advanced AI
                </p>
                <button className="px-6 py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700">
                  Start Conversation
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                <h4 className="font-semibold text-gray-900 dark:text-white mb-2">Natural Language</h4>
                <p className="text-sm text-gray-600 dark:text-gray-300">
                  Ask questions in plain English
                </p>
              </div>
              <div className="bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                <h4 className="font-semibold text-gray-900 dark:text-white mb-2">Real-Time Data</h4>
                <p className="text-sm text-gray-600 dark:text-gray-300">
                  Insights backed by current market data
                </p>
              </div>
              <div className="bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                <h4 className="font-semibold text-gray-900 dark:text-white mb-2">Learning Engine</h4>
                <p className="text-sm text-gray-600 dark:text-gray-300">
                  AI that improves with your feedback
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
                Step 2: Ask a Market Question
              </h2>
              <p className="text-gray-600 dark:text-gray-300 mb-4">
                Type your question about markets, stocks, or trading strategies.
              </p>
            </div>

            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-6">
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
                  Your Question
                </label>
                <textarea
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="e.g., What are the key indicators for AAPL right now? Should I consider it for momentum trading?"
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 dark:bg-gray-800 dark:text-white resize-none"
                  rows={4}
                  defaultValue="What are the key indicators for AAPL right now? Should I consider it for momentum trading?"
                />
              </div>

              <div className="flex gap-3">
                <button className="flex-1 px-6 py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700">
                  Ask ZiggyAI
                </button>
                <button className="px-6 py-3 bg-white dark:bg-gray-600 border border-gray-300 dark:border-gray-500 text-gray-700 dark:text-gray-200 rounded-lg font-medium hover:bg-gray-50 dark:hover:bg-gray-500">
                  Clear
                </button>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-4">
              <h4 className="font-semibold text-gray-900 dark:text-white mb-3">Suggested Questions:</h4>
              <div className="space-y-2">
                {[
                  'What are the top momentum stocks today?',
                  'Explain the current market regime',
                  'Is NVDA overbought based on technical indicators?',
                  'What sectors are showing strength this week?',
                ].map((suggested, idx) => (
                  <button
                    key={idx}
                    onClick={() => setQuestion(suggested)}
                    className="w-full text-left px-4 py-2 bg-gray-50 dark:bg-gray-600 hover:bg-gray-100 dark:hover:bg-gray-500 rounded text-sm text-gray-700 dark:text-gray-200"
                  >
                    💡 {suggested}
                  </button>
                ))}
              </div>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Step 3: Review AI Response
              </h2>
              <p className="text-gray-600 dark:text-gray-300 mb-4">
                Analyze the AI-generated insights and recommendations.
              </p>
            </div>

            {/* Question Display */}
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
              <p className="text-sm font-medium text-blue-900 dark:text-blue-200 mb-1">Your Question:</p>
              <p className="text-gray-700 dark:text-gray-300">
                {question || 'What are the key indicators for AAPL right now? Should I consider it for momentum trading?'}
              </p>
            </div>

            {/* AI Response */}
            <div className="bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-6">
              <div className="flex items-start gap-3 mb-4">
                <div className="flex-shrink-0 w-10 h-10 bg-purple-100 dark:bg-purple-900 rounded-full flex items-center justify-center">
                  <span className="text-xl">🤖</span>
                </div>
                <div className="flex-1">
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-2">ZiggyAI Analysis</h4>
                  <div className="text-gray-700 dark:text-gray-300 space-y-3 text-sm">
                    <p>
                      Based on current technical indicators, AAPL shows <strong>strong momentum characteristics</strong>:
                    </p>
                    <ul className="list-disc list-inside space-y-1 ml-2">
                      <li><strong>RSI at 68.5</strong> - In bullish territory but not yet overbought</li>
                      <li><strong>Volume surge</strong> - 41% above 20-day average, confirming trend</li>
                      <li><strong>Moving average alignment</strong> - Price above both 20 and 50 SMAs</li>
                      <li><strong>MACD positive divergence</strong> - Histogram expanding</li>
                    </ul>
                    <p>
                      <strong>Recommendation:</strong> AAPL is suitable for momentum trading with a 3-5 day holding period. 
                      Consider entry on pullbacks to the 20 SMA (~$176) with a stop loss at $172.
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-4">
                      Confidence: 85% | Data sources: Technical indicators, Volume analysis, Price action
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex gap-2 mt-4">
                <button className="px-3 py-1 text-xs bg-gray-100 dark:bg-gray-600 text-gray-700 dark:text-gray-200 rounded hover:bg-gray-200 dark:hover:bg-gray-500">
                  👍 Helpful
                </button>
                <button className="px-3 py-1 text-xs bg-gray-100 dark:bg-gray-600 text-gray-700 dark:text-gray-200 rounded hover:bg-gray-200 dark:hover:bg-gray-500">
                  👎 Not Helpful
                </button>
                <button className="px-3 py-1 text-xs bg-gray-100 dark:bg-gray-600 text-gray-700 dark:text-gray-200 rounded hover:bg-gray-200 dark:hover:bg-gray-500">
                  📋 Copy
                </button>
                <button className="px-3 py-1 text-xs bg-gray-100 dark:bg-gray-600 text-gray-700 dark:text-gray-200 rounded hover:bg-gray-200 dark:hover:bg-gray-500">
                  🔗 Share
                </button>
              </div>
            </div>
          </div>
        );

      case 4:
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Step 4: Explore Cognitive Features
              </h2>
              <p className="text-gray-600 dark:text-gray-300 mb-4">
                Discover advanced AI capabilities for decision enhancement and learning.
              </p>
            </div>

            <div className="grid gap-4">
              <div className="bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-6">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
                    <span className="text-2xl">🧠</span>
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                      Decision Enhancement
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-300 mb-3">
                      Get AI-powered analysis to improve your trading decisions with contextual insights and risk assessment.
                    </p>
                    <button className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700">
                      Try Decision Enhancement
                    </button>
                  </div>
                </div>
              </div>

              <div className="bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-6">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-12 h-12 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center">
                    <span className="text-2xl">📚</span>
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                      Learning Engine
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-300 mb-3">
                      The system learns from your outcomes and feedback to provide increasingly personalized recommendations.
                    </p>
                    <button className="px-4 py-2 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700">
                      View Learning Progress
                    </button>
                  </div>
                </div>
              </div>

              <div className="bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-6">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-12 h-12 bg-purple-100 dark:bg-purple-900 rounded-lg flex items-center justify-center">
                    <span className="text-2xl">🔍</span>
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                      Explain & Trace
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-300 mb-3">
                      Understand how the AI arrived at its conclusions with full transparency and reasoning trails.
                    </p>
                    <button className="px-4 py-2 bg-purple-600 text-white text-sm rounded-lg hover:bg-purple-700">
                      Explore Explanations
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );

      case 5:
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Step 5: Validate with Real Data
              </h2>
              <p className="text-gray-600 dark:text-gray-300 mb-4">
                Cross-check AI insights against actual market data and charts.
              </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* AI Recommendation */}
              <div className="bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-6">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-4">AI Recommendation</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-300">Symbol</span>
                    <span className="font-medium text-gray-900 dark:text-white">AAPL</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-300">Strategy</span>
                    <span className="font-medium text-gray-900 dark:text-white">Momentum</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-300">Entry Price</span>
                    <span className="font-medium text-gray-900 dark:text-white">$176.00</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-300">Stop Loss</span>
                    <span className="font-medium text-red-600 dark:text-red-400">$172.00</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-300">Target</span>
                    <span className="font-medium text-green-600 dark:text-green-400">$184.00</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-300">Confidence</span>
                    <span className="font-medium text-gray-900 dark:text-white">85%</span>
                  </div>
                </div>
              </div>

              {/* Market Data */}
              <div className="bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-6">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Current Market Data</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-300">Current Price</span>
                    <span className="font-medium text-green-600 dark:text-green-400">$178.50</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-300">RSI (14)</span>
                    <span className="font-medium text-gray-900 dark:text-white">68.5</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-300">20 SMA</span>
                    <span className="font-medium text-gray-900 dark:text-white">$176.20</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-300">Volume</span>
                    <span className="font-medium text-gray-900 dark:text-white">52.3M</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-300">Avg Volume</span>
                    <span className="font-medium text-gray-900 dark:text-white">37.1M</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-300">Status</span>
                    <span className="px-2 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 rounded text-xs font-medium">
                      Aligned ✓
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
              <p className="text-sm text-green-800 dark:text-green-200">
                ✅ <strong>Validation Complete!</strong> AI recommendations align with current market data. The momentum setup appears valid.
              </p>
            </div>

            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
              <p className="text-sm text-blue-800 dark:text-blue-200">
                🎉 <strong>Journey Complete!</strong> You've experienced the power of AI-driven research. Continue exploring or try other journeys.
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
