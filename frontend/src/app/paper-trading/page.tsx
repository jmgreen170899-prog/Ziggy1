'use client';

import { useState, useEffect } from 'react';
import { AdminGuard } from '@/components/auth/AdminGuard';
import { LoadingState } from '@/components/ui/Loading';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { 
  paperTradingApi, 
  type PaperRun, 
  type SystemHealth, 
  type Trade, 
  type TheoryPerformance
} from '@/services/paperTradingApi';

export default function PaperTradingPage() {
  return (
    <AdminGuard>
      <ErrorBoundary 
        fallback={
          <div className="space-y-8">
            <div className="border-b border-gray-200 dark:border-gray-700 pb-6">
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                🤖 Paper Trading Lab
              </h1>
              <p className="mt-2 text-lg text-gray-600 dark:text-gray-300">
                Autonomous micro-trading monitoring and control center
              </p>
            </div>
            <div className="text-center p-8">
              <p className="text-gray-500">Error loading paper trading dashboard. Please refresh the page.</p>
            </div>
          </div>
        }
      >
        <div className="space-y-8">
          <div className="border-b border-gray-200 dark:border-gray-700 pb-6">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              🤖 Paper Trading Lab
            </h1>
            <p className="mt-2 text-lg text-gray-600 dark:text-gray-300">
              Autonomous micro-trading monitoring and control center
            </p>
        </div>

        <PaperTradingDashboard />
        </div>
      </ErrorBoundary>
    </AdminGuard>
  );
}function PaperTradingDashboard() {
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [paperRuns, setPaperRuns] = useState<PaperRun[]>([]);
  const [recentTrades, setRecentTrades] = useState<Trade[]>([]);
  const [theoryPerformance, setTheoryPerformance] = useState<TheoryPerformance[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Data fetching functions
  const fetchSystemHealth = async () => {
    try {
      const health = await paperTradingApi.getSystemHealth();
      setSystemHealth(health);
    } catch (err) {
      console.error('Failed to fetch system health:', err);
    }
  };

  const fetchPaperRuns = async () => {
    try {
      const runs = await paperTradingApi.getRuns(10);
      setPaperRuns(runs);
    } catch (err) {
      console.error('Failed to fetch paper runs:', err);
    }
  };

  const fetchRecentTrades = async () => {
    try {
      const trades = await paperTradingApi.getRecentTrades(20);
      setRecentTrades(trades);
    } catch (err) {
      console.error('Failed to fetch recent trades:', err);
    }
  };

  const fetchTheoryPerformance = async () => {
    try {
      const performance = await paperTradingApi.getAllTheoryPerformance();
      setTheoryPerformance(performance);
    } catch (err) {
      console.error('Failed to fetch theory performance:', err);
    }
  };

  // Auto-refresh setup
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError(null);
      
      try {
        await Promise.all([
          fetchSystemHealth(),
          fetchPaperRuns(),
          fetchRecentTrades(),
          fetchTheoryPerformance()
        ]);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load data');
      } finally {
        setLoading(false);
      }
    };

    loadData();

    // Set up auto-refresh every 10 seconds
    const interval = setInterval(() => {
      fetchSystemHealth();
      fetchRecentTrades();
    }, 10000);

    return () => {
      clearInterval(interval);
    };
  }, []);

  // Emergency controls
  const handleEmergencyStop = async () => {
    try {
      await paperTradingApi.emergencyStop();
      await fetchSystemHealth();
      alert('Emergency stop executed successfully');
    } catch (err) {
      alert('Emergency stop failed: ' + (err instanceof Error ? err.message : 'Unknown error'));
    }
  };

  const handlePauseTrading = async () => {
    try {
      await paperTradingApi.pauseTrading();
      await fetchSystemHealth();
    } catch (err) {
      alert('Pause failed: ' + (err instanceof Error ? err.message : 'Unknown error'));
    }
  };

  const handleResumeTrading = async () => {
    try {
      await paperTradingApi.resumeTrading();
      await fetchSystemHealth();
    } catch (err) {
      alert('Resume failed: ' + (err instanceof Error ? err.message : 'Unknown error'));
    }
  };

  if (loading) {
    return <LoadingState />;
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
        <div className="text-red-800 dark:text-red-200">
          <h3 className="font-semibold">Error Loading Paper Trading Data</h3>
          <p className="mt-2">{error}</p>
          <button 
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* System Health Panel */}
      <SystemHealthPanel 
        health={systemHealth} 
        onEmergencyStop={handleEmergencyStop}
        onPause={handlePauseTrading}
        onResume={handleResumeTrading}
      />

      {/* Main Dashboard Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Recent Trades */}
        <RecentTradesPanel trades={recentTrades} />
        
        {/* Theory Performance */}
        <TheoryPerformancePanel theories={theoryPerformance} />
      </div>

      {/* Paper Runs */}
      <PaperRunsPanel runs={paperRuns} onRefresh={fetchPaperRuns} />
    </div>
  );
}

function SystemHealthPanel({ 
  health, 
  onEmergencyStop, 
  onPause, 
  onResume 
}: { 
  health: SystemHealth | null;
  onEmergencyStop: () => void;
  onPause: () => void;
  onResume: () => void;
}) {
  if (!health) {
    return (
      <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">System Health</h2>
        <div className="text-gray-500">Loading system status...</div>
      </div>
    );
  }

  const statusColor = health.worker_status === 'running' ? 'green' : 
                     health.worker_status === 'error' ? 'red' : 'yellow';

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold">System Health</h2>
        <div className="flex gap-2">
          <button
            onClick={onEmergencyStop}
            className="px-3 py-2 bg-red-600 text-white text-sm rounded hover:bg-red-700"
          >
            🛑 Emergency Stop
          </button>
          {health.worker_status === 'running' ? (
            <button
              onClick={onPause}
              className="px-3 py-2 bg-yellow-600 text-white text-sm rounded hover:bg-yellow-700"
            >
              ⏸️ Pause
            </button>
          ) : (
            <button
              onClick={onResume}
              className="px-3 py-2 bg-green-600 text-white text-sm rounded hover:bg-green-700"
            >
              ▶️ Resume
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="text-center">
          <div className={`text-2xl font-bold text-${statusColor}-600`}>
            {health.worker_status === 'running' ? '🟢' : 
             health.worker_status === 'error' ? '🔴' : '🟡'}
          </div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Status</div>
          <div className="font-medium capitalize">{health.worker_status}</div>
        </div>

        <div className="text-center">
          <div className="text-2xl font-bold text-blue-600">
            {health.trades_per_minute.toFixed(1)}
          </div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Trades/Min</div>
        </div>

        <div className="text-center">
          <div className="text-2xl font-bold text-purple-600">
            {health.active_theories.length}
          </div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Active Theories</div>
        </div>

        <div className="text-center">
          <div className="text-2xl font-bold text-orange-600">
            {health.memory_usage_mb.toFixed(0)}MB
          </div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Memory</div>
        </div>
      </div>

      {health.error_count > 0 && (
        <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded">
          <div className="text-red-800 dark:text-red-200">
            ⚠️ {health.error_count} errors in the last hour
          </div>
        </div>
      )}
    </div>
  );
}

function RecentTradesPanel({ trades }: { trades: Trade[] }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6">
      <h3 className="text-lg font-semibold mb-4">Recent Trades</h3>
      
      {trades.length === 0 ? (
        <div className="text-gray-500 text-center py-8">No recent trades</div>
      ) : (
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {trades.map((trade) => (
            <div 
              key={trade.id} 
              className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-700 rounded"
            >
              <div>
                <div className="font-medium">
                  {trade.side === 'buy' ? '🟢' : '🔴'} {trade.symbol}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  {trade.quantity} @ ${trade.price.toFixed(2)}
                </div>
                <div className="text-xs text-gray-500">
                  {trade.theory_used} ({(trade.signal_confidence * 100).toFixed(0)}%)
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm">
                  {new Date(trade.timestamp).toLocaleTimeString()}
                </div>
                {trade.pnl !== undefined && (
                  <div className={`text-sm font-medium ${
                    trade.pnl >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {trade.pnl >= 0 ? '+' : ''}${trade.pnl.toFixed(2)}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function TheoryPerformancePanel({ theories }: { theories: TheoryPerformance[] }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6">
      <h3 className="text-lg font-semibold mb-4">Theory Performance</h3>
      
      {theories.length === 0 ? (
        <div className="text-gray-500 text-center py-8">No theory data available</div>
      ) : (
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {theories.map((theory) => (
            <div 
              key={theory.id} 
              className="p-3 bg-gray-50 dark:bg-gray-700 rounded"
            >
              <div className="flex justify-between items-center mb-2">
                <div className="font-medium">{theory.theory_name}</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  Weight: {(theory.allocation_weight * 100).toFixed(1)}%
                </div>
              </div>
              
              <div className="grid grid-cols-3 gap-2 text-sm">
                <div>
                  <span className="text-gray-600 dark:text-gray-400">Win Rate:</span>
                  <div className={`font-medium ${
                    theory.win_rate >= 0.5 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {(theory.win_rate * 100).toFixed(1)}%
                  </div>
                </div>
                
                <div>
                  <span className="text-gray-600 dark:text-gray-400">Avg PnL:</span>
                  <div className={`font-medium ${
                    theory.avg_pnl >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    ${theory.avg_pnl.toFixed(2)}
                  </div>
                </div>
                
                <div>
                  <span className="text-gray-600 dark:text-gray-400">Signals:</span>
                  <div className="font-medium">{theory.total_signals}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function PaperRunsPanel({ runs, onRefresh }: { runs: PaperRun[]; onRefresh: () => void }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Paper Trading Runs</h3>
        <button
          onClick={onRefresh}
          className="px-3 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
        >
          🔄 Refresh
        </button>
      </div>
      
      {runs.length === 0 ? (
        <div className="text-gray-500 text-center py-8">No trading runs found</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-700">
                <th className="text-left p-2">ID</th>
                <th className="text-left p-2">Status</th>
                <th className="text-left p-2">Symbols</th>
                <th className="text-left p-2">Balance</th>
                <th className="text-left p-2">Trades</th>
                <th className="text-left p-2">Win Rate</th>
                <th className="text-left p-2">Started</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run) => (
                <tr key={run.id} className="border-b border-gray-100 dark:border-gray-700">
                  <td className="p-2 font-mono text-xs">{run.id.slice(0, 8)}...</td>
                  <td className="p-2">
                    <span className={`px-2 py-1 rounded text-xs ${
                      run.status === 'active' ? 'bg-green-100 text-green-800' :
                      run.status === 'error' ? 'bg-red-100 text-red-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {run.status}
                    </span>
                  </td>
                  <td className="p-2">{run.symbols.slice(0, 3).join(', ')}{run.symbols.length > 3 ? '...' : ''}</td>
                  <td className="p-2">
                    <div>${run.current_balance.toLocaleString()}</div>
                    <div className={`text-xs ${
                      run.current_balance >= run.initial_balance ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {run.current_balance >= run.initial_balance ? '+' : ''}
                      {((run.current_balance - run.initial_balance) / run.initial_balance * 100).toFixed(2)}%
                    </div>
                  </td>
                  <td className="p-2">{run.total_trades}</td>
                  <td className="p-2">
                    {run.total_trades > 0 ? 
                      `${((run.winning_trades / run.total_trades) * 100).toFixed(1)}%` : 
                      'N/A'
                    }
                  </td>
                  <td className="p-2">{new Date(run.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}