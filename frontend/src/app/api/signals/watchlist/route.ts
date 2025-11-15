/**
 * Next.js API Route: Signals Watchlist
 * - Proxies POST requests to backend /signals/watchlist
 * - Adds short timeout and keeps responses structured
 */

import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const revalidate = 0;

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8000";
const SIGNALS_WATCHLIST_PATH =
  process.env.SIGNALS_WATCHLIST_PATH || "/signals/watchlist";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json().catch(() => ({}));

    // Expecting { tickers: string[], include_regime?: boolean }
    const tickers: string[] =
      Array.isArray(body?.tickers) && body.tickers.length > 0
        ? body.tickers
        : ["AAPL", "MSFT", "NVDA", "TSLA"];
    const include_regime: boolean = body?.include_regime ?? false;

    const controller = new AbortController();
    // Allow more time for backend computation; fast enough for UX, avoids spurious aborts
    const to = setTimeout(() => controller.abort(), 7000);
    const backendRes = await fetch(`${BACKEND_URL}${SIGNALS_WATCHLIST_PATH}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ tickers, include_regime }),
      // Do not cache; we want fresh signals
      cache: "no-store",
      signal: controller.signal,
    });
    clearTimeout(to);

    const text = await backendRes.text();
    if (!backendRes.ok) {
      // Try to forward backend error body if JSON, else wrap
      try {
        const maybeJson = JSON.parse(text);
        return NextResponse.json(maybeJson, { status: backendRes.status });
      } catch {
        return NextResponse.json(
          { error: text || backendRes.statusText },
          { status: backendRes.status },
        );
      }
    }

    const data = text ? JSON.parse(text) : {};
    return NextResponse.json(data, {
      status: 200,
      headers: {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        Pragma: "no-cache",
        Expires: "0",
      },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error";
    console.error("Error proxying /api/signals/watchlist:", message);
    const status =
      message.includes("aborted") || message.includes("AbortError") ? 504 : 500;
    return NextResponse.json(
      {
        status: "error",
        error: message,
        source: "frontend_proxy",
        timestamp: new Date().toISOString(),
      },
      { status },
    );
  }
}
