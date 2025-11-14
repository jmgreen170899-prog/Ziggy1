/**
 * Demo mode configuration for ZiggyAI
 * 
 * Enables safe demonstration mode with deterministic data
 */

export const isDemoMode = (): boolean => {
  return import.meta.env.VITE_DEMO_MODE === 'true';
};

export const demoConfig = {
  // Default demo ticker
  defaultTicker: 'AAPL',
  
  // Default demo tickers for various scenarios
  demoTickers: ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'GOOGL', 'META', 'AMZN'],
  
  // Disable dangerous actions in demo mode
  disableRealTrading: true,
  disableDataIngestion: true,
  disableSystemChanges: true,
  
  // Show demo indicator
  showDemoIndicator: true,
  
  // Demo mode messages
  messages: {
    tradingDisabled: 'Real trading is disabled in demo mode. Use paper trading to simulate.',
    dataIngestionDisabled: 'Data ingestion is disabled in demo mode.',
    systemChangesDisabled: 'System changes are disabled in demo mode.',
  },
};

export default { isDemoMode, demoConfig };
