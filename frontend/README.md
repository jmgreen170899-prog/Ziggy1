# ZiggyClean Frontend

A comprehensive financial trading and market analysis platform frontend built with Next.js, TypeScript, and modern React patterns.

## 🚀 Features

### Core Functionality

- **RAG Query System**: AI-powered query interface for financial data
- **Agent Interactions**: Intelligent agent-based trading assistance
- **Real-time WebSocket**: Live market data and notifications
- **Health Monitoring**: System health checks and status monitoring

### Market Data

- **Live Quotes**: Real-time stock price updates
- **Interactive Charts**: Advanced charting with multiple timeframes
- **Risk Metrics**: Comprehensive risk analysis and metrics
- **Symbol Search**: Intelligent symbol search and discovery
- **Watchlists**: Customizable symbol tracking

### Trading Features

- **Trading Signals**: AI-generated buy/sell/hold recommendations
- **Portfolio Management**: Complete portfolio tracking and analytics
- **Market Screener**: Advanced filtering and screening tools
- **Signal Analysis**: Detailed signal breakdown with confidence scores

### News & Analysis

- **Live News Feed**: Real-time financial news aggregation
- **Sentiment Analysis**: AI-powered news sentiment tracking
- **Symbol-specific News**: Targeted news for individual securities
- **News Filtering**: Advanced filtering by sentiment, source, and symbols

### Cryptocurrency

- **Crypto Prices**: Real-time cryptocurrency price tracking
- **Technical Analysis**: Advanced crypto technical analysis
- **Favorites Management**: Customizable crypto watchlists
- **Market Data**: Comprehensive crypto market information

### Alerts System

- **Custom Alerts**: User-defined price and condition alerts
- **Real-time Notifications**: Instant browser notifications
- **Alert Management**: Create, update, and delete alerts
- **WebSocket Integration**: Live alert triggering

### Learning & Adaptation

- **Feedback System**: User feedback collection for AI improvement
- **Performance Metrics**: AI adaptation and learning metrics
- **Continuous Learning**: System that learns from user interactions

## 🛠️ Tech Stack

- **Framework**: Next.js 15.5.6 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: Zustand with persistence
- **Real-time Communication**: Socket.IO Client
- **HTTP Client**: Axios with interceptors
- **Charts**: Chart.js and React Chart.js 2
- **UI Components**: Custom component library
- **Data Fetching**: TanStack React Query

## 📁 Project Structure

```
src/
├── app/                    # Next.js App Router pages
│   ├── globals.css        # Global styles
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Dashboard page
├── components/            # React components
│   ├── ui/               # Base UI components (Button, Card, etc.)
│   ├── market/           # Market data components
│   ├── trading/          # Trading-related components
│   ├── news/            # News components
│   ├── crypto/          # Cryptocurrency components
│   ├── alerts/          # Alert components
│   ├── learning/        # Learning system components
│   └── Dashboard.tsx    # Main dashboard component
├── hooks/               # Custom React hooks
│   └── index.ts        # Market data, portfolio, news hooks
├── services/           # External service integrations
│   ├── api.ts         # REST API client
│   └── websocket.ts   # WebSocket service
├── store/             # State management
│   └── index.ts      # Zustand stores for all features
├── types/             # TypeScript type definitions
│   └── api.ts        # API response types
└── utils/             # Utility functions
    └── index.ts      # Formatting, validation, helpers
```

## 🚀 Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Backend API running on `http://localhost:8000` (default)

### Installation

1. **Install dependencies**:

   ```bash
   npm install
   ```

2. **Set up environment variables**:

   ```bash
   # Create .env.local file
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXT_PUBLIC_WS_URL=ws://localhost:8000
   ```

3. **Run the development server**:

   ```bash
   npm run dev
   ```

4. **Open your browser**:
   Navigate to [http://localhost:3000](http://localhost:3000)

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

## 🔧 Configuration

### API Configuration

The frontend connects to the backend API via environment variables:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000    # Backend API URL
NEXT_PUBLIC_WS_URL=ws://localhost:8000       # WebSocket URL
```

### WebSocket Events

The application listens for these real-time events:

- `quote_update` - Live price updates
- `news_update` - New news items
- `alert_triggered` - Alert notifications
- `signal_generated` - New trading signals
- `portfolio_update` - Portfolio changes
- `market_status` - Market status updates

## 📊 Features Overview

### Dashboard

- Portfolio overview with P&L tracking
- Watchlist with real-time updates
- Latest trading signals
- Recent news feed
- Quick navigation to all features

### Real-time Features

- Live price updates via WebSocket
- Instant news notifications
- Real-time alert triggering
- Portfolio update notifications

## 🔌 API Integration

The frontend integrates with the following backend endpoints:

- **Core**: `/query`, `/agent`, `/health`
- **Market**: `/api/market/*` (quotes, charts, risk, search)
- **Trading**: `/api/trading/*` (signals, portfolio, screener)
- **News**: `/api/news/*` (feed, sentiment, filtering)
- **Crypto**: `/api/crypto/*` (prices, analysis)
- **Alerts**: `/api/alerts/*` (CRUD operations)
- **Learning**: `/api/learning/*` (feedback, metrics)
- **Integration**: `/api/integration/*` (hub status, refresh)

## 🎨 Styling

The project uses Tailwind CSS with a dark theme by default. The color scheme includes:

- Green for positive values/gains
- Red for negative values/losses
- Blue for primary actions
- Gray for neutral elements

## 🔄 State Management

Zustand stores manage application state:

- **MarketStore**: Quotes, watchlists, loading states
- **PortfolioStore**: Portfolio data, trading signals
- **NewsStore**: News items, filters, sentiment
- **CryptoStore**: Cryptocurrency prices, favorites
- **AlertsStore**: Alert management and notifications
- **AppStore**: Theme, sidebar, notifications

## 📈 Performance

- Server-side rendering with Next.js App Router
- Efficient state management with Zustand
- Real-time updates via WebSocket
- Optimized bundle size with tree shaking

## 🆘 Troubleshooting

### Common Issues

1. **WebSocket connection fails**:
   - Check if backend is running
   - Verify WebSocket URL in environment variables

2. **API calls fail**:
   - Confirm backend API is accessible
   - Check API URL configuration

3. **Build errors**:
   - Run `npm run lint` for code quality issues

### Development Notes

- The application expects the backend to be running on `http://localhost:8000`
- WebSocket connections are automatically managed with reconnection logic
- All API calls include error handling and loading states
- The theme system supports both light and dark modes (defaults to dark)
