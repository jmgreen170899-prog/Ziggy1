import { screen } from '@testing-library/react';
import { render, mockTradingSignal } from '@/__tests__/test-utils';
import { SignalsList } from '@/components/trading/SignalsList';

// Mock the accessibility hooks
jest.mock('@/hooks/useAccessibility', () => ({
  useKeyboardNavigation: () => ({
    listRef: { current: null },
    currentIndex: 0,
  }),
  useScreenReader: () => ({
    announce: jest.fn(),
    ScreenReaderAnnouncer: () => null,
  }),
}));

describe('SignalsList', () => {
  const mockSignals = [
    mockTradingSignal(),
    mockTradingSignal({
      id: '2',
      symbol: 'MSFT',
      signal_type: 'SELL',
      strength: 75,
      confidence: 0.85,
    }),
    mockTradingSignal({
      id: '3',
      symbol: 'GOOGL',
      signal_type: 'HOLD',
      strength: 60,
      confidence: 0.70,
    }),
  ];

  it('renders loading state correctly', () => {
    render(<SignalsList signals={[]} loading={true} />);
    
    expect(screen.getByRole('status')).toBeInTheDocument();
    expect(screen.getByText(/loading trading signals/i)).toBeInTheDocument();
  });

  it('renders error state correctly', () => {
    const errorMessage = 'Failed to fetch signals';
    render(<SignalsList signals={[]} error={errorMessage} />);
    
    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText('Failed to load signals')).toBeInTheDocument();
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  it('renders empty state correctly', () => {
    render(<SignalsList signals={[]} />);
    
    expect(screen.getByRole('status')).toBeInTheDocument();
    expect(screen.getByText('No trading signals available')).toBeInTheDocument();
  });

  it('renders signals list correctly', () => {
    render(<SignalsList signals={mockSignals} />);
    
    expect(screen.getByText('Trading Signals')).toBeInTheDocument();
    expect(screen.getByText('3 signals')).toBeInTheDocument();
    
    // Check each signal is rendered
    expect(screen.getByText('AAPL')).toBeInTheDocument();
    expect(screen.getByText('MSFT')).toBeInTheDocument();
    expect(screen.getByText('GOOGL')).toBeInTheDocument();
  });

  it('displays signal type badges correctly', () => {
    render(<SignalsList signals={mockSignals} />);
    
    expect(screen.getByText('BUY')).toBeInTheDocument();
    expect(screen.getByText('SELL')).toBeInTheDocument();
    expect(screen.getByText('HOLD')).toBeInTheDocument();
  });

  it('displays signal strength correctly', () => {
    render(<SignalsList signals={mockSignals} />);
    
    expect(screen.getByText('85%')).toBeInTheDocument();
    expect(screen.getByText('75%')).toBeInTheDocument();
    expect(screen.getByText('60%')).toBeInTheDocument();
  });

  it('displays confidence levels correctly', () => {
    render(<SignalsList signals={mockSignals} />);
    
    expect(screen.getByText('92.00%')).toBeInTheDocument();
    expect(screen.getByText('85.00%')).toBeInTheDocument();
    expect(screen.getByText('70.00%')).toBeInTheDocument();
  });

  it('displays price targets when available', () => {
    const signalWithTarget = mockTradingSignal({
      price_target: 160.00,
    });
    
    render(<SignalsList signals={[signalWithTarget]} />);
    
    expect(screen.getByText(/target/i)).toBeInTheDocument();
    expect(screen.getByText('$160.00')).toBeInTheDocument();
  });

  it('displays stop loss when available', () => {
    const signalWithStopLoss = mockTradingSignal({
      stop_loss: 135.00,
    });
    
    render(<SignalsList signals={[signalWithStopLoss]} />);
    
    expect(screen.getByText(/stop loss/i)).toBeInTheDocument();
    expect(screen.getByText('$135.00')).toBeInTheDocument();
  });

  it('displays reasoning when available', () => {
    const signalWithReasoning = mockTradingSignal({
      reasoning: 'Strong technical indicators suggest upward momentum',
    });
    
    render(<SignalsList signals={[signalWithReasoning]} />);
    
    expect(screen.getByText(/reasoning/i)).toBeInTheDocument();
    expect(screen.getByText('Strong technical indicators suggest upward momentum')).toBeInTheDocument();
  });

  it('has proper accessibility structure', () => {
    render(<SignalsList signals={mockSignals} />);
    
    expect(screen.getByRole('feed')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Trading Signals' })).toBeInTheDocument();
    expect(screen.getAllByRole('article')).toHaveLength(3);
  });

  it('provides keyboard navigation help text', () => {
    render(<SignalsList signals={mockSignals} />);
    
    const helpText = screen.getByText(/use arrow keys to navigate/i);
    expect(helpText).toBeInTheDocument();
    expect(helpText).toHaveClass('sr-only');
  });

  it('announces signal count changes', () => {
    const { rerender } = render(<SignalsList signals={mockSignals} />);
    
    // Change the number of signals
    const newSignals = [...mockSignals, mockTradingSignal({ id: '4', symbol: 'TSLA' })];
    rerender(<SignalsList signals={newSignals} />);
    
    expect(screen.getByText('4 signals')).toBeInTheDocument();
  });

  it('handles singular signal count correctly', () => {
    render(<SignalsList signals={[mockSignals[0]]} />);
    
    expect(screen.getByText('1 signal')).toBeInTheDocument();
  });

  it('applies correct color classes for signal types', () => {
    render(<SignalsList signals={mockSignals} />);
    
    const buySignal = screen.getByText('BUY');
    const sellSignal = screen.getByText('SELL');
    const holdSignal = screen.getByText('HOLD');
    
    expect(buySignal).toHaveClass('text-green-600');
    expect(sellSignal).toHaveClass('text-red-600');
    expect(holdSignal).toHaveClass('text-yellow-600');
  });

  it('supports keyboard navigation on signal cards', () => {
    render(<SignalsList signals={mockSignals} />);
    
    const signalCards = screen.getAllByRole('article');
    
    // Each card should be focusable
    signalCards.forEach(card => {
      expect(card).toHaveAttribute('tabIndex', '0');
    });
    
    // Test focus on first card
    signalCards[0].focus();
    expect(signalCards[0]).toHaveFocus();
  });

  it('displays signal timestamps correctly', () => {
    const signalWithTimestamp = mockTradingSignal({
      timestamp: '2024-01-15T10:30:00Z',
    });
    
    render(<SignalsList signals={[signalWithTimestamp]} />);
    
    const timeElement = screen.getByRole('time');
    expect(timeElement).toBeInTheDocument();
    expect(timeElement).toHaveAttribute('dateTime', '2024-01-15T10:30:00Z');
  });
});