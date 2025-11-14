import { useState, useCallback } from 'react';

/**
 * Journey configuration
 */
export interface JourneyStep {
  id: string;
  title: string;
  description: string;
  component?: string;
}

export interface JourneyConfig {
  id: string;
  name: string;
  title: string;
  description: string;
  steps: JourneyStep[];
  estimatedDuration: string;
}

/**
 * Predefined journey configurations
 */
export const journeyConfigs: Record<string, JourneyConfig> = {
  trader: {
    id: 'trader',
    name: 'Trader Journey',
    title: '📈 Trader Journey',
    description: 'Experience real-time market data, signals, and paper trading',
    estimatedDuration: '5-7 minutes',
    steps: [
      {
        id: 'select_ticker',
        title: 'Select Ticker',
        description: 'Search and choose a stock symbol to analyze',
      },
      {
        id: 'view_chart',
        title: 'View Chart',
        description: 'See live price chart with technical indicators',
      },
      {
        id: 'analyze_signals',
        title: 'Analyze Signals',
        description: 'Review Market Brain insights and trading signals',
      },
      {
        id: 'execute_trade',
        title: 'Execute Paper Trade',
        description: 'Place a simulated trade without real money',
      },
      {
        id: 'monitor_portfolio',
        title: 'Monitor Portfolio',
        description: 'Track your paper trading positions and performance',
      },
    ],
  },
  analyst: {
    id: 'analyst',
    name: 'Analyst Journey',
    title: '🔍 Analyst Journey',
    description: 'Screen the market and discover trading opportunities',
    estimatedDuration: '4-6 minutes',
    steps: [
      {
        id: 'open_screener',
        title: 'Open Screener',
        description: 'Access the market screening tool',
      },
      {
        id: 'choose_preset',
        title: 'Choose Preset',
        description: 'Select momentum or mean reversion strategy',
      },
      {
        id: 'run_scan',
        title: 'Run Scan',
        description: 'Execute screening query across the market',
      },
      {
        id: 'review_results',
        title: 'Review Results',
        description: 'Analyze sorted results with key metrics',
      },
      {
        id: 'drill_down',
        title: 'Drill Down',
        description: 'Explore detailed analysis for selected symbols',
      },
    ],
  },
  research: {
    id: 'research',
    name: 'Research Journey',
    title: '🤖 Research Journey',
    description: 'Leverage AI for market insights and decision support',
    estimatedDuration: '3-5 minutes',
    steps: [
      {
        id: 'open_chat',
        title: 'Open Chat',
        description: 'Access the AI-powered research assistant',
      },
      {
        id: 'ask_question',
        title: 'Ask Question',
        description: 'Type a market or strategy question',
      },
      {
        id: 'review_response',
        title: 'Review Response',
        description: 'Read AI-generated insights and analysis',
      },
      {
        id: 'explore_cognitive',
        title: 'Explore Cognitive',
        description: 'Discover advanced cognitive features',
      },
      {
        id: 'validate_data',
        title: 'Validate Data',
        description: 'Cross-check insights with real market data',
      },
    ],
  },
};

/**
 * Hook for managing journey state
 */
export function useJourney(journeyId: string) {
  const config = journeyConfigs[journeyId];
  
  if (!config) {
    throw new Error(`Unknown journey: ${journeyId}`);
  }

  const [currentStep, setCurrentStep] = useState(1);
  const [completed, setCompleted] = useState(false);

  const totalSteps = config.steps.length;

  const goNext = useCallback(() => {
    if (currentStep < totalSteps) {
      setCurrentStep((prev) => prev + 1);
    } else {
      setCompleted(true);
    }
  }, [currentStep, totalSteps]);

  const goPrevious = useCallback(() => {
    if (currentStep > 1) {
      setCurrentStep((prev) => prev - 1);
    }
  }, [currentStep]);

  const goToStep = useCallback((step: number) => {
    if (step >= 1 && step <= totalSteps) {
      setCurrentStep(step);
      setCompleted(false);
    }
  }, [totalSteps]);

  const reset = useCallback(() => {
    setCurrentStep(1);
    setCompleted(false);
  }, []);

  const complete = useCallback(() => {
    setCompleted(true);
  }, []);

  return {
    config,
    currentStep,
    totalSteps,
    completed,
    currentStepData: config.steps[currentStep - 1],
    goNext,
    goPrevious,
    goToStep,
    reset,
    complete,
    progress: (currentStep / totalSteps) * 100,
  };
}

/**
 * Get all available journeys
 */
export function getAllJourneys(): JourneyConfig[] {
  return Object.values(journeyConfigs);
}

/**
 * Get journey by ID
 */
export function getJourneyById(id: string): JourneyConfig | null {
  return journeyConfigs[id] || null;
}

/**
 * Track journey completion for analytics
 */
export function trackJourneyCompletion(journeyId: string, stepId: string) {
  // In production, send to analytics service
  console.log(`Journey ${journeyId} - Step ${stepId} completed`);
  
  // Store in localStorage for persistence
  const key = `journey_${journeyId}_progress`;
  const progress = JSON.parse(localStorage.getItem(key) || '{}');
  progress[stepId] = {
    completed: true,
    timestamp: new Date().toISOString(),
  };
  localStorage.setItem(key, JSON.stringify(progress));
}

/**
 * Get journey progress from localStorage
 */
export function getJourneyProgress(journeyId: string): Record<string, any> {
  const key = `journey_${journeyId}_progress`;
  return JSON.parse(localStorage.getItem(key) || '{}');
}

/**
 * Clear journey progress
 */
export function clearJourneyProgress(journeyId: string) {
  const key = `journey_${journeyId}_progress`;
  localStorage.removeItem(key);
}
