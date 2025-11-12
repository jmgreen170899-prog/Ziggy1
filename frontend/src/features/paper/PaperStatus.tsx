/**
 * Paper Trading Status Dashboard
 * 
 * Real-time monitoring of paper trading system health:
 * - Paper trading enabled and isolated
 * - Trade execution and persistence
 * - Brain learning integration
 * - Database connectivity
 */

'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { RefreshCw, CheckCircle, XCircle, AlertTriangle, Activity } from 'lucide-react';

interface PaperHealthData {
  status: 'healthy' | 'unhealthy' | 'error';
  paper_enabled: boolean;
  strict_isolation: boolean;
  broker: string;
  open_trades: number;
  recent_trades_5m: number;
  last_trade_at?: string;
  learner_batches_5m: number;
  queue_depth: number;
  db_ok: boolean;
  gateway_running: boolean;
  last_error?: string;
  brain_metrics: {
    queue_depth: number;
    events_total: number;
    events_5m: number;
  };
  learner_metrics: {
    batches_total: number;
    batches_5m: number;
    last_batch_at?: string;
    learner_available: boolean;
    last_error?: string;
  };
  timestamp: string;
}

interface DetailedStatus {
  worker_status: {
    is_running: boolean;
    engine_status: {
      status: string;
      run_id?: string;
      uptime_mins: number;
    };
    worker_stats: {
      signals_generated: number;
      trades_executed: number;
      learning_updates: number;
      error_count: number;
    };
  };
  trade_statistics: Record<string, number>;
  failed_trades_1h: number;
}

const StatusIndicator: React.FC<{ 
  status: boolean; 
  label: string; 
  description?: string;
}> = ({ status, label, description }) => (
  <div className="flex items-center space-x-2 p-2 rounded">
    {status ? (
      <CheckCircle className="h-5 w-5 text-green-500" />
    ) : (
      <XCircle className="h-5 w-5 text-red-500" />
    )}
    <div>
      <span className="font-medium">{label}</span>
      {description && (
        <p className="text-sm text-gray-600 dark:text-gray-400">{description}</p>
      )}
    </div>
  </div>
);

const MetricCard: React.FC<{
  title: string;
  value: string | number;
  subtitle?: string;
  status?: 'good' | 'warning' | 'error';
}> = ({ title, value, subtitle, status }) => (
  <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm font-medium text-gray-600 dark:text-gray-400">{title}</p>
        <p className="text-2xl font-bold">{value}</p>
        {subtitle && (
          <p className="text-xs text-gray-500 dark:text-gray-500">{subtitle}</p>
        )}
      </div>
      {status && (
        <div className="ml-2">
          {status === 'good' && <CheckCircle className="h-6 w-6 text-green-500" />}
          {status === 'warning' && <AlertTriangle className="h-6 w-6 text-yellow-500" />}
          {status === 'error' && <XCircle className="h-6 w-6 text-red-500" />}
        </div>
      )}
    </div>
  </div>
);

export default function PaperTradingStatus() {
  const [healthData, setHealthData] = useState<PaperHealthData | null>(null);
  const [detailedStatus, setDetailedStatus] = useState<DetailedStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const fetchHealthData = async () => {
    try {
      const response = await fetch('/api/paper/health');
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      setHealthData(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch health data');
    }
  };

  const fetchDetailedStatus = async () => {
    try {
      const response = await fetch('/api/paper/status/detailed');
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      setDetailedStatus(data);
    } catch (err) {
      console.warn('Failed to fetch detailed status:', err);
      // Don't set error for detailed status - it's optional
    }
  };

  const refresh = async () => {
    setLoading(true);
    await Promise.all([fetchHealthData(), fetchDetailedStatus()]);
    setLastUpdate(new Date());
    setLoading(false);
  };

  useEffect(() => {
    const performRefresh = async () => {
      setLoading(true);
      await Promise.all([fetchHealthData(), fetchDetailedStatus()]);
      setLastUpdate(new Date());
      setLoading(false);
    };
    
    performRefresh();
    
    // Poll every 5 seconds
    const interval = setInterval(performRefresh, 5000);
    
    return () => clearInterval(interval);
  }, []);

  if (loading && !healthData) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="flex items-center space-x-2">
          <RefreshCw className="h-5 w-5 animate-spin" />
          <span>Loading paper trading status...</span>
        </div>
      </div>
    );
  }

  if (error && !healthData) {
    return (
      <Card className="border-red-200">
        <CardHeader>
          <CardTitle className="text-red-600">Error Loading Status</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-red-600 mb-4">{error}</p>
          <Button onClick={refresh} variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (!healthData) return null;

  const overallStatus = healthData.status === 'healthy' ? 'good' : 
                       healthData.status === 'unhealthy' ? 'warning' : 'error';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Paper Trading Status</h1>
          <p className="text-gray-600 dark:text-gray-400">
            Real-time monitoring of autonomous trading system
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant={overallStatus === 'good' ? 'default' : 'destructive'}>
            {healthData.status.toUpperCase()}
          </Badge>
          <Button onClick={refresh} size="sm" variant="outline">
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Error Alert */}
      {healthData.last_error && (
        <Card className="border-red-200 bg-red-50 dark:bg-red-900/20">
          <CardContent className="pt-4">
            <div className="flex items-center space-x-2">
              <XCircle className="h-5 w-5 text-red-500" />
              <span className="font-medium text-red-700 dark:text-red-400">
                System Error: {healthData.last_error}
              </span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Core System Health */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Activity className="h-5 w-5" />
            <span>Core System Health</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <StatusIndicator 
            status={healthData.paper_enabled} 
            label="Paper Trading Enabled"
            description="Autonomous trading system is active"
          />
          <StatusIndicator 
            status={healthData.strict_isolation} 
            label="Strict Isolation"
            description="No live broker connections detected"
          />
          <StatusIndicator 
            status={healthData.broker === 'paper'} 
            label="Paper Broker Active"
            description={`Current broker: ${healthData.broker}`}
          />
          <StatusIndicator 
            status={healthData.db_ok} 
            label="Database Connected"
            description="Trade persistence operational"
          />
          <StatusIndicator 
            status={healthData.gateway_running} 
            label="Brain Gateway Running"
            description="Learning integration active"
          />
        </CardContent>
      </Card>

      {/* Trading Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Recent Trades (5m)"
          value={healthData.recent_trades_5m}
          status={healthData.recent_trades_5m > 0 ? 'good' : 'warning'}
        />
        <MetricCard
          title="Open Positions"
          value={healthData.open_trades}
          status="good"
        />
        <MetricCard
          title="Brain Queue Depth"
          value={healthData.queue_depth}
          subtitle={`${healthData.brain_metrics.events_5m} events in 5m`}
          status={healthData.queue_depth < 1000 ? 'good' : 'warning'}
        />
        <MetricCard
          title="Learner Batches (5m)"
          value={healthData.learner_batches_5m}
          status={healthData.learner_batches_5m > 0 ? 'good' : 'warning'}
        />
      </div>

      {/* Brain Learning Integration */}
      <Card>
        <CardHeader>
          <CardTitle>Brain Learning Integration</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <MetricCard
              title="Total Brain Events"
              value={healthData.brain_metrics.events_total}
              subtitle="Lifetime trade ingestions"
            />
            <MetricCard
              title="Recent Events (5m)"
              value={healthData.brain_metrics.events_5m}
              subtitle="Trade events queued"
            />
            <MetricCard
              title="Total Learner Batches"
              value={healthData.learner_metrics.batches_total}
              subtitle="Processed by AI"
            />
          </div>
          
          <div className="mt-4">
            <StatusIndicator 
              status={healthData.learner_metrics.learner_available} 
              label="Online Learner Available"
              description={healthData.learner_metrics.learner_available ? 
                "AI learning from trade outcomes" : 
                "Learning counted but not processed"
              }
            />
          </div>
        </CardContent>
      </Card>

      {/* Detailed Worker Status */}
      {detailedStatus && (
        <Card>
          <CardHeader>
            <CardTitle>Worker Details</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <MetricCard
                title="Worker Status"
                value={detailedStatus.worker_status.is_running ? 'Running' : 'Stopped'}
                status={detailedStatus.worker_status.is_running ? 'good' : 'error'}
              />
              <MetricCard
                title="Uptime"
                value={`${Math.round(detailedStatus.worker_status.engine_status.uptime_mins)}m`}
                subtitle="Minutes running"
              />
              <MetricCard
                title="Signals Generated"
                value={detailedStatus.worker_status.worker_stats.signals_generated}
                subtitle="Total signals"
              />
              <MetricCard
                title="Trades Executed"
                value={detailedStatus.worker_status.worker_stats.trades_executed}
                subtitle="Total executions"
              />
            </div>
          </CardContent>
        </Card>
      )}

      {/* Footer */}
      <div className="text-center text-sm text-gray-500 dark:text-gray-400">
        Last updated: {lastUpdate?.toLocaleString() || 'Never'}
        {healthData.timestamp && (
          <> • Server time: {new Date(healthData.timestamp).toLocaleString()}</>
        )}
      </div>
    </div>
  );
}