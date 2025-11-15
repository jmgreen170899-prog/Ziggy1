/**
 * Typed API Client for ZiggyAI Backend
 *
 * Generated based on Phase 1 OpenAPI standardization
 *
 * This client provides type-safe access to all backend endpoints with:
 * - Compile-time type checking
 * - Auto-completion in IDEs
 * - Standardized error handling
 * - Request/response transformation
 *
 * Usage:
 *   import { apiClient } from '@/services/apiClient';
 *   const data = await apiClient.getRiskLite();
 */

import axios, { AxiosInstance, AxiosError, AxiosRequestConfig } from "axios";
import type {
  // Core responses
  ErrorResponse,
  AckResponse,
  HealthResponse,
  CoreHealthResponse,
  // Risk
  RiskLiteResponse,
  // Trading
  BacktestIn,
  BacktestOut,
  // Alerts
  AlertResponse,
  AlertStatusResponse,
  // Tasks
  TaskScheduleResponse,
  TaskListResponse,
  TaskCancelResponse,
  IngestPdfResponse,
  ResetResponse,
  // News
  SentimentResponse,
  NewsPingResponse,
  // Screener
  ScreenerHealthResponse,
  ScreenerResponse,
  // Chat
  ChatHealthResponse,
  ChatConfigResponse,
  ChatCompletionRequest,
  // RAG
  RAGQueryRequest,
  QueryResponse,
} from "@/types/api/generated";

/**
 * API Client Configuration
 */
export interface ApiClientConfig extends AxiosRequestConfig {
  baseURL?: string;
  timeout?: number;
}

/**
 * Typed API Client for ZiggyAI Backend
 */
export class ZiggyAPIClient {
  private client: AxiosInstance;

  constructor(config?: ApiClientConfig) {
    const baseURL =
      config?.baseURL ||
      process.env.NEXT_PUBLIC_API_URL ||
      "http://localhost:8000";

    this.client = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        "Content-Type": "application/json",
      },
      ...config,
    });

    // Request interceptor for authentication
    this.client.interceptors.request.use((config) => {
      if (typeof window !== "undefined") {
        const token = window.localStorage.getItem("auth_token");
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
      }
      return config;
    });

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<ErrorResponse>) => {
        // Standardized error handling
        const apiError: ErrorResponse = error.response?.data || {
          detail: error.message || "An unknown error occurred",
          code: error.code || "network_error",
          meta: {
            status: error.response?.status,
            statusText: error.response?.statusText,
          },
        };

        console.error("API Error:", {
          url: error.config?.url,
          method: error.config?.method,
          status: error.response?.status,
          error: apiError,
        });

        return Promise.reject(apiError);
      },
    );
  }

  // ========================================================================
  // Health & Core Endpoints
  // ========================================================================

  /**
   * Basic health check
   * GET /health
   */
  async getHealth(): Promise<AckResponse> {
    const response = await this.client.get<AckResponse>("/health");
    return response.data;
  }

  /**
   * Detailed health check with router information
   * GET /health/detailed
   */
  async getHealthDetailed(): Promise<HealthResponse> {
    const response = await this.client.get<HealthResponse>("/health/detailed");
    return response.data;
  }

  /**
   * Core health check with dependencies
   * GET /api/core/health
   */
  async getCoreHealth(): Promise<CoreHealthResponse> {
    const response =
      await this.client.get<CoreHealthResponse>("/api/core/health");
    return response.data;
  }

  // ========================================================================
  // RAG & Query Endpoints
  // ========================================================================

  /**
   * Query RAG system
   * POST /api/query
   */
  async queryRAG(request: RAGQueryRequest): Promise<QueryResponse> {
    const response = await this.client.post<QueryResponse>(
      "/api/query",
      request,
    );
    return response.data;
  }

  /**
   * Ingest web content
   * POST /api/ingest/web
   */
  async ingestWeb(data: { query: string; max_results?: number }): Promise<any> {
    const response = await this.client.post("/api/ingest/web", data);
    return response.data;
  }

  /**
   * Ingest PDF document
   * POST /api/ingest/pdf
   */
  async ingestPDF(file: File, sourceUrl?: string): Promise<IngestPdfResponse> {
    const formData = new FormData();
    formData.append("file", file);
    if (sourceUrl) {
      formData.append("source_url", sourceUrl);
    }

    const response = await this.client.post<IngestPdfResponse>(
      "/api/ingest/pdf",
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      },
    );
    return response.data;
  }

  /**
   * Reset vector store
   * POST /api/reset
   */
  async resetVectorStore(): Promise<ResetResponse> {
    const response = await this.client.post<ResetResponse>("/api/reset");
    return response.data;
  }

  // ========================================================================
  // Task Management
  // ========================================================================

  /**
   * Schedule a watch task
   * POST /api/tasks/watch
   */
  async scheduleTask(data: {
    topic: string;
    cron?: string;
    job_id?: string;
  }): Promise<TaskScheduleResponse> {
    const response = await this.client.post<TaskScheduleResponse>(
      "/api/tasks/watch",
      data,
    );
    return response.data;
  }

  /**
   * List scheduled tasks
   * GET /api/tasks
   */
  async listTasks(): Promise<TaskListResponse> {
    const response = await this.client.get<TaskListResponse>("/api/tasks");
    return response.data;
  }

  /**
   * Cancel a scheduled task
   * DELETE /api/tasks
   */
  async cancelTask(jobId: string): Promise<TaskCancelResponse> {
    const response = await this.client.delete<TaskCancelResponse>(
      "/api/tasks",
      {
        data: { job_id: jobId },
      },
    );
    return response.data;
  }

  // ========================================================================
  // Risk & Market Data
  // ========================================================================

  /**
   * Get market risk lite (Put/Call ratio)
   * GET /market-risk-lite
   */
  async getRiskLite(params?: {
    period_days?: number;
    window?: number;
    use_cache?: boolean;
  }): Promise<RiskLiteResponse> {
    const response = await this.client.get<RiskLiteResponse>(
      "/market-risk-lite",
      { params },
    );
    return response.data;
  }

  // ========================================================================
  // Trading & Backtesting
  // ========================================================================

  /**
   * Run a backtest
   * POST /backtest
   */
  async runBacktest(data: BacktestIn): Promise<BacktestOut> {
    const response = await this.client.post<BacktestOut>("/backtest", data);
    return response.data;
  }

  // ========================================================================
  // Alerts
  // ========================================================================

  /**
   * Get alert system status
   * GET /alerts/status
   */
  async getAlertStatus(): Promise<AlertStatusResponse> {
    const response =
      await this.client.get<AlertStatusResponse>("/alerts/status");
    return response.data;
  }

  /**
   * Start alert scanning
   * POST /alerts/start
   */
  async startAlerts(): Promise<AlertStatusResponse> {
    const response =
      await this.client.post<AlertStatusResponse>("/alerts/start");
    return response.data;
  }

  /**
   * Stop alert scanning
   * POST /alerts/stop
   */
  async stopAlerts(): Promise<AlertStatusResponse> {
    const response =
      await this.client.post<AlertStatusResponse>("/alerts/stop");
    return response.data;
  }

  /**
   * Create a 50-day SMA alert
   * POST /alerts/sma50
   */
  async createSMA50Alert(data: {
    symbol?: string;
    ticker?: string;
    rule?: string;
  }): Promise<AlertResponse> {
    const response = await this.client.post<AlertResponse>(
      "/alerts/sma50",
      data,
    );
    return response.data;
  }

  // ========================================================================
  // News & Sentiment
  // ========================================================================

  /**
   * Get news sentiment for a ticker
   * GET /news/sentiment
   */
  async getNewsSentiment(params: {
    ticker?: string;
    symbol?: string;
    lookback_days?: number;
    limit?: number;
  }): Promise<SentimentResponse> {
    const response = await this.client.get<SentimentResponse>(
      "/news/sentiment",
      { params },
    );
    return response.data;
  }

  /**
   * Ping news service
   * GET /news/ping
   */
  async pingNews(): Promise<NewsPingResponse> {
    const response = await this.client.get<NewsPingResponse>("/news/ping");
    return response.data;
  }

  // ========================================================================
  // Screener
  // ========================================================================

  /**
   * Screen market for signals
   * POST /screener/scan
   */
  async screenMarket(data: {
    universe: string[];
    min_confidence?: number;
    min_probability?: number;
    max_probability?: number;
    regimes?: string[];
    sort_by?: string;
    limit?: number;
  }): Promise<ScreenerResponse> {
    const response = await this.client.post<ScreenerResponse>(
      "/screener/scan",
      data,
    );
    return response.data;
  }

  /**
   * Get screener health
   * GET /screener/health
   */
  async getScreenerHealth(): Promise<ScreenerHealthResponse> {
    const response =
      await this.client.get<ScreenerHealthResponse>("/screener/health");
    return response.data;
  }

  // ========================================================================
  // Chat & LLM
  // ========================================================================

  /**
   * Get chat service health
   * GET /chat/health
   */
  async getChatHealth(): Promise<ChatHealthResponse> {
    const response = await this.client.get<ChatHealthResponse>("/chat/health");
    return response.data;
  }

  /**
   * Get chat configuration
   * GET /chat/config
   */
  async getChatConfig(): Promise<ChatConfigResponse> {
    const response = await this.client.get<ChatConfigResponse>("/chat/config");
    return response.data;
  }

  /**
   * Send chat completion request
   * POST /chat/complete
   */
  async chatComplete(request: ChatCompletionRequest): Promise<any> {
    const response = await this.client.post("/chat/complete", request);
    return response.data;
  }

  // ========================================================================
  // Generic request method for custom endpoints
  // ========================================================================

  /**
   * Make a custom GET request
   */
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<T>(url, config);
    return response.data;
  }

  /**
   * Make a custom POST request
   */
  async post<T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig,
  ): Promise<T> {
    const response = await this.client.post<T>(url, data, config);
    return response.data;
  }

  /**
   * Make a custom PUT request
   */
  async put<T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig,
  ): Promise<T> {
    const response = await this.client.put<T>(url, data, config);
    return response.data;
  }

  /**
   * Make a custom DELETE request
   */
  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete<T>(url, config);
    return response.data;
  }
}

// ========================================================================
// Export singleton instance
// ========================================================================

/**
 * Default API client instance
 *
 * Usage:
 *   import { apiClient } from '@/services/apiClient';
 *   const health = await apiClient.getHealth();
 */
export const apiClient = new ZiggyAPIClient();

/**
 * Create a new API client instance with custom configuration
 *
 * Usage:
 *   import { createApiClient } from '@/services/apiClient';
 *   const customClient = createApiClient({ baseURL: 'https://api.ziggy.ai' });
 */
export function createApiClient(config?: ApiClientConfig): ZiggyAPIClient {
  return new ZiggyAPIClient(config);
}
