/**
 * Polling-based live data service as fallback for WebSocket
 * Polls REST API endpoints to simulate live data updates
 */
import type {
  Quote,
  NewsItem,
  Alert,
  TradingSignal,
  Portfolio,
} from "@/types/api";
import { apiClient } from "./api";

export interface PollingLiveDataCallbacks {
  onQuoteUpdate?: (quote: Quote) => void;
  onNewsUpdate?: (news: NewsItem) => void;
  onAlertTriggered?: (alert: Alert) => void;
  onSignalGenerated?: (signal: TradingSignal) => void;
  onPortfolioUpdate?: (portfolio: Portfolio) => void;
  onConnect?: (endpoint: string) => void;
  onDisconnect?: (endpoint: string, reason: string) => void;
  onError?: (endpoint: string, error: string) => void;
}

class PollingLiveDataService {
  private callbacks: PollingLiveDataCallbacks = {};
  private subscribedSymbols: Set<string> = new Set();
  private pollingIntervals: Map<string, NodeJS.Timeout> = new Map();
  private isActive = false;

  // Polling intervals (in milliseconds)
  private readonly MARKET_POLL_INTERVAL = 5000; // 5 seconds
  private readonly NEWS_POLL_INTERVAL = 30000; // 30 seconds
  private readonly ALERTS_POLL_INTERVAL = 10000; // 10 seconds
  private readonly SIGNALS_POLL_INTERVAL = 15000; // 15 seconds
  private readonly PORTFOLIO_POLL_INTERVAL = 10000; // 10 seconds

  // Cache for last seen data to detect changes
  private lastQuotes: Map<string, Quote> = new Map();
  private lastNewsIds: Set<string> = new Set();

  /**
   * Initialize polling-based live data connections
   */
  connect(callbacks: PollingLiveDataCallbacks = {}): void {
    if (typeof window === "undefined") return; // SSR guard

    console.log(
      "🔌 PollingLiveDataService.connect() - using REST polling fallback",
    );
    this.callbacks = { ...this.callbacks, ...callbacks };
    this.isActive = true;

    // Notify connection (simulated)
    setTimeout(() => {
      this.callbacks.onConnect?.("polling");
    }, 100);

    // Start polling if we have subscribed symbols
    if (this.subscribedSymbols.size > 0) {
      this.startMarketPolling();
    }

    // Start other polling tasks
    this.startNewsPolling();
    this.startAlertsPolling();
    this.startSignalsPolling();
    this.startPortfolioPolling();
  }

  /**
   * Stop all polling activities
   */
  disconnect(): void {
    console.log("🔌 PollingLiveDataService.disconnect()");
    this.isActive = false;

    // Clear all polling intervals
    for (const [key, interval] of this.pollingIntervals) {
      clearInterval(interval);
      console.log(`🔌 Stopped polling: ${key}`);
    }
    this.pollingIntervals.clear();

    // Notify disconnection
    this.callbacks.onDisconnect?.("polling", "Service stopped");
    this.callbacks = {};
  }

  /**
   * Subscribe to symbol quotes
   */
  subscribeToSymbols(symbols: string[]): void {
    if (!symbols || symbols.length === 0) return;

    console.log("📊 Subscribing to symbols:", symbols);
    const hadSymbols = this.subscribedSymbols.size > 0;

    symbols.forEach((symbol) => this.subscribedSymbols.add(symbol));

    // Start market polling if this is the first subscription
    if (!hadSymbols && this.isActive) {
      this.startMarketPolling();
    }
  }

  /**
   * Unsubscribe from symbol quotes
   */
  unsubscribeFromSymbols(symbols: string[]): void {
    symbols.forEach((symbol) => {
      this.subscribedSymbols.delete(symbol);
      this.lastQuotes.delete(symbol);
    });

    // Stop market polling if no more subscriptions
    if (this.subscribedSymbols.size === 0) {
      const interval = this.pollingIntervals.get("market");
      if (interval) {
        clearInterval(interval);
        this.pollingIntervals.delete("market");
      }
    }
  }

  /**
   * Get connection status
   */
  getConnectionStatus(): Record<string, boolean> {
    return {
      polling: this.isActive,
      market: this.pollingIntervals.has("market"),
      news: this.pollingIntervals.has("news"),
      alerts: this.pollingIntervals.has("alerts"),
      signals: this.pollingIntervals.has("signals"),
      portfolio: this.pollingIntervals.has("portfolio"),
    };
  }

  /**
   * Start polling for market quotes
   */
  private startMarketPolling(): void {
    if (this.pollingIntervals.has("market")) return;

    console.log("📈 Starting market data polling...");

    const poll = async () => {
      if (!this.isActive || this.subscribedSymbols.size === 0) return;

      try {
        const symbols = Array.from(this.subscribedSymbols);
        const quotes = await apiClient.getMultipleQuotes(symbols);

        for (const quote of quotes) {
          // Check if quote has changed
          const lastQuote = this.lastQuotes.get(quote.symbol);
          if (
            !lastQuote ||
            lastQuote.price !== quote.price ||
            lastQuote.timestamp !== quote.timestamp
          ) {
            this.lastQuotes.set(quote.symbol, quote);
            this.callbacks.onQuoteUpdate?.(quote);
          }
        }
      } catch (error) {
        console.error("📈 Market polling error:", error);
        this.callbacks.onError?.("market", String(error));
      }
    };

    // Initial poll
    poll();

    // Set up interval
    const interval = setInterval(poll, this.MARKET_POLL_INTERVAL);
    this.pollingIntervals.set("market", interval);
  }

  /**
   * Start polling for news
   */
  private startNewsPolling(): void {
    if (this.pollingIntervals.has("news")) return;

    console.log("📰 Starting news polling...");

    const poll = async () => {
      if (!this.isActive) return;

      try {
        const news = await apiClient.getNews();

        // Only notify about new news items
        for (const item of news) {
          if (!this.lastNewsIds.has(item.id)) {
            this.lastNewsIds.add(item.id);
            this.callbacks.onNewsUpdate?.(item);
          }
        }

        // Limit cache size to prevent memory leak
        if (this.lastNewsIds.size > 1000) {
          const toDelete = Array.from(this.lastNewsIds).slice(0, 500);
          toDelete.forEach((id) => this.lastNewsIds.delete(id));
        }
      } catch (error) {
        console.error("📰 News polling error:", error);
        this.callbacks.onError?.("news", String(error));
      }
    };

    // Initial poll
    poll();

    // Set up interval
    const interval = setInterval(poll, this.NEWS_POLL_INTERVAL);
    this.pollingIntervals.set("news", interval);
  }

  /**
   * Start polling for alerts
   */
  private startAlertsPolling(): void {
    if (this.pollingIntervals.has("alerts")) return;

    console.log("🔔 Starting alerts polling...");

    const poll = async () => {
      if (!this.isActive) return;

      try {
        const alerts = await apiClient.getAlerts();

        // Notify about triggered alerts
        for (const alert of alerts) {
          if (alert.triggered_at && alert.is_active) {
            this.callbacks.onAlertTriggered?.(alert);
          }
        }
      } catch (error) {
        console.error("🔔 Alerts polling error:", error);
        this.callbacks.onError?.("alerts", String(error));
      }
    };

    // Initial poll
    poll();

    // Set up interval
    const interval = setInterval(poll, this.ALERTS_POLL_INTERVAL);
    this.pollingIntervals.set("alerts", interval);
  }

  /**
   * Start polling for trading signals
   */
  private startSignalsPolling(): void {
    if (this.pollingIntervals.has("signals")) return;

    console.log("📊 Starting signals polling...");

    const poll = async () => {
      if (!this.isActive) return;

      try {
        const signals = await apiClient.getTradingSignals();

        // Notify about new signals
        for (const signal of signals) {
          this.callbacks.onSignalGenerated?.(signal);
        }
      } catch (error) {
        console.error("📊 Signals polling error:", error);
        this.callbacks.onError?.("signals", String(error));
      }
    };

    // Initial poll
    poll();

    // Set up interval
    const interval = setInterval(poll, this.SIGNALS_POLL_INTERVAL);
    this.pollingIntervals.set("signals", interval);
  }

  /**
   * Start polling for portfolio updates
   */
  private startPortfolioPolling(): void {
    if (this.pollingIntervals.has("portfolio")) return;

    console.log("💼 Starting portfolio polling...");

    const poll = async () => {
      if (!this.isActive) return;

      try {
        const portfolio = await apiClient.getPortfolio();
        this.callbacks.onPortfolioUpdate?.(portfolio);
      } catch (error) {
        console.error("💼 Portfolio polling error:", error);
        this.callbacks.onError?.("portfolio", String(error));
      }
    };

    // Initial poll
    poll();

    // Set up interval
    const interval = setInterval(poll, this.PORTFOLIO_POLL_INTERVAL);
    this.pollingIntervals.set("portfolio", interval);
  }
}

// Export singleton instance
export const pollingLiveDataService = new PollingLiveDataService();
export default pollingLiveDataService;
