import { render, RenderOptions } from '@testing-library/react';
import { ReactElement } from 'react';
import { ThemeProvider } from '@/providers/ThemeProvider';

// Custom render function that includes providers
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  return (
    <ThemeProvider>
      {children}
    </ThemeProvider>
  );
};

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>,
) => render(ui, { wrapper: AllTheProviders, ...options });

export * from '@testing-library/react';
export { customRender as render };

// Mock data generators
export const mockTradingSignal = (overrides = {}) => ({
  id: '1',
  symbol: 'AAPL',
  signal_type: 'BUY' as const,
  strength: 85,
  confidence: 0.92,
  price_target: 150.00,
  stop_loss: 140.00,
  reasoning: 'Strong technical indicators and positive earnings outlook',
  timestamp: new Date().toISOString(),
  ...overrides,
});

export const mockQuote = (overrides = {}) => ({
  symbol: 'AAPL',
  price: 145.67,
  change: 2.34,
  change_percent: 1.63,
  volume: 45678900,
  high: 147.20,
  low: 143.10,
  open: 144.50,
  close: 145.67,
  timestamp: new Date().toISOString(),
  ...overrides,
});

export const mockPortfolioData = (overrides = {}) => ({
  totalValue: 125000,
  totalGain: 8500,
  totalGainPercent: 7.3,
  dayGain: 425,
  dayGainPercent: 0.34,
  holdings: [
    {
      symbol: 'AAPL',
      shares: 100,
      averageCost: 140.00,
      currentPrice: 145.67,
      totalValue: 14567.00,
      gain: 567.00,
      gainPercent: 4.05,
    },
    {
      symbol: 'MSFT',
      shares: 50,
      averageCost: 320.00,
      currentPrice: 335.20,
      totalValue: 16760.00,
      gain: 760.00,
      gainPercent: 4.75,
    },
  ],
  ...overrides,
});

export const mockNewsItem = (overrides = {}) => ({
  id: '1',
  title: 'Apple Reports Strong Q4 Earnings',
  summary: 'Apple Inc. reported better-than-expected quarterly results...',
  url: 'https://example.com/news/1',
  source: 'Financial Times',
  publishedAt: new Date().toISOString(),
  sentiment: 'positive' as const,
  relevantSymbols: ['AAPL'],
  ...overrides,
});

// Mock intersection observer for testing virtual scrolling
export const mockIntersectionObserver = () => {
  const mockIntersectionObserver = jest.fn();
  mockIntersectionObserver.mockReturnValue({
    observe: () => null,
    unobserve: () => null,
    disconnect: () => null,
  });
  window.IntersectionObserver = mockIntersectionObserver;
  return mockIntersectionObserver;
};