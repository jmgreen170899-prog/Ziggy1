#!/usr/bin/env ts-node
/**
 * Compares frontend-discovered calls against backend OpenAPI.
 * Input: tools/out/frontend-calls.json (from scan-frontend.ts)
 * Output: tools/out/api-diff.json
 */

import fs from 'fs';
import fse from 'fs-extra';
import path from 'path';
import fetch from 'node-fetch';

const OUT_DIR = path.resolve(process.cwd(), 'tools', 'out');
const IN_FILE = path.join(OUT_DIR, 'frontend-calls.json');
const OUT_FILE = path.join(OUT_DIR, 'api-diff.json');
const OPENAPI_URL = process.env.OPENAPI_URL || 'http://127.0.0.1:8000/openapi.json';

function toPosix(p: string) { return p.replace(/\\/g, '/'); }

function normalizeUrl(url: string) {
  // Strip query strings and trailing slashes
  const u = url.split('#')[0].split('?')[0].replace(/\/$/, '') || '/';
  return u;
}

function normalizeCall(method: string, url: string) {
  const m = method.toUpperCase();
  let kind: 'proxy'|'backend'|'relative' = 'relative';
  let path = url;
  if (url.startsWith('/api/')) { kind = 'proxy'; path = url; }
  else if (/^https?:\/\/127\.0\.0\.1:8000\//.test(url) || /^https?:\/\/localhost:8000\//.test(url)) { kind = 'backend'; path = url.replace(/^https?:\/\/[^/]+/, ''); }
  else if (url.startsWith('/')) { kind = 'relative'; path = url; }
  return { method: m, path: normalizeUrl(path), kind };
}

async function loadOpenAPI() {
  try {
    const res = await fetch(OPENAPI_URL, { timeout: 5000 as any });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (e) {
    return null;
  }
}

async function main() {
  fse.ensureDirSync(OUT_DIR);
  if (!fs.existsSync(IN_FILE)) {
    console.error(`Missing input file: ${IN_FILE}. Run 'npm run audit:scan' first.`);
    process.exit(1);
  }
  const scan = JSON.parse(fs.readFileSync(IN_FILE, 'utf8'));
  const calls = Object.values(scan.byRoute || {}).flat() as Array<{method:string;url:string;file:string;line:number;via:string}>;

  const normalized = calls.map(c => ({
    ...c,
    norm: normalizeCall(c.method, c.url),
  }));

  const openapi = await loadOpenAPI();
  const backendAvailable = !!openapi;

  const apiPaths: Record<string, string[]> = {};
  if (openapi?.paths) {
    for (const p of Object.keys(openapi.paths)) {
      const methods = Object.keys(openapi.paths[p]).map(m => m.toUpperCase());
      apiPaths[p] = methods;
    }
  }

  const issues: Array<{ type: string; message: string; route?: string; method?: string; path?: string; file?: string; line?: number }>= [];

  for (const c of normalized) {
    const { method, path: pth, kind } = c.norm;
    const isBackendPath = kind === 'backend' || (kind === 'proxy' && backendAvailable);

    if (!backendAvailable) {
      // Cannot verify against OpenAPI; mark as unknown
      issues.push({ type: 'backend-unavailable', message: `OpenAPI not reachable while checking ${method} ${pth}`, method, path: pth, file: toPosix(c.file), line: c.line });
      continue;
    }

    if (kind === 'relative') {
      // Likely a frontend-only or proxy; warn but don't block
      issues.push({ type: 'relative-url', message: `Relative URL encountered: ${method} ${pth}`, method, path: pth, file: toPosix(c.file), line: c.line });
      continue;
    }

    // Compare to OpenAPI (with proxy normalization candidates)
    const candidates = [normalizeUrl(pth)];
    if (kind === 'proxy') {
      // Normalize Next.js API proxy to backend path by stripping '/api'
      candidates.push(normalizeUrl(pth.replace(/^\/api/, '')));
    }

    let foundPath: string | null = null;
    let methodsForPath: string[] | undefined;
    for (const cand of candidates) {
      if (apiPaths[cand]) {
        foundPath = cand;
        methodsForPath = apiPaths[cand];
        break;
      }
    }

    if (!foundPath || !methodsForPath) {
      issues.push({ type: 'missing-endpoint', message: `No OpenAPI path for ${method} ${pth}`, method, path: pth, file: toPosix(c.file), line: c.line });
    } else if (!methodsForPath.includes(method)) {
      issues.push({ type: 'wrong-method', message: `Method mismatch for ${method} ${pth} (OpenAPI allows: ${methodsForPath.join(',')})`, method, path: pth, file: toPosix(c.file), line: c.line });
    }
  }

  const result = {
    generatedAt: new Date().toISOString(),
    openapiUrl: OPENAPI_URL,
    backendAvailable,
    totals: {
      calls: normalized.length,
      issues: issues.length
    },
    issues,
    openapiSummary: backendAvailable ? { paths: Object.keys(apiPaths).length } : { paths: 0 }
  };

  fs.writeFileSync(OUT_FILE, JSON.stringify(result, null, 2));
  console.log(`Wrote ${OUT_FILE}`);
}

main().catch(err => { console.error(err); process.exit(1); });
