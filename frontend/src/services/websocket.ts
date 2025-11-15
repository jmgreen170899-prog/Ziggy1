/* eslint-disable @typescript-eslint/no-unused-vars */
import { liveDataService } from "@/services/liveData";
import type {
  Portfolio,
  Quote,
  NewsItem,
  Alert,
  TradingSignal,
} from "@/types/api";

// Compatibility types (kept for existing imports)
export type WebSocketEventType =
  | "quote_update"
  | "news_update"
  | "alert_triggered"
  | "signal_generated"
  | "portfolio_update"
  | "market_status"
  | "heartbeat"
  | "subscription_ack"
  | "subscription_error";

export interface MarketStatusUpdate {
  status: "open" | "closed" | "pre_market" | "after_hours";
  timestamp: string;
  next_state_change?: string;
}

export interface WebSocketError {
  message: string;
  code?: string;
  timestamp: number;
  reconnectable: boolean;
}

export interface SubscriptionAck {
  type: string;
  symbol?: string;
  status: "subscribed" | "unsubscribed";
  timestamp: number;
}

export interface SubscriptionError {
  type: string;
  symbol?: string;
  error: string;
  timestamp: number;
}

export interface WebSocketCallbacks {
  onQuoteUpdate?: (quote: Quote) => void;
  onNewsUpdate?: (news: NewsItem) => void;
  onAlertTriggered?: (alert: Alert) => void;
  onSignalGenerated?: (signal: TradingSignal) => void;
  onPortfolioUpdate?: (portfolio: Portfolio) => void;
  onMarketStatus?: (status: MarketStatusUpdate) => void;
  onConnect?: () => void;
  onDisconnect?: (reason: string) => void;
  onError?: (error: WebSocketError) => void;
  onHeartbeat?: (timestamp: number) => void;
  onSubscriptionAck?: (subscription: SubscriptionAck) => void;
  onSubscriptionError?: (error: SubscriptionError) => void;
}

export interface WebSocketConfig {
  enabled?: boolean;
}

export type SubscriptionType =
  | "quote"
  | "news"
  | "alert"
  | "portfolio"
  | "market_status";

export interface SubscriptionData {
  type: SubscriptionType;
  key: string;
  params: Record<string, unknown>;
  active: boolean;
  createdAt: number;
}

export interface ConnectionMetrics {
  latency: number;
  lastPong: number;
  reconnectCount: number;
  uptime: number;
}

// Thin compatibility shim that delegates to the native LiveData service
class WebSocketServiceShim {
  private callbacks: WebSocketCallbacks = {};
  private isEnabled = true;
  private subscriptions = new Map<string, SubscriptionData>();
  private connectionStartTime = 0;
  private connectionMetrics: ConnectionMetrics = {
    latency: 0,
    lastPong: 0,
    reconnectCount: 0,
    uptime: 0,
  };

  constructor(_config: WebSocketConfig = {}) {}

  connect = (callbacks?: WebSocketCallbacks): void => {
    // Merge provided callbacks
    if (callbacks) {
      this.callbacks = { ...this.callbacks, ...callbacks };
    }

    this.connectionStartTime = Date.now();

    // Map existing callbacks into LiveData callbacks
    liveDataService.connect({
      onQuoteUpdate: (q) => this.callbacks.onQuoteUpdate?.(q),
      onNewsUpdate: (n) => this.callbacks.onNewsUpdate?.(n),
      onAlertTriggered: (a) => this.callbacks.onAlertTriggered?.(a),
      onSignalGenerated: (s) => this.callbacks.onSignalGenerated?.(s),
      onPortfolioUpdate: (p) => this.callbacks.onPortfolioUpdate?.(p),
      onConnect: () => {
        this.callbacks.onConnect?.();
      },
      onDisconnect: (_endpoint, reason) => {
        this.callbacks.onDisconnect?.(reason);
      },
      onError: (_endpoint, error) => {
        this.callbacks.onError?.({
          message: error,
          timestamp: Date.now(),
          reconnectable: true,
        });
      },
    });
  };

  // Compatibility helpers
  updateCallbacks(callbacks: Partial<WebSocketCallbacks>): void {
    this.callbacks = { ...this.callbacks, ...callbacks };
  }

  // Symbol subscriptions map to LiveData subscribe/unsubscribe
  addSubscription(
    type: SubscriptionType,
    key: string,
    params?: Record<string, unknown>,
  ): void {
    const subscriptionKey = `${type}:${key}`;
    if (this.subscriptions.has(subscriptionKey)) return;
    const sub: SubscriptionData = {
      type,
      key,
      params: params || {},
      active: true,
      createdAt: Date.now(),
    };
    this.subscriptions.set(subscriptionKey, sub);

    if (type === "quote") {
      liveDataService.subscribeToSymbols([key]);
    }
  }

  removeSubscription(type: SubscriptionType, key: string): void {
    const subscriptionKey = `${type}:${key}`;
    if (this.subscriptions.delete(subscriptionKey)) {
      if (type === "quote") {
        liveDataService.unsubscribeFromSymbols([key]);
      }
    }
  }

  resubscribeAll(): void {
    const symbols = Array.from(this.subscriptions.values())
      .filter((s) => s.type === "quote" && s.active)
      .map((s) => s.key);
    if (symbols.length) liveDataService.subscribeToSymbols(symbols);
  }

  getActiveSubscriptions(): Map<string, SubscriptionData> {
    return new Map(this.subscriptions);
  }

  clearSubscriptions(): void {
    const symbols = Array.from(this.subscriptions.values())
      .filter((s) => s.type === "quote")
      .map((s) => s.key);
    if (symbols.length) liveDataService.unsubscribeFromSymbols(symbols);
    this.subscriptions.clear();
  }

  subscribeToSymbol(symbol: string): void {
    this.addSubscription("quote", symbol);
  }

  unsubscribeFromSymbol(symbol: string): void {
    this.removeSubscription("quote", symbol);
  }

  // Not needed with LiveData, kept as no-ops for compatibility
  subscribeToAlert(_alertId: string): void {}
  subscribeToPortfolio(): void {}

  send(event: string, data: Record<string, unknown>): void {
    // Optional: map to chart commands if needed
    if (event === "chart_command") {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (liveDataService as any).sendChartCommand?.(data);
    }
  }

  // Status and metrics
  isConnected(): boolean {
    const status = liveDataService.getConnectionStatus();
    return Object.values(status).some(Boolean);
  }

  isMockMode(): boolean {
    return !this.isEnabled;
  }

  getConnectionMetrics(): ConnectionMetrics {
    const uptime = this.connectionStartTime
      ? Date.now() - this.connectionStartTime
      : 0;
    return { ...this.connectionMetrics, uptime };
  }

  getSubscriptionCount(): number {
    return this.subscriptions.size;
  }

  getActiveSubscriptionCount(): number {
    return this.subscriptions.size;
  }

  setReconnectDelay(_delay: number): void {}
  setMaxReconnectAttempts(_attempts: number): void {}
  enableMockMode(): void {
    this.isEnabled = false;
  }
  disableMockMode(): void {
    this.isEnabled = true;
  }

  disconnect(): void {
    this.clearSubscriptions();
    liveDataService.disconnect();
    this.callbacks = {};
  }
}

export const wsService = new WebSocketServiceShim();
export default wsService;
