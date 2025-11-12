// ContractGuard: runtime response validation using Zod.
// TODO: Adjust schemas to match backend responses precisely.

import { z } from 'zod';

// Health: GET /paper/health
export const HealthSchema = z.object({
  status: z.string().optional(),
  ok: z.boolean().optional(),
}).passthrough();

// Market overview: GET /market/overview
export const MarketOverviewSchema = z.object({
  summary: z.any().optional(),
  sectors: z.array(z.any()).optional(),
}).passthrough();

// OHLC: GET /trade/ohlc
export const OhlcSchema = z.object({
  symbol: z.string().optional(),
  ohlc: z.array(z.object({
    t: z.union([z.string(), z.number()]).optional(),
    o: z.number().nullable().optional(),
    h: z.number().nullable().optional(),
    l: z.number().nullable().optional(),
    c: z.number().nullable().optional(),
    v: z.number().nullable().optional(),
  })).optional(),
}).passthrough();

// Signals: GET /signals/watchlist (and possibly POST for batch)
export const SignalsSchema = z.object({
  items: z.array(z.object({
    id: z.union([z.string(), z.number()]).optional(),
    symbol: z.string().optional(),
    signal: z.string().optional(),
    score: z.number().nullable().optional(),
  })).optional(),
}).passthrough();

export type ContractSchemas = {
  health: typeof HealthSchema,
  overview: typeof MarketOverviewSchema,
  ohlc: typeof OhlcSchema,
  signals: typeof SignalsSchema,
};

const schemas: ContractSchemas = {
  health: HealthSchema,
  overview: MarketOverviewSchema,
  ohlc: OhlcSchema,
  signals: SignalsSchema,
};

export type ContractKey = keyof ContractSchemas;

export function validateContract(
  key: ContractKey,
  payload: unknown,
  ctx?: { route?: string; endpoint?: string }
) {
  const schema = schemas[key];
  const result = schema.safeParse(payload);
  if (!result.success) {
    const first = result.error.issues[0];
  const where = [ctx?.route, ctx?.endpoint].filter(Boolean).join(' | ');
  console.warn(`[ContractGuard] ${key} mismatch at ${where}: ${first.path.join('.') || '(root)'} – ${first.message}`);
  }
  return result.success;
}

// Example usage (non-blocking):
// const data = await fetch('http://127.0.0.1:8000/market/overview').then(r => r.json());
// validateContract('overview', data, { route: '/dashboard', endpoint: '/market/overview' });
