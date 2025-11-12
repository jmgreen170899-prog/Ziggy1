"use client";

import React from 'react';
import { Activity, Database, ShieldAlert, Server } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';

interface PaperHealthData {
  status?: string;
  paper_enabled?: boolean;
  db_ok?: boolean;
  gateway_running?: boolean;
  strict_isolation?: boolean;
  recent_trades_5m?: number;
  learner_batches_5m?: number;
  queue_depth?: number;
  timestamp?: string;
  last_error?: string | null;
}

export function PaperHealthWidget() {
  const [data, setData] = React.useState<PaperHealthData | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  const fetchHealth = React.useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch('/api/paper/health', { cache: 'no-store' });
      const json = await res.json();
      setData(json);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    fetchHealth();
    const id = setInterval(fetchHealth, 15_000);
    return () => clearInterval(id);
  }, [fetchHealth]);

  const statusBadge = (
    ok: boolean | undefined,
    label: string,
    Icon: React.ComponentType<{ className?: string }>,
    color: string
  ) => (
    <div className="flex items-center gap-2 p-2 rounded-lg border bg-white">
      <Icon className={`w-4 h-4 ${ok ? 'text-green-600' : color}`} />
      <span className="text-sm">{label}</span>
      <span className={`ml-auto text-xs font-medium ${ok ? 'text-green-700' : 'text-red-600'}`}>
        {ok ? 'OK' : 'Issue'}
      </span>
    </div>
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <Activity className="w-5 h-5 text-blue-600" />
          Paper Trading Health
        </CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-2" aria-busy>
            <div className="h-4 bg-gray-200 rounded animate-pulse" />
            <div className="h-4 bg-gray-200 rounded animate-pulse" />
            <div className="h-4 bg-gray-200 rounded animate-pulse" />
          </div>
        ) : error ? (
          <div className="text-sm text-red-600">{error}</div>
        ) : data ? (
          <div className="space-y-3">
            {statusBadge(data.paper_enabled, 'Worker Running', Server, 'text-gray-500')}
            {statusBadge(data.db_ok, 'Database Connected', Database, 'text-gray-500')}
            {statusBadge(data.strict_isolation, 'Strict Isolation', ShieldAlert, 'text-yellow-600')}
            {statusBadge(data.gateway_running, 'Learner Gateway', Activity, 'text-gray-500')}

            <div className="grid grid-cols-3 gap-2 text-center text-sm">
              <div className="p-2 rounded bg-gray-50 border">
                <div className="text-gray-500">Trades 5m</div>
                <div className="font-semibold">{data.recent_trades_5m ?? 0}</div>
              </div>
              <div className="p-2 rounded bg-gray-50 border">
                <div className="text-gray-500">Batches 5m</div>
                <div className="font-semibold">{data.learner_batches_5m ?? 0}</div>
              </div>
              <div className="p-2 rounded bg-gray-50 border">
                <div className="text-gray-500">Queue</div>
                <div className="font-semibold">{data.queue_depth ?? 0}</div>
              </div>
            </div>

            {data.last_error && (
              <div className="text-xs text-red-600">{data.last_error}</div>
            )}

            <button
              onClick={fetchHealth}
              className="mt-2 w-full p-2 rounded bg-blue-600 text-white text-sm hover:bg-blue-700"
              aria-label="Refresh paper trading health"
            >
              Refresh
            </button>
          </div>
        ) : (
          <div className="text-sm text-gray-500">No health data</div>
        )}
      </CardContent>
    </Card>
  );
}

export default PaperHealthWidget;
