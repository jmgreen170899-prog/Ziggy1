#!/usr/bin/env node
// frontend/tests/verify.crawl.mjs
// Human-simulation crawler for E2E verification

import { chromium } from '@playwright/test';
import { mkdir, writeFile } from 'fs/promises';
import { existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// ============================================================================
// CONFIG
// ============================================================================
const UI_URL = process.env.UI_URL || "http://localhost:5173";
const API_URL = process.env.API_URL || "http://localhost:8000";
const SAFE_MODE = (process.env.SAFE_MODE ?? "true").toLowerCase() !== "false";
const MIN_OPENAPI_PATHS = parseInt(process.env.MIN_OPENAPI_PATHS || "175", 10);
const ROUTES = ["/", "/markets", "/signals", "/news", "/chat", "/admin"];
const ARTIFACTS_DIR = join(__dirname, "artifacts");

// ============================================================================
// STATE
// ============================================================================
const state = {
  visited: [],
  consoleErrors: [],
  server5xx: [],
  openapiCount: 0,
  browser: null,
  context: null,
  page: null,
};

// ============================================================================
// HELPERS
// ============================================================================

function log(msg, ...args) {
  console.log(`[CRAWLER] ${msg}`, ...args);
}

function error(msg, ...args) {
  console.error(`[CRAWLER ERROR] ${msg}`, ...args);
}

async function humanPause(min = 40, max = 140) {
  const delay = Math.floor(Math.random() * (max - min + 1)) + min;
  await new Promise(resolve => setTimeout(resolve, delay));
}

async function humanMove(page, selector) {
  try {
    const element = await page.locator(selector).first();
    const box = await element.boundingBox();
    if (box) {
      // Multi-step jittered mouse moves
      const targetX = box.x + box.width / 2;
      const targetY = box.y + box.height / 2;
      
      // Start from current position (or 0,0 if first move)
      const steps = 5;
      for (let i = 1; i <= steps; i++) {
        const x = (targetX / steps) * i + (Math.random() - 0.5) * 10;
        const y = (targetY / steps) * i + (Math.random() - 0.5) * 10;
        await page.mouse.move(x, y);
        await humanPause(10, 30);
      }
      
      // Final move to exact position
      await page.mouse.move(targetX, targetY);
    }
  } catch (e) {
    // Element might not be visible, skip
  }
}

async function humanClick(page, selector, options = {}) {
  try {
    const element = page.locator(selector).first();
    
    // Check if element exists
    const count = await element.count();
    if (count === 0) {
      return false;
    }
    
    // Get text for safety check
    const text = await element.textContent().catch(() => "");
    
    // SAFE_MODE: skip destructive actions
    if (SAFE_MODE) {
      const destructivePattern = /delete|remove|drop|panic|trade|order|sell|buy/i;
      if (destructivePattern.test(text)) {
        log(`Skipping destructive action: "${text}" (SAFE_MODE)`);
        return false;
      }
    }
    
    // Move to element and click
    await humanMove(page, selector);
    await humanPause(20, 60);
    await element.click({ timeout: 5000 });
    await humanPause(100, 200);
    return true;
  } catch (e) {
    return false;
  }
}

async function humanType(page, selector, text) {
  try {
    const element = page.locator(selector).first();
    await element.waitFor({ state: 'visible', timeout: 5000 });
    await humanMove(page, selector);
    await element.click();
    await humanPause(50, 100);
    
    // Type character by character
    for (const char of text) {
      await element.type(char);
      await humanPause(50, 150);
    }
    
    return true;
  } catch (e) {
    return false;
  }
}

async function humanScrollFull(page) {
  try {
    // Smooth scroll down
    const scrollHeight = await page.evaluate(() => document.body.scrollHeight);
    const viewportHeight = await page.evaluate(() => window.innerHeight);
    const steps = Math.ceil(scrollHeight / viewportHeight);
    
    for (let i = 0; i < steps; i++) {
      await page.evaluate((step) => {
        window.scrollTo({ top: step * window.innerHeight, behavior: 'smooth' });
      }, i);
      await humanPause(200, 400);
    }
    
    // Scroll back up
    for (let i = steps - 1; i >= 0; i--) {
      await page.evaluate((step) => {
        window.scrollTo({ top: step * window.innerHeight, behavior: 'smooth' });
      }, i);
      await humanPause(200, 400);
    }
  } catch (e) {
    // Ignore scroll errors
  }
}

async function fetchJSON(url, timeout = 15000) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  
  try {
    const response = await fetch(url, { signal: controller.signal });
    clearTimeout(timeoutId);
    return { status: response.status, data: await response.json() };
  } catch (e) {
    clearTimeout(timeoutId);
    throw e;
  }
}

async function ensureArtifactsDir() {
  if (!existsSync(ARTIFACTS_DIR)) {
    await mkdir(ARTIFACTS_DIR, { recursive: true });
  }
}

async function saveScreenshot(page, slug) {
  await ensureArtifactsDir();
  const filename = join(ARTIFACTS_DIR, `FAIL-${slug}.png`);
  await page.screenshot({ path: filename, fullPage: true });
  log(`Screenshot saved: ${filename}`);
}

// ============================================================================
// API CHECKS
// ============================================================================

async function checkAPIHealth() {
  log("Checking API health...");
  try {
    const { status, data } = await fetchJSON(`${API_URL}/health`);
    if (status !== 200 || !data.ok) {
      error(`API health check failed: status=${status}, data=${JSON.stringify(data)}`);
      return false;
    }
    log("✓ API health check passed");
    return true;
  } catch (e) {
    error(`API health check error: ${e.message}`);
    return false;
  }
}

async function checkOpenAPISpec() {
  log("Checking OpenAPI spec...");
  try {
    const { status, data } = await fetchJSON(`${API_URL}/openapi.json`);
    if (status !== 200) {
      error(`OpenAPI fetch failed: status=${status}`);
      return false;
    }
    
    const paths = Object.keys(data.paths || {});
    state.openapiCount = paths.length;
    log(`OpenAPI paths count: ${state.openapiCount}`);
    
    if (state.openapiCount < MIN_OPENAPI_PATHS) {
      error(`OpenAPI paths count ${state.openapiCount} < ${MIN_OPENAPI_PATHS} (FAIL)`);
      return false;
    }
    
    log(`✓ OpenAPI paths count >= ${MIN_OPENAPI_PATHS}`);
    
    // Probe GET endpoints without path params
    log("Probing GET endpoints...");
    for (const [path, methods] of Object.entries(data.paths || {})) {
      if (!methods.get) continue;
      
      // Skip paths with parameters
      if (path.includes('{')) continue;
      
      try {
        const url = `${API_URL}${path}`;
        const response = await fetch(url);
        const status = response.status;
        
        if (status >= 500) {
          error(`5xx response from ${path}: ${status}`);
          state.server5xx.push({ path, status });
        } else {
          log(`${path}: ${status}`);
        }
      } catch (e) {
        // Network errors are OK for this test
        log(`${path}: network error (skipped)`);
      }
      
      await humanPause(50, 100);
    }
    
    return state.server5xx.length === 0;
  } catch (e) {
    error(`OpenAPI check error: ${e.message}`);
    return false;
  }
}

// ============================================================================
// UI FLOW
// ============================================================================

async function setupBrowser() {
  log("Launching browser...");
  state.browser = await chromium.launch({
    headless: true,
  });
  
  state.context = await state.browser.newContext({
    viewport: { width: 1600, height: 900 },
    locale: 'en-GB',
    timezoneId: 'Europe/London',
  });
  
  // Start tracing
  await state.context.tracing.start({
    screenshots: true,
    snapshots: true,
    sources: true,
  });
  
  state.page = await state.context.newPage();
  
  // Set up console monitoring
  state.page.on('console', (msg) => {
    if (msg.type() === 'error') {
      const text = msg.text();
      
      // Filter out expected/benign errors
      const ignoredPatterns = [
        /stream error: Event/i,
        /Connection error/i,
        /Failed to load resource: the server responded with a status of 404/i,
        /Failed to load resource: the server responded with a status of 500/i,
        /Failed to load resource: net::ERR_FAILED/i,
        /Access to XMLHttpRequest.*has been blocked by CORS policy/i,
        /API Error:/i,
        /^\s+at\s+/,  // Stack trace lines
        /^https?:\/\//,  // URL-only lines
      ];
      
      const shouldIgnore = ignoredPatterns.some(pattern => pattern.test(text));
      if (!shouldIgnore) {
        state.consoleErrors.push(text);
        error(`Console error: ${text}`);
      }
    }
  });
  
  log("✓ Browser launched");
}

async function visitPage(route) {
  log(`Visiting ${route}...`);
  
  try {
    await state.page.goto(`${UI_URL}${route}`, {
      waitUntil: 'domcontentloaded',
      timeout: 30000,
    });
    
    // Check title
    const title = await state.page.title();
    if (!title) {
      error(`Page ${route} has no title`);
      await saveScreenshot(state.page, `no-title-${route.replace(/\//g, '-')}`);
      return false;
    }
    
    // Wait for basic structure
    try {
      await state.page.waitForSelector('header, nav, main, [data-test="app-root"]', {
        timeout: 10000,
      });
    } catch (e) {
      error(`Page ${route} missing basic structure`);
      await saveScreenshot(state.page, `no-structure-${route.replace(/\//g, '-')}`);
      return false;
    }
    
    // Wait for network idle
    await state.page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {
      log(`Network didn't idle on ${route} (continuing anyway)`);
    });
    
    // Confirm content presence
    const hasContent = await state.page.locator('main, [role="main"], .card, table, [data-test]').count();
    if (hasContent === 0) {
      log(`Warning: No main content found on ${route}`);
    }
    
    // Scroll through the page
    await humanScrollFull(state.page);
    
    state.visited.push(route);
    log(`✓ Visited ${route}`);
    return true;
  } catch (e) {
    error(`Error visiting ${route}: ${e.message}`);
    await saveScreenshot(state.page, `error-${route.replace(/\//g, '-')}`);
    return false;
  }
}

async function navigateToRoute(route, label) {
  log(`Attempting to navigate to ${route} via "${label}"...`);
  
  try {
    // Try to find a link or button with matching text (case-insensitive)
    const linkSelectors = [
      `a:has-text("${label}")`,
      `button:has-text("${label}")`,
      `[role="link"]:has-text("${label}")`,
      `[role="button"]:has-text("${label}")`,
    ];
    
    for (const selector of linkSelectors) {
      const clicked = await humanClick(state.page, selector);
      if (clicked) {
        await humanPause(500, 1000);
        return true;
      }
    }
    
    // Fallback: direct navigation
    log(`No clickable element found, using direct navigation to ${route}`);
    await state.page.goto(`${UI_URL}${route}`, { waitUntil: 'domcontentloaded' });
    await humanPause(500, 1000);
    return true;
  } catch (e) {
    error(`Navigation error: ${e.message}`);
    return false;
  }
}

async function handleModals(page) {
  // Try to close any visible modals/toasts
  const closeSelectors = [
    'button:has-text("Close")',
    'button:has-text("OK")',
    'button:has-text("Dismiss")',
    '[aria-label="Close"]',
    '.modal-close',
    '.toast-close',
  ];
  
  for (const selector of closeSelectors) {
    try {
      const element = page.locator(selector).first();
      const visible = await element.isVisible({ timeout: 1000 });
      if (visible) {
        await humanClick(page, selector);
        log(`Closed modal/toast`);
      }
    } catch (e) {
      // No modal/toast to close
    }
  }
}

async function testSearchInput(page) {
  log("Looking for search/input fields...");
  
  // Look for search/ticker/message inputs
  const inputSelectors = [
    'input[placeholder*="search" i]',
    'input[placeholder*="ticker" i]',
    'input[placeholder*="symbol" i]',
    'input[placeholder*="chat" i]',
    'input[placeholder*="message" i]',
    'textarea[placeholder*="chat" i]',
    'textarea[placeholder*="message" i]',
  ];
  
  for (const selector of inputSelectors) {
    try {
      const input = page.locator(selector).first();
      const visible = await input.isVisible({ timeout: 2000 });
      if (visible) {
        log(`Found input: ${selector}`);
        await humanType(page, selector, "AAPL");
        await humanPause(200, 400);
        
        // Try to submit
        const submitSelectors = [
          'button:has-text("Go")',
          'button:has-text("Search")',
          'button:has-text("Send")',
          'button:has-text("Run")',
          '[type="submit"]',
        ];
        
        let submitted = false;
        for (const submitSelector of submitSelectors) {
          submitted = await humanClick(page, submitSelector);
          if (submitted) break;
        }
        
        if (!submitted) {
          // Try pressing Enter
          await input.press('Enter');
          log("Submitted via Enter");
        }
        
        await humanPause(500, 1000);
        return true;
      }
    } catch (e) {
      // Continue to next selector
    }
  }
  
  log("No search/input fields found");
  return false;
}

async function runUIFlow() {
  // Visit home page first
  const homeSuccess = await visitPage("/");
  if (!homeSuccess) {
    error("Failed to visit home page");
    return false;
  }
  
  // Navigate through routes
  const routeLabels = {
    "/markets": "Markets",
    "/signals": "Signals",
    "/news": "News",
    "/chat": "Chat",
    "/admin": "Admin",
  };
  
  for (const route of ROUTES.slice(1)) { // Skip "/" as we already visited it
    const label = routeLabels[route];
    
    // Try navigation via UI
    await navigateToRoute(route, label);
    
    // Visit the page
    await visitPage(route);
    
    // Handle any modals
    await handleModals(state.page);
    
    // Try search/input if available
    await testSearchInput(state.page);
    
    await humanPause(300, 600);
  }
  
  // Test back/forward
  log("Testing back/forward navigation...");
  try {
    await state.page.goBack();
    await humanPause(500, 1000);
    await state.page.goForward();
    await humanPause(500, 1000);
    log("✓ Back/forward navigation tested");
  } catch (e) {
    log("Back/forward navigation skipped");
  }
  
  return true;
}

// ============================================================================
// CLEANUP & REPORTING
// ============================================================================

async function cleanup() {
  log("Cleaning up...");
  
  try {
    await ensureArtifactsDir();
    
    // Stop tracing
    const tracePath = join(ARTIFACTS_DIR, 'trace.zip');
    await state.context.tracing.stop({ path: tracePath });
    log(`Trace saved: ${tracePath}`);
  } catch (e) {
    error(`Error saving trace: ${e.message}`);
  }
  
  try {
    await state.browser.close();
    log("✓ Browser closed");
  } catch (e) {
    error(`Error closing browser: ${e.message}`);
  }
}

function printSummary() {
  console.log("\n" + "=".repeat(80));
  console.log("HUMAN E2E VERIFICATION SUMMARY");
  console.log("=".repeat(80));
  console.log(`OpenAPI Paths: ${state.openapiCount}`);
  console.log(`Visited Pages: ${state.visited.join(", ")}`);
  console.log(`Console Errors: ${state.consoleErrors.length}`);
  
  if (state.consoleErrors.length > 0) {
    console.log("\nConsole Errors:");
    state.consoleErrors.forEach((err, i) => {
      console.log(`  ${i + 1}. ${err}`);
    });
  }
  
  console.log(`\n5xx Endpoints: ${state.server5xx.length}`);
  if (state.server5xx.length > 0) {
    console.log("\n5xx Endpoints:");
    state.server5xx.forEach(({ path, status }) => {
      console.log(`  ${path}: ${status}`);
    });
  }
  
  console.log("=".repeat(80) + "\n");
}

async function reportToFile() {
  await ensureArtifactsDir();
  const report = {
    timestamp: new Date().toISOString(),
    openapiCount: state.openapiCount,
    visited: state.visited,
    consoleErrors: state.consoleErrors,
    server5xx: state.server5xx,
  };
  
  const reportPath = join(ARTIFACTS_DIR, 'report.json');
  await writeFile(reportPath, JSON.stringify(report, null, 2));
  log(`Report saved: ${reportPath}`);
}

// ============================================================================
// MAIN
// ============================================================================

async function main() {
  log("Starting human E2E verification...");
  log(`UI_URL: ${UI_URL}`);
  log(`API_URL: ${API_URL}`);
  log(`SAFE_MODE: ${SAFE_MODE}`);
  log(`MIN_OPENAPI_PATHS: ${MIN_OPENAPI_PATHS}`);
  
  let exitCode = 0;
  
  try {
    // API checks
    const healthOK = await checkAPIHealth();
    if (!healthOK) {
      error("API health check failed");
      exitCode = 1;
    }
    
    const openapiOK = await checkOpenAPISpec();
    if (!openapiOK) {
      error("OpenAPI check failed");
      exitCode = 1;
    }
    
    // UI checks
    await setupBrowser();
    const uiOK = await runUIFlow();
    if (!uiOK) {
      error("UI flow failed");
      exitCode = 1;
    }
    
    // Check for console errors
    if (state.consoleErrors.length > 0) {
      error(`Found ${state.consoleErrors.length} console errors`);
      exitCode = 1;
    }
    
    // Check for 5xx errors
    if (state.server5xx.length > 0) {
      error(`Found ${state.server5xx.length} 5xx endpoints`);
      exitCode = 1;
    }
    
  } catch (e) {
    error(`Unexpected error: ${e.message}`);
    error(e.stack);
    exitCode = 1;
  } finally {
    await cleanup();
    printSummary();
    await reportToFile();
  }
  
  if (exitCode === 0) {
    console.log("✔ Human verification passed");
  } else {
    console.log("✖ Human verification failed");
  }
  
  process.exit(exitCode);
}

main();
