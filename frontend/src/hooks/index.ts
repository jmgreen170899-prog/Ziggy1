import { useEffect, useRef, useState, useCallback } from "react";
import {
  useMarketStore,
  usePortfolioStore,
  useNewsStore,
  useCryptoStore,
  useAlertsStore,
} from "@/store";
import { apiClient } from "@/services/api";
import { wsService } from "@/services/websocket";
import type {
  Quote,
  NewsItem,
  Alert,
  TradingSignal,
  CryptoPrice,
} from "@/types/api";

// Enhanced error handling and retry logic
interface UseAsyncStateOptions {
  retryAttempts?: number;
  retryDelay?: number;
  onError?: (error: Error) => void;
}

function useAsyncState<T>(
  asyncFn: () => Promise<T>,
  dependencies: React.DependencyList = [],
  options: UseAsyncStateOptions = {},
) {
  const { retryAttempts = 3, retryDelay = 1000, onError } = options;
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  const execute = useCallback(async () => {
    setLoading(true);
    setError(null);

    for (let attempt = 0; attempt <= retryAttempts; attempt++) {
      try {
        const result = await asyncFn();
        setData(result);
        setRetryCount(0);
        setLoading(false);
        return result;
      } catch (err) {
        const error =
          err instanceof Error ? err : new Error("Unknown error occurred");

        if (attempt === retryAttempts) {
          setError(error);
          setRetryCount(attempt + 1);
          onError?.(error);
          break;
        }

        // Wait before retry
        await new Promise((resolve) =>
          setTimeout(resolve, retryDelay * Math.pow(2, attempt)),
        );
      }
    }

    setLoading(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [asyncFn, retryAttempts, retryDelay, onError, ...dependencies]);

  const retry = useCallback(() => {
    execute();
  }, [execute]);

  return {
    data,
    loading,
    error,
    retryCount,
    execute,
    retry,
  };
}

// Enhanced real-time market data hook with connection management
export function useRealTimeMarket() {
  const { quotes, watchlist, updateQuote, setError, setLoading } =
    useMarketStore();
  const [connected, setConnected] = useState(false);
  const [metrics, setMetrics] = useState({ latency: 0, reconnectCount: 0 });
  const connectionRef = useRef(false);

  const handleConnectionMetrics = useCallback(() => {
    if (wsService.isConnected()) {
      const connectionMetrics = wsService.getConnectionMetrics();
      setMetrics({
        latency: connectionMetrics.latency,
        reconnectCount: connectionMetrics.reconnectCount,
      });
    }
  }, []);

  useEffect(() => {
    if (connectionRef.current) return; // Prevent duplicate connections
    connectionRef.current = true;

    setLoading(true);

    // Configure WebSocket callbacks
    wsService.updateCallbacks({
      onConnect: () => {
        console.log("WebSocket connected");
        setConnected(true);
        setError(null);
        setLoading(false);

        // Subscribe to all watchlist symbols using enhanced subscription management
        watchlist.forEach((symbol) => {
          wsService.addSubscription("quote", symbol);
        });
      },

      onDisconnect: (reason: string) => {
        console.log("WebSocket disconnected:", reason);
        setConnected(false);
        setLoading(false);
      },

      onError: (error) => {
        console.error("WebSocket error:", error);
        setError(error.message);
        setConnected(false);
        setLoading(false);
      },

      onQuoteUpdate: (quote: Quote) => {
        updateQuote(quote);
      },
    });

    // Start connection
    wsService.connect();

    // Set up metrics monitoring
    const metricsInterval = setInterval(handleConnectionMetrics, 5000);

    return () => {
      connectionRef.current = false;
      clearInterval(metricsInterval);
      wsService.disconnect();
    };
  }, [watchlist, updateQuote, setError, setLoading, handleConnectionMetrics]);

  const subscribeToSymbol = useCallback((symbol: string) => {
    if (wsService.isConnected()) {
      wsService.addSubscription("quote", symbol);
    }
  }, []);

  const unsubscribeFromSymbol = useCallback((symbol: string) => {
    if (wsService.isConnected()) {
      wsService.removeSubscription("quote", symbol);
    }
  }, []);

  const forceReconnect = useCallback(() => {
    wsService.disconnect();
    setTimeout(() => wsService.connect(), 1000);
  }, []);

  const getConnectionStatus = useCallback(
    () => ({
      connected: wsService.isConnected(),
      isMockMode: wsService.isMockMode(),
      subscriptionCount: wsService.getSubscriptionCount(),
      activeSubscriptions: wsService.getActiveSubscriptionCount(),
      metrics: wsService.getConnectionMetrics(),
    }),
    [],
  );

  return {
    quotes,
    connected,
    metrics,
    subscribeToSymbol,
    unsubscribeFromSymbol,
    forceReconnect,
    getConnectionStatus,
  };
}

// Enhanced market data hook with error handling
export function useMarketData() {
  const { setQuotes, setLoading, setError, watchlist } = useMarketStore();

  const fetchQuotes = useCallback(
    async (symbols: string[] = watchlist) => {
      try {
        setLoading(true);
        setError(null);
        const quotes = await apiClient.getMultipleQuotes(symbols);
        setQuotes(quotes);
        return quotes;
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : "Failed to fetch quotes";
        setError(errorMessage);
        throw new Error(errorMessage);
      } finally {
        setLoading(false);
      }
    },
    [watchlist, setQuotes, setLoading, setError],
  );

  const fetchSingleQuote = useCallback(
    async (symbol: string) => {
      try {
        setError(null);
        const quote = await apiClient.getQuote(symbol);
        setQuotes([quote]);
        return quote;
      } catch (error) {
        const errorMessage =
          error instanceof Error
            ? error.message
            : `Failed to fetch quote for ${symbol}`;
        setError(errorMessage);
        throw new Error(errorMessage);
      }
    },
    [setQuotes, setError],
  );

  const {
    data: quotesData,
    loading: quotesLoading,
    error: quotesError,
    retry: retryQuotes,
  } = useAsyncState(() => fetchQuotes(watchlist), [watchlist], {
    retryAttempts: 3,
    retryDelay: 2000,
    onError: (error) => {
      console.error("Failed to fetch quotes after retries:", error);
    },
  });

  return {
    fetchQuotes,
    fetchSingleQuote,
    quotesData,
    quotesLoading,
    quotesError,
    retryQuotes,
  };
}

// Enhanced portfolio hook with comprehensive error handling
// Enhanced portfolio hook with comprehensive error handling
export function usePortfolio() {
  const {
    portfolio,
    signals,
    setPortfolio,
    setSignals,
    setLoading,
    setError,
    loading,
    error,
  } = usePortfolioStore();

  const fetchPortfolio = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const portfolioData = await apiClient.getPortfolio();
      setPortfolio(portfolioData);
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to fetch portfolio";
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [setPortfolio, setLoading, setError]);

  const fetchSignals = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const signalsData = await apiClient.getTradingSignals();
      setSignals(signalsData);
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to fetch signals";
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [setSignals, setLoading, setError]);

  const retry = useCallback(async () => {
    try {
      await Promise.all([fetchPortfolio(), fetchSignals()]);
    } catch (error) {
      console.error("Retry failed:", error);
    }
  }, [fetchPortfolio, fetchSignals]);

  useEffect(() => {
    // Setup WebSocket for portfolio updates
    wsService.updateCallbacks({
      onPortfolioUpdate: (data) => {
        setPortfolio(data);
      },
      onSignalGenerated: (signal: TradingSignal) => {
        setSignals([signal, ...signals]);
      },
    });

    wsService.subscribeToPortfolio();
  }, [setPortfolio, setSignals, signals]);

  return {
    portfolio,
    signals,
    loading,
    error,
    fetchPortfolio,
    fetchSignals,
    retry,
  };
}

// Enhanced news hook with error handling
export function useNews() {
  const { news, setNews, addNews, setLoading, setError, loading, error } =
    useNewsStore();

  const fetchNews = useCallback(
    async (symbol?: string) => {
      try {
        setLoading(true);
        setError(null);
        const newsData = symbol
          ? await apiClient.getNewsForSymbol(symbol)
          : await apiClient.getNews();
        setNews(newsData);
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : "Failed to fetch news";
        setError(errorMessage);
        throw new Error(errorMessage);
      } finally {
        setLoading(false);
      }
    },
    [setNews, setLoading, setError],
  );

  const retry = useCallback(async () => {
    try {
      await fetchNews();
    } catch (error) {
      console.error("News retry failed:", error);
    }
  }, [fetchNews]);

  useEffect(() => {
    // Setup WebSocket for news updates
    wsService.updateCallbacks({
      onNewsUpdate: (newsItem: NewsItem) => {
        addNews(newsItem);
      },
    });
  }, [addNews]);

  return {
    news,
    loading,
    error,
    fetchNews,
    retry,
  };
}

// Hook for crypto data
export function useCrypto() {
  const { prices, setPrices, updatePrice, setLoading, setError } =
    useCryptoStore();

  const fetchCryptoPrices = useCallback(async () => {
    try {
      setLoading(true);
      const cryptoPrices = await apiClient.getCryptoPrices();
      setPrices(cryptoPrices);
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Failed to fetch crypto prices",
      );
    } finally {
      setLoading(false);
    }
  }, [setPrices, setLoading, setError]);

  useEffect(() => {
    // Setup WebSocket for crypto price updates
    wsService.updateCallbacks({
      onQuoteUpdate: (quote: Quote) => {
        // Convert quote to crypto price if it's a crypto symbol
        if (quote.symbol.endsWith("-USD") || quote.symbol.length <= 5) {
          const cryptoPrice: CryptoPrice = {
            symbol: quote.symbol,
            name: quote.symbol,
            price: quote.price,
            change_24h: quote.change,
            change_percent_24h: quote.change_percent,
            volume_24h: quote.volume,
            market_cap: 0, // Would need separate API call
            rank: 0, // Would need separate API call
          };
          updatePrice(cryptoPrice);
        }
      },
    });
  }, [updatePrice]);

  return {
    prices,
    fetchCryptoPrices,
  };
}

// Hook for alerts management
export function useAlerts() {
  const {
    alerts,
    setAlerts,
    addAlert,
    removeAlert,
    triggerAlert,
    setLoading,
    setError,
  } = useAlertsStore();

  const fetchAlerts = useCallback(async () => {
    try {
      setLoading(true);
      const alertsData = await apiClient.getAlerts();
      setAlerts(alertsData);
    } catch (error) {
      setError(
        error instanceof Error ? error.message : "Failed to fetch alerts",
      );
    } finally {
      setLoading(false);
    }
  }, [setAlerts, setLoading, setError]);

  const createAlert = useCallback(
    async (alertData: Omit<Alert, "id" | "created_at">) => {
      try {
        setLoading(true);
        const newAlert = await apiClient.createAlert(alertData);
        addAlert(newAlert);
        wsService.subscribeToAlert(newAlert.id);
        return newAlert;
      } catch (error) {
        setError(
          error instanceof Error ? error.message : "Failed to create alert",
        );
        throw error;
      } finally {
        setLoading(false);
      }
    },
    [addAlert, setLoading, setError],
  );

  const deleteAlert = useCallback(
    async (id: string) => {
      try {
        setLoading(true);
        await apiClient.deleteAlert(id);
        removeAlert(id);
      } catch (error) {
        setError(
          error instanceof Error ? error.message : "Failed to delete alert",
        );
        throw error;
      } finally {
        setLoading(false);
      }
    },
    [removeAlert, setLoading, setError],
  );

  useEffect(() => {
    // Setup WebSocket for alert notifications
    wsService.updateCallbacks({
      onAlertTriggered: (alert: Alert) => {
        triggerAlert(alert);
        // Show notification
        if ("Notification" in window && Notification.permission === "granted") {
          new Notification("Alert Triggered", {
            body: `${alert.symbol}: ${alert.message || alert.condition}`,
            icon: "/favicon.ico",
          });
        }
      },
    });
  }, [triggerAlert]);

  return {
    alerts,
    fetchAlerts,
    createAlert,
    deleteAlert,
  };
}

// Hook for managing WebSocket connection
export function useWebSocket() {
  const [connected, setConnected] = useState(false);
  const [reconnecting, setReconnecting] = useState(false);

  useEffect(() => {
    wsService.connect({
      onConnect: () => {
        setConnected(true);
        setReconnecting(false);
      },
      onDisconnect: () => {
        setConnected(false);
        setReconnecting(true);
      },
      onError: () => {
        setConnected(false);
      },
    });

    return () => {
      wsService.disconnect();
    };
  }, []);

  return {
    connected,
    reconnecting,
    wsService,
  };
}

// Hook for interval-based data updates
export function useInterval(callback: () => void, delay: number | null) {
  const savedCallback = useRef<() => void>(callback);

  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  useEffect(() => {
    function tick() {
      savedCallback.current?.();
    }
    if (delay !== null) {
      const id = setInterval(tick, delay);
      return () => clearInterval(id);
    }
  }, [delay]);
}

// Hook for previous value
export function usePrevious<T>(value: T): T | undefined {
  const ref = useRef<T | undefined>(undefined);
  useEffect(() => {
    ref.current = value;
  });
  return ref.current;
}
