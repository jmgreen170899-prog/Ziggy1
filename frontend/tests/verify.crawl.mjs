#!/usr/bin/env node
/**
 * Human-like browser verification crawler for Ziggy frontend
 * Simulates realistic user interactions with delay, jitter, and navigation
 */

import { chromium } from '@playwright/test';
import { createWriteStream } from 'fs';
import { mkdir } from 'fs/promises';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Configuration
const CONFIG = {
  UI: "http://localhost:5173",
  API: "http://localhost:8000",
  HUMAN: {
    minDelay: 40,
    maxDelay: 140,
    scrollStep: 0.6, // viewport height fraction
    jitter: true
  },
  ROUTES: ["/", "/markets", "/signals", "/news", "/chat", "/admin"],
  SAFE_MODE: process.env.SAFE_MODE !== "false", // default true
  TIMEOUT: 25000
};

// State tracking
const RESULTS = {
  openApiPaths: 0,
  pagesVisited: [],
  selectorsConfirmed: [],
  consoleErrors: [],
  apiErrors: [],
  screenshots: [],
  success: true
};

// Utilities
function rand(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function slug(text) {
  return text.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

async function ensureArtifactsDir() {
  const artifactsPath = join(__dirname, 'artifacts');
  await mkdir(artifactsPath, { recursive: true });
  return artifactsPath;
}

// Human-like interaction helpers
async function humanPause() {
  await new Promise(resolve => setTimeout(resolve, rand(CONFIG.HUMAN.minDelay, CONFIG.HUMAN.maxDelay)));
}

async function humanMove(page, selector) {
  try {
    const element = page.locator(selector).first();
    const box = await element.boundingBox({ timeout: 5000 });
    if (!box) return false;

    // Current mouse position (start from center)
    let currentX = await page.evaluate(() => Math.floor(window.innerWidth / 2));
    let currentY = await page.evaluate(() => Math.floor(window.innerHeight / 2));

    // Target position with slight jitter
    const targetX = box.x + box.width / 2 + (CONFIG.HUMAN.jitter ? rand(-5, 5) : 0);
    const targetY = box.y + box.height / 2 + (CONFIG.HUMAN.jitter ? rand(-5, 5) : 0);

    // Move in 6-12 steps with micro jitter
    const steps = rand(6, 12);
    for (let i = 0; i <= steps; i++) {
      const progress = i / steps;
      const x = currentX + (targetX - currentX) * progress + (CONFIG.HUMAN.jitter ? rand(-2, 2) : 0);
      const y = currentY + (targetY - currentY) * progress + (CONFIG.HUMAN.jitter ? rand(-2, 2) : 0);
      
      await page.mouse.move(x, y);
      await new Promise(resolve => setTimeout(resolve, rand(10, 30)));
    }
    return true;
  } catch (error) {
    return false;
  }
}

async function humanClick(page, selector) {
  const moved = await humanMove(page, selector);
  if (!moved) return false;
  
  await humanPause();
  try {
    await page.click(selector, { timeout: 8000 });
    return true;
  } catch (error) {
    return false;
  }
}

async function humanType(page, selector, text) {
  try {
    await page.focus(selector, { timeout: 5000 });
    await humanPause();
    
    for (const char of text) {
      await page.keyboard.type(char);
      await humanPause();
    }
    return true;
  } catch (error) {
    return false;
  }
}

async function humanScrollFull(page) {
  try {
    const { scrollHeight, clientHeight } = await page.evaluate(() => ({
      scrollHeight: document.body.scrollHeight,
      clientHeight: window.innerHeight
    }));

    let currentScroll = 0;
    const scrollStep = Math.max(200, Math.floor(clientHeight * CONFIG.HUMAN.scrollStep));

    // Scroll down in chunks
    while (currentScroll < scrollHeight - clientHeight) {
      currentScroll += scrollStep;
      await page.mouse.wheel(0, scrollStep);
      await humanPause();
      
      // Small chance to pause longer (human-like reading)
      if (Math.random() < 0.1) {
        await new Promise(resolve => setTimeout(resolve, rand(500, 1500)));
      }
    }

    // Scroll back to top
    await page.mouse.wheel(0, -currentScroll);
    await humanPause();
  } catch (error) {
    console.warn('Scroll failed:', error.message);
  }
}

// Verification functions
async function verifyApiHealth(page) {
  console.log('🔍 Verifying API health...');
  
  try {
    // Check health endpoint
    const healthResponse = await page.request.get(`${CONFIG.API}/health`);
    if (!healthResponse.ok()) {
      RESULTS.apiErrors.push(`Health check failed: ${healthResponse.status()}`);
      RESULTS.success = false;
      return false;
    }
    console.log('✓ API health check passed');

    // Check OpenAPI documentation
    const openApiResponse = await page.request.get(`${CONFIG.API}/openapi.json`);
    if (!openApiResponse.ok()) {
      RESULTS.apiErrors.push(`OpenAPI fetch failed: ${openApiResponse.status()}`);
      RESULTS.success = false;
      return false;
    }

    const openApiData = await openApiResponse.json();
    const paths = Object.keys(openApiData.paths || {});
    RESULTS.openApiPaths = paths.length;
    
    if (paths.length < 140) {
      RESULTS.apiErrors.push(`Insufficient API paths: ${paths.length} < 140 (minimum for basic functionality)`);
      RESULTS.success = false;
      return false;
    }
    console.log(`✓ OpenAPI validation passed (${paths.length} paths)`);

    // Probe GET endpoints without parameters
    let probeCount = 0;
    for (const path of paths) {
      const pathData = openApiData.paths[path];
      if (pathData.get && !path.includes('{')) {
        try {
          const probeResponse = await page.request.get(`${CONFIG.API}${path}`);
          const status = probeResponse.status();
          
          if (status >= 500) {
            RESULTS.apiErrors.push(`5xx error on GET ${path}: ${status}`);
            RESULTS.success = false;
          }
          probeCount++;
          
          // Limit probes to avoid overwhelming
          if (probeCount >= 50) break;
        } catch (error) {
          // Network errors are acceptable for probing
        }
      }
    }
    console.log(`✓ Probed ${probeCount} GET endpoints`);
    
    return true;
  } catch (error) {
    RESULTS.apiErrors.push(`API verification failed: ${error.message}`);
    RESULTS.success = false;
    return false;
  }
}

async function captureFailure(page, reason, artifactsPath) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const screenshotPath = join(artifactsPath, `FAIL-${slug(reason)}-${timestamp}.png`);
  
  try {
    await page.screenshot({ path: screenshotPath, fullPage: true });
    RESULTS.screenshots.push(screenshotPath);
    console.log(`📸 Failure screenshot: ${screenshotPath}`);
  } catch (error) {
    console.warn('Failed to capture screenshot:', error.message);
  }
}

async function findNavElement(page, text) {
  const selectors = [
    `nav a:has-text("${text}")`,
    `header a:has-text("${text}")`,
    `[role="navigation"] a:has-text("${text}")`,
    `a:has-text("${text}")`,
    `button:has-text("${text}")`,
    `[data-nav] a:has-text("${text}")`,
    `[data-test*="nav"] a:has-text("${text}")`
  ];

  for (const selector of selectors) {
    try {
      const element = page.locator(selector).first();
      if (await element.isVisible({ timeout: 1000 })) {
        return selector;
      }
    } catch {
      continue;
    }
  }
  return null;
}

async function waitForContent(page, route) {
  // Wait for page to load
  await page.waitForLoadState('domcontentloaded');
  
  // Look for content indicators
  const contentSelectors = [
    '[data-test]',
    'main',
    'h1',
    'h2',
    'table',
    '.card',
    '[class*="card"]',
    'section',
    'article',
    '[role="main"]'
  ];

  let foundContent = false;
  for (const selector of contentSelectors) {
    try {
      const element = page.locator(selector).first();
      if (await element.isVisible({ timeout: 3000 })) {
        RESULTS.selectorsConfirmed.push(`${route}: ${selector}`);
        foundContent = true;
        break;
      }
    } catch {
      continue;
    }
  }

  if (!foundContent) {
    console.warn(`⚠️ No content selectors found for ${route}`);
  }

  return foundContent;
}

async function handleModalsAndToasts(page) {
  // Check for modals and close them
  const modalSelectors = [
    '[role="dialog"]',
    '[data-modal]',
    '.modal',
    '[class*="modal"]'
  ];

  for (const selector of modalSelectors) {
    try {
      const modal = page.locator(selector).first();
      if (await modal.isVisible({ timeout: 1000 })) {
        // Try to find close button
        const closeSelectors = [
          `${selector} button:has-text("Close")`,
          `${selector} button:has-text("OK")`,
          `${selector} button:has-text("×")`,
          `${selector} [aria-label="Close"]`,
          `${selector} .close`
        ];

        let closed = false;
        for (const closeSelector of closeSelectors) {
          if (await humanClick(page, closeSelector)) {
            console.log('✓ Closed modal');
            closed = true;
            break;
          }
        }

        if (!closed) {
          // Try Escape key
          await page.keyboard.press('Escape');
        }
      }
    } catch {
      continue;
    }
  }
}

async function interactWithForms(page, route) {
  if (!CONFIG.SAFE_MODE) {
    console.log('⚠️ SAFE_MODE disabled - skipping form interactions');
    return;
  }

  // Find search inputs
  const searchSelectors = [
    'input[type="search"]',
    'input[placeholder*="search" i]',
    'input[placeholder*="ticker" i]',
    'input[placeholder*="symbol" i]',
    'input[placeholder*="chat" i]',
    'input[placeholder*="message" i]'
  ];

  for (const selector of searchSelectors) {
    try {
      const input = page.locator(selector).first();
      if (await input.isVisible({ timeout: 2000 })) {
        const placeholder = await input.getAttribute('placeholder') || '';
        
        let testValue = 'AAPL';
        if (placeholder.toLowerCase().includes('chat') || placeholder.toLowerCase().includes('message')) {
          testValue = 'hello';
        }

        if (await humanType(page, selector, testValue)) {
          console.log(`✓ Typed "${testValue}" into ${selector}`);
          
          // Try to submit
          const submitSelectors = [
            'button:has-text("Go")',
            'button:has-text("Search")',
            'button:has-text("Send")',
            'button:has-text("Run")',
            '[type="submit"]'
          ];

          let submitted = false;
          for (const submitSelector of submitSelectors) {
            if (await humanClick(page, submitSelector)) {
              console.log('✓ Submitted form');
              submitted = true;
              break;
            }
          }

          if (!submitted) {
            // Try Enter key
            await page.keyboard.press('Enter');
            await humanPause();
          }

          // Wait for potential response
          await new Promise(resolve => setTimeout(resolve, 2000));
        }
        break; // Only interact with first found input
      }
    } catch {
      continue;
    }
  }
}

async function checkSafetyGuards(page, selector) {
  if (!CONFIG.SAFE_MODE) return true;

  try {
    const element = page.locator(selector).first();
    const text = await element.textContent() || '';
    
    const dangerousPatterns = /delete|remove|drop|panic|trade|order|sell|buy/i;
    if (dangerousPatterns.test(text)) {
      console.log(`⚠️ SAFE_MODE: Skipping dangerous action: "${text}"`);
      return false;
    }
  } catch {
    // If we can't read the text, err on the side of caution
    return false;
  }

  return true;
}

// Main crawler
async function runHumanVerification() {
  console.log('🚀 Starting human-like verification crawler...');
  console.log(`📋 Config: UI=${CONFIG.UI}, API=${CONFIG.API}, SAFE_MODE=${CONFIG.SAFE_MODE}`);
  
  const artifactsPath = await ensureArtifactsDir();
  let browser, context, page;

  try {
    // Launch browser with human-like configuration
    browser = await chromium.launch({
      headless: process.env.CI === 'true', // Show browser locally
      slowMo: CONFIG.HUMAN.jitter ? rand(50, 100) : 0
    });

    context = await browser.newContext({
      viewport: { width: 1600, height: 900 },
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      locale: 'en-GB',
      timezoneId: 'Europe/London',
      permissions: [], // No geolocation
      deviceScaleFactor: 1
    });

    // Start tracing for debugging
    await context.tracing.start({
      screenshots: true,
      snapshots: true,
      sources: true
    });

    page = await context.newPage();
    page.setDefaultTimeout(CONFIG.TIMEOUT);

    // Console error monitoring
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        RESULTS.consoleErrors.push(msg.text());
        RESULTS.success = false;
      }
    });

    // API verification first
    if (!await verifyApiHealth(page)) {
      await captureFailure(page, 'api-health-failed', artifactsPath);
      throw new Error('API health verification failed');
    }

    // Visit UI root
    console.log(`🌐 Navigating to ${CONFIG.UI}...`);
    await page.goto(CONFIG.UI, { waitUntil: 'domcontentloaded' });
    RESULTS.pagesVisited.push('/');

    // Check title
    const title = await page.title();
    if (!title || title.trim() === '') {
      RESULTS.success = false;
      await captureFailure(page, 'empty-title', artifactsPath);
      throw new Error('Page title is empty');
    }
    console.log(`✓ Page title: "${title}"`);

    // Wait for app shell
    const appShellSelectors = ['header', 'nav', '[data-test="app-root"]', 'main', '[role="banner"]'];
    let appShellFound = false;
    
    for (const selector of appShellSelectors) {
      try {
        await page.waitForSelector(selector, { timeout: 5000 });
        RESULTS.selectorsConfirmed.push(`/: ${selector}`);
        appShellFound = true;
        break;
      } catch {
        continue;
      }
    }

    if (!appShellFound) {
      RESULTS.success = false;
      await captureFailure(page, 'no-app-shell', artifactsPath);
      throw new Error('No app shell elements found');
    }

    // Navigate through routes like a human
    for (const route of CONFIG.ROUTES) {
      if (route === '/') continue; // Already visited
      
      console.log(`📍 Navigating to ${route}...`);
      
      // Try UI navigation first
      const routeName = route.slice(1) || 'home';
      const navSelector = await findNavElement(page, routeName);
      
      let navigated = false;
      if (navSelector && await checkSafetyGuards(page, navSelector)) {
        navigated = await humanClick(page, navSelector);
        if (navigated) {
          console.log(`✓ Used UI navigation for ${route}`);
          await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});
        }
      }

      // Fallback to direct navigation
      if (!navigated) {
        try {
          await page.goto(`${CONFIG.UI}${route}`, { waitUntil: 'domcontentloaded' });
          console.log(`✓ Direct navigation to ${route}`);
        } catch (error) {
          if (error.message.includes('404')) {
            console.log(`⚠️ Skipping ${route} (404)`);
            continue;
          }
          throw error;
        }
      }

      RESULTS.pagesVisited.push(route);

      // Wait for content and verify
      await waitForContent(page, route);
      await handleModalsAndToasts(page);
      
      // Scroll through page like a human
      await humanScrollFull(page);
      
      // Interact with forms if present
      await interactWithForms(page, route);
      
      // Random pause between pages
      await new Promise(resolve => setTimeout(resolve, rand(1000, 3000)));
    }

    // Test browser navigation
    console.log('🔄 Testing browser navigation...');
    await page.goBack();
    await humanPause();
    await page.goForward();
    await humanPause();

    console.log('✅ Human verification completed successfully');

  } catch (error) {
    console.error('❌ Verification failed:', error.message);
    RESULTS.success = false;
    
    if (page) {
      await captureFailure(page, 'verification-failed', artifactsPath);
    }
  } finally {
    // Save tracing
    if (context) {
      try {
        await context.tracing.stop({ path: join(artifactsPath, 'trace.zip') });
        console.log(`💾 Trace saved to artifacts/trace.zip`);
      } catch (error) {
        console.warn('Failed to save trace:', error.message);
      }
    }

    if (browser) {
      await browser.close();
    }
  }

  // Final report
  console.log('\n📊 VERIFICATION SUMMARY');
  console.log('========================');
  console.log(`OpenAPI paths: ${RESULTS.openApiPaths}`);
  console.log(`Pages visited: ${RESULTS.pagesVisited.join(', ')}`);
  console.log(`Selectors confirmed: ${RESULTS.selectorsConfirmed.length}`);
  
  if (RESULTS.consoleErrors.length > 0) {
    console.log(`Console errors: ${RESULTS.consoleErrors.length}`);
    RESULTS.consoleErrors.forEach(error => console.log(`  - ${error}`));
  }
  
  if (RESULTS.apiErrors.length > 0) {
    console.log(`API errors: ${RESULTS.apiErrors.length}`);
    RESULTS.apiErrors.forEach(error => console.log(`  - ${error}`));
  }

  if (RESULTS.screenshots.length > 0) {
    console.log(`Failure screenshots: ${RESULTS.screenshots.length}`);
  }

  if (RESULTS.success) {
    console.log('\n✅ Human verification passed');
    process.exit(0);
  } else {
    console.log('\n❌ Human verification failed');
    process.exit(1);
  }
}

// Run unconditionally - this is a script, not a module
console.log('🎯 Crawler script starting...');
runHumanVerification().catch(error => {
  console.error('❌ Fatal error:', error);
  process.exit(1);
});