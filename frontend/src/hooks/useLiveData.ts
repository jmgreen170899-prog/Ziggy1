/**
 * React hook for ZiggyAI live data integration
 * Manages WebSocket connections and provides real-time updates
 */
import { useEffect, useRef, useState, useCallback } from "react";
import { liveDataService, type LiveDataCallbacks } from "@/services/liveData";
import type {
  Quote,
  NewsItem,
  Alert,
  TradingSignal,
  Portfolio,
  PortfolioPosition,
} from "@/types/api";

export interface LiveDataState {
  quotes: Map<string, Quote>;
  news: NewsItem[];
  alerts: Alert[];
  signals: TradingSignal[];
  portfolio: Portfolio | null;
  positions: PortfolioPosition[];
  connectionStatus: {
    market: boolean;
    news: boolean;
    alerts: boolean;
    signals: boolean;
    portfolio: boolean;
  };
  lastUpdate: {
    quotes: Date | null;
    news: Date | null;
    alerts: Date | null;
    signals: Date | null;
    portfolio: Date | null;
  };
}

export interface UseLiveDataOptions {
  symbols?: string[];
  maxNewsItems?: number;
  maxAlerts?: number;
  maxSignals?: number;
  autoConnect?: boolean;
}

export function useLiveData(options: UseLiveDataOptions = {}) {
  const {
    symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "SPY"],
    maxNewsItems = 50,
    maxAlerts = 20,
    maxSignals = 10,
    autoConnect = true,
  } = options;

  const [state, setState] = useState<LiveDataState>({
    quotes: new Map(),
    news: [],
    alerts: [],
    signals: [],
    portfolio: null,
    positions: [],
    connectionStatus: {
      market: false,
      news: false,
      alerts: false,
      signals: false,
      portfolio: false,
    },
    lastUpdate: {
      quotes: null,
      news: null,
      alerts: null,
      signals: null,
      portfolio: null,
    },
  });

  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const connectedRef = useRef(false);

  // Update quote data
  const handleQuoteUpdate = useCallback((quote: Quote) => {
    setState((prev) => ({
      ...prev,
      quotes: new Map(prev.quotes.set(quote.symbol, quote)),
      lastUpdate: {
        ...prev.lastUpdate,
        quotes: new Date(),
      },
    }));
  }, []);

  // Update news data with deduplication
  const handleNewsUpdate = useCallback(
    (newsItem: NewsItem) => {
      setState((prev) => {
        const existingIndex = prev.news.findIndex(
          (item) => item.id === newsItem.id,
        );
        let updatedNews;

        if (existingIndex >= 0) {
          // Update existing item
          updatedNews = [...prev.news];
          updatedNews[existingIndex] = newsItem;
        } else {
          // Add new item and limit array size
          updatedNews = [newsItem, ...prev.news].slice(0, maxNewsItems);
        }

        return {
          ...prev,
          news: updatedNews,
          lastUpdate: {
            ...prev.lastUpdate,
            news: new Date(),
          },
        };
      });
    },
    [maxNewsItems],
  );

  // Update alerts
  const handleAlertTriggered = useCallback(
    (alert: Alert) => {
      setState((prev) => {
        const updatedAlerts = [alert, ...prev.alerts].slice(0, maxAlerts);
        return {
          ...prev,
          alerts: updatedAlerts,
          lastUpdate: {
            ...prev.lastUpdate,
            alerts: new Date(),
          },
        };
      });
    },
    [maxAlerts],
  );

  // Update signals
  const handleSignalGenerated = useCallback(
    (signal: TradingSignal) => {
      setState((prev) => {
        const updatedSignals = [signal, ...prev.signals].slice(0, maxSignals);
        return {
          ...prev,
          signals: updatedSignals,
          lastUpdate: {
            ...prev.lastUpdate,
            signals: new Date(),
          },
        };
      });
    },
    [maxSignals],
  );

  // Update portfolio
  const handlePortfolioUpdate = useCallback((portfolio: Portfolio) => {
    setState((prev) => ({
      ...prev,
      portfolio,
      lastUpdate: {
        ...prev.lastUpdate,
        portfolio: new Date(),
      },
    }));
  }, []);

  // Update positions
  const handlePositionsUpdate = useCallback(
    (positions: PortfolioPosition[]) => {
      setState((prev) => ({
        ...prev,
        positions,
        lastUpdate: {
          ...prev.lastUpdate,
          portfolio: new Date(),
        },
      }));
    },
    [],
  );

  // Handle connection status updates
  const handleConnect = useCallback((endpoint: string) => {
    console.log(`🔌 ${endpoint} connected`);
    setState((prev) => ({
      ...prev,
      connectionStatus: {
        ...prev.connectionStatus,
        [endpoint]: true,
      },
    }));

    // Check if all endpoints are connected
    const status = liveDataService.getConnectionStatus();
    const allConnected = Object.values(status).every(Boolean);
    setIsConnected(allConnected);

    if (allConnected && !connectedRef.current) {
      connectedRef.current = true;
      setError(null);
      console.log("🚀 All ZiggyAI live data streams connected!");
    }
  }, []);

  const handleDisconnect = useCallback((endpoint: string, reason: string) => {
    console.log(`🔌 ${endpoint} disconnected: ${reason}`);
    setState((prev) => ({
      ...prev,
      connectionStatus: {
        ...prev.connectionStatus,
        [endpoint]: false,
      },
    }));

    setIsConnected(false);
    connectedRef.current = false;
  }, []);

  const handleError = useCallback((endpoint: string, error: string) => {
    console.error(`❌ ${endpoint} error: ${error}`);
    setError(`${endpoint}: ${error}`);
  }, []);

  // Subscribe to symbols
  const subscribeToSymbols = useCallback((newSymbols: string[]) => {
    liveDataService.subscribeToSymbols(newSymbols);
  }, []);

  // Unsubscribe from symbols
  const unsubscribeFromSymbols = useCallback((symbolsToRemove: string[]) => {
    liveDataService.unsubscribeFromSymbols(symbolsToRemove);
  }, []);

  // Test alert functionality
  const testAlert = useCallback(() => {
    liveDataService.testAlert();
  }, []);

  // Connect to live data service
  const connect = useCallback(() => {
    if (connectedRef.current) return;

    console.log("🔌 Connecting to ZiggyAI live data...");

    const callbacks: LiveDataCallbacks = {
      onQuoteUpdate: handleQuoteUpdate,
      onNewsUpdate: handleNewsUpdate,
      onAlertTriggered: handleAlertTriggered,
      onSignalGenerated: handleSignalGenerated,
      onPortfolioUpdate: handlePortfolioUpdate,
      onPositionsUpdate: handlePositionsUpdate,
      onConnect: handleConnect,
      onDisconnect: handleDisconnect,
      onError: handleError,
    };

    liveDataService.connect(callbacks);
  }, [
    handleQuoteUpdate,
    handleNewsUpdate,
    handleAlertTriggered,
    handleSignalGenerated,
    handlePortfolioUpdate,
    handlePositionsUpdate,
    handleConnect,
    handleDisconnect,
    handleError,
  ]);

  // Disconnect from live data service
  const disconnect = useCallback(() => {
    console.log("🔌 Disconnecting from ZiggyAI live data...");
    liveDataService.disconnect();
    setIsConnected(false);
    connectedRef.current = false;
    setError(null);
  }, []);

  // Auto-connect on mount if enabled
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      if (autoConnect) {
        disconnect();
      }
    };
  }, [autoConnect, connect, disconnect]);

  // Subscribe to initial symbols
  useEffect(() => {
    if (isConnected && symbols.length > 0) {
      subscribeToSymbols(symbols);
    }
  }, [isConnected, symbols, subscribeToSymbols]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      liveDataService.disconnect();
    };
  }, []);

  return {
    // State
    ...state,
    isConnected,
    error,

    // Actions
    connect,
    disconnect,
    subscribeToSymbols,
    unsubscribeFromSymbols,
    testAlert,
    forcePortfolioUpdate: () => liveDataService.forcePortfolioUpdate(),

    // Utilities
    getQuote: (symbol: string) => state.quotes.get(symbol),
    getConnectionStatus: () => liveDataService.getConnectionStatus(),
    isSymbolSubscribed: (symbol: string) => state.quotes.has(symbol),

    // Statistics
    stats: {
      totalQuotes: state.quotes.size,
      totalNews: state.news.length,
      totalAlerts: state.alerts.length,
      totalSignals: state.signals.length,
      totalPositions: state.positions.length,
      portfolioValue: state.portfolio?.total_value || 0,
      uptime: connectedRef.current ? new Date() : null,
    },
  };
}

export default useLiveData;
