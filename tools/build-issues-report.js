#!/usr/bin/env node
/**
 * Aggregates scan outputs and Playwright artifacts into a human-readable ISSUES.md at the repo root.
 */

const fs = require('fs');
const fse = require('fs-extra');
const path = require('path');

const ROOT = process.cwd();
const OUT_DIR = path.join(ROOT, 'tools', 'out');
const FRONTEND_CALLS = path.join(OUT_DIR, 'frontend-calls.json');
const API_DIFF = path.join(OUT_DIR, 'api-diff.json');
const ARTIFACTS_DIR = path.join(ROOT, 'frontend', 'tests', 'artifacts');
const ISSUES_MD = path.join(ROOT, 'ISSUES.md');

function loadJsonSafe(p, fallback) {
  try { return JSON.parse(fs.readFileSync(p, 'utf8')); } catch { return fallback; }
}

function summarizeArtifacts() {
  if (!fs.existsSync(ARTIFACTS_DIR)) return [];
  const files = fs.readdirSync(ARTIFACTS_DIR);
  return files.map(f => ({ file: f, path: path.join('frontend/tests/artifacts', f) }));
}

function buildSection(title, contentLines) {
  return `\n## ${title}\n\n${contentLines.join('\n')}\n`;
}

function mdCode(code, lang = '') { return '```' + lang + `\n${code}\n` + '```\n'; }

function guessCurl(method, url) {
  const m = (method || 'GET').toUpperCase();
  return `curl -s -X ${m} "${url}"`;
}

function normalizeBackendUrl(callUrl) {
  if (/^https?:\/\//.test(callUrl)) return callUrl;
  if (callUrl.startsWith('/api/')) return `http://127.0.0.1:3000${callUrl}`; // proxy
  if (callUrl.startsWith('/')) return `http://127.0.0.1:8000${callUrl}`; // assume backend direct
  return callUrl;
}

function main() {
  fse.ensureDirSync(path.dirname(ISSUES_MD));
  const scan = loadJsonSafe(FRONTEND_CALLS, { routes: [], byRoute: {} });
  const diff = loadJsonSafe(API_DIFF, { backendAvailable: false, issues: [] });
  const artifacts = summarizeArtifacts();

  const lines = [];
  lines.push('# Ziggy – End-to-End Issues Report');
  lines.push('');
  lines.push(`Generated: ${new Date().toISOString()}`);

  // Startup & Env
  lines.push(buildSection('Startup & Env', [
    '- Frontend dev: http://127.0.0.1:3000',
    '- Backend dev: http://127.0.0.1:8000',
    `- Backend OpenAPI reachable: ${diff.backendAvailable ? 'Yes' : 'No'}`,
    `- Discovered routes: ${scan.routes?.length || 0}`,
    `- Total frontend API calls: ${Object.values(scan.byRoute || {}).flat().length}`
  ]));

  // Aggregate issues by route
  const byRoute = scan.byRoute || {};
  const issueList = diff.issues || [];

  for (const route of scan.routes || []) {
    const calls = byRoute[route] || [];
    const statusSummaries = calls.map(c => `- ${c.method} ${c.url} (${c.via}) @ ${c.file}:${c.line}`);

    // Link issues related to this route (by file match)
    const routeIssues = issueList.filter(i => {
      return calls.some(c => i.file && i.file.replace(/\\/g,'/') === c.file);
    });

    const repro = [];
    if (calls.length) {
      const c0 = calls[0];
      const target = normalizeBackendUrl(c0.url);
      repro.push('Repro:');
      repro.push(mdCode(guessCurl(c0.method, target), 'bash'));
    }

    const routeLines = [
      `- Route: ${route}`,
      ...(statusSummaries.length ? statusSummaries : ['- No API calls detected on this route.']),
      ...(routeIssues.length ? ['- Detected mismatches:', ...routeIssues.map(i => `  - [${i.type}] ${i.message}`)] : []),
      ...repro
    ];
    lines.push(buildSection(`Route: ${route}`, routeLines));
  }

  // Themed sections skeleton
  const themed = [
    'Auth',
    'Market/Overview',
    'Signals (single+batch)',
    'Trading',
    'News',
    'Charts/OHLC',
    'WebSockets',
    'Proxies',
    'DX'
  ];
  for (const t of themed) {
    lines.push(buildSection(t, [
      '_Summary:_ TODO – fill with findings (failures, mismatches, stack traces first line).',
    ]));
  }

  // Artifacts
  lines.push(buildSection('Artifacts', [
    ...(artifacts.length ? artifacts.map(a => `- ${a.path}`) : ['- No artifacts yet. Run the smoke test.'])
  ]));

  fs.writeFileSync(ISSUES_MD, lines.join('\n'));
  console.log(`Wrote ${ISSUES_MD}`);
}

main();
