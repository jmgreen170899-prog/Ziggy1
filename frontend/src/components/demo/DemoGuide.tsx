/**
 * Demo Guide Component
 * 
 * Provides guided tours for key user journeys
 */
'use client';

import { useState } from 'react';
import { isDemoMode } from '@/config/demo';

export interface DemoStep {
  title: string;
  description: string;
  action?: string;
  highlight?: string; // CSS selector to highlight
}

export interface DemoJourney {
  name: string;
  title: string;
  description: string;
  steps: DemoStep[];
  icon: string;
}

const demoJourneys: DemoJourney[] = [
  {
    name: 'trader',
    title: '📈 Trader Journey',
    description: 'Explore charts, signals, and execute paper trades',
    icon: '📈',
    steps: [
      {
        title: 'Select a Ticker',
        description: 'Choose a stock symbol like AAPL, MSFT, or NVDA to analyze',
        action: 'Click on a ticker or use the search',
      },
      {
        title: 'View Live Chart',
        description: 'See real-time price data and technical indicators',
        action: 'Charts update automatically with market data',
      },
      {
        title: 'Check Market Brain',
        description: 'Review AI-generated trading signals and market regime',
        action: 'View signals panel for buy/sell recommendations',
      },
      {
        title: 'Execute Paper Trade',
        description: 'Place a simulated trade to test your strategy',
        action: 'Use paper trading panel (no real money)',
      },
      {
        title: 'Monitor Portfolio',
        description: 'Track your positions, P&L, and performance metrics',
        action: 'Navigate to portfolio page',
      },
    ],
  },
  {
    name: 'analyst',
    title: '🔍 Analyst Journey',
    description: 'Screen markets and analyze opportunities',
    icon: '🔍',
    steps: [
      {
        title: 'Open Screener',
        description: 'Access the market screening tool',
        action: 'Navigate to /screener',
      },
      {
        title: 'Choose Preset',
        description: 'Select a preset like Momentum or Mean Reversion',
        action: 'Click on a preset or customize filters',
      },
      {
        title: 'Run Scan',
        description: 'Execute the scan across thousands of stocks',
        action: 'Click "Run Scan" button',
      },
      {
        title: 'Review Results',
        description: 'See ranked list of stocks matching your criteria',
        action: 'Results appear with scores and metrics',
      },
      {
        title: 'Drill Down',
        description: 'Click any ticker to see detailed analysis',
        action: 'View charts, signals, and fundamentals',
      },
    ],
  },
  {
    name: 'research',
    title: '🤖 Research Journey',
    description: 'Ask questions and get AI-powered insights',
    icon: '🤖',
    steps: [
      {
        title: 'Open Chat',
        description: 'Navigate to the AI chat interface',
        action: 'Click on Chat in navigation',
      },
      {
        title: 'Ask a Question',
        description: 'Type a question about any ticker or market condition',
        action: 'Example: "What should I know about AAPL?"',
      },
      {
        title: 'Review AI Response',
        description: 'Get comprehensive analysis with sources',
        action: 'AI provides reasoning and confidence levels',
      },
      {
        title: 'Explore Cognitive Features',
        description: 'Use explain and trace endpoints for deeper insights',
        action: 'Access advanced analysis tools',
      },
      {
        title: 'Validate with Data',
        description: 'Cross-reference AI insights with market data',
        action: 'View charts and signals for validation',
      },
    ],
  },
];

export function DemoGuide() {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedJourney, setSelectedJourney] = useState<DemoJourney | null>(null);
  const [currentStep, setCurrentStep] = useState(0);

  if (!isDemoMode()) {
    return null;
  }

  const handleStartJourney = (journey: DemoJourney) => {
    setSelectedJourney(journey);
    setCurrentStep(0);
  };

  const handleNextStep = () => {
    if (selectedJourney && currentStep < selectedJourney.steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      // Journey complete
      setSelectedJourney(null);
      setCurrentStep(0);
    }
  };

  const handlePrevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleClose = () => {
    setSelectedJourney(null);
    setCurrentStep(0);
    setIsOpen(false);
  };

  // Journey selection view
  if (!selectedJourney) {
    return (
      <>
        {/* Floating guide button */}
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="fixed bottom-6 right-6 z-50 bg-blue-600 hover:bg-blue-700 text-white rounded-full p-4 shadow-lg transition-transform hover:scale-110"
          title="Demo Guide"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </button>

        {/* Guide panel */}
        {isOpen && (
          <div className="fixed bottom-24 right-6 z-50 w-96 bg-white dark:bg-gray-800 rounded-lg shadow-2xl border border-gray-200 dark:border-gray-700">
            <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                🎯 Demo Journeys
              </h3>
              <button
                onClick={() => setIsOpen(false)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>

            <div className="p-4 space-y-3 max-h-96 overflow-y-auto">
              {demoJourneys.map((journey) => (
                <button
                  key={journey.name}
                  onClick={() => handleStartJourney(journey)}
                  className="w-full text-left p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-blue-500 dark:hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
                >
                  <div className="flex items-start gap-3">
                    <span className="text-2xl">{journey.icon}</span>
                    <div className="flex-1">
                      <h4 className="font-semibold text-gray-900 dark:text-white mb-1">
                        {journey.title}
                      </h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {journey.description}
                      </p>
                      <p className="text-xs text-blue-600 dark:text-blue-400 mt-2">
                        {journey.steps.length} steps →
                      </p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
      </>
    );
  }

  // Journey step view
  const currentStepData = selectedJourney.steps[currentStep];
  const progress = ((currentStep + 1) / selectedJourney.steps.length) * 100;

  return (
    <div className="fixed bottom-6 right-6 z-50 w-96 bg-white dark:bg-gray-800 rounded-lg shadow-2xl border border-gray-200 dark:border-gray-700">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {selectedJourney.icon} {selectedJourney.title}
          </h3>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        </div>
        
        {/* Progress bar */}
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          Step {currentStep + 1} of {selectedJourney.steps.length}
        </p>
      </div>

      {/* Content */}
      <div className="p-4">
        <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
          {currentStepData.title}
        </h4>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
          {currentStepData.description}
        </p>
        {currentStepData.action && (
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded p-3">
            <p className="text-sm text-blue-900 dark:text-blue-300">
              <strong>Action:</strong> {currentStepData.action}
            </p>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
        <button
          onClick={handlePrevStep}
          disabled={currentStep === 0}
          className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
        >
          ← Previous
        </button>
        <button
          onClick={handleNextStep}
          className="px-4 py-2 text-sm font-medium bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
        >
          {currentStep === selectedJourney.steps.length - 1 ? 'Finish' : 'Next →'}
        </button>
      </div>
    </div>
  );
}

export default DemoGuide;
