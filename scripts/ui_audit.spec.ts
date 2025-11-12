import { test, expect, Page } from '@playwright/test';
import * as path from 'path';
import * as fs from 'fs';

interface TabAuditData {
  tabName: string;
  route: string;
  timestamp: string;
  dataMetrics: {
    totalElements: number;
    dataCards: number;
    dataRows: number;
    missingFields: string[];
    nanValues: string[];
    staleTimestamps: string[];
    emptyStates: string[];
  };
  layoutIssues: {
    overflowElements: string[];
    hiddenElements: string[];
    responsiveIssues: string[];
  };
  consoleErrors: string[];
  loadTimes: {
    domContentLoaded: number;
    networkIdle: number;
    dataLoaded: number;
  };
  screenshotPath: string;
}

interface UIAuditReport {
  timestamp: string;
  environment: {
    backendUrl: string;
    frontendUrl: string;
    userAgent: string;
    viewport: { width: number; height: number };
  };
  tabs: TabAuditData[];
  summary: {
    totalTabs: number;
    totalIssues: number;
    criticalIssues: number;
  };
}

// Define all ZiggyAI routes to audit
const ROUTES_TO_AUDIT = [
  { name: 'Dashboard', path: '/' },
  { name: 'Chat', path: '/chat' },
  { name: 'Market', path: '/market' },
  { name: 'Alerts', path: '/alerts' },
  { name: 'Portfolio', path: '/portfolio' },
  { name: 'Trading', path: '/trading' },
  { name: 'Predictions', path: '/predictions' },
  { name: 'News', path: '/news' },
  { name: 'Paper-Trading', path: '/paper-trading' },
  { name: 'Paper-Status', path: '/paper/status' },
  { name: 'Live', path: '/live' },
  { name: 'Crypto', path: '/crypto' },
  { name: 'Learning', path: '/learning' },
  { name: 'Account', path: '/account' }
];

// Data selectors for common ZiggyAI components
const DATA_SELECTORS = {
  dataCards: '[data-testid*="card"], .card, [class*="card"]',
  dataRows: '[data-testid*="row"], tr, .row',
  loadingStates: '[data-testid="loading"], .loading, [class*="loading"]',
  errorStates: '[data-testid="error"], .error, [class*="error"]',
  emptyStates: '[data-testid="empty"], .empty, [class*="empty"]',
  timestamps: '[data-testid*="time"], [class*="time"], .timestamp',
  prices: '[data-testid*="price"], [class*="price"], .price',
  percentages: '[data-testid*="percent"], [class*="percent"]'
};

async function captureConsoleErrors(page: Page): Promise<string[]> {
  const errors: string[] = [];
  
  page.on('console', msg => {
    if (msg.type() === 'error') {
      errors.push(msg.text());
    }
  });
  
  page.on('pageerror', error => {
    errors.push(`Page Error: ${error.message}`);
  });
  
  return errors;
}

async function analyzeDataQuality(page: Page): Promise<TabAuditData['dataMetrics']> {
  return await page.evaluate((selectors) => {
    const metrics = {
      totalElements: 0,
      dataCards: 0,
      dataRows: 0,
      missingFields: [],
      nanValues: [],
      staleTimestamps: [],
      emptyStates: []
    };
    
    // Count data elements
    metrics.dataCards = document.querySelectorAll(selectors.dataCards).length;
    metrics.dataRows = document.querySelectorAll(selectors.dataRows).length;
    metrics.totalElements = document.querySelectorAll('*').length;
    
    // Check for NaN/Infinity values in text content
    const textElements = document.querySelectorAll(selectors.prices + ', ' + selectors.percentages);
    textElements.forEach(el => {
      const text = el.textContent || '';
      if (text.includes('NaN') || text.includes('Infinity') || text.includes('undefined')) {
        metrics.nanValues.push(`${el.tagName}.${el.className}: ${text}`);
      }
    });
    
    // Check for stale timestamps (older than 1 hour)
    const timestampElements = document.querySelectorAll(selectors.timestamps);
    const oneHourAgo = Date.now() - (60 * 60 * 1000);
    timestampElements.forEach(el => {
      const text = el.textContent || '';
      const timestamp = new Date(text).getTime();
      if (timestamp && timestamp < oneHourAgo) {
        metrics.staleTimestamps.push(`${el.tagName}.${el.className}: ${text}`);
      }
    });
    
    // Check for empty states
    const emptyElements = document.querySelectorAll(selectors.emptyStates);
    emptyElements.forEach(el => {
      if (el.textContent?.trim()) {
        metrics.emptyStates.push(el.textContent.trim());
      }
    });
    
    // Check for missing data fields (elements with no content)
    const dataElements = document.querySelectorAll('[data-testid], [class*="data-"]');
    dataElements.forEach(el => {
      if (!el.textContent?.trim() && !el.querySelector('svg, img')) {
        metrics.missingFields.push(`${el.tagName}.${el.className}`);
      }
    });
    
    return metrics;
  }, DATA_SELECTORS);
}

async function analyzeLayoutIssues(page: Page): Promise<TabAuditData['layoutIssues']> {
  return await page.evaluate(() => {
    const issues = {
      overflowElements: [],
      hiddenElements: [],
      responsiveIssues: []
    };
    
    // Check for horizontal overflow
    const allElements = document.querySelectorAll('*');
    allElements.forEach(el => {
      const rect = el.getBoundingClientRect();
      if (rect.right > window.innerWidth) {
        issues.overflowElements.push(`${el.tagName}.${el.className}`);
      }
      
      // Check for completely hidden elements
      if (rect.width === 0 && rect.height === 0 && el.textContent?.trim()) {
        issues.hiddenElements.push(`${el.tagName}.${el.className}`);
      }
    });
    
    // Check for responsive issues (elements too small on mobile-like viewport)
    if (window.innerWidth < 768) {
      const smallElements = document.querySelectorAll('button, input, a');
      smallElements.forEach(el => {
        const rect = el.getBoundingClientRect();
        if (rect.width < 44 || rect.height < 44) {
          issues.responsiveIssues.push(`Touch target too small: ${el.tagName}.${el.className}`);
        }
      });
    }
    
    return issues;
  });
}

async function waitForDataLoad(page: Page, timeout: number = 10000): Promise<number> {
  const startTime = Date.now();
  
  try {
    // Wait for common loading indicators to disappear
    await page.waitForFunction(
      (selectors) => {
        const loadingElements = document.querySelectorAll(selectors.loadingStates);
        return loadingElements.length === 0 || 
               Array.from(loadingElements).every(el => 
                 getComputedStyle(el).display === 'none' || 
                 !el.textContent?.trim()
               );
      },
      DATA_SELECTORS,
      { timeout }
    );
  } catch (e) {
    // Continue if loading indicators don't disappear
  }
  
  // Wait for network to be mostly idle
  try {
    await page.waitForLoadState('networkidle', { timeout: 5000 });
  } catch (e) {
    // Continue if network doesn't go idle
  }
  
  return Date.now() - startTime;
}

test.describe('ZiggyAI UI Audit', () => {
  let auditReport: UIAuditReport;
  let consoleErrors: string[] = [];

  test.beforeAll(async () => {
    auditReport = {
      timestamp: new Date().toISOString(),
      environment: {
        backendUrl: 'http://localhost:8000',
        frontendUrl: 'http://localhost:3000',
        userAgent: '',
        viewport: { width: 1920, height: 1080 }
      },
      tabs: [],
      summary: {
        totalTabs: ROUTES_TO_AUDIT.length,
        totalIssues: 0,
        criticalIssues: 0
      }
    };
  });

  for (const route of ROUTES_TO_AUDIT) {
    test(`Audit ${route.name} tab`, async ({ page, browser }) => {
      const tabData: TabAuditData = {
        tabName: route.name,
        route: route.path,
        timestamp: new Date().toISOString(),
        dataMetrics: {
          totalElements: 0,
          dataCards: 0,
          dataRows: 0,
          missingFields: [],
          nanValues: [],
          staleTimestamps: [],
          emptyStates: []
        },
        layoutIssues: {
          overflowElements: [],
          hiddenElements: [],
          responsiveIssues: []
        },
        consoleErrors: [],
        loadTimes: {
          domContentLoaded: 0,
          networkIdle: 0,
          dataLoaded: 0
        },
        screenshotPath: `artifacts/ui/${route.name.toLowerCase()}.png`
      };

      // Set up console error capture
      const routeErrors: string[] = [];
      page.on('console', msg => {
        if (msg.type() === 'error') {
          routeErrors.push(msg.text());
        }
      });

      page.on('pageerror', error => {
        routeErrors.push(`Page Error: ${error.message}`);
      });

      // Set viewport and user agent
      await page.setViewportSize({ width: 1920, height: 1080 });
      auditReport.environment.userAgent = await page.evaluate(() => navigator.userAgent);

      const startTime = Date.now();

      try {
        // Navigate to the route
        await page.goto(`http://localhost:3000${route.path}`, {
          waitUntil: 'domcontentloaded',
          timeout: 30000
        });

        tabData.loadTimes.domContentLoaded = Date.now() - startTime;

        // Wait for data to load
        tabData.loadTimes.dataLoaded = await waitForDataLoad(page, 15000);

        // Wait for network idle
        try {
          await page.waitForLoadState('networkidle', { timeout: 10000 });
          tabData.loadTimes.networkIdle = Date.now() - startTime;
        } catch (e) {
          tabData.loadTimes.networkIdle = Date.now() - startTime;
        }

        // Additional wait for React components to fully render
        await page.waitForTimeout(2000);

        // Analyze data quality
        tabData.dataMetrics = await analyzeDataQuality(page);

        // Analyze layout issues
        tabData.layoutIssues = await analyzeLayoutIssues(page);

        // Capture console errors
        tabData.consoleErrors = routeErrors;

        // Take full-page screenshot
        const screenshotPath = path.resolve(tabData.screenshotPath);
        await page.screenshot({
          path: screenshotPath,
          fullPage: true,
          type: 'png'
        });

        console.log(`✅ Audited ${route.name}: ${tabData.dataMetrics.dataCards} cards, ${tabData.dataMetrics.dataRows} rows, ${tabData.consoleErrors.length} errors`);

      } catch (error) {
        console.error(`❌ Failed to audit ${route.name}:`, error);
        tabData.consoleErrors.push(`Navigation Error: ${error.message}`);
        
        // Still try to take a screenshot of the error state
        try {
          await page.screenshot({
            path: path.resolve(tabData.screenshotPath),
            fullPage: true,
            type: 'png'
          });
        } catch (screenshotError) {
          console.error(`Failed to capture error screenshot for ${route.name}`);
        }
      }

      // Add tab data to report
      auditReport.tabs.push(tabData);
    });
  }

  test.afterAll(async () => {
    // Calculate summary statistics
    auditReport.summary.totalIssues = auditReport.tabs.reduce((total, tab) => {
      return total + 
        tab.dataMetrics.missingFields.length +
        tab.dataMetrics.nanValues.length +
        tab.dataMetrics.staleTimestamps.length +
        tab.layoutIssues.overflowElements.length +
        tab.layoutIssues.hiddenElements.length +
        tab.layoutIssues.responsiveIssues.length +
        tab.consoleErrors.length;
    }, 0);

    auditReport.summary.criticalIssues = auditReport.tabs.reduce((total, tab) => {
      return total + 
        tab.dataMetrics.nanValues.length +
        tab.layoutIssues.overflowElements.length +
        tab.consoleErrors.filter(err => err.includes('Error:')).length;
    }, 0);

    // Save audit report
    const reportPath = path.resolve('artifacts/ui/ui_audit.json');
    fs.writeFileSync(reportPath, JSON.stringify(auditReport, null, 2));
    
    console.log(`\n📊 UI Audit Complete!`);
    console.log(`📁 Report saved to: ${reportPath}`);
    console.log(`📸 Screenshots saved to: artifacts/ui/`);
    console.log(`🔍 Total tabs audited: ${auditReport.summary.totalTabs}`);
    console.log(`⚠️  Total issues found: ${auditReport.summary.totalIssues}`);
    console.log(`🚨 Critical issues: ${auditReport.summary.criticalIssues}`);
  });
});