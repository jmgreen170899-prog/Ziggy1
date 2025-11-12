/**
 * Next.js API Route: Paper Trading Health Status
 * - Never throws to callers; always returns 200 JSON with ok/status
 * - Uses short timeout + small retry/backoff to smooth DB backoff
 * - In-memory TTL cache (3s) to avoid thundering herd
 */

import { NextResponse } from 'next/server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';
export const revalidate = 0;

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000';
const PAPER_HEALTH_PATH = process.env.PAPER_HEALTH_PATH || '/paper/health';

type BackendPayload = unknown; // backend payload is opaque to this proxy
type CacheEntry = { at: number; body: BackendPayload };
const cache: Map<string, CacheEntry> = new Map();
const TTL_MS = 3000; // 3s TTL to dedupe bursts

async function fetchWithTimeout(url: string, ms: number, init?: RequestInit) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), ms);
  try {
    const res = await fetch(url, { ...init, signal: controller.signal, cache: 'no-store' });
    return res;
  } finally {
    clearTimeout(id);
  }
}

async function getBackendHealth(): Promise<{ ok: boolean; status: string; backendStatus: number; latencyMs: number; data?: BackendPayload; details?: string }>
{
  const start = Date.now();
  const url = `${BACKEND_URL}${PAPER_HEALTH_PATH}`;
  let lastErr: string | undefined;
  let res: Response | null = null;

  for (const delay of [0, 150, 400]) {
    if (delay) await new Promise(r => setTimeout(r, delay));
    try {
      res = await fetchWithTimeout(url, 2000, { method: 'GET', headers: { 'Content-Type': 'application/json' } });
      break;
    } catch (e) {
      lastErr = e instanceof Error ? e.message : 'fetch_failed';
    }
  }

  const latencyMs = Date.now() - start;
  if (!res) {
    return { ok: false, status: 'unreachable', backendStatus: 0, latencyMs, details: lastErr || 'no_response' };
  }

  let data: BackendPayload = undefined;
  try {
    const text = await res.text();
    data = text ? JSON.parse(text) : undefined;
  } catch {
    // ignore parse errors, treat as degraded
  }

  if (!res.ok) {
    // Map backend 503/500 to a structured degraded/initialising state
    const status = res.status === 503 ? 'initialising' : 'degraded';
    return { ok: false, status, backendStatus: res.status, latencyMs, data };
  }

  return { ok: true, status: 'ready', backendStatus: res.status, latencyMs, data };
}

export async function GET() {
  const key = 'paper_health';
  const now = Date.now();
  const entry = cache.get(key);
  if (entry && now - entry.at < TTL_MS) {
    return NextResponse.json(entry.body, { status: 200 });
  }

  const result = await getBackendHealth();

  // Shape the response to be compatible with existing UI callers that expect
  // top-level fields like paper_enabled, db_ok, and a simple status string.
  let body: Record<string, unknown>;
  if (result.ok) {
    const payload = result.data as unknown;
    if (payload && typeof payload === 'object') {
      // Flatten backend payload at the top level and standardize status to 'ok'
      body = { status: 'ok', latencyMs: result.latencyMs, ...(payload as Record<string, unknown>) };
    } else {
      // Backend returned no/invalid JSON; still indicate we reached it
      body = { status: 'ok', latencyMs: result.latencyMs, raw: payload };
    }
  } else {
    // Preserve failure details; keep a simple status string for UI checks
    const detailsFromPayload =
      result.data && typeof result.data === 'object' && result.data !== null && 'reason' in (result.data as Record<string, unknown>)
        ? String((result.data as Record<string, unknown>)['reason'])
        : undefined;
    body = {
      status: result.status || 'error',
      ok: false,
      backendStatus: result.backendStatus,
      latencyMs: result.latencyMs,
      lastGoodAt: null,
      details: result.details || detailsFromPayload || 'backend_unavailable',
    };
  }

  cache.set(key, { at: now, body });
  return NextResponse.json(body, {
    status: 200,
    headers: {
      'Cache-Control': 'no-cache, no-store, must-revalidate',
      Pragma: 'no-cache',
      Expires: '0',
    },
  });
}