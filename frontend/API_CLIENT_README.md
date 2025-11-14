# ZiggyAI Typed API Client

## Overview

The typed API client provides type-safe access to all ZiggyAI backend endpoints with compile-time type checking, auto-completion, and standardized error handling.

## Phase 2 Implementation

This is part of **Phase 2 – Typed client & frontend alignment** following Phase 1's OpenAPI standardization.

### What's Included

1. **Generated Types** (`src/types/api/generated.ts`)
   - TypeScript interfaces matching backend Pydantic models
   - All response models from Phase 1 standardization
   - Full type safety for requests and responses

2. **Typed API Client** (`src/services/apiClient.ts`)
   - Type-safe methods for all endpoints
   - Automatic authentication token injection
   - Standardized error handling
   - Request/response interceptors

3. **Generation Script** (`scripts/generate-api-client.ts`)
   - Can fetch and parse OpenAPI spec from backend
   - Generates TypeScript types automatically
   - Generates typed client methods

## Usage

### Basic Usage

```typescript
import { apiClient } from '@/services/apiClient';

// Health check - returns AckResponse
const health = await apiClient.getHealth();

// Get risk data - returns RiskLiteResponse
const riskData = await apiClient.getRiskLite({
  period_days: 180,
  window: 20,
});

// Run backtest - returns BacktestOut
const backtest = await apiClient.runBacktest({
  symbol: 'AAPL',
  strategy: 'sma50_cross',
  timeframe: '1Y',
});
```

### With Type Safety

```typescript
import { apiClient } from '@/services/apiClient';
import type { SentimentResponse } from '@/types/api';

async function fetchSentiment(ticker: string): Promise<SentimentResponse> {
  // Full type checking - parameters and return type
  const sentiment = await apiClient.getNewsSentiment({
    ticker,
    lookback_days: 3,
    limit: 40,
  });
  
  // TypeScript knows the shape of the response
  console.log(`Sentiment for ${sentiment.ticker}: ${sentiment.label}`);
  console.log(`Score: ${sentiment.score}, Confidence: ${sentiment.confidence}`);
  
  return sentiment;
}
```

### Error Handling

All errors follow the standardized `ErrorResponse` format:

```typescript
import { apiClient } from '@/services/apiClient';
import type { ErrorResponse } from '@/types/api';

async function handleApiCall() {
  try {
    const data = await apiClient.getRiskLite();
    return data;
  } catch (error) {
    // Error is typed as ErrorResponse
    const apiError = error as ErrorResponse;
    console.error(`Error ${apiError.code}: ${apiError.detail}`);
    console.error('Metadata:', apiError.meta);
  }
}
```

## Available Endpoints

### Health & Core
- `getHealth()` - Basic health check
- `getHealthDetailed()` - Detailed health with routes
- `getCoreHealth()` - Core health with dependencies

### RAG & Query
- `queryRAG(request)` - Query RAG system
- `ingestWeb(data)` - Ingest web content
- `ingestPDF(file, sourceUrl?)` - Ingest PDF document
- `resetVectorStore()` - Reset vector store

### Tasks
- `scheduleTask(data)` - Schedule a watch task
- `listTasks()` - List all tasks
- `cancelTask(jobId)` - Cancel a task

### Risk & Market
- `getRiskLite(params?)` - Get Put/Call ratio data

### Trading
- `runBacktest(data)` - Run strategy backtest

### Alerts
- `getAlertStatus()` - Get alert system status
- `startAlerts()` - Start alert scanning
- `stopAlerts()` - Stop alert scanning
- `createSMA50Alert(data)` - Create 50-day SMA alert

### News
- `getNewsSentiment(params)` - Get news sentiment
- `pingNews()` - Ping news service

### Screener
- `screenMarket(data)` - Screen market for signals
- `getScreenerHealth()` - Get screener health

### Chat
- `getChatHealth()` - Get chat service health
- `getChatConfig()` - Get chat configuration
- `chatComplete(request)` - Send chat completion request

### Generic Methods
- `get<T>(url, config?)` - Custom GET request
- `post<T>(url, data?, config?)` - Custom POST request
- `put<T>(url, data?, config?)` - Custom PUT request
- `delete<T>(url, config?)` - Custom DELETE request

## Deprecated Endpoints

The following endpoints are marked as deprecated in the backend. Use the preferred endpoints instead:

- `/market/risk-lite` → Use `/market-risk-lite`
- `/market-risk-lite` (in trading) → Use `/market/risk-lite`
- `/market/risk` → Use `/market/risk-lite`
- `/strategy/backtest` → Use `/backtest`
- `/moving-average/50` → Use `/sma50`
- `/headwind` → Use `/sentiment`

## Regenerating the Client

When the backend OpenAPI spec changes:

```bash
# Make sure backend is running on http://localhost:8000
npm run generate:api
```

This will:
1. Fetch `/openapi.json` from the backend
2. Generate TypeScript types in `src/types/api/generated.ts`
3. Generate API client methods in `src/services/apiClient.ts`
4. Save the OpenAPI spec to `openapi.json` for reference

## Migration from Old API Client

### Before (old api.ts)

```typescript
import { api } from '@/services/api';

// Untyped, string-based paths
const response = await api.get('/market-risk-lite');
// No type checking on response.data
const cpc = response.data.cpc;
```

### After (new apiClient.ts)

```typescript
import { apiClient } from '@/services/apiClient';

// Fully typed
const response = await apiClient.getRiskLite();
// TypeScript knows response.cpc is CPCData | null
const cpc = response.cpc;
```

## Benefits

1. **Type Safety**: Catch errors at compile time, not runtime
2. **Auto-completion**: IDEs suggest available methods and properties
3. **Documentation**: Types serve as inline documentation
4. **Refactoring**: Rename and restructure with confidence
5. **Consistency**: All API calls follow the same pattern
6. **Error Handling**: Standardized error format across all endpoints
7. **OpenAPI Alignment**: Types stay in sync with backend contracts

## Next Steps

1. Refactor existing components to use the typed client
2. Remove string-based endpoint paths from components
3. Update pages: `/markets`, `/signals`, `/news`, `/chat`, `/paper`, `/trade`, `/admin`
4. Add tests for API client methods
5. Set up CI to regenerate types when OpenAPI spec changes

## Related Documentation

- [Phase 1 - Contract Hygiene](../backend/PHASE_1_COMPLETE.md)
- [OpenAPI Spec](./openapi.json)
- [Backend Response Models](../backend/app/models/api_responses.py)
