# Migration Example: Using the Typed API Client

## Before: Untyped API Calls

Here's how you might have been making API calls before Phase 2:

```typescript
// Old way - untyped, error-prone
import axios from "axios";

async function fetchMarketRisk() {
  try {
    // String-based path, no type checking
    const response = await axios.get("http://localhost:8000/market-risk-lite");

    // No type safety on response.data
    const cpc = response.data.cpc;
    const last = cpc.last; // Could be undefined, no warning

    return {
      value: last,
      zScore: cpc.z20,
    };
  } catch (error) {
    // Error format is unknown
    console.error("Error:", error);
    return null;
  }
}
```

**Problems:**

- ❌ No compile-time type checking
- ❌ No auto-completion
- ❌ Easy to make typos in URLs
- ❌ Response structure is unknown
- ❌ Error handling is inconsistent
- ❌ Hard to refactor

## After: Typed API Client

Here's the same code using the new typed client:

```typescript
// New way - fully typed, compile-time safe
import { apiClient } from "@/services/apiClient";
import type { RiskLiteResponse, ErrorResponse } from "@/types/api";

async function fetchMarketRisk() {
  try {
    // Type-safe method, IDE shows parameters
    const response: RiskLiteResponse = await apiClient.getRiskLite({
      period_days: 180, // IDE suggests valid parameters
      window: 20,
      use_cache: true,
    });

    // TypeScript knows cpc is CPCData | null
    if (response.cpc) {
      // Auto-completion shows: ticker, last, ma20, z20, date
      return {
        value: response.cpc.last,
        zScore: response.cpc.z20,
        ticker: response.cpc.ticker,
      };
    }

    // Handle error case (response.error is string | null)
    console.error("Risk data unavailable:", response.error);
    return null;
  } catch (error) {
    // Error is typed as ErrorResponse
    const apiError = error as ErrorResponse;
    console.error(`Error ${apiError.code}: ${apiError.detail}`);
    console.error("Meta:", apiError.meta);
    return null;
  }
}
```

**Benefits:**

- ✅ Compile-time type checking
- ✅ IDE auto-completion
- ✅ Type-safe parameters
- ✅ Known response structure
- ✅ Standardized error format
- ✅ Safe refactoring

## Real-World Component Example

### Before: Untyped React Component

```typescript
import { useState, useEffect } from 'react';
import axios from 'axios';

export function RiskWidget() {
  const [risk, setRisk] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadRisk() {
      try {
        const response = await axios.get('/market-risk-lite');
        setRisk(response.data);
      } catch (error) {
        console.error('Failed to load risk:', error);
      } finally {
        setLoading(false);
      }
    }
    loadRisk();
  }, []);

  if (loading) return <div>Loading...</div>;
  if (!risk?.cpc) return <div>No data</div>;

  // No type safety on risk.cpc
  return (
    <div>
      <h3>Market Risk</h3>
      <p>Put/Call: {risk.cpc.last?.toFixed(2)}</p>
      <p>Z-Score: {risk.cpc.z20?.toFixed(2)}</p>
    </div>
  );
}
```

### After: Typed React Component

```typescript
import { useState, useEffect } from 'react';
import { apiClient } from '@/services/apiClient';
import type { RiskLiteResponse } from '@/types/api';

export function RiskWidget() {
  // Fully typed state
  const [risk, setRisk] = useState<RiskLiteResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadRisk() {
      try {
        // Type-safe API call
        const data = await apiClient.getRiskLite({
          period_days: 180,
          window: 20,
        });
        setRisk(data);
        setError(null);
      } catch (err) {
        const apiError = err as ErrorResponse;
        setError(apiError.detail);
      } finally {
        setLoading(false);
      }
    }
    loadRisk();
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!risk?.cpc) return <div>No data available</div>;

  // TypeScript knows all properties exist and their types
  return (
    <div>
      <h3>Market Risk ({risk.cpc.ticker})</h3>
      <p>Put/Call: {risk.cpc.last.toFixed(2)}</p>
      <p>20-Day MA: {risk.cpc.ma20.toFixed(2)}</p>
      <p>Z-Score: {risk.cpc.z20.toFixed(2)}</p>
      <p>Date: {risk.cpc.date}</p>
    </div>
  );
}
```

## More Examples

### News Sentiment

```typescript
import { apiClient } from "@/services/apiClient";
import type { SentimentResponse } from "@/types/api";

async function fetchSentiment(ticker: string): Promise<SentimentResponse> {
  const sentiment = await apiClient.getNewsSentiment({
    ticker,
    lookback_days: 3,
    limit: 40,
  });

  // TypeScript knows:
  // - sentiment.score is number
  // - sentiment.label is string
  // - sentiment.samples is SentimentSample[]
  console.log(`${ticker} sentiment: ${sentiment.label} (${sentiment.score})`);
  console.log(`Analyzed ${sentiment.sample_count} articles`);

  return sentiment;
}
```

### Backtesting

```typescript
import { apiClient } from "@/services/apiClient";
import type { BacktestOut } from "@/types/api";

async function runStrategy(symbol: string): Promise<BacktestOut> {
  const result = await apiClient.runBacktest({
    symbol,
    strategy: "sma50_cross",
    timeframe: "1Y",
  });

  // TypeScript knows:
  // - result.metrics is Record<string, any>
  // - result.trades is Array<Record<string, any>>
  // - result.equity is number[]
  console.log(`Backtest for ${result.symbol}:`);
  console.log(`Strategy: ${result.strategy}`);
  console.log(`Summary: ${result.summary}`);

  return result;
}
```

### Alerts

```typescript
import { apiClient } from "@/services/apiClient";
import type { AlertResponse } from "@/types/api";

async function setupAlert(ticker: string): Promise<AlertResponse> {
  const alert = await apiClient.createSMA50Alert({
    symbol: ticker,
    rule: "cross",
  });

  // TypeScript knows:
  // - alert.ok is boolean
  // - alert.message is string
  // - alert.alert is AlertRecord | Record<string, any> | null
  if (alert.ok && alert.alert) {
    console.log(`Alert created: ${alert.alert.id}`);
  }

  return alert;
}
```

## Migration Checklist

When migrating a component to use the typed client:

1. **Replace axios imports**

   ```typescript
   // Before
   import axios from "axios";

   // After
   import { apiClient } from "@/services/apiClient";
   ```

2. **Replace API calls**

   ```typescript
   // Before
   const response = await axios.get("/endpoint");
   const data = response.data;

   // After
   const data = await apiClient.getEndpoint();
   ```

3. **Add type imports**

   ```typescript
   import type { ResponseType } from "@/types/api";
   ```

4. **Update state types**

   ```typescript
   // Before
   const [data, setData] = useState<any>(null);

   // After
   const [data, setData] = useState<ResponseType | null>(null);
   ```

5. **Update error handling**

   ```typescript
   // Before
   catch (error) {
     console.error(error);
   }

   // After
   catch (error) {
     const apiError = error as ErrorResponse;
     console.error(`${apiError.code}: ${apiError.detail}`);
   }
   ```

6. **Test thoroughly**
   - Verify auto-completion works
   - Check for type errors
   - Test error cases
   - Validate response handling

## Benefits Summary

| Aspect          | Before             | After                |
| --------------- | ------------------ | -------------------- |
| Type Safety     | ❌ None            | ✅ Full compile-time |
| Auto-completion | ❌ No              | ✅ Yes               |
| Error Detection | ❌ Runtime only    | ✅ Compile-time      |
| Refactoring     | ❌ Risky           | ✅ Safe              |
| Documentation   | ❌ External        | ✅ Inline JSDoc      |
| Error Format    | ❌ Inconsistent    | ✅ Standardized      |
| URL Management  | ❌ String literals | ✅ Method names      |

## Getting Started

1. **Import the client:**

   ```typescript
   import { apiClient } from "@/services/apiClient";
   ```

2. **Use typed methods:**

   ```typescript
   const data = await apiClient.methodName(params);
   ```

3. **Handle errors:**

   ```typescript
   import type { ErrorResponse } from "@/types/api";

   try {
     const data = await apiClient.methodName();
   } catch (error) {
     const apiError = error as ErrorResponse;
     console.error(apiError.detail);
   }
   ```

4. **Enjoy type safety!** 🎉

## Need Help?

- See `API_CLIENT_README.md` for full documentation
- Check `src/services/apiClient.ts` for available methods
- Review `src/types/api/generated.ts` for all types
- Refer to `PHASE_1_AND_2_COMPLETE.md` for background

---

**Generated:** 2025-11-13  
**For:** Phase 2 Migration
