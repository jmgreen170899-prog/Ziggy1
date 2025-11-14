'use client';

import React from 'react';

type Status = 'online' | 'degraded' | 'offline' | 'unknown';

export function WsStatusPill() {
  const [status, setStatus] = React.useState<Status>('unknown');
  const [lastChecked, setLastChecked] = React.useState<number | null>(null);

  const check = React.useCallback(async () => {
    try {
      const controller = new AbortController();
      const id = setTimeout(() => controller.abort(), 5000);
      const res = await fetch('/api/paper/health', { cache: 'no-store', signal: controller.signal });
      clearTimeout(id);
      setLastChecked(Date.now());
      if (!res.ok) {
        setStatus('offline');
        return;
      }
      const json = await res.json();
      // Consider online if any of these conditions are true:
      // - status === "ok" or status === "healthy"
      // - ok === true
      // - paper_enabled === true
      // - db_ok === true
      if (json && (
        json.status === 'ok' || 
        json.status === 'healthy' ||
        json.ok === true || 
        json.paper_enabled === true || 
        json.db_ok === true
      )) {
        setStatus('online');
      } else {
        setStatus('degraded');
      }
    } catch {
      setStatus('offline');
    }
  }, []);

  React.useEffect(() => {
    check();
    const id = setInterval(check, 15000);
    return () => clearInterval(id);
  }, [check]);

  const color = status === 'online' ? 'bg-green-500' : status === 'degraded' ? 'bg-yellow-500' : status === 'offline' ? 'bg-red-500' : 'bg-gray-400';
  const label = status === 'online' ? 'Live services: online' : status === 'degraded' ? 'Live services: degraded' : status === 'offline' ? 'Live services: offline' : 'Live services: unknown';
  const title = `${label}${lastChecked ? ` • Checked ${new Date(lastChecked).toLocaleTimeString()}` : ''}`;

  return (
    <div className="flex items-center gap-2" aria-label={label} title={title}>
      <span className={`inline-block w-2.5 h-2.5 rounded-full ${color}`} />
      <span className="text-xs text-gray-600 dark:text-gray-300 hidden sm:block">Live</span>
    </div>
  );
}

export default WsStatusPill;
