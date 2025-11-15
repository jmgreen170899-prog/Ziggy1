/**
 * TypeScript types generated from backend OpenAPI spec
 * Based on Phase 1 standardized response models
 *
 * Generated on 2025-11-13
 *
 * These types match the backend Pydantic models:
 * - app/models/api_responses.py
 * - app/api/routes_*.py response models
 */

// ============================================================================
// Core Response Models (from app/models/api_responses.py)
// ============================================================================

/** Standardized error response for all API errors */
export interface ErrorResponse {
  /** Human-readable error message */
  detail: string;
  /** Machine-readable error code */
  code: string;
  /** Additional error context and metadata */
  meta: Record<string, any>;
}

/** Simple acknowledgment response for operations that don't return data */
export interface AckResponse {
  /** Operation succeeded */
  ok: boolean;
  /** Optional success message */
  message?: string | null;
}

/** Health check response */
export interface HealthResponse {
  /** Health status (ok, degraded, error) */
  status: string;
  /** Health check details */
  details: Record<string, any>;
}

/** Generic message response */
export interface MessageResponse {
  /** Response message */
  message: string;
  /** Optional response data */
  data?: Record<string, any> | null;
}

// ============================================================================
// Risk Lite (from routes_risk_lite.py)
// ============================================================================

/** Put/Call ratio data */
export interface CPCData {
  /** Ticker symbol used (^CPC or ^CPCE) */
  ticker: string;
  /** Most recent Put/Call ratio */
  last: number;
  /** 20-period moving average */
  ma20: number;
  /** Z-score relative to 20-period window */
  z20: number;
  /** Date of last data point */
  date: string;
}

/** Risk lite endpoint response */
export interface RiskLiteResponse {
  /** Put/Call ratio data, null on error */
  cpc: CPCData | null;
  /** Error message if data unavailable */
  error?: string | null;
}

// ============================================================================
// Trading (from routes_trading.py)
// ============================================================================

/** Backtest input parameters */
export interface BacktestIn {
  symbol?: string | null;
  ticker?: string | null;
  /** Strategy key */
  strategy?: string;
  timeframe?: string | null;
  lookback_days?: number | null;
}

/** Backtest output */
export interface BacktestOut {
  ok: boolean;
  symbol: string;
  strategy: string;
  metrics: Record<string, any>;
  summary?: string | null;
  url?: string | null;
  report_url?: string | null;
  html_url?: string | null;
  meta: Record<string, any>;
  period?: string | number | null;
  trades: Array<Record<string, any>>;
  returns: number[];
  equity: number[];
  notes?: string | null;
}

// ============================================================================
// Alerts (from routes_alerts.py)
// ============================================================================

/** Alert record details */
export interface AlertRecord {
  /** Alert identifier */
  id: string;
  /** Symbol/ticker */
  symbol: string;
  /** Alert type */
  type: string;
  /** Alert parameters */
  params: Record<string, any>;
  /** Creation timestamp */
  created_at: number;
  /** Alert status */
  status: string;
  /** Alert engine used */
  engine: string;
  /** Error message if failed */
  error?: string | null;
}

/** Standard alert operation response */
export interface AlertResponse {
  /** Operation succeeded */
  ok: boolean;
  /** Response message */
  message: string;
  /** Alert record */
  alert?: AlertRecord | Record<string, any> | null;
  /** Response timestamp */
  asof: number;
}

/** Alert system status response */
export interface AlertStatusResponse {
  /** Status check succeeded */
  ok: boolean;
  /** Whether alerts are enabled */
  enabled: boolean;
  /** Detailed status information */
  status?: Record<string, any> | null;
  /** Response timestamp */
  asof: number;
}

// ============================================================================
// Core Routes (from routes.py)
// ============================================================================

/** Core health check response with dependencies status */
export interface CoreHealthResponse {
  /** Overall status */
  status: string;
  /** Status of each dependency */
  details: Record<string, any>;
}

/** PDF ingestion response */
export interface IngestPdfResponse {
  /** Number of chunks indexed */
  chunks_indexed: number;
  /** Original filename */
  filename?: string | null;
  /** Source URL if provided */
  source_url?: string | null;
}

/** Vector store reset response */
export interface ResetResponse {
  /** Operation status */
  status: string;
  /** Status message */
  message: string;
}

/** Task scheduling response */
export interface TaskScheduleResponse {
  /** Scheduling status */
  status: string;
  /** Job identifier */
  job_id: string;
  /** Watch topic */
  topic: string;
  /** Cron schedule expression */
  cron: string;
}

/** Task list response */
export interface TaskListResponse {
  /** List of scheduled jobs */
  jobs: Array<Record<string, any>>;
}

/** Task cancellation response */
export interface TaskCancelResponse {
  /** Cancellation status */
  status: string;
  /** Cancelled job identifier */
  job_id: string;
}

// ============================================================================
// News (from routes_news.py)
// ============================================================================

/** Individual article sentiment sample */
export interface SentimentSample {
  /** News source */
  source: string;
  /** Article title */
  title: string;
  /** Article URL */
  url: string;
  /** Publication date */
  published: string;
  /** Sentiment score [-1, 1] */
  score: number;
  /** Sentiment label (negative/neutral/positive) */
  label: string;
}

/** Sentiment analysis response */
export interface SentimentResponse {
  /** Ticker symbol */
  ticker: string;
  /** Aggregated sentiment score [-1, 1] */
  score: number;
  /** Sentiment label (negative/neutral/positive) */
  label: string;
  /** Confidence score [0, 1] */
  confidence: number;
  /** Number of articles analyzed */
  sample_count: number;
  /** Last update timestamp */
  updated_at: string;
  /** Individual article sentiments */
  samples: SentimentSample[];
}

/** News service ping response */
export interface NewsPingResponse {
  /** Service status */
  status: string;
  /** Response timestamp */
  asof: number;
}

// ============================================================================
// Screener (from routes_screener.py)
// ============================================================================

/** Screener health check response */
export interface ScreenerHealthResponse {
  /** Whether cognitive core is available */
  cognitive_core_available: boolean;
  /** Supported symbol universes */
  supported_universes: string[];
  /** Maximum symbols per request */
  max_symbols_per_request: number;
  /** Available screening presets */
  available_presets: string[];
  /** Response timestamp */
  timestamp: string;
}

/** Screener result for a single symbol */
export interface ScreenerResult {
  symbol: string;
  p_up: number;
  confidence: number;
  regime: string;
  top_features: Array<any>;
  score: number;
  position_size?: Record<string, any> | null;
}

/** Response from screener */
export interface ScreenerResponse {
  results: ScreenerResult[];
  total_screened: number;
  filters_applied: Record<string, any>;
  execution_time_ms: number;
  regime_breakdown: Record<string, number>;
}

// ============================================================================
// Chat (from routes_chat.py)
// ============================================================================

/** Chat service health check response */
export interface ChatHealthResponse {
  /** LLM provider (openai or local) */
  provider: string;
  /** Base URL for the provider */
  base: string;
  /** Model being used */
  model: string;
  /** Health check passed */
  ok: boolean;
  /** HTTP status code from provider */
  status_code?: number | null;
  /** Error details if health check failed */
  detail?: string | null;
  /** Exception error if check failed */
  error?: string | null;
}

/** Chat service configuration response */
export interface ChatConfigResponse {
  /** LLM provider (openai or local) */
  provider: string;
  /** Base URL for the provider */
  base: string;
  /** Default model name */
  default_model: string;
  /** Request timeout in seconds */
  timeout_sec: number;
  /** Whether OpenAI is being used */
  use_openai: boolean;
}

/** Chat completion request */
export interface ChatCompletionRequest {
  /** Chat messages */
  messages: Array<{
    role: "system" | "user" | "assistant";
    content: string;
  }>;
  /** Model to use */
  model?: string;
  /** Temperature for sampling */
  temperature?: number;
  /** Maximum tokens to generate */
  max_tokens?: number;
  /** Whether to stream the response */
  stream?: boolean;
}

// ============================================================================
// RAG and Query Types (legacy types from original api.ts)
// ============================================================================

export interface RAGQueryRequest {
  query: string;
  top_k?: number;
}

export interface Citation {
  url?: string | null;
  title?: string | null;
  score: number;
  snippet: string;
}

export interface QueryResponse {
  answer: string;
  citations: Citation[];
  contexts: string[];
}

// ============================================================================
// Re-export for backward compatibility
// ============================================================================

export type {
  // Errors
  ErrorResponse as ApiError,
  // Health
  HealthResponse as ApiHealthResponse,
  // Common
  AckResponse as ApiAckResponse,
  MessageResponse as ApiMessageResponse,
};
