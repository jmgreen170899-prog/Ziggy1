#requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = Resolve-Path (Join-Path $PSScriptRoot '..')
$Docs = Join-Path $Root 'docs'
$Raw  = Join-Path $Docs '_raw'
if (-not (Test-Path $Raw)) { New-Item -ItemType Directory -Path $Raw -Force | Out-Null }

$frontend = Join-Path $Root 'frontend'
$routesOut = Join-Path $Raw '_routes_frontend.json'

if (-not (Test-Path -LiteralPath $frontend)) {
    '{"routes": []}' | Out-File -LiteralPath $routesOut -Encoding UTF8
    return
}

$node = Get-Command node -ErrorAction SilentlyContinue
if ($null -eq $node) {
    '{"routes": [], "error": "Node not available"}' | Out-File -LiteralPath $routesOut -Encoding UTF8
    return
}

# Ensure helper exists
$toolsDir = Join-Path $frontend 'tools'
if (-not (Test-Path $toolsDir)) { New-Item -ItemType Directory -Path $toolsDir -Force | Out-Null }
$helper = Join-Path $toolsDir 'export_routes.js'

@'
#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

function listFiles(dir) {
  let results = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isSymbolicLink && entry.isSymbolicLink()) continue; // no symlinks
    if (entry.isDirectory()) {
      results = results.concat(listFiles(full));
    } else {
      results.push(full);
    }
  }
  return results;
}

function normalize(p) { return p.replace(/\\/g, '/'); }
function toRouteFromApp(appDir, file) {
  const rel = normalize(path.relative(appDir, file));
  // match page.(js|jsx|ts|tsx) or route.(js|ts)
  let bp = rel
    .replace(/\\/g, '/')
    .replace(/(^|\/)page\.(jsx?|tsx?)$/i, '')
    .replace(/(^|\/)route\.(jsx?|tsx?)$/i, '')
    .replace(/\/(page|route)\.(jsx?|tsx?)$/i, '');
  if (!bp) return '/';
  // dynamic [id] => :id; catch-all [...slug] => :slug*
  bp = '/' + bp
    .replace(/\\/g, '/')
    .replace(/index$/i, '')
    .replace(/\[(\.\.\.)?([\w-]+)\]/g, (_, dots, name) => dots ? `:${name}*` : `:${name}`)
    .replace(/\/+$/, '');
  return bp || '/';
}

function toRouteFromPages(pagesDir, file) {
  const rel = normalize(path.relative(pagesDir, file));
  if (rel.startsWith('api/')) return null; // skip API routes
  let bp = rel.replace(/\.(jsx?|tsx?)$/i, '')
              .replace(/index$/i, '')
              .replace(/\[(\.\.\.)?([\w-]+)\]/g, (_, dots, name) => dots ? `:${name}*` : `:${name}`);
  bp = '/' + bp;
  bp = bp.replace(/\/+$/, '');
  return bp || '/';
}

function discoverRoutes(frontendRoot) {
  const routes = [];
  const srcDir = path.join(frontendRoot, 'src');
  const appDir = path.join(srcDir, 'app');
  const pagesDir = path.join(srcDir, 'pages');
  const exists = p => { try { return fs.statSync(p).isDirectory(); } catch { return false; } };
  const isCode = f => /\.(jsx?|tsx?)$/i.test(f);

  if (exists(appDir)) {
    const files = listFiles(appDir).filter(f => /\/(page|route)\.(jsx?|tsx?)$/i.test(f));
    for (const f of files) {
      const route = toRouteFromApp(appDir, f);
      routes.push({ path: route, component: path.basename(f), file: normalize(path.relative(frontendRoot, f)), line: null });
    }
  } else if (exists(pagesDir)) {
    const files = listFiles(pagesDir).filter(isCode);
    for (const f of files) {
      const route = toRouteFromPages(pagesDir, f);
      if (route) routes.push({ path: route, component: path.basename(f), file: normalize(path.relative(frontendRoot, f)), line: null });
    }
  } else {
    // generic: scan for react-router definitions (best-effort)
    const files = listFiles(srcDir).filter(isCode);
    const rx = /<Route\s+path=\"([^\"]+)\"[^>]*?element=\{?<([\w.]+)/g;
    for (const f of files) {
      const text = fs.readFileSync(f, 'utf8');
      let m; while ((m = rx.exec(text))) {
        routes.push({ path: m[1], component: m[2], file: normalize(path.relative(frontendRoot, f)), line: null });
      }
    }
  }
  // dedupe by path+file
  const seen = new Set();
  return routes.filter(r => { const k = r.path+'|'+r.file; if (seen.has(k)) return false; seen.add(k); return true; });
}

function main() {
  const frontendRoot = path.resolve(__dirname, '..');
  try {
    const routes = discoverRoutes(frontendRoot);
    process.stdout.write(JSON.stringify({ routes }, null, 0));
  } catch (e) {
    process.stdout.write(JSON.stringify({ routes: [], error: String(e) }));
  }
}
main();
'@ | Out-File -LiteralPath $helper -Encoding UTF8

try {
    & node $helper | Out-File -LiteralPath $routesOut -Encoding UTF8
} catch {
    '{"routes": []}' | Out-File -LiteralPath $routesOut -Encoding UTF8
}
