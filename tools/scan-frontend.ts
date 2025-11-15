#!/usr/bin/env ts-node
/**
 * Scans the Next.js frontend to enumerate user-facing routes and static API calls.
 * Output: tools/out/frontend-calls.json -> { [route: string]: Array<{ method: string; url: string; file: string; line: number; via: 'direct'|'proxy'|'relative'; }> }
 */

import fg from "fast-glob";
import fs from "fs";
import fse from "fs-extra";
import path from "path";

const RE_FETCH =
  /(fetch\s*\(\s*(["'`])([^\2\n\r]+)\2\s*(?:,\s*\{[\s\S]*?method\s*:\s*(["'`])([A-Za-z]+)\3[\s\S]*?\})?\s*\))/g;
const RE_AXIOS =
  /(axios\.(get|post|put|patch|delete|head|options)\s*\(\s*(["'`])([^\3\n\r]+)\3)/g;

const FRONTEND_DIR = path.resolve(process.cwd(), "frontend");
const APP_DIR = path.join(FRONTEND_DIR, "src", "app");
const PAGES_DIR = path.join(FRONTEND_DIR, "pages");
const API_APP_DIR = path.join(FRONTEND_DIR, "src", "app", "api");
const API_PAGES_DIR = path.join(FRONTEND_DIR, "pages", "api");
const OUT_DIR = path.resolve(process.cwd(), "tools", "out");
const OUT_FILE = path.join(OUT_DIR, "frontend-calls.json");

function toPosix(p: string) {
  return p.replace(/\\/g, "/");
}

function detectVia(url: string): "proxy" | "direct" | "relative" {
  if (url.startsWith("/api/")) return "proxy";
  if (
    /^https?:\/\/127\.0\.0\.1:8000\//.test(url) ||
    /^https?:\/\/localhost:8000\//.test(url)
  )
    return "direct";
  if (url.startsWith("http")) return "direct";
  return "relative";
}

function normalizeRouteFromFile(file: string): string | null {
  const rel = toPosix(path.relative(FRONTEND_DIR, file));
  // app directory routing
  if (rel.startsWith("src/app/")) {
    const segs = rel.replace(/^src\/app\//, "").split("/");
    // look for page.(tsx|jsx|mdx) or route.tsx? - only page for UI routes
    if (!segs[segs.length - 1].match(/^page\.(t|j)sx?$/)) return null;
    const withoutFile = segs.slice(0, -1);
    const routePath =
      "/" +
      withoutFile
        .map((s) => {
          if (s.startsWith("(") && s.endsWith(")")) return ""; // route group
          if (s === "index") return "";
          if (s.startsWith("[") && s.endsWith("]"))
            return s.replace(/\[|\]/g, ":"); // dynamic -> :param
          return s;
        })
        .filter(Boolean)
        .join("/");
    return routePath || "/";
  }
  // pages directory routing
  if (rel.startsWith("pages/")) {
    if (!rel.match(/\.(t|j)sx?$/)) return null;
    if (rel.startsWith("pages/api/")) return null; // API routes not UI
    let route = rel.replace(/^pages\//, "").replace(/\.(t|j)sx?$/, "");
    if (route === "index") return "/";
    route =
      "/" +
      route
        .replace(/index$/, "")
        .replace(/\[\w+?\]/g, (m) => ":" + m.slice(1, -1));
    route = route.replace(/\/+/g, "/");
    return route.endsWith("/") ? route.slice(0, -1) || "/" : route;
  }
  return null;
}

async function enumerateRoutes(): Promise<string[]> {
  const pageFiles = await fg(
    [
      toPosix(path.join(APP_DIR, "**/page.@(tsx|jsx|ts|js)")),
      toPosix(path.join(PAGES_DIR, "**/*.@(tsx|jsx|ts|js)")),
    ],
    { dot: false, onlyFiles: true, ignore: ["**/node_modules/**"] },
  );
  const set = new Set<string>();
  for (const file of pageFiles) {
    const route = normalizeRouteFromFile(file);
    if (route) set.add(route);
  }
  return Array.from(set).sort();
}

function scanFileForCalls(file: string) {
  const src = fs.readFileSync(file, "utf8");
  const calls: Array<{
    method: string;
    url: string;
    file: string;
    line: number;
    via: "direct" | "proxy" | "relative";
  }> = [];
  const add = (method: string, url: string, index: number) => {
    const pre = src.slice(0, index);
    const line = pre.split(/\r?\n/).length;
    calls.push({
      method: method.toUpperCase(),
      url,
      file: toPosix(file),
      line,
      via: detectVia(url),
    });
  };
  let m: RegExpExecArray | null;
  RE_FETCH.lastIndex = 0;
  while ((m = RE_FETCH.exec(src))) {
    const [, , , url, , method] = m;
    add(method || "GET", url, m.index);
  }
  RE_AXIOS.lastIndex = 0;
  while ((m = RE_AXIOS.exec(src))) {
    const [, method, , url] = m;
    add(method, url, m.index);
  }
  return calls;
}

async function scanFrontendCalls() {
  const files = await fg(
    [
      toPosix(path.join(FRONTEND_DIR, "src/**/*.@(tsx|ts|js|jsx)")),
      toPosix(path.join(FRONTEND_DIR, "pages/**/*.@(tsx|ts|js|jsx)")),
    ],
    { dot: false, onlyFiles: true, ignore: ["**/node_modules/**"] },
  );
  const allCalls: ReturnType<typeof scanFileForCalls>[] = [];
  for (const file of files) {
    try {
      allCalls.push(scanFileForCalls(file));
    } catch {}
  }
  return allCalls.flat();
}

function groupCallsByRoute(
  routes: string[],
  calls: ReturnType<typeof scanFileForCalls>,
) {
  const map: Record<
    string,
    Array<{
      method: string;
      url: string;
      file: string;
      line: number;
      via: "direct" | "proxy" | "relative";
    }>
  > = {};
  for (const r of routes) map[r] = [];

  // Simple heuristic: associate a call with a route if it's in a component/page under the route's folder
  for (const c of calls) {
    // Try to find the closest route by comparing path segments
    let picked: string | null = null;
    let maxMatch = -1;
    for (const r of routes) {
      const rSegs = r.split("/").filter(Boolean);
      const rel = toPosix(path.relative(FRONTEND_DIR, c.file));
      const idx = rel.indexOf(rSegs[rSegs.length - 1] || "");
      const score = r === "/" ? 0 : idx >= 0 ? rSegs.length : -1;
      if (score > maxMatch) {
        maxMatch = score;
        picked = r;
      }
    }
    if (!picked) picked = "/";
    map[picked].push(c);
  }
  return map;
}

async function main() {
  fse.ensureDirSync(OUT_DIR);
  const routes = await enumerateRoutes();
  const calls = await scanFrontendCalls();

  // Scan Next API routes for backend calls to connect proxy -> backend URL
  const apiFiles = await fg(
    [
      toPosix(path.join(API_APP_DIR, "**/*.@(ts|tsx|js)")),
      toPosix(path.join(API_PAGES_DIR, "**/*.@(ts|tsx|js)")),
    ],
    { onlyFiles: true },
  );
  const apiCalls = apiFiles.flatMap(scanFileForCalls);

  const grouped = groupCallsByRoute(routes, calls);

  const result = {
    generatedAt: new Date().toISOString(),
    frontendRoot: FRONTEND_DIR,
    routes,
    apiRoutes: { app: fs.existsSync(APP_DIR), pages: fs.existsSync(PAGES_DIR) },
    proxyBacklinks: apiCalls, // TODO: correlate '/api/*' to backend URLs via these
    byRoute: grouped,
  } as const;

  fs.writeFileSync(OUT_FILE, JSON.stringify(result, null, 2));
  console.log(`Wrote ${OUT_FILE}`);
}

main().catch((err) => {
  console.error("scan-frontend failed:", err);
  process.exitCode = 1;
});
