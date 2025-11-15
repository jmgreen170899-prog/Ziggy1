import { NextResponse } from "next/server";

type Status = "ok" | "degraded" | "mixed" | "error";

export type ProxyEnvelope<T> = {
  ok: boolean;
  status: Status;
  data?: T;
  reason?: string;
  errors?: Array<{ path: string; status?: number; message?: string }>;
  meta?: Record<string, unknown>;
};

const DEFAULT_TIMEOUT_MS = 5000;
const BACKEND_BASE =
  process.env.BACKEND_BASE?.replace(/\/$/, "") || "http://127.0.0.1:8000";

function withTimeout<T>(p: Promise<T>, ms = DEFAULT_TIMEOUT_MS): Promise<T> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), ms);
  const promised = (async () => {
    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      return await (p as any);
    } finally {
      clearTimeout(timer);
    }
  })();
  // We can't inject the signal post hoc, so prefer call sites to pass it in; fallback is best-effort.
  return promised;
}

function buildBackendUrl(req: Request, backendPath: string): string {
  const url = new URL(req.url);
  const target = new URL(
    BACKEND_BASE +
      (backendPath.startsWith("/") ? backendPath : `/${backendPath}`),
  );
  // Copy query params
  url.searchParams.forEach((v, k) => target.searchParams.set(k, v));
  return target.toString();
}

export async function proxyJson<T = unknown>(
  req: Request,
  backendPath: string,
  init?: RequestInit & { timeoutMs?: number },
): Promise<NextResponse<ProxyEnvelope<T>>> {
  const timeoutMs = init?.timeoutMs ?? DEFAULT_TIMEOUT_MS;
  const url = buildBackendUrl(req, backendPath);

  try {
    const res = await withTimeout(
      fetch(url, {
        method: init?.method || "GET",
        headers: {
          Accept: "application/json",
          ...init?.headers,
        },
        body: init?.body,
        // Consider credentials pass-through if needed
      }),
      timeoutMs,
    );

    const ct = res.headers.get("content-type") || "";
    const isJson = ct.includes("application/json");
    const data = isJson ? await res.json() : await res.text();

    if (res.ok) {
      return NextResponse.json<ProxyEnvelope<T>>({
        ok: true,
        status: "ok",
        data: data as T,
      });
    }

    // Non-2xx -> degrade but do not break UI
    return NextResponse.json<ProxyEnvelope<T>>({
      ok: false,
      status: "degraded",
      reason: `backend_${res.status}`,
      errors: [
        {
          path: backendPath,
          status: res.status,
          message: typeof data === "string" ? data : undefined,
        },
      ],
      data: isJson ? (data as T) : undefined,
    });
  } catch (e) {
    const msg =
      (e instanceof Error ? e.message : String(e)) || "request_failed";
    const reason = /abort|timed out|timeout/i.test(msg)
      ? "timeout"
      : "network_error";
    return NextResponse.json<ProxyEnvelope<T>>({
      ok: false,
      status: "degraded",
      reason,
      errors: [{ path: backendPath, message: msg }],
    });
  }
}

// Helper for batch OHLC to compute mixed status
export function mixedStatusFromBatch(
  batch: { summary?: { failed?: number } } | null | undefined,
): Status {
  if (!batch || !batch.summary) return "ok";
  const failed = Number(batch.summary.failed || 0);
  return failed > 0 ? "mixed" : "ok";
}

// Small helpers to keep responses consistent
export function ok<T>(data: T) {
  return NextResponse.json<ProxyEnvelope<T>>({ ok: true, status: "ok", data });
}
export function degraded<T>(
  reason: string,
  data?: T,
  errors?: ProxyEnvelope<T>["errors"],
) {
  return NextResponse.json<ProxyEnvelope<T>>({
    ok: false,
    status: "degraded",
    reason,
    data,
    errors,
  });
}
export function mixed<T>(data: T) {
  return NextResponse.json<ProxyEnvelope<T>>({
    ok: true,
    status: "mixed",
    data,
  });
}
