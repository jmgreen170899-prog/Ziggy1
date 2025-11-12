import { promises as fs } from 'fs';
import path from 'path';
import React from 'react';

async function loadUsageJson() {
  try {
    const p = path.resolve(process.cwd(), 'scripts/.endpoint-usage.json');
    const raw = await fs.readFile(p, 'utf8');
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

async function loadOpenApi() {
  const base = (process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
  const res = await fetch(`${base}/openapi.json`, { cache: 'no-store' });
  if (!res.ok) return null;
  return res.json();
}

function Badge({ status }: { status: 'OK' | 'MISSING' }) {
  const ok = status === 'OK';
  return (
    <span className={`px-2 py-1 rounded text-xs font-semibold ${ok ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
      {status}
    </span>
  );
}

export default async function Page() {
  if (process.env.NODE_ENV !== 'development') {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-2">API Coverage</h1>
        <p className="text-gray-500">This page is available in development only.</p>
      </div>
    );
  }

  const [usage, openapi] = await Promise.all([loadUsageJson(), loadOpenApi()]);

  const endpoints: Array<{ method: string; path: string; operationId?: string; tags?: string[] }> = [];
  if (openapi?.paths) {
    const paths = openapi.paths as Record<string, unknown>;
    for (const [p, item] of Object.entries(paths)) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const itemAny = item as Record<string, any>;
      for (const m of Object.keys(itemAny)) {
        const method = m.toUpperCase();
        if (!['GET','POST','PUT','DELETE','PATCH'].includes(method)) continue;
        const op = itemAny[m];
        if (/^\/(?:docs|openapi\.json|redoc)/i.test(p) || /^\/__debug\//.test(p)) continue;
        endpoints.push({ method, path: p, operationId: op.operationId, tags: op.tags });
      }
    }
  }

  const usageMap: Record<string, { usedBy: string[]; placeholdersFound: number }> = usage?.endpoints || {};

  const probeable = endpoints.filter((e) => e.method === 'GET');
  async function probeEndpoint(endpoint: { method: string; path: string }) {
    'use server';
    const base = (process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
    const res = await fetch(`${base}${endpoint.path}`, { cache: 'no-store' });
    return { status: res.status, ok: res.ok };
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">API Coverage</h1>
        <p className="text-gray-500">Development-only dashboard summarizing frontend usage of backend endpoints.</p>
        {!usage && (
          <div className="mt-2 text-yellow-700 bg-yellow-50 border border-yellow-200 rounded p-3">
            No usage JSON found. Run <code>npm run verify:endpoints</code> in the frontend project to generate it.
          </div>
        )}
      </div>

      <div className="overflow-auto border rounded">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left p-2">Method</th>
              <th className="text-left p-2">Path</th>
              <th className="text-left p-2">Used By</th>
              <th className="text-left p-2">Tags</th>
              <th className="text-left p-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {endpoints.map((e) => {
              const key = `${e.method} ${e.path}`;
              const usedBy = usageMap[key]?.usedBy || [];
              const status = usedBy.length > 0 ? 'OK' as const : 'MISSING' as const;
              return (
                <tr key={key} className="border-t">
                  <td className="p-2 font-mono">{e.method}</td>
                  <td className="p-2 font-mono">{e.path}</td>
                  <td className="p-2">
                    {usedBy.length === 0 ? (
                      <span className="text-gray-400">—</span>
                    ) : (
                      <details>
                        <summary>{usedBy.length} reference(s)</summary>
                        <ul className="list-disc pl-5">
                          {usedBy.map((u) => <li key={u} className="font-mono">{u}</li>)}
                        </ul>
                      </details>
                    )}
                  </td>
                  <td className="p-2">{(e.tags || []).join(', ')}</td>
                  <td className="p-2"><Badge status={status} /></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="space-y-2">
        <h2 className="text-xl font-semibold">Quick probe (GET only)</h2>
        <p className="text-gray-500">Click to probe an endpoint. Results appear in the console.</p>
        <div className="flex flex-wrap gap-2">
          {probeable.slice(0, 50).map((e) => {
            const key = `${e.method} ${e.path}`;
            return (
              <form key={key} action={async () => {
                const res = await probeEndpoint(e);
                console.log('Probe', key, res.status, res.ok);
              }}>
                <button type="submit" className="px-3 py-1 border rounded text-xs hover:bg-gray-50">
                  {e.method} {e.path}
                </button>
              </form>
            );
          })}
        </div>
      </div>

      {usage?.placeholders && (
        <div>
          <h2 className="text-xl font-semibold">Placeholders</h2>
          {Object.keys(usage.placeholders as Record<string, number>).length === 0 ? (
            <div className="text-sm text-gray-500">None detected.</div>
          ) : (
            <ul className="list-disc pl-6 text-sm">
              {(Object.entries(usage.placeholders as Record<string, number>)).map(([file, count]) => (
                <li key={file}><span className="font-mono">{file}</span>: {count as number}</li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
