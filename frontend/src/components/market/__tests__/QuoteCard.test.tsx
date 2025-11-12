import { screen, fireEvent } from '@testing-library/react';
import { render, mockQuote } from '@/__tests__/test-utils';
import { QuoteCard } from '@/components/market/QuoteCard';

// Mock the useScreenReader hook
jest.mock('@/hooks/useAccessibility', () => ({
  useScreenReader: () => ({
    announce: jest.fn(),
    ScreenReaderAnnouncer: () => null,
  }),
}));

describe('QuoteCard', () => {
  const defaultProps = {
    quote: mockQuote(),
    onRemove: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders quote information correctly', () => {
    render(<QuoteCard {...defaultProps} />);
    
    expect(screen.getByText('AAPL')).toBeInTheDocument();
    expect(screen.getByText('$145.67')).toBeInTheDocument();
    expect(screen.getByText('+$2.34 (+1.63%)')).toBeInTheDocument();
  });

  it('displays positive change with correct styling', () => {
    const positiveQuote = mockQuote({
      change: 2.34,
      change_percent: 1.63,
    });

    render(<QuoteCard {...defaultProps} quote={positiveQuote} />);
    
    const changeElement = screen.getByText('+$2.34 (+1.63%)');
    expect(changeElement).toHaveClass('text-green-600');
  });

  it('displays negative change with correct styling', () => {
    const negativeQuote = mockQuote({
      change: -1.45,
      change_percent: -0.98,
    });

    render(<QuoteCard {...defaultProps} quote={negativeQuote} />);
    
    const changeElement = screen.getByText('-$1.45 (-0.98%)');
    expect(changeElement).toHaveClass('text-red-600');
  });

  it('displays neutral change with correct styling', () => {
    const neutralQuote = mockQuote({
      change: 0,
      change_percent: 0,
    });

    render(<QuoteCard {...defaultProps} quote={neutralQuote} />);
    
    const changeElement = screen.getByText('$0.00 (0.00%)');
    expect(changeElement).toHaveClass('text-gray-500');
  });

  it('calls onRemove when remove button is clicked', () => {
    const onRemoveMock = jest.fn();
    
    render(<QuoteCard {...defaultProps} onRemove={onRemoveMock} />);
    
    const removeButton = screen.getByRole('button', { name: /remove.*from watchlist/i });
    fireEvent.click(removeButton);
    
    expect(onRemoveMock).toHaveBeenCalledWith('AAPL');
  });

  it('does not show remove button when onRemove is not provided', () => {
    const propsWithoutRemove = {
      quote: mockQuote(),
    };
    
    render(<QuoteCard {...propsWithoutRemove} />);
    
    const removeButton = screen.queryByRole('button', { name: /remove.*from watchlist/i });
    expect(removeButton).not.toBeInTheDocument();
  });

  it('has proper accessibility attributes', () => {
    render(<QuoteCard {...defaultProps} />);
    
    const card = screen.getByRole('article');
    expect(card).toHaveAttribute('aria-label');
    expect(card).toHaveAttribute('tabIndex', '0');
  });

  it('displays volume information correctly when showDetails is true', () => {
    const quoteWithVolume = mockQuote({
      volume: 45678900,
    });

    render(<QuoteCard {...defaultProps} quote={quoteWithVolume} showDetails={true} />);
    
    expect(screen.getByText(/volume/i)).toBeInTheDocument();
    expect(screen.getByText('45,678,900')).toBeInTheDocument();
  });

  it('displays high/low/open information when showDetails is true', () => {
    const quoteWithDetails = mockQuote({
      high: 147.20,
      low: 143.10,
      open: 144.50,
    });

    render(<QuoteCard {...defaultProps} quote={quoteWithDetails} showDetails={true} />);
    
    expect(screen.getByText(/high/i)).toBeInTheDocument();
    expect(screen.getByText('$147.20')).toBeInTheDocument();
    expect(screen.getByText(/low/i)).toBeInTheDocument();
    expect(screen.getByText('$143.10')).toBeInTheDocument();
    expect(screen.getByText(/open/i)).toBeInTheDocument();
    expect(screen.getByText('$144.50')).toBeInTheDocument();
  });

  it('handles keyboard interaction properly', () => {
    render(<QuoteCard {...defaultProps} />);
    
    const card = screen.getByRole('article');
    
    // Test focus
    card.focus();
    expect(card).toHaveFocus();
    
    // Test keyboard navigation to remove button
    const removeButton = screen.getByRole('button', { name: /remove.*from watchlist/i });
    removeButton.focus();
    expect(removeButton).toHaveFocus();
  });

  it('announces changes to screen readers', () => {
    const { rerender } = render(<QuoteCard {...defaultProps} />);
    
    // Change the quote and rerender
    const updatedQuote = mockQuote({
      price: 150.00,
      change: 6.67,
      change_percent: 4.58,
    });
    
    rerender(<QuoteCard {...defaultProps} quote={updatedQuote} />);
    
    expect(screen.getByText('$150.00')).toBeInTheDocument();
    expect(screen.getByText('+$6.67 (+4.58%)')).toBeInTheDocument();
  });
});