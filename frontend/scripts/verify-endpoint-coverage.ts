/* eslint-disable @typescript-eslint/no-explicit-any */
// Minimal Node globals/types for this script without requiring @types/node
declare const __dirname: string;
declare const process: any;
declare function require(name: string): any;
/*
  verify-endpoint-coverage.ts
  - Fetches OpenAPI from backend
  - Scans src/** for endpoint usage and placeholder patterns
  - Writes scripts/.endpoint-usage.json
  - Exits non-zero if uncovered endpoints or placeholders present
*/

const { readFileSync, writeFileSync, readdirSync, statSync, promises: fsp } = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const SRC_DIR = path.join(ROOT, 'src');
const OUT_JSON = path.join(__dirname, '.endpoint-usage.json');

const PLACEHOLDER_TOKENS = [
  // Deliberately exclude common comment markers and JSX attributes like placeholder/TODO/TBD
  'mock', 'dummy', 'lorem', 'sample', 'fake', 'hardcoded'
];
// Note: numeric placeholders like 0.00 often appear in UI formatting; avoid scanning numbers to reduce false positives
// If needed later, reintroduce numeric heuristics with proper context awareness.
const PLACEHOLDER_IMPORT_PATTERNS = [/mocks\//i, /fixtures\//i, /dummy/i];

let EXCLUDE_ENDPOINTS: RegExp[] = [
  /^\/?docs\b/i,
  /^\/?openapi\.json$/i,
  /^\/?redoc\b/i,
  /^\/__debug\//i
];

// Attempt to load external config for excludes (optional)
// scripts/endpoint-coverage.config.json supports: { "excludePaths": ["^/paper/", "^/dev/", ...] }
try {
  const cfgPath = path.join(__dirname, 'endpoint-coverage.config.json');
  const raw = readFileSync(cfgPath, 'utf8');
  const cfg = JSON.parse(raw) as { excludePaths?: string[] };
  if (cfg.excludePaths && Array.isArray(cfg.excludePaths)) {
    const extra = cfg.excludePaths
      .filter((s) => typeof s === 'string' && s.trim().length > 0)
      .map((s) => new RegExp(s, 'i'));
    EXCLUDE_ENDPOINTS = EXCLUDE_ENDPOINTS.concat(extra);
  }
} catch {
  // no config present; proceed with defaults
}

function getenv(name: string, fallback?: string) {
  const v = process.env[name];
  return (v && v.trim().length > 0) ? v.trim() : fallback;
}

function normalizePathSignature(p: string): string {
  // Ensure leading slash, remove trailing slash (except root), strip query
  let out = p.trim();
  if (!out.startsWith('/')) out = '/' + out;
  out = out.replace(/\?.*$/, '');
  out = out !== '/' ? out.replace(/\/$/, '') : out;
  // Replace template literals ${...} with {param}
  out = out.replace(/\$\{[^}]+\}/g, '{param}');
  // Collapse duplicate slashes
  out = out.replace(/\/+/g, '/');
  return out;
}

function walk(dir: string, acc: string[] = []) {
  for (const name of readdirSync(dir)) {
    const fp = path.join(dir, name);
    const st = statSync(fp);
    if (st.isDirectory()) {
      // Skip build/system folders
      if (['.next', 'node_modules', 'public', 'artifacts'].includes(name)) continue;
      walk(fp, acc);
    } else if (/\.(ts|tsx|js|jsx)$/i.test(name)) {
      acc.push(fp);
    }
  }
  return acc;
}

async function fetchJson<T = any>(url: string): Promise<T> {
  const res = await fetch(url, { headers: { 'accept': 'application/json' } });
  if (!res.ok) throw new Error(`Failed to fetch ${url}: ${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

function extractUsagesFromContent(file: string, content: string) {
  const usages: Array<{ method: string; path: string; file: string; line: number }> = [];

  const add = (method: string, rawPath: string, index: number) => {
    const methodUp = method.toUpperCase();
    const norm = normalizePathSignature(rawPath);
    // compute line number from index
    const pre = content.slice(0, index);
    const line = pre.split(/\r?\n/).length;
    usages.push({ method: methodUp, path: norm, file, line });
  };

  // axios/client/apiClient calls across newlines
    // Tolerate nested generic closers like ">>" by allowing one or more closing angle brackets
    // Generalize receiver (this.client, apiClient, axios instances, etc.)
    const axiosRegexAll = /[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*\.(get|post|put|delete|patch)\s*(<[^>]+>+\s*)?\(\s*([`'"])(\/[^`'"\)\s]+)\3/gs;
    let m: RegExpExecArray | null;
    while ((m = axiosRegexAll.exec(content)) !== null) {
      add(m[1], m[4], m.index);
    }

  // fetch calls
  const fetchRegexAll = /\bfetch\(\s*([`'"])(https?:\/\/[^`'"\s]+|\/[^`'"\s]+)\1\s*(?:,\s*\{([\s\S]*?)\})?/gs;
  let f: RegExpExecArray | null;
  while ((f = fetchRegexAll.exec(content)) !== null) {
    const raw = f[2];
    const opts = f[3] || '';
    const mm = /method\s*:\s*['"](GET|POST|PUT|DELETE|PATCH)['"]/i.exec(opts);
    const method = mm ? mm[1] : 'GET';
    add(method, raw, f.index);
  }

  // RTK Query style
  const rtkRegexAll = /url\s*:\s*([`'"])(\/[^`'"\s]+)\1([\s\S]*?)\}/gs;
  let r: RegExpExecArray | null;
  while ((r = rtkRegexAll.exec(content)) !== null) {
    const methodMatch = /method\s*:\s*['"](GET|POST|PUT|DELETE|PATCH)['"]/i.exec(r[3] || '');
    const method = methodMatch ? methodMatch[1] : 'GET';
    add(method, r[2], r.index);
  }

  // Fallback: plain string literal paths starting with '/...'
  // Assign GET by default; unmatched paths will be ignored when building the OpenAPI keyed report
  const literalPathRegex = /([`'"])(\/[A-Za-z0-9_\-\/\{\}]+(?:\?[^`'"\s\)]*)?)\1/g;
  let l: RegExpExecArray | null;
  while ((l = literalPathRegex.exec(content)) !== null) {
    add('GET', l[2], l.index);
  }

  return usages;
}

function stripComments(input: string): string {
  // Remove block comments (/* ... */) including JSX block comments within braces
  let out = input.replace(/\/\*[\s\S]*?\*\//g, '');
  // Remove line comments (// ...)
  out = out.replace(/(^|\s)\/\/.*$/gm, '$1');
  return out;
}

function scanPlaceholders(file: string, content: string) {
  const matches: Array<{ token: string; count: number }> = [];
  let total = 0;

  // Ignore comments when scanning for placeholder tokens to reduce noise
  const withoutComments = stripComments(content);

  for (const token of PLACEHOLDER_TOKENS) {
    const re = new RegExp(`\\b${token}\\b`, 'ig');
    const count = (withoutComments.match(re) || []).length;
    if (count > 0) {
      matches.push({ token, count });
      total += count;
    }
  }

  // look for bad import paths
  const importLines = withoutComments.match(/import[^;]+;?/g) || [];
  for (const imp of importLines) {
    for (const pat of PLACEHOLDER_IMPORT_PATTERNS) {
      if (pat.test(imp)) {
        matches.push({ token: 'import:' + imp.trim(), count: 1 });
        total += 1;
      }
    }
  }

  return { total, matches };
}

async function main() {
  const base = getenv('NEXT_PUBLIC_API_URL', 'http://127.0.0.1:8000');
  const openapiUrl = new URL('/openapi.json', base).toString();

  console.log(`Fetching OpenAPI from ${openapiUrl} ...`);
  let openapi: any;
  try {
    openapi = await fetchJson<any>(openapiUrl);
  } catch (err) {
    console.error('Failed to fetch OpenAPI. If your backend is not running, start it first.');
    throw err;
  }

  const operations: Array<{ method: string; path: string; operationId?: string; tags?: string[]; responses?: string[] }> = [];
  for (const [p, item] of Object.entries<any>(openapi.paths || {})) {
    const pathTemplate = normalizePathSignature(p);
    for (const m of Object.keys(item)) {
      const method = m.toUpperCase();
      if (!['GET','POST','PUT','DELETE','PATCH'].includes(method)) continue;
      const op = item[m];
      const skip = EXCLUDE_ENDPOINTS.some((re) => re.test(pathTemplate));
      if (skip) continue;
      operations.push({
        method,
        path: pathTemplate,
        operationId: op.operationId,
        tags: op.tags,
        responses: Object.keys(op.responses || {})
      });
    }
  }

  // Scan source files
  const files = walk(SRC_DIR);
  const usageMap = new Map<string, { usedBy: string[]; placeholdersFound: number }>();
  const placeholderByFile: Record<string, number> = {};

  for (const file of files) {
    const content = readFileSync(file, 'utf8');
    const usages = extractUsagesFromContent(path.relative(ROOT, file), content);
    for (const u of usages) {
      const key = `${u.method} ${u.path}`;
      const arr = usageMap.get(key) || { usedBy: [], placeholdersFound: 0 };
      arr.usedBy.push(`${u.file}:${u.line}`);
      usageMap.set(key, arr);
    }
    const rel = path.relative(ROOT, file).replace(/\\/g, '/');
    // Skip placeholder scan for tests and known mock/dev files
    if (/\/__tests__\//.test(rel) || /\/mocks\//.test(rel) || /services\/auth\/mockAuthProvider\.ts$/.test(rel) || /services\/mockData\.ts$/.test(rel) || /lib\/guardRealData\.ts$/.test(rel)) {
      // skip
    } else {
      const ph = scanPlaceholders(file, content);
      if (ph.total > 0) {
        placeholderByFile[rel] = ph.total;
      }
    }
  }

  // Build report JSON
  const report: any = {};
  for (const op of operations) {
    const key = `${op.method} ${op.path}`;
    const usage = usageMap.get(key);
    report[key] = {
      usedBy: usage?.usedBy || [],
      placeholdersFound: 0
    };
  }

  // Attach placeholder counts per file
  const placeholders: Record<string, number> = placeholderByFile;

  // Write JSON file
  const payload = {
    generatedAt: new Date().toISOString(),
    apiBase: base,
    endpoints: report,
    placeholders
  };
  await fsp.mkdir(path.dirname(OUT_JSON), { recursive: true });
  writeFileSync(OUT_JSON, JSON.stringify(payload, null, 2), 'utf8');

  // Console tables
  const missing = Object.entries(report)
    .filter(([, v]) => (v as any).usedBy.length === 0)
    .map(([k]) => k);

  console.log('\nAPI Coverage:');
  console.table(
    Object.entries(report).map(([k, v]: any) => ({
      Endpoint: k,
      UsedBy: v.usedBy.length,
      Status: v.usedBy.length > 0 ? 'OK' : 'MISSING'
    }))
  );

  if (Object.keys(placeholders).length > 0) {
    console.log('\nPlaceholder occurrences:');
    console.table(
      Object.entries(placeholders).map(([file, count]) => ({ File: file, Count: count }))
    );
  } else {
    console.log('\nNo placeholder tokens found.');
  }

  let exitCode = 0;
  if (missing.length > 0) {
    console.error(`\nUncovered endpoints (${missing.length}):`);
    for (const m of missing) console.error('  -', m);
    exitCode = 1;
  }
  if (Object.keys(placeholders).length > 0) {
    console.error(`\nPlaceholder tokens found in ${Object.keys(placeholders).length} file(s).`);
    exitCode = 1;
  }

  // Explicitly exit
  process.exit(exitCode);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
