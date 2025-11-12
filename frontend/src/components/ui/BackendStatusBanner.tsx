'use client';

import React from 'react';
import { AlertCircle } from 'lucide-react';

type HealthState = 'ok' | 'down' | 'unknown';

export function BackendStatusBanner() {
  const [state, setState] = React.useState<HealthState>('unknown');
  const [dismissed, setDismissed] = React.useState(false);

  const checkHealth = React.useCallback(async () => {
    try {
      const controller = new AbortController();
      const id = setTimeout(() => controller.abort(), 8000);
      const res = await fetch('/api/paper/health', { cache: 'no-store', signal: controller.signal });
      clearTimeout(id);
      if (!res.ok) {
        setState('down');
        return;
      }
      const json = await res.json();
      // Consider healthy if endpoint responds OK and paper_enabled or db_ok is truthy
      if (json && (json.paper_enabled || json.db_ok || json.status === 'ok')) {
        setState('ok');
      } else {
        setState('down');
      }
    } catch {
      setState('down');
    }
  }, []);

  React.useEffect(() => {
    checkHealth();
    const id = setInterval(checkHealth, 15000);
    return () => clearInterval(id);
  }, [checkHealth]);

  if (dismissed || state === 'ok') return null;

  return (
    <div
      role="status"
      aria-live="polite"
      className="w-full bg-amber-100 text-amber-900 dark:bg-amber-900/30 dark:text-amber-100 border-y border-amber-300 dark:border-amber-700"
    >
      <div className="mx-auto max-w-7xl px-4 py-2 flex items-start sm:items-center gap-2 sm:gap-3">
        <AlertCircle className="w-4 h-4 sm:w-5 sm:h-5 flex-shrink-0" />
        <div className="text-sm">
          <strong className="mr-1">Backend unavailable.</strong>
          Some data and live features may be limited. We’ll keep retrying in the background.
        </div>
        <button
          type="button"
          onClick={() => setDismissed(true)}
          className="ml-auto text-sm underline decoration-dotted hover:opacity-80"
          aria-label="Dismiss backend unavailable notification"
        >
          Dismiss
        </button>
      </div>
    </div>
  );
}

export default BackendStatusBanner;
