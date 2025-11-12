// frontend/src/services/api.js
// Smart fetch wrapper that honors VITE_API_BASE, discovers /api prefix,
// retries common aliases, and caches results in localStorage.

const RAW_BASE = (import.meta?.env?.VITE_API_BASE ?? "").trim().replace(/\/+$/, "");
const BASE = RAW_BASE; // if "", requests are same-origin
const DEBUG = String(import.meta?.env?.VITE_DEBUG_API ?? "0") === "1";
const DEFAULT_TIMEOUT_MS = Number(import.meta?.env?.VITE_API_TIMEOUT_MS ?? 10000);
const FORCED_PREFIX = (import.meta?.env?.VITE_API_PREFIX ?? "").trim(); // "", "/api", or ""

// NEW: dedupe/debounce defaults (non-breaking; opt-out via opts.dedupe=false)
const DEFAULT_DEDUPE_MS = Number(import.meta?.env?.VITE_API_DEDUPE_MS ?? 300);

// Cache: API prefix ("", "/api") and any learned path aliases
let cachedPrefix = localStorage.getItem("ziggy_api_prefix");
let discovering; // in-flight discovery promise

// Aliases for historically renamed routes (retry on 404)
const STATIC_ALIASES = {
  "/market/risk-lite": "/market-risk-lite", // old → new
  "/quotes": "/crypto/quotes",              // legacy frontend → new backend

  // QUICK ACTIONS ++ handy fallbacks (app may call lhs; backend might expose rhs)
  "/trading/backtest": "/backtest",
  "/strategy/backtest": "/backtest",
  "/alerts/sma50": "/alerts/moving-average/50",
  "/alerts/create": "/alerts",
  "/watchlist/add": "/watchlist",

  // NEW: trading fallbacks for one-click paper trade
  "/trading/market": "/trade/market",
  "/paper/market": "/trade/market",

  // NEW: news sentiment/headwind endpoint fallbacks
  // Any of these will be retried toward a canonical sentiment route
  "/news/nlp": "/news/sentiment",
  "/news/headwind": "/news/sentiment",
  "/sentiment/news": "/news/sentiment",
};

const LS_ALIASES_KEY = "ziggy_api_aliases";
let dynamicAliases = {};
try {
  dynamicAliases = JSON.parse(localStorage.getItem(LS_ALIASES_KEY) || "{}");
} catch {
  dynamicAliases = {};
}

const ABSOLUTE_RE = /^(?:https?:)?\/\//i;

function normPath(p) {
  if (!p) return "/";
  return p.startsWith("/") ? p : `/${p}`;
}

function withBase(path, prefix = "") {
  // Absolute URL passthrough (check BEFORE normalization)
  if (ABSOLUTE_RE.test(path)) return path;
  const p = normPath(path);
  // Base may be "" (same-origin)
  return `${BASE}${prefix}${p}`;
}

function isJsonResponse(res) {
  return (res.headers.get("content-type") || "").toLowerCase().includes("application/json");
}

async function discoverPrefix() {
  // 0) Respect forced prefix when provided
  if (FORCED_PREFIX === "" || FORCED_PREFIX === "/api") {
    cachedPrefix = FORCED_PREFIX;
    try { localStorage.setItem("ziggy_api_prefix", FORCED_PREFIX); } catch {}
    DEBUG && console.debug("[api] prefix forced:", FORCED_PREFIX || "''");
    return cachedPrefix;
  }

  if (cachedPrefix !== null) return cachedPrefix;
  if (discovering) return discovering;

  discovering = (async () => {
    // 1) Try root: /health (FastAPI returns "ok" or JSON with ok)
    try {
      const r = await fetch(withBase("/health"), { cache: "no-store" });
      if (r.ok) {
        let healthy = false;
        if (isJsonResponse(r)) {
          const j = await r.clone().json().catch(() => ({}));
          healthy =
            j?.fastapi === "ok" ||
            j?.ok?.fastapi === "ok" ||
            Object.values(j || {}).some((v) => String(v).toLowerCase() === "ok");
        } else {
          const t = (await r.clone().text().catch(() => "")).trim().toLowerCase();
          healthy = t === "ok";
        }
        if (healthy) {
          cachedPrefix = "";
          localStorage.setItem("ziggy_api_prefix", "");
          DEBUG && console.debug("[api] prefix discovered: ''");
          return cachedPrefix;
        }
      }
    } catch {}

    // 2) Try /api: /api/health
    try {
      const r = await fetch(withBase("/health", "/api"), { cache: "no-store" });
      if (r.ok) {
        let healthy = false;
        if (isJsonResponse(r)) {
          const j = await r.clone().json().catch(() => ({}));
          healthy =
            j?.fastapi === "ok" ||
            j?.ok?.fastapi === "ok" ||
            Object.values(j || {}).some((v) => String(v).toLowerCase() === "ok");
        } else {
          const t = (await r.clone().text().catch(() => "")).trim().toLowerCase();
          healthy = t === "ok";
        }
        if (healthy) {
          cachedPrefix = "/api";
          localStorage.setItem("ziggy_api_prefix", "/api");
          DEBUG && console.debug("[api] prefix discovered: '/api'");
          return cachedPrefix;
        }
      }
    } catch {}

    // 3) Default to root (still works for same-origin dev)
    cachedPrefix = "";
    localStorage.setItem("ziggy_api_prefix", "");
    DEBUG && console.debug("[api] prefix defaulted: ''");
    return cachedPrefix;
  })();

  const p = await discovering;
  discovering = null;
  return p;
}

function resolveAlias(path) {
  const p = normPath(path);
  return dynamicAliases[p] || STATIC_ALIASES[p] || null;
}

function learnAlias(from, to) {
  const src = normPath(from);
  const dst = normPath(to);
  if (src === dst) return;
  dynamicAliases[src] = dst;
  try { localStorage.setItem(LS_ALIASES_KEY, JSON.stringify(dynamicAliases)); } catch {}
  DEBUG && console.debug("[api] learned alias:", src, "→", dst);
}

function withTimeout(signal, ms = DEFAULT_TIMEOUT_MS) {
  if (!ms || ms <= 0) return signal;
  const ctrl = new AbortController();
  const timer = setTimeout(() => {
    try {
      ctrl.abort(new DOMException("Timeout", "AbortError"));
    } catch {
      // Some browsers don't construct DOMException directly; fall back.
      ctrl.abort();
    }
  }, ms);
  signal?.addEventListener?.("abort", () => clearTimeout(timer));
  return ctrl.signal;
}

function buildUrlWithQuery(path, query) {
  if (!query) return path;
  const url = new URL(withBase(path, cachedPrefix || ""), ABSOLUTE_RE.test(BASE) ? undefined : window.location.origin);
  Object.entries(query).forEach(([k, v]) => {
    if (v === undefined || v === null) return;
    if (Array.isArray(v)) v.forEach((x) => url.searchParams.append(k, String(x)));
    else url.searchParams.set(k, String(v));
  });
  // Return pathname+search relative to base to keep fetch same-origin when BASE=""
  if (!ABSOLUTE_RE.test(BASE)) return url.pathname + url.search;
  return url.toString();
}

/* ---------- Scan meta helpers (non-breaking) ---------- */

function coerceEpochMs(input) {
  if (input == null) return null;
  // number could be seconds or ms
  if (typeof input === "number" && Number.isFinite(input)) {
    // heuristic: seconds < 1e12
    return input < 1e12 ? Math.round(input * 1000) : Math.round(input);
  }
  // ISO or date-like string
  if (typeof input === "string" && input.trim()) {
    const n = Number(input);
    if (!Number.isNaN(n)) return coerceEpochMs(n);
    const d = new Date(input);
    if (!isNaN(d.getTime())) return d.getTime();
  }
  return null;
}

function maybeEmitScanStatus(path, data) {
  try {
    const p = normPath(path);
    const isScanEndpoint =
      p === "/trade/scan/status" ||
      p === "/trade/scan/enable" ||
      p === "/trade/scan" ||             // future-proof
      p.endsWith("/trade/scan/status") ||
      p.endsWith("/trade/scan/enable");

    if (!isScanEndpoint || !data || typeof window === "undefined") return;

    // Accept several shapes:
    // { enabled: true, next: ..., state: "enabled" }
    // { scan: { enabled, next, state } }
    // { next_run, next_at, schedule: { next }, ... }
    const root = data.scan && typeof data.scan === "object" ? data.scan : data;
    const enabled = typeof root.enabled === "boolean" ? root.enabled : undefined;
    const state =
      root.state ??
      (enabled === true ? "enabled" : enabled === false ? "disabled" : undefined);

    const nextRaw =
      root.next ??
      root.next_run ??
      root.next_at ??
      (root.schedule && (root.schedule.next || root.schedule.next_at));

    const nextMs = coerceEpochMs(nextRaw);

    // expose on the global for TopBar readers
    const g = (window.__ziggyApi = window.__ziggyApi || {});
    g.status = {
      ...(g.status || {}),
      scanState: state ?? (g.status && g.status.scanState) ?? "",
      scanNext: nextMs ?? (g.status && g.status.scanNext) ?? null,
    };

    // notify listeners
    window.dispatchEvent(
      new CustomEvent("ziggy:status", {
        detail: {
          scanState: g.status.scanState,
          scanNext: g.status.scanNext,
        },
      })
    );

    DEBUG && console.debug("[api] scan status", { state: g.status.scanState, next: g.status.scanNext });
  } catch (e) {
    // never throw
    DEBUG && console.warn("[api] scan status emit failed:", e);
  }
}

/* ---------- NEW: unified refreshing status from API layer ---------- */

let activeDataRequests = 0;
function isDataEndpoint(p) {
  // Heuristic: count most app data endpoints, ignore trivial ones
  const np = normPath(p);
  if (np === "/health" || np.startsWith("/trade/notify")) return false;
  return true;
}
function emitRefreshing() {
  try {
    const g = (window.__ziggyApi = window.__ziggyApi || {});
    g.status = { ...(g.status || {}), refreshing: activeDataRequests > 0 };
    window.dispatchEvent(
      new CustomEvent("ziggy:status", { detail: { refreshing: g.status.refreshing } })
    );
  } catch {}
}

/* ---------- NEW: in-flight request dedupe + short debounce cache ---------- */

const inflight = new Map(); // key -> Promise
const shortCache = new Map(); // key -> { expires:number, data:any }

function keyFor(method, url, body) {
  // body may be string/undefined; keep short for map key
  let b = "";
  if (typeof body === "string") b = body.slice(0, 256);
  return `${method || "GET"} ${url} ${b}`;
}

/**
 * Core fetch with:
 *  - prefix discovery ("" vs "/api")
 *  - timeout (AbortController)
 *  - automatic JSON body handling (object → JSON)
 *  - 404 retry with /api if we guessed ""
 *  - 404 retry using known/learned aliases (e.g. /market/risk-lite → /market-risk-lite)
 *  - in-flight dedupe & short debounce for identical GETs (non-breaking, override via opts.dedupe=false)
 *  - side-effect: emit ziggy:status for scan endpoints and refreshing counter
 */
async function coreFetch(path, opts = {}, expectJson = true) {
  const prefix = await discoverPrefix();
  const p = normPath(path);

  // Extract and strip helper-only options
  const { timeout, query, json, dedupe, dedupeMs, ...rest } = opts || {};

  // Auto JSON: if caller provided `json`, or body is plain object and no Content-Type set
  let headers = { Accept: "application/json", ...(rest.headers || {}) };
  let body = rest.body;
  if (json !== undefined) {
    if (!(headers["Content-Type"] || headers["content-type"])) {
      headers["Content-Type"] = "application/json";
    }
    body = JSON.stringify(json);
  } else if (
    body &&
    typeof body === "object" &&
    !(body instanceof FormData) &&
    !(body instanceof Blob) &&
    !(body instanceof ArrayBuffer) &&
    !(body instanceof URLSearchParams)
  ) {
    if (!(headers["Content-Type"] || headers["content-type"])) {
      headers["Content-Type"] = "application/json";
    }
    body = JSON.stringify(body);
  }

  const userSignal = rest.signal;
  const signal = withTimeout(userSignal, timeout ?? DEFAULT_TIMEOUT_MS);

  // Build URL (query params supported)
  let url = buildUrlWithQuery(p, query);
  if (!ABSOLUTE_RE.test(url)) url = withBase(url, prefix);

  const method = (rest.method || "GET").toUpperCase();
  const wantDedupe = dedupe !== false && method === "GET";
  const windowMs = Number.isFinite(dedupeMs) ? Number(dedupeMs) : DEFAULT_DEDUPE_MS;

  // Short debounce cache: if we fetched this very recently, return cached value
  const cacheKey = keyFor(method, url, null);
  if (wantDedupe && windowMs > 0) {
    const cached = shortCache.get(cacheKey);
    if (cached && cached.expires > Date.now()) {
      DEBUG && console.debug("[api] cache-hit (short debounce):", url);
      // Ensure shape matches JSON/text expectation
      return expectJson ? cached.data : String(cached.data ?? "");
    }
  }

  // In-flight dedupe: reuse the same promise for identical GETs
  const inflightKey = wantDedupe ? keyFor(method, url, null) : null;
  if (wantDedupe && inflight.has(inflightKey)) {
    DEBUG && console.debug("[api] dedupe-hit (reusing in-flight):", url);
    return inflight.get(inflightKey);
  }

  DEBUG && console.debug("[api] →", url);

  // Wrap the whole request (incl. retries) so we can place it in inflight map
  const doRequest = (async () => {
    let res;
    const countIt = isDataEndpoint(p);
    if (countIt) {
      activeDataRequests += 1;
      emitRefreshing();
    }

    try {
      res = await fetch(url, {
        ...rest,
        headers,
        body,
        signal,
      });
    } catch (e) {
      if (countIt) {
        activeDataRequests = Math.max(0, activeDataRequests - 1);
        emitRefreshing();
      }
      const err = new Error(`Network error: ${e?.message || e}`);
      err.cause = e;
      err.url = url;
      DEBUG && console.warn("[api] ❌ network", err);
      throw err;
    }

    // If we got a 404 and we assumed "", try /api once
    if (res.status === 404 && prefix === "") {
      const url2 = withBase(p + (query ? "?" + new URLSearchParams(query).toString() : ""), "/api");
      DEBUG && console.debug("[api] 404 retry with /api:", url2);
      try {
        const res2 = await fetch(url2, {
          ...rest,
          headers,
          body,
          signal,
        });
        if (res2.ok) {
          // lock onto /api going forward
          cachedPrefix = "/api";
          localStorage.setItem("ziggy_api_prefix", "/api");
          res = res2;
        }
      } catch {}
    }

    // If still 404, try a route alias (with current/locked prefix)
    if (res.status === 404) {
      const alias = resolveAlias(p);
      if (alias) {
        const aliasedUrl = withBase(alias + (query ? "?" + new URLSearchParams(query).toString() : ""), cachedPrefix || "");
        DEBUG && console.debug("[api] 404 alias retry:", p, "→", alias, "|", aliasedUrl);
        const res3 = await fetch(aliasedUrl, {
          ...rest,
          headers,
          body,
          signal,
        }).catch(() => null);
        if (res3?.ok) {
          learnAlias(p, alias);
          res = res3;
        }
      }
    }

    if (!res.ok) {
      if (countIt) {
        activeDataRequests = Math.max(0, activeDataRequests - 1);
        emitRefreshing();
      }
      let bodyText = "";
      try { bodyText = await res.text(); } catch {}
      const err = new Error(`HTTP ${res.status} ${res.statusText}`);
      err.status = res.status;
      err.statusText = res.statusText;
      err.url = res.url || url;
      err.body = bodyText;
      DEBUG && console.warn("[api] ❌", err, bodyText);
      throw err;
    }

    if (!expectJson) {
      const txt = await res.text();
      if (countIt) {
        activeDataRequests = Math.max(0, activeDataRequests - 1);
        emitRefreshing();
      }
      // no scan emit here (non-JSON)
      // short-cache for GET text responses too
      if (wantDedupe && windowMs > 0) {
        shortCache.set(cacheKey, { expires: Date.now() + windowMs, data: txt });
      }
      return txt;
    }
    if (res.status === 204) {
      if (countIt) {
        activeDataRequests = Math.max(0, activeDataRequests - 1);
        emitRefreshing();
      }
      if (wantDedupe && windowMs > 0) {
        shortCache.set(cacheKey, { expires: Date.now() + windowMs, data: null });
      }
      return null;
    }

    let data;
    try {
      data = await res.json();
    } catch (e) {
      const txt = await res.text().catch(() => "");
      try { data = JSON.parse(txt); } catch { data = txt; }
    } finally {
      if (isDataEndpoint(p)) {
        activeDataRequests = Math.max(0, activeDataRequests - 1);
        emitRefreshing();
      }
    }

    // Side-effect: if this is a scan endpoint, publish scanState/scanNext
    try { maybeEmitScanStatus(p, data); } catch {}

    // Store short debounce cache for identical GETs
    if (wantDedupe && windowMs > 0) {
      shortCache.set(cacheKey, { expires: Date.now() + windowMs, data });
    }

    return data;
  })();

  if (wantDedupe) {
    inflight.set(inflightKey, doRequest);
    // cleanup when settled
    doRequest.finally(() => {
      inflight.delete(inflightKey);
    });
  }

  return doRequest;
}

/** JSON helper (default) */
export async function api(path, opts = {}) {
  return coreFetch(path, opts, true);
}

/** Text helper (for plain-text endpoints like /health) */
api.text = async function apiText(path, opts = {}) {
  return coreFetch(path, opts, false);
};

/** Convenience HTTP helpers */
api.get = (path, opts = {}) => api(path, { ...opts, method: "GET" });
api.post = (path, body, opts = {}) => api(path, { ...opts, method: "POST", body });
api.put = (path, body, opts = {}) => api(path, { ...opts, method: "PUT", body });
api.patch = (path, body, opts = {}) => api(path, { ...opts, method: "PATCH", body });
api.delete = (path, opts = {}) => api(path, { ...opts, method: "DELETE" });

/** Query helper: api.getQ("/market/scan", { symbols: ["AAPL","TSLA"] }) */
api.getQ = (path, query, opts = {}) => api(path, { ...opts, method: "GET", query });

/** QUICK ACTIONS ++: simple multi-path fallbacks */
api.tryPost = async (paths = [], jsonBody = {}, opts = {}) => {
  let lastErr;
  for (const p of paths) {
    try {
      return await api(p, { ...opts, method: "POST", query: opts.query, json: jsonBody });
    } catch (e) { lastErr = e; }
  }
  throw lastErr || new Error("All POST fallbacks failed");
};
api.tryGet = async (paths = [], query = null, opts = {}) => {
  let lastErr;
  for (const p of paths) {
    try {
      return await api(p, { ...opts, method: "GET", query });
    } catch (e) { lastErr = e; }
  }
  throw lastErr || new Error("All GET fallbacks failed");
};

/* ===================== NEW: Trading convenience wrappers ===================== */
/** One-click paper market order with endpoint fallbacks.
 * Accepts the same payload you build in the RightRail (symbol, side, qty, entry, stop, target, sizing, meta, etc.)
 * Adds optional idempotency header if opts.idempotencyKey is provided.
 */
api.trade = api.trade || {};
api.trade.paperMarket = async function paperMarket(jsonBody = {}, opts = {}) {
  const headers = { ...(opts.headers || {}) };
  if (opts.idempotencyKey) headers["X-Idempotency-Key"] = String(opts.idempotencyKey);
  return api.tryPost(
    ["/trade/market", "/trading/market", "/paper/market"],
    jsonBody,
    { ...opts, headers }
  );
};

/** Optional: backtest convenience (mirrors RightRail quick action) */
api.trade.backtest = async function backtest(jsonBody = {}, opts = {}) {
  return api.tryPost(
    ["/trading/backtest", "/backtest", "/strategy/backtest"],
    jsonBody,
    opts
  );
};

/* ===================== NEW: News helpers (non-breaking) ===================== */
/** Fetch NLP news sentiment/headwind for a ticker, with tolerant fallbacks.
 * Returns whatever the backend provides; consumers should normalize if needed.
 */
api.news = api.news || {};
api.news.sentiment = async function newsSentiment(ticker, opts = {}) {
  const q = { ...(opts.query || {}), ticker: ticker, symbol: ticker };
  return api.tryGet(
    ["/news/sentiment", "/news/nlp", "/news/headwind", "/sentiment/news"],
    q,
    opts
  );
};
/* ============================================================================ */

/** Expose base and current prefix for debugging */
api.base = BASE;
api.getPrefix = async () => discoverPrefix();
api.resetDiscovery = () => {
  cachedPrefix = null;
  try { localStorage.removeItem("ziggy_api_prefix"); } catch {}
};

/** Optional: expose to window for console poking */
if (typeof window !== "undefined") {
  // eslint-disable-next-line no-underscore-dangle
  window.__ziggyApi = api;
}

export default api;
