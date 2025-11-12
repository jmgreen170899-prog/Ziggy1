import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import type { Quote, Portfolio, NewsItem, Alert, CryptoPrice, TradingSignal } from '@/types/api';

// Export chat store
export { useChatStore } from './chatStore';

// Market Data Store
interface MarketState {
  quotes: Record<string, Quote>;
  watchlist: string[];
  loading: boolean;
  error: string | null;
  
  setQuotes: (quotes: Quote[]) => void;
  updateQuote: (quote: Quote) => void;
  addToWatchlist: (symbol: string) => void;
  removeFromWatchlist: (symbol: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useMarketStore = create<MarketState>()(
  devtools(
    persist(
      (set) => ({
        quotes: {},
        watchlist: ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA'],
        loading: false,
        error: null,

        setQuotes: (quotes) => set((state) => ({
          quotes: quotes.reduce((acc, quote) => ({ ...acc, [quote.symbol]: quote }), state.quotes)
        })),

        updateQuote: (quote) => set((state) => ({
          quotes: { ...state.quotes, [quote.symbol]: quote }
        })),

        addToWatchlist: (symbol) => set((state) => ({
          watchlist: state.watchlist.includes(symbol) 
            ? state.watchlist 
            : [...state.watchlist, symbol]
        })),

        removeFromWatchlist: (symbol) => set((state) => ({
          watchlist: state.watchlist.filter(s => s !== symbol)
        })),

        setLoading: (loading) => set({ loading }),
        setError: (error) => set({ error }),
      }),
      {
        name: 'market-store',
        partialize: (state) => ({ watchlist: state.watchlist }),
      }
    ),
    { name: 'MarketStore' }
  )
);

// Portfolio Store
interface PortfolioState {
  portfolio: Portfolio | null;
  signals: TradingSignal[];
  loading: boolean;
  error: string | null;

  setPortfolio: (portfolio: Portfolio) => void;
  setSignals: (signals: TradingSignal[]) => void;
  addSignal: (signal: TradingSignal) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const usePortfolioStore = create<PortfolioState>()(
  devtools(
    (set) => ({
      portfolio: null,
      signals: [],
      loading: false,
      error: null,

      setPortfolio: (portfolio) => set({ portfolio }),
      setSignals: (signals) => set({ signals }),
      addSignal: (signal) => set((state) => ({ 
        signals: [signal, ...state.signals] 
      })),
      setLoading: (loading) => set({ loading }),
      setError: (error) => set({ error }),
    }),
    { name: 'PortfolioStore' }
  )
);

// News Store
interface NewsState {
  news: NewsItem[];
  loading: boolean;
  error: string | null;
  filter: {
    symbols: string[];
    sentiment: string[];
    sources: string[];
  };

  setNews: (news: NewsItem[]) => void;
  addNews: (newsItem: NewsItem) => void;
  setFilter: (filter: Partial<NewsState['filter']>) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  getFilteredNews: () => NewsItem[];
}

export const useNewsStore = create<NewsState>()(
  devtools(
    (set, get) => ({
      news: [],
      loading: false,
      error: null,
      filter: {
        symbols: [],
        sentiment: [],
        sources: [],
      },

      setNews: (news) => set({ news }),
      addNews: (newsItem) => set((state) => ({ 
        news: [newsItem, ...state.news] 
      })),

      setFilter: (filter) => set((state) => ({
        filter: { ...state.filter, ...filter }
      })),

      setLoading: (loading) => set({ loading }),
      setError: (error) => set({ error }),

      getFilteredNews: () => {
        const { news, filter } = get();
        return news.filter(item => {
          const symbolMatch = filter.symbols.length === 0 || 
            filter.symbols.some(symbol => item.symbols?.includes(symbol));
          
          const sentimentMatch = filter.sentiment.length === 0 || 
            (item.sentiment && filter.sentiment.includes(item.sentiment));
          
          const sourceMatch = filter.sources.length === 0 || 
            filter.sources.includes(item.source);

          return symbolMatch && sentimentMatch && sourceMatch;
        });
      },
    }),
    { name: 'NewsStore' }
  )
);

// Crypto Store
interface CryptoState {
  prices: CryptoPrice[];
  favorites: string[];
  loading: boolean;
  error: string | null;

  setPrices: (prices: CryptoPrice[]) => void;
  updatePrice: (price: CryptoPrice) => void;
  addToFavorites: (symbol: string) => void;
  removeFromFavorites: (symbol: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useCryptoStore = create<CryptoState>()(
  devtools(
    persist(
      (set) => ({
        prices: [],
        favorites: ['BTC', 'ETH', 'BNB', 'ADA', 'SOL'],
        loading: false,
        error: null,

        setPrices: (prices) => set({ prices }),
        updatePrice: (price) => set((state) => ({
          prices: state.prices.map(p => 
            p.symbol === price.symbol ? price : p
          )
        })),

        addToFavorites: (symbol) => set((state) => ({
          favorites: state.favorites.includes(symbol) 
            ? state.favorites 
            : [...state.favorites, symbol]
        })),

        removeFromFavorites: (symbol) => set((state) => ({
          favorites: state.favorites.filter(s => s !== symbol)
        })),

        setLoading: (loading) => set({ loading }),
        setError: (error) => set({ error }),
      }),
      {
        name: 'crypto-store',
        partialize: (state) => ({ favorites: state.favorites }),
      }
    ),
    { name: 'CryptoStore' }
  )
);

// Alerts Store
interface AlertsState {
  alerts: Alert[];
  loading: boolean;
  error: string | null;

  setAlerts: (alerts: Alert[]) => void;
  addAlert: (alert: Alert) => void;
  updateAlert: (alert: Alert) => void;
  removeAlert: (id: string) => void;
  triggerAlert: (alert: Alert) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useAlertsStore = create<AlertsState>()(
  devtools(
    (set) => ({
      alerts: [],
      loading: false,
      error: null,

      setAlerts: (alerts) => set({ alerts }),
      addAlert: (alert) => set((state) => ({ 
        alerts: [...state.alerts, alert] 
      })),

      updateAlert: (alert) => set((state) => ({
        alerts: state.alerts.map(a => a.id === alert.id ? alert : a)
      })),

      removeAlert: (id) => set((state) => ({
        alerts: state.alerts.filter(a => a.id !== id)
      })),

      triggerAlert: (alert) => set((state) => ({
        alerts: state.alerts.map(a => 
          a.id === alert.id ? { ...a, triggered_at: new Date().toISOString() } : a
        )
      })),

      setLoading: (loading) => set({ loading }),
      setError: (error) => set({ error }),
    }),
    { name: 'AlertsStore' }
  )
);

// App Store for global state
interface AppState {
  sidebarOpen: boolean;
  notifications: Array<{
    id: string;
    type: 'success' | 'error' | 'warning' | 'info';
    message: string;
    timestamp: string;
  }>;

  toggleSidebar: () => void;
  addNotification: (notification: Omit<AppState['notifications'][0], 'id' | 'timestamp'>) => void;
  removeNotification: (id: string) => void;
}

export const useAppStore = create<AppState>()(
  devtools(
    persist(
      (set) => ({
        sidebarOpen: true,
        notifications: [],

        toggleSidebar: () => set((state) => ({ 
          sidebarOpen: !state.sidebarOpen 
        })),

        addNotification: (notification) => set((state) => ({
          notifications: [...state.notifications, {
            ...notification,
            id: Math.random().toString(36).substr(2, 9),
            timestamp: new Date().toISOString(),
          }]
        })),

        removeNotification: (id) => set((state) => ({
          notifications: state.notifications.filter(n => n.id !== id)
        })),
      }),
      {
        name: 'app-store',
        partialize: (state) => ({ sidebarOpen: state.sidebarOpen }),
      }
    ),
    { name: 'AppStore' }
  )
);