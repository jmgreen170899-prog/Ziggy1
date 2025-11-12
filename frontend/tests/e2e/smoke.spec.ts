import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';

const ROOT = path.resolve(__dirname, '../../..');
const OUT_DIR = path.join(ROOT, 'tools', 'out');
const IN_FILE = path.join(OUT_DIR, 'frontend-calls.json');
const ARTIFACTS_DIR = path.resolve(__dirname, '../artifacts');

function sanitizeRoute(route: string) {
  return route.replace(/[^a-zA-Z0-9-_]+/g, '_') || 'root';
}

function loadRoutes(): string[] {
  try {
    const data = JSON.parse(fs.readFileSync(IN_FILE, 'utf8'));
    return data.routes || ['/'];
  } catch {
    return ['/'];
  }
}

const ROUTES = loadRoutes();

for (const route of ROUTES) {
  test.describe(`Route ${route}`, () => {
    test(`should render and have healthy network`, async ({ browser }) => {
      const harPath = path.join(ARTIFACTS_DIR, `${sanitizeRoute(route)}.har`);
      const screenshotPath = path.join(ARTIFACTS_DIR, `${sanitizeRoute(route)}.png`);
      const context = await browser.newContext({
        recordHar: { path: harPath, content: 'embed' },
        ignoreHTTPSErrors: true,
      });
      const page = await context.newPage();

      const badRequests: Array<{url: string; status: number; method: string}> = [];

      page.on('response', async (resp) => {
        try {
          const url = resp.url();
          const status = resp.status();
          const req = resp.request();
          const method = req.method();
          if (req.resourceType() === 'xhr' || req.resourceType() === 'fetch') {
            if (!(status >= 200 && status < 400)) {
              badRequests.push({ url, status, method });
            }
          }
        } catch {}
      });

      const url = `http://127.0.0.1:3000${route}`;
      await page.goto(url, { waitUntil: 'networkidle', timeout: 60_000 });

      // Basic presence checks (TODO: refine per app)
      const selectors = [
        'h1, h2',
        '[role="table"], table',
        '[data-testid], .card, .panel'
      ];
      let foundAny = false;
      for (const sel of selectors) {
        const el = await page.$(sel);
        if (el) { foundAny = true; break; }
      }
      expect(foundAny, 'Expected core UI selectors to be present').toBeTruthy();

      // Look for NaN/undefined/null in visible text
      const bodyText = await page.textContent('body');
      if (bodyText && /(NaN|undefined|null)/i.test(bodyText)) {
        test.info().annotations.push({ type: 'data-warning', description: 'Found NaN/undefined/null in page text' });
      }

      if (badRequests.length) {
        await page.screenshot({ path: screenshotPath, fullPage: true });
      }

      // Assert no 4xx/5xx for XHR/fetch
      if (badRequests.length) {
        console.error('Bad network requests:', badRequests);
      }
      expect.soft(badRequests, 'No XHR/fetch should fail with 4xx/5xx').toEqual([]);

      await context.close();
    });
  });
}
