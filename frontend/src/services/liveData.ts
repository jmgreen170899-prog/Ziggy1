/**
 * Native WebSocket service for ZiggyAI live data integration
 * Connects directly to backend WebSocket endpoints
 */
import type {
  Quote,
  NewsItem,
  Alert,
  TradingSignal,
  Portfolio,
  PortfolioPosition,
} from "@/types/api";
import WSClient from "./wsClient";

export interface LiveDataCallbacks {
  onQuoteUpdate?: (quote: Quote) => void;
  onNewsUpdate?: (news: NewsItem) => void;
  onAlertTriggered?: (alert: Alert) => void;
  onSignalGenerated?: (signal: TradingSignal) => void;
  onPortfolioUpdate?: (portfolio: Portfolio) => void;
  onPositionsUpdate?: (positions: PortfolioPosition[]) => void;
  onConnect?: (endpoint: string) => void;
  onDisconnect?: (endpoint: string, reason: string) => void;
  onError?: (endpoint: string, error: string) => void;
}

export interface WebSocketMessage {
  type: string;
  data?: Record<string, unknown>;
  symbol?: string;
  timestamp: number;
}

class LiveDataService {
  private marketClient: WSClient | null = null;
  private newsClient: WSClient | null = null;
  private alertsClient: WSClient | null = null;
  private signalsClient: WSClient | null = null;
  private portfolioClient: WSClient | null = null;
  private chartsClient: WSClient | null = null;
  private sentimentClient: WSClient | null = null;

  private callbacks: LiveDataCallbacks = {};
  private baseUrl: string;
  private maxReconnectAttempts: number;

  constructor() {
    // Prefer explicit env; otherwise derive from window location (respect https -> wss),
    // and finally fall back to localhost for local dev.
    const envUrl = (process.env.NEXT_PUBLIC_WS_URL || "").trim();
    if (envUrl) {
      this.baseUrl = envUrl.replace(/\/$/, "");
    } else if (typeof window !== "undefined" && window.location) {
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const host = window.location.host; // includes hostname:port
      this.baseUrl = `${protocol}//${host}`;
    } else {
      this.baseUrl = "ws://localhost:8000";
    }

    // Configure reconnect policy from env (build-time). 0 attempts means infinite retries.
    const envMax = Number(
      (process.env.NEXT_PUBLIC_WS_MAX_RECONNECT_ATTEMPTS || "0").trim(),
    );
    this.maxReconnectAttempts =
      Number.isFinite(envMax) && envMax >= 0 ? envMax : 0;
    // Max reconnect delay handled inside WSClient; see wsClient.ts
  }

  /**
   * Safely send a message on a specific WebSocket instance.
   * Handles CONNECTING state by waiting for the 'open' event once,
   * and avoids races when class fields are reassigned during reconnects.
   */
  private sendWhenOpen(
    socket: WebSocket | null,
    data: Record<string, unknown>,
    endpoint: string,
  ): void {
    try {
      if (!socket) {
        console.warn(
          `🔕 ${endpoint}: no socket instance available to send message`,
        );
        return;
      }

      if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify(data));
        return;
      }

      if (socket.readyState === WebSocket.CONNECTING) {
        // Wait until this exact socket opens, then send once.
        socket.addEventListener(
          "open",
          () => {
            try {
              socket.send(JSON.stringify(data));
            } catch (err) {
              console.error(
                `❌ Failed to send on ${endpoint} after open:`,
                err,
              );
            }
          },
          { once: true },
        );
        return;
      }

      console.warn(
        `🔕 ${endpoint}: socket not open (state ${socket.readyState}), dropping message`,
      );
    } catch (err) {
      console.error(`❌ Error in sendWhenOpen for ${endpoint}:`, err);
    }
  }

  /**
   * Initialize all WebSocket connections
   */
  connect(callbacks: LiveDataCallbacks = {}): void {
    console.log(
      "🔌 LiveDataService.connect() called with callbacks:",
      Object.keys(callbacks),
    );
    this.callbacks = { ...this.callbacks, ...callbacks };

    console.log("🔌 Connecting to ZiggyAI live data services...");
    console.log("🔌 Base URL:", this.baseUrl);

    // Connect to all live data endpoints
    this.connectMarketData();
    this.connectNewsStream();
    this.connectAlerts();
    this.connectSignals();
    this.connectPortfolio();
    this.connectCharts();
    // Note: /ws/sentiment endpoint not yet implemented in backend
    // this.connectSentiment();
  }

  /**
   * Connect to market data stream
   */
  private connectMarketData(): void {
    console.log("📈 connectMarketData() called");
    console.log("📈 Connecting to:", `${this.baseUrl}/ws/market`);
    try {
      this.marketClient = new WSClient("/ws/market", {
        baseUrl: this.baseUrl,
        maxReconnectAttempts: this.maxReconnectAttempts,
      });
      this.marketClient.onOpen(() => {
        console.log("📈 Market data stream connected");
        console.log("📈 Base URL:", this.baseUrl);
        this.callbacks.onConnect?.("market");
        // Subscribe to default watchlist (sendWhenOpen queue ensures delivery)
        // Subscribe to default watchlist
        console.log("📈 Subscribing to default symbols...");
        this.subscribeToSymbols([
          "AAPL",
          "MSFT",
          "GOOGL",
          "TSLA",
          "NVDA",
          "SPY",
        ]);
      });

      this.marketClient.onMessage((event) => {
        console.log("📈 Raw message received:", event.data);
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          console.log("📈 Parsed message:", message);

          if (
            message.type === "market_data" ||
            message.type === "quote_update"
          ) {
            const data = message.data as Record<string, unknown>;
            console.log("📈 Processing market data:", data);
            const quote: Quote = {
              symbol: (message.symbol || data?.symbol || "") as string,
              price: (data?.price || 0) as number,
              change: (data?.change || 0) as number,
              change_percent: (data?.change_percent || 0) as number,
              volume: (data?.volume || 0) as number,
              timestamp: new Date(message.timestamp * 1000).toISOString(),
              high: (data?.day_high || data?.high || 0) as number,
              low: (data?.day_low || data?.low || 0) as number,
              open: (data?.open_price || data?.open || 0) as number,
              close: (data?.close || 0) as number,
            };

            console.log("📈 Created quote object:", quote);
            this.callbacks.onQuoteUpdate?.(quote);
            console.log("📈 Called onQuoteUpdate callback");
          } else {
            console.log("📈 Non-market message type:", message.type);
          }
        } catch (error) {
          console.error("📈 Error parsing market data:", error);
          console.error("📈 Raw data that failed:", event.data);
        }
      });

      this.marketClient.onClose(() => {
        console.log("📈 Market data stream disconnected");
        this.callbacks.onDisconnect?.("market", "Connection closed");
      });

      this.marketClient.onError((error) => {
        console.error("📈 Market data stream error:", error);
        this.callbacks.onError?.("market", "Connection error");
      });

      this.marketClient.connect();
    } catch (error) {
      console.error("Failed to connect to market data stream:", error);
    }
  }

  /**
   * Connect to news stream
   */
  private connectNewsStream(): void {
    console.log("📰 connectNewsStream() called");
    console.log("📰 Connecting to:", `${this.baseUrl}/ws/news`);
    try {
      this.newsClient = new WSClient("/ws/news", {
        baseUrl: this.baseUrl,
        maxReconnectAttempts: this.maxReconnectAttempts,
      });
      this.newsClient.onOpen(() => {
        console.log("📰 News stream connected");
        this.callbacks.onConnect?.("news");
      });
      this.newsClient.onMessage((event) => {
        console.log("📰 Raw news message received:", event.data);
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          console.log("📰 Parsed news message:", message);

          if (message.type === "news_update") {
            const data = message.data as Record<string, unknown>;
            console.log("📰 Processing news data:", data);
            const newsItem: NewsItem = {
              id: (data?.id || "") as string,
              title: (data?.title || "") as string,
              summary: (data?.summary || "") as string,
              content: (data?.content || "") as string,
              url: (data?.url || "") as string,
              source: (data?.source || "") as string,
              published_date: (data?.published ||
                new Date().toISOString()) as string,
              symbols: (data?.tickers || []) as string[],
              sentiment: "neutral" as const, // Default sentiment
              sentiment_score: 0.5,
            };

            console.log("📰 Created news item:", newsItem);
            this.callbacks.onNewsUpdate?.(newsItem);
            console.log("📰 Called onNewsUpdate callback");
          } else {
            console.log("📰 Non-news message type:", message.type);
          }
        } catch (error) {
          console.error("📰 Error parsing news data:", error);
          console.error("📰 Raw news data that failed:", event.data);
        }
      });
      this.newsClient.onClose(() => {
        console.log("📰 News stream disconnected");
        this.callbacks.onDisconnect?.("news", "Connection closed");
      });
      this.newsClient.onError((error) => {
        console.error("📰 News stream error:", error);
        this.callbacks.onError?.("news", "Connection error");
      });
      this.newsClient.connect();
    } catch (error) {
      console.error("Failed to connect to news stream:", error);
    }
  }

  /**
   * Connect to alerts stream
   */
  private connectAlerts(): void {
    try {
      this.alertsClient = new WSClient("/ws/alerts", {
        baseUrl: this.baseUrl,
        maxReconnectAttempts: this.maxReconnectAttempts,
      });
      this.alertsClient.onOpen(() => {
        console.log("🚨 Alerts stream connected");
        this.callbacks.onConnect?.("alerts");
      });
      this.alertsClient.onMessage((event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);

          if (message.type === "alert_triggered") {
            const data = message.data as Record<string, unknown>;
            const alertData = data?.alert as Record<string, unknown>;
            const alert: Alert = {
              id: (alertData?.id || "") as string,
              type: (alertData?.type || "price") as
                | "price"
                | "volume"
                | "news"
                | "technical",
              symbol: (alertData?.symbol || "") as string,
              condition: (alertData?.condition || "") as string,
              target_value: (alertData?.target_value ||
                alertData?.value ||
                0) as number,
              current_value: (alertData?.current_value || 0) as number,
              message: (alertData?.message || "") as string,
              is_active: true,
              created_at: new Date().toISOString(),
              triggered_at: new Date(message.timestamp * 1000).toISOString(),
            };

            this.callbacks.onAlertTriggered?.(alert);
          }
        } catch (error) {
          console.error("Error parsing alert data:", error);
        }
      });
      this.alertsClient.onClose(() => {
        console.log("🚨 Alerts stream disconnected");
        this.callbacks.onDisconnect?.("alerts", "Connection closed");
      });
      this.alertsClient.onError((error) => {
        console.error("🚨 Alerts stream error:", error);
        this.callbacks.onError?.("alerts", "Connection error");
      });
      this.alertsClient.connect();
    } catch (error) {
      console.error("Failed to connect to alerts stream:", error);
    }
  }

  /**
   * Connect to trading signals stream
   */
  private connectSignals(): void {
    try {
      this.signalsClient = new WSClient("/ws/signals", {
        baseUrl: this.baseUrl,
        maxReconnectAttempts: this.maxReconnectAttempts,
      });
      this.signalsClient.onOpen(() => {
        console.log("📈 Trading signals stream connected");
        this.callbacks.onConnect?.("signals");
      });
      this.signalsClient.onMessage((event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);

          if (message.type === "signal_generated") {
            const data = message.data as Record<string, unknown>;
            const signal: TradingSignal = {
              symbol: (data?.symbol || "") as string,
              signal_type: (data?.action || data?.signal_type || "HOLD") as
                | "BUY"
                | "SELL"
                | "HOLD",
              confidence: (data?.confidence || 0.5) as number,
              price_target: (data?.price || data?.price_target) as number,
              reasoning: (data?.reasoning || "") as string,
              timestamp: new Date(message.timestamp * 1000).toISOString(),
              strength: (data?.strength || data?.confidence || 0.5) as number,
            };

            this.callbacks.onSignalGenerated?.(signal);
          }
        } catch (error) {
          console.error("Error parsing signal data:", error);
        }
      });
      this.signalsClient.onClose(() => {
        console.log("📈 Trading signals stream disconnected");
        this.callbacks.onDisconnect?.("signals", "Connection closed");
      });
      this.signalsClient.onError((error) => {
        console.error("📈 Trading signals stream error:", error);
        this.callbacks.onError?.("signals", "Connection error");
      });
      this.signalsClient.connect();
    } catch (error) {
      console.error("Failed to connect to trading signals stream:", error);
    }
  }

  /**
   * Connect to portfolio stream
   */
  private connectPortfolio(): void {
    try {
      this.portfolioClient = new WSClient("/ws/portfolio", {
        baseUrl: this.baseUrl,
        maxReconnectAttempts: this.maxReconnectAttempts,
      });
      this.portfolioClient.onOpen(() => {
        console.log("💰 Portfolio stream connected");
        this.callbacks.onConnect?.("portfolio");

        // Request initial portfolio snapshot
        this.portfolioClient?.send({ action: "force_update" });
      });
      this.portfolioClient.onMessage((event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);

          if (
            message.type === "portfolio_update" ||
            message.type === "portfolio_snapshot"
          ) {
            const data = message.data as Record<string, unknown>;
            const portfolioData = data?.portfolio as Record<string, unknown>;
            const positionsData = data?.positions as Array<
              Record<string, unknown>
            >;

            if (portfolioData) {
              const portfolio: Portfolio = {
                total_value: (portfolioData.total_value || 0) as number,
                cash_balance: (portfolioData.cash_balance || 0) as number,
                daily_pnl: (portfolioData.daily_pnl || 0) as number,
                daily_pnl_percent: (portfolioData.daily_pnl_percent ||
                  0) as number,
                positions: [],
              };

              this.callbacks.onPortfolioUpdate?.(portfolio);
            }

            if (positionsData && Array.isArray(positionsData)) {
              const positions: PortfolioPosition[] = positionsData.map(
                (pos) => ({
                  symbol: (pos.symbol || "") as string,
                  quantity: (pos.quantity || 0) as number,
                  avg_price: (pos.avg_price || 0) as number,
                  current_price: (pos.current_price || 0) as number,
                  market_value: (pos.market_value || 0) as number,
                  pnl: (pos.unrealized_pnl || 0) as number,
                  pnl_percent: (pos.unrealized_pnl_percent || 0) as number,
                }),
              );

              this.callbacks.onPositionsUpdate?.(positions);
            }
          }
        } catch (error) {
          console.error("Error parsing portfolio data:", error);
        }
      });
      this.portfolioClient.onClose(() => {
        console.log("💰 Portfolio stream disconnected");
        this.callbacks.onDisconnect?.("portfolio", "Connection closed");
      });
      this.portfolioClient.onError((error) => {
        console.error("💰 Portfolio stream error:", error);
        this.callbacks.onError?.("portfolio", "Connection error");
      });
      this.portfolioClient.connect();
    } catch (error) {
      console.error("Failed to connect to portfolio stream:", error);
    }
  }

  /**
   * Connect to charts stream
   */
  private connectCharts(): void {
    try {
      this.chartsClient = new WSClient("/ws/charts", {
        baseUrl: this.baseUrl,
        maxReconnectAttempts: this.maxReconnectAttempts,
      });
      this.chartsClient.onOpen(() => {
        console.log("📊 Charts stream connected");
        this.callbacks.onConnect?.("charts");
      });
      this.chartsClient.onMessage((event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          // Chart messages are handled by the chart component directly
          console.log("📊 Chart data received:", message.type);
        } catch (error) {
          console.error("Error parsing chart data:", error);
        }
      });
      this.chartsClient.onClose(() => {
        console.log("📊 Charts stream disconnected");
        this.callbacks.onDisconnect?.("charts", "Connection closed");
      });
      this.chartsClient.onError((error) => {
        console.error("📊 Charts stream error:", error);
        this.callbacks.onError?.("charts", "Connection error");
      });
      this.chartsClient.connect();
    } catch (error) {
      console.error("Failed to connect to charts stream:", error);
    }
  }

  /**
   * Connect to sentiment stream
   */
  private connectSentiment(): void {
    try {
      this.sentimentClient = new WSClient("/ws/sentiment", {
        baseUrl: this.baseUrl,
        maxReconnectAttempts: this.maxReconnectAttempts,
      });
      this.sentimentClient.onOpen(() => {
        console.log("💭 Sentiment stream connected");
        this.callbacks.onConnect?.("sentiment");

        // Subscribe to sentiment for tracked symbols
        this.sentimentClient?.send({
          action: "subscribe",
          symbols: ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "SPY"],
        });
      });
      this.sentimentClient.onMessage((event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);

          if (message.type === "sentiment_update") {
            console.log("💭 Sentiment data received:", message.data);
            // Sentiment updates are handled by sentiment components
          } else if (message.type === "subscription_confirmed") {
            console.log("💭 Sentiment subscription confirmed");
          }
        } catch (error) {
          console.error("Error parsing sentiment data:", error);
        }
      });
      this.sentimentClient.onClose(() => {
        console.log("💭 Sentiment stream disconnected");
        this.callbacks.onDisconnect?.("sentiment", "Connection closed");
      });
      this.sentimentClient.onError((error) => {
        console.error("💭 Sentiment stream error:", error);
        this.callbacks.onError?.("sentiment", "Connection error");
      });
      this.sentimentClient.connect();
    } catch (error) {
      console.error("Failed to connect to sentiment stream:", error);
    }
  }

  /**
   * Subscribe to symbols for market data
   */
  subscribeToSymbols(symbols: string[]): void {
    if (this.marketClient) {
      this.marketClient.send({ action: "subscribe", symbols });
      console.log("📈 Subscribed to symbols:", symbols);
    }
  }

  /**
   * Unsubscribe from specific symbols
   */
  unsubscribeFromSymbols(symbols: string[]): void {
    if (this.marketClient) {
      this.marketClient.send({ action: "unsubscribe", symbols });
      console.log("📈 Unsubscribed from symbols:", symbols);
    }
  }

  /**
   * Test alert system
   */
  testAlert(): void {
    if (this.alertsClient) {
      this.alertsClient.send({ action: "test_alert" });
      console.log("🚨 Alert test triggered");
    }
  }

  /**
   * Schedule reconnection with exponential backoff
   */
  // Reconnect behavior is centralized inside WSClient

  /**
   * Disconnect all WebSocket connections
   */
  disconnect(): void {
    console.log("🔌 Disconnecting from ZiggyAI live data services...");

    [
      this.marketClient,
      this.newsClient,
      this.alertsClient,
      this.signalsClient,
      this.portfolioClient,
      this.chartsClient,
      this.sentimentClient,
    ].forEach((c) => c?.disconnect());

    this.marketClient = null;
    this.newsClient = null;
    this.alertsClient = null;
    this.signalsClient = null;
    this.portfolioClient = null;
    this.chartsClient = null;
    this.sentimentClient = null;
  }

  /**
   * Get connection status
   */
  getConnectionStatus() {
    return {
      market: this.marketClient?.state === "OPEN",
      news: this.newsClient?.state === "OPEN",
      alerts: this.alertsClient?.state === "OPEN",
      signals: this.signalsClient?.state === "OPEN",
      portfolio: this.portfolioClient?.state === "OPEN",
      charts: this.chartsClient?.state === "OPEN",
      sentiment: this.sentimentClient?.state === "OPEN",
    };
  }

  /**
   * Force portfolio update
   */
  forcePortfolioUpdate(): void {
    if (this.portfolioClient) {
      this.portfolioClient.send({ action: "force_update" });
      console.log("💰 Portfolio update forced");
    }
  }

  /**
   * Send chart command
   */
  sendChartCommand(message: Record<string, unknown>): void {
    if (this.chartsClient) {
      this.chartsClient.send(message);
      const action = (message as Record<string, unknown>)?.action as
        | string
        | undefined;
      console.log("📊 Chart command sent via client:", action ?? "unknown");
    }
  }

  /**
   * Get chart socket for direct message handling
   */
  getChartSocket(): WebSocket | null {
    // Legacy compatibility: direct WebSocket no longer exposed; use sendChartCommand instead.
    return null;
  }
}

// Export singleton instance
export const liveDataService = new LiveDataService();
export default liveDataService;
