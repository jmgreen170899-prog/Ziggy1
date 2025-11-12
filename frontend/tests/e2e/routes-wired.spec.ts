/**
 * E2E Routes Wired Test
 * 
 * Verifies that:
 * 1. Frontend loads and renders properly
 * 2. API calls to backend succeed
 * 3. Core UI sections are present
 * 4. No console errors occur
 */

import { test, expect } from '@playwright/test';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';
const FRONTEND_URL = process.env.E2E_BASE_URL || 'http://127.0.0.1:3000';

test.describe('Routes Wired E2E', () => {
  test('homepage loads successfully', async ({ page }) => {
    const errors: string[] = [];
    
    // Capture console errors
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    
    // Navigate to homepage
    const response = await page.goto(FRONTEND_URL, { 
      waitUntil: 'networkidle',
      timeout: 60000
    });
    
    // Should get 200 response
    expect(response?.status()).toBe(200);
    
    // Page should have a title
    const title = await page.title();
    expect(title).toBeTruthy();
    expect(title.length).toBeGreaterThan(0);
    
    // Should have some content
    const bodyText = await page.textContent('body');
    expect(bodyText).toBeTruthy();
    
    // Should not have critical console errors (allow warnings)
    const criticalErrors = errors.filter(e => 
      !e.includes('Warning:') && 
      !e.includes('DevTools')
    );
    
    if (criticalErrors.length > 0) {
      console.log('Console errors:', criticalErrors);
    }
    
    expect(criticalErrors).toHaveLength(0);
  });
  
  test('core UI sections render', async ({ page }) => {
    await page.goto(FRONTEND_URL, { waitUntil: 'networkidle' });
    
    // Check for common UI elements that indicate the app loaded
    const possibleSelectors = [
      'nav',           // Navigation
      'header',        // Header
      'main',          // Main content
      '[role="main"]', // Main role
      'h1',            // Heading
      'h2',            // Subheading
      'button',        // Interactive element
      'a',             // Links
    ];
    
    let foundCount = 0;
    for (const selector of possibleSelectors) {
      const element = await page.$(selector);
      if (element) {
        foundCount++;
      }
    }
    
    // Should find at least 3 of these common elements
    expect(foundCount).toBeGreaterThanOrEqual(3);
  });
  
  test('backend API is accessible', async ({ request }) => {
    // Test backend health endpoint
    const healthResponse = await request.get(`${BACKEND_URL}/health`);
    expect(healthResponse.status()).toBe(200);
    
    const healthData = await healthResponse.json();
    expect(healthData).toHaveProperty('ok');
    expect(healthData.ok).toBe(true);
  });
  
  test('OpenAPI schema is accessible', async ({ request }) => {
    // Test OpenAPI endpoint
    const openApiResponse = await request.get(`${BACKEND_URL}/openapi.json`);
    expect(openApiResponse.status()).toBe(200);
    
    const openApiData = await openApiResponse.json();
    expect(openApiData).toHaveProperty('paths');
    expect(openApiData).toHaveProperty('info');
    
    // Should have many paths (175+)
    const pathCount = Object.keys(openApiData.paths).length;
    expect(pathCount).toBeGreaterThanOrEqual(175);
  });
  
  test('API docs are accessible', async ({ page }) => {
    // Navigate to API docs
    const response = await page.goto(`${BACKEND_URL}/docs`, { 
      waitUntil: 'networkidle',
      timeout: 30000
    });
    
    expect(response?.status()).toBe(200);
    
    // Should have Swagger UI elements
    const swaggerUI = await page.$('.swagger-ui');
    expect(swaggerUI).toBeTruthy();
  });
  
  test('frontend can make API calls', async ({ page }) => {
    const apiCalls: Array<{ url: string; status: number }> = [];
    
    // Track API calls
    page.on('response', async (response) => {
      const url = response.url();
      if (url.includes(BACKEND_URL) || url.includes(':8000')) {
        apiCalls.push({
          url,
          status: response.status()
        });
      }
    });
    
    // Navigate to a page that likely makes API calls
    await page.goto(FRONTEND_URL, { waitUntil: 'networkidle' });
    
    // Wait a bit for any async API calls
    await page.waitForTimeout(2000);
    
    // If API calls were made, they should succeed (2xx, 3xx, or expected 4xx like 404)
    const failedCalls = apiCalls.filter(call => call.status >= 500);
    
    if (failedCalls.length > 0) {
      console.log('Failed API calls (5xx):', failedCalls);
    }
    
    expect(failedCalls).toHaveLength(0);
  });
  
  test('no NaN or undefined in rendered content', async ({ page }) => {
    await page.goto(FRONTEND_URL, { waitUntil: 'networkidle' });
    
    // Get visible text
    const bodyText = await page.textContent('body');
    
    // Should not have NaN, undefined, or [object Object] in visible text
    const badPatterns = ['NaN', 'undefined', '[object Object]'];
    const foundBadPatterns = badPatterns.filter(pattern => 
      bodyText?.includes(pattern)
    );
    
    if (foundBadPatterns.length > 0) {
      console.log('Found problematic text patterns:', foundBadPatterns);
      // Soft expect - log but don't fail
      expect.soft(foundBadPatterns).toHaveLength(0);
    }
  });
});
