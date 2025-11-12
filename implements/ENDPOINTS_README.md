# ZiggyClean API Architecture & Mock Alignment

## Backend Routes Analysis

Based on frontend API client integration, the following endpoints are available or anticipated:

### Core RAG & Agent Endpoints
```
POST /query                    - RAG query processing
POST /agent                    - Agent interactions  
GET  /health                   - System health check
```

### Market Data Endpoints
```
GET  /api/market/quote/{symbol}     - Single quote
POST /api/market/quotes             - Multiple quotes
GET  /api/market/chart/{symbol}     - Chart data with timeframe
GET  /api/market/risk/{symbol}      - Risk metrics (VaR, beta, etc.)
GET  /api/market/search             - Symbol search
```

### Trading Endpoints
```
GET  /api/trading/signals           - All trading signals
GET  /api/trading/signals/{symbol}  - Symbol-specific signals
GET  /api/trading/portfolio         - Portfolio data
POST /api/trading/screener          - Market screening
```

### News Endpoints
```
GET  /api/news                      - General news feed
GET  /api/news/{symbol}             - Symbol-specific news
GET  /api/news/sentiment            - Sentiment analysis
```

### Crypto Endpoints
```
GET  /api/crypto/prices             - All crypto prices
GET  /api/crypto/price/{symbol}     - Single crypto price
GET  /api/crypto/analysis/{symbol}  - Technical analysis
```

### Alert Endpoints
```
GET    /api/alerts              - Get all alerts
POST   /api/alerts              - Create alert
PUT    /api/alerts/{id}         - Update alert
DELETE /api/alerts/{id}         - Delete alert
```

### Learning Endpoints
```
POST /api/learning/feedback     - Submit user feedback
GET  /api/learning/metrics      - Adaptation metrics
POST /api/learning/update       - Trigger learning update
```

### Integration Hub Endpoints
```
GET  /api/integration/status    - Hub connection status
POST /api/integration/refresh   - Refresh hub data
```

## Frontend API Usage Mapping

### Current API Callers → Routes

**Market Store:**
- `apiClient.getQuote(symbol)` → `GET /api/market/quote/{symbol}`
- `apiClient.getMultipleQuotes(symbols)` → `POST /api/market/quotes`

**Portfolio Store:**
- `apiClient.getPortfolio()` → `GET /api/trading/portfolio`
- `apiClient.getTradingSignals()` → `GET /api/trading/signals`

**News Store:**
- `apiClient.getNews()` → `GET /api/news`
- `apiClient.getNewsForSymbol(symbol)` → `GET /api/news/{symbol}`

**Crypto Store:**
- `apiClient.getCryptoPrices()` → `GET /api/crypto/prices`

**Alerts Store:**
- `apiClient.getAlerts()` → `GET /api/alerts`
- `apiClient.createAlert()` → `POST /api/alerts`

## Inferred Data Domains for Predictive AI

### 1. Predictions/Signals Domain
- **Current**: Basic trading signals with confidence
- **Enhanced**: Multi-timeframe predictions, quality scores, rationale chains
- **Endpoints**: `/api/predictions/*`, `/api/signals/enhanced`

### 2. Confidence/Probabilities Domain  
- **Current**: Single confidence percentage
- **Enhanced**: Probabilistic distributions, scenario modeling
- **Endpoints**: `/api/probabilities/*`, `/api/scenarios/*`

### 3. Entry/Stop/Targets Domain
- **Current**: Optional price targets
- **Enhanced**: Dynamic ATR sizing, risk budgets, R-multiples
- **Endpoints**: `/api/plans/*`, `/api/sizing/*`

### 4. Sentiment/Headlines Domain
- **Current**: Basic news sentiment
- **Enhanced**: Weighted contribution analysis, similar patterns
- **Endpoints**: `/api/evidence/*`, `/api/patterns/*`

### 5. Risk/Throttle/Macro Guard Domain
- **Current**: Basic risk metrics
- **Enhanced**: Regime detection, macro guard windows
- **Endpoints**: `/api/risk/regime`, `/api/macro/guards`

### 6. Backtests Domain
- **Current**: None identified
- **Enhanced**: Historical performance, what-if scenarios
- **Endpoints**: `/api/backtest/*`, `/api/whatif/*`

### 7. Alerts/Warnings Domain
- **Current**: Basic price/volume alerts
- **Enhanced**: Model quality alerts, drift warnings
- **Endpoints**: `/api/monitoring/*`, `/api/quality/*`

### 8. Orders/Logs Domain
- **Current**: None identified
- **Enhanced**: Agent actions queue, execution logs
- **Endpoints**: `/api/orders/*`, `/api/agent/queue`

## Mock Schema Design

### Predictions Schema (`src/mocks/predictions.json`)
```typescript
interface Prediction {
  id: string;
  symbol: string;
  timeframe: '5m' | '15m' | '1h' | '4h' | '1d' | '1w';
  signal: 'bullish' | 'bearish' | 'neutral';
  confidence: number; // 0-100
  expectedMovePct: number;
  rationale: string[];
  quality: number; // 0-100
  createdAt: string;
  expiresAt: string;
  evidence: {
    technicalWeight: number;
    fundamentalWeight: number;
    sentimentWeight: number;
    macroWeight: number;
  };
}
```

### Plans Schema (`src/mocks/plans.json`)
```typescript
interface TradingPlan {
  id: string;
  symbol: string;
  predictionId: string;
  entry: number;
  stop: number;
  target: number;
  atr: number;
  riskAmount: number;
  rMultiple: number;
  size: number;
  status: 'draft' | 'approved' | 'executed' | 'cancelled';
  createdAt: string;
  approvedAt?: string;
}
```

### Evidence Schema (`src/mocks/evidence.json`)
```typescript
interface Evidence {
  predictionId: string;
  sentiment: {
    score: number; // -1 to 1
    label: 'bearish' | 'neutral' | 'bullish';
    sources: number;
  };
  headlines: Array<{
    title: string;
    source: string;
    date: string;
    url: string;
    sentiment: number;
    relevance: number;
  }>;
  indicators: {
    rsi: number;
    macd: { value: number; signal: number; histogram: number };
    sma50: number;
    sma200: number;
    volume_ratio: number;
  };
  history: {
    similarSetups: Array<{
      date: string;
      outcome: 'win' | 'loss';
      movePercent: number;
      similarity: number;
    }>;
  };
}
```

### Agent Queue Schema (`src/mocks/agentQueue.json`)
```typescript
interface AgentAction {
  id: string;
  type: 'monitor' | 'alert' | 'plan' | 'execute' | 'research';
  symbol: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  payload: Record<string, any>;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'requires_approval';
  eta?: string;
  createdAt: string;
  completedAt?: string;
  result?: string;
}
```

## Mock Service Adapter Design

### Environment-Based Switching
```typescript
// src/services/mockAdapter.ts
const USE_MOCKS = process.env.NODE_ENV === 'development' && !process.env.NEXT_PUBLIC_BACKEND_AVAILABLE;

export async function apiCall<T>(
  endpoint: string,
  mockData: T,
  realApiCall: () => Promise<T>
): Promise<T> {
  if (USE_MOCKS) {
    await simulateApiDelay();
    return mockData;
  }
  return realApiCall();
}
```

### Mock Data Generation Strategy
- **Static Mocks**: Base scenarios for initial development
- **Dynamic Mocks**: Time-sensitive data with realistic variation
- **Relationship Mocks**: Connected data (predictions → plans → evidence)

## Integration Points

### Existing Components Enhancement
- **Dashboard**: Add predictions overview card
- **SignalsList**: Enhance with quality scores and rationale
- **QuoteCard**: Add prediction badges and confidence overlays
- **Sidebar**: Add new navigation items for predictive features

### New Component Integration
- **PredictionsHub**: Center panel in main layout
- **EvidenceTab**: Right rail panel
- **PlanBuilder**: Modal/slide-over component
- **ScenarioSimulator**: Bottom panel or dedicated tab
- **AgentConsole**: Bottom panel with action queue
- **SignalCalendar**: Right rail calendar widget
- **QualityMonitor**: Right rail metrics panel

## Development Phases

### Phase 1: Mock Foundation
1. Create all mock schemas and data files
2. Build mock service adapter with environment switching
3. Create TypeScript types for all new interfaces

### Phase 2: Core Predictive Components
1. PredictionsHub - Main prediction cards display
2. EvidenceTab - Rationale and evidence drawer
3. Basic mock integration and testing

### Phase 3: Planning & Simulation
1. PlanBuilder - Trade planning interface
2. ScenarioSimulator - What-if analysis
3. Enhanced mock data with relationships

### Phase 4: AI Agent & Monitoring
1. AgentConsole - Action queue management
2. SignalCalendar - Timeline and scheduling
3. QualityMonitor - Model health tracking

### Phase 5: Integration & Polish
1. Navigation integration
2. Real API endpoint alignment
3. Testing and optimization

## Alignment with Backend

### Expected Backend Implementation
- FastAPI framework with similar endpoint structure
- SQLAlchemy models matching mock schemas
- WebSocket events for real-time prediction updates
- Background tasks for agent actions and model monitoring

### Migration Strategy
- Mock schemas designed to match anticipated backend models
- Environment flag for easy switching between mock and real data
- Incremental backend endpoint replacement
- Backward compatibility maintenance

This architecture ensures the frontend can be developed and tested independently while maintaining alignment with expected backend data structures and API patterns.