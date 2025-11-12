// Mock data for development when backend is not available
import type { 
  Portfolio, 
  TradingSignal, 
  Quote, 
  NewsItem, 
  CryptoPrice, 
  Alert 
} from '@/types/api';

// Mock Portfolio Data
export const mockPortfolio: Portfolio = {
  total_value: 125000.00,
  cash_balance: 15000.00,
  daily_pnl: 2500.00,
  daily_pnl_percent: 2.05,
  positions: [
    {
      symbol: 'AAPL',
      quantity: 100,
      avg_price: 150.00,
      current_price: 155.25,
      market_value: 15525.00,
      pnl: 525.00,
      pnl_percent: 3.50
    },
    {
      symbol: 'MSFT',
      quantity: 50,
      avg_price: 300.00,
      current_price: 310.50,
      market_value: 15525.00,
      pnl: 525.00,
      pnl_percent: 3.50
    },
    {
      symbol: 'GOOGL',
      quantity: 25,
      avg_price: 2800.00,
      current_price: 2950.00,
      market_value: 73750.00,
      pnl: 3750.00,
      pnl_percent: 5.36
    },
    {
      symbol: 'TSLA',
      quantity: 30,
      avg_price: 200.00,
      current_price: 195.00,
      market_value: 5850.00,
      pnl: -150.00,
      pnl_percent: -2.50
    }
  ]
};

// Mock Trading Signals
export const mockSignals: TradingSignal[] = [
  {
    symbol: 'NVDA',
    signal_type: 'BUY',
    confidence: 85.5,
    strength: 82,
    price_target: 950.00,
    stop_loss: 800.00,
    reasoning: 'Strong earnings beat expected, AI demand surge continues. Technical indicators show bullish momentum with volume confirmation.',
    timestamp: new Date().toISOString()
  },
  {
    symbol: 'AMD',
    signal_type: 'SELL',
    confidence: 78.2,
    strength: 75,
    price_target: 120.00,
    stop_loss: 140.00,
    reasoning: 'Competitive pressure from Intel and NVIDIA. Overvalued based on P/E ratio analysis.',
    timestamp: new Date(Date.now() - 3600000).toISOString() // 1 hour ago
  },
  {
    symbol: 'AAPL',
    signal_type: 'HOLD',
    confidence: 72.8,
    strength: 68,
    reasoning: 'Mixed signals from technical analysis. iPhone sales steady but not growing significantly.',
    timestamp: new Date(Date.now() - 7200000).toISOString() // 2 hours ago
  }
];

// Mock Market Quotes
export const mockQuotes: Record<string, Quote> = {
  'AAPL': {
    symbol: 'AAPL',
    price: 155.25,
    change: 2.75,
    change_percent: 1.80,
    volume: 52340000,
    open: 153.50,
    high: 156.80,
    low: 152.90,
    close: 152.50,
    timestamp: new Date().toISOString()
  },
  'MSFT': {
    symbol: 'MSFT',
    price: 310.50,
    change: -1.25,
    change_percent: -0.40,
    volume: 31200000,
    open: 312.00,
    high: 314.50,
    low: 309.75,
    close: 311.75,
    timestamp: new Date().toISOString()
  },
  'GOOGL': {
    symbol: 'GOOGL',
    price: 2950.00,
    change: 45.00,
    change_percent: 1.55,
    volume: 1850000,
    open: 2920.00,
    high: 2965.00,
    low: 2915.00,
    close: 2905.00,
    timestamp: new Date().toISOString()
  },
  'TSLA': {
    symbol: 'TSLA',
    price: 195.00,
    change: -5.50,
    change_percent: -2.74,
    volume: 89500000,
    open: 201.50,
    high: 203.00,
    low: 194.25,
    close: 200.50,
    timestamp: new Date().toISOString()
  },
  'NVDA': {
    symbol: 'NVDA',
    price: 875.00,
    change: 25.50,
    change_percent: 3.00,
    volume: 45600000,
    open: 850.00,
    high: 880.00,
    low: 845.00,
    close: 849.50,
    timestamp: new Date().toISOString()
  }
};

// Mock News Items
export const mockNews: NewsItem[] = [
  {
    id: '1',
    title: 'Federal Reserve Signals Potential Rate Cut in Q4 2025',
    summary: 'Fed officials hint at accommodative monetary policy amid economic uncertainty',
    content: 'Federal Reserve officials suggested today that they may consider cutting interest rates in the fourth quarter of 2025 if economic conditions warrant such action. The central bank has been monitoring inflation closely while balancing employment targets.',
    url: 'https://example.com/fed-rate-cut',
    source: 'Financial Times',
    published_date: new Date(Date.now() - 1800000).toISOString(), // 30 min ago
    sentiment: 'positive',
    symbols: ['SPY', 'QQQ']
  },
  {
    id: '2',
    title: 'NVIDIA Reports Record Q3 Earnings, Beats Estimates',
    summary: 'AI chip demand drives 94% revenue growth year-over-year',
    content: 'NVIDIA Corporation reported record third-quarter earnings today, significantly beating analyst estimates with revenue of $60.9 billion, up 94% from the same period last year. The exceptional growth was driven primarily by data center revenue.',
    url: 'https://example.com/nvidia-earnings',
    source: 'Reuters',
    published_date: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
    sentiment: 'positive',
    symbols: ['NVDA']
  },
  {
    id: '3',
    title: 'Tesla Faces Production Challenges in Shanghai Plant',
    summary: 'Supply chain disruptions impact Q4 delivery targets',
    content: 'Tesla\'s Shanghai Gigafactory is experiencing supply chain disruptions that could impact the company\'s Q4 delivery targets. The company is working with suppliers to resolve bottlenecks and maintain production schedules.',
    url: 'https://example.com/tesla-production',
    source: 'Bloomberg',
    published_date: new Date(Date.now() - 5400000).toISOString(), // 1.5 hours ago
    sentiment: 'negative',
    symbols: ['TSLA']
  },
  {
    id: '4',
    title: 'Apple Announces New AI Features for iPhone 16',
    summary: 'Enhanced Siri capabilities and on-device processing improvements',
    content: 'Apple unveiled significant AI enhancements for the iPhone 16 series, including improved Siri natural language processing and new on-device machine learning capabilities that enhance privacy while improving performance.',
    url: 'https://example.com/apple-ai',
    source: 'TechCrunch',
    published_date: new Date(Date.now() - 7200000).toISOString(), // 2 hours ago
    sentiment: 'positive',
    symbols: ['AAPL']
  },
  {
    id: '5',
    title: 'Cryptocurrency Market Sees Mixed Performance',
    summary: 'Bitcoin holds above $35k while altcoins show volatility',
    content: 'The cryptocurrency market showed mixed performance today with Bitcoin maintaining support above $35,000 while many altcoins experienced increased volatility. Market analysts attribute the divergence to institutional interest in Bitcoin versus speculative trading in smaller cryptocurrencies.',
    url: 'https://example.com/crypto-market',
    source: 'CoinDesk',
    published_date: new Date(Date.now() - 10800000).toISOString(), // 3 hours ago
    sentiment: 'neutral',
    symbols: ['BTC', 'ETH']
  }
];

// Mock Crypto Prices
export const mockCryptoPrices: CryptoPrice[] = [
  {
    symbol: 'BTC',
    name: 'Bitcoin',
    price: 35250.00,
    change_24h: 850.00,
    change_percent_24h: 2.47,
    volume_24h: 15500000000,
    market_cap: 689000000000,
    rank: 1
  },
  {
    symbol: 'ETH',
    name: 'Ethereum',
    price: 2150.00,
    change_24h: -45.00,
    change_percent_24h: -2.05,
    volume_24h: 8200000000,
    market_cap: 258000000000,
    rank: 2
  },
  {
    symbol: 'BNB',
    name: 'Binance Coin',
    price: 285.50,
    change_24h: 12.75,
    change_percent_24h: 4.68,
    volume_24h: 1100000000,
    market_cap: 42700000000,
    rank: 3
  },
  {
    symbol: 'ADA',
    name: 'Cardano',
    price: 0.375,
    change_24h: 0.015,
    change_percent_24h: 4.17,
    volume_24h: 245000000,
    market_cap: 13200000000,
    rank: 8
  },
  {
    symbol: 'SOL',
    name: 'Solana',
    price: 95.50,
    change_24h: -2.25,
    change_percent_24h: -2.30,
    volume_24h: 1800000000,
    market_cap: 42100000000,
    rank: 5
  }
];

// Mock Alerts
export const mockAlerts: Alert[] = [
  {
    id: '1',
    type: 'price',
    symbol: 'AAPL',
    condition: 'price_above',
    target_value: 155.00,
    current_value: 155.25,
    is_active: true,
    created_at: new Date(Date.now() - 86400000).toISOString(), // 1 day ago
    triggered_at: new Date(Date.now() - 1800000).toISOString(), // 30 min ago
    message: 'AAPL crossed above $155'
  },
  {
    id: '2',
    type: 'price',
    symbol: 'TSLA',
    condition: 'price_below',
    target_value: 200.00,
    current_value: 195.00,
    is_active: true,
    created_at: new Date(Date.now() - 172800000).toISOString(), // 2 days ago
    triggered_at: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
    message: 'TSLA dropped below $200'
  },
  {
    id: '3',
    type: 'volume',
    symbol: 'NVDA',
    condition: 'volume_above',
    target_value: 40000000,
    current_value: 45600000,
    is_active: true,
    created_at: new Date(Date.now() - 259200000).toISOString(), // 3 days ago
    message: 'NVDA volume spike detected'
  }
];

// Development mode detection
export const isDevelopmentMode = process.env.NODE_ENV === 'development';
export const isBackendAvailable = process.env.NEXT_PUBLIC_BACKEND_AVAILABLE === 'true';

// Helper function to simulate API delay
export const simulateApiDelay = (ms: number = 500) => 
  new Promise(resolve => setTimeout(resolve, ms));