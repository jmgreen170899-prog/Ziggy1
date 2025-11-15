import { test, expect, Page } from "@playwright/test";
import { promises as fs } from "fs";
import path from "path";

interface RouteAuditResult {
  route: string;
  url: string;
  timestamp: string;
  screenshot: string;
  metrics: {
    cardCount: number;
    tableCount: number;
    nanCells: number;
    infinityCells: number;
    missingFields: string[];
    staleBadges: number;
    consoleErrors: string[];
    networkErrors: string[];
    loadTime: number;
  };
  status: "success" | "error" | "timeout";
  error?: string;
}

const ROUTES = [
  { name: "home", path: "/", dataSelector: '[data-testid="dashboard"]' },
  {
    name: "chat",
    path: "/chat",
    dataSelector: '[data-testid="chat-interface"]',
  },
  {
    name: "market",
    path: "/market",
    dataSelector: '[data-testid="market-data"]',
  },
  {
    name: "alerts",
    path: "/alerts",
    dataSelector: '[data-testid="alerts-list"]',
  },
  {
    name: "paper-trading",
    path: "/paper",
    dataSelector: '[data-testid="paper-trading"]',
  },
  {
    name: "portfolio",
    path: "/portfolio",
    dataSelector: '[data-testid="portfolio"]',
  },
  {
    name: "settings",
    path: "/settings",
    dataSelector: '[data-testid="settings"]',
  },
  {
    name: "status",
    path: "/status",
    dataSelector: '[data-testid="status-page"]',
  },
];

async function ensureArtifactsDir() {
  const artifactsDir = path.join(process.cwd(), "artifacts", "ui");
  try {
    await fs.mkdir(artifactsDir, { recursive: true });
  } catch (error) {
    console.warn("Could not create artifacts directory:", error);
  }
  return artifactsDir;
}

async function captureConsoleErrors(page: Page): Promise<string[]> {
  const errors: string[] = [];

  page.on("console", (msg) => {
    if (msg.type() === "error") {
      errors.push(msg.text());
    }
  });

  page.on("pageerror", (error) => {
    errors.push(`Page Error: ${error.message}`);
  });

  return errors;
}

async function captureNetworkErrors(page: Page): Promise<string[]> {
  const errors: string[] = [];

  page.on("response", (response) => {
    if (response.status() >= 400) {
      errors.push(`${response.status()} - ${response.url()}`);
    }
  });

  page.on("requestfailed", (request) => {
    errors.push(`Failed: ${request.url()} - ${request.failure()?.errorText}`);
  });

  return errors;
}

async function analyzePageContent(
  page: Page,
): Promise<RouteAuditResult["metrics"]> {
  const metrics = await page.evaluate(() => {
    // Count cards (common patterns)
    const cardSelectors = [
      '[data-testid*="card"]',
      ".card",
      '[class*="card"]',
      '[role="article"]',
      ".bg-white.rounded",
      ".bg-gray-50.rounded",
    ];

    const cardCount = cardSelectors.reduce((count, selector) => {
      return count + document.querySelectorAll(selector).length;
    }, 0);

    // Count tables
    const tableCount = document.querySelectorAll(
      'table, [role="table"], [data-testid*="table"]',
    ).length;

    // Check for NaN and Infinity values in text content
    const allText = document.body.textContent || "";
    const nanCells = (allText.match(/\bNaN\b/g) || []).length;
    const infinityCells = (allText.match(/\bInfinity\b/g) || []).length;

    // Check for missing field indicators
    const missingFields: string[] = [];
    const missingIndicators = document.querySelectorAll(
      '[data-testid*="missing"], .text-gray-400, .opacity-50',
    );
    missingIndicators.forEach((el, index) => {
      const text = el.textContent?.trim();
      if (
        text &&
        (text.includes("--") ||
          text.includes("N/A") ||
          text.includes("Loading") ||
          text === "")
      ) {
        missingFields.push(`Element ${index}: ${text}`);
      }
    });

    // Count stale badges or TTL indicators
    const staleBadges = document.querySelectorAll(
      '[data-testid*="stale"], [class*="stale"], .text-red-500',
    ).length;

    return {
      cardCount,
      tableCount,
      nanCells,
      infinityCells,
      missingFields,
      staleBadges,
      loadTime: performance.now(),
    };
  });

  return {
    ...metrics,
    consoleErrors: [],
    networkErrors: [],
  };
}

test.describe("UI Audit - Route Health Check", () => {
  let artifactsDir: string;
  let auditResults: RouteAuditResult[] = [];

  test.beforeAll(async () => {
    artifactsDir = await ensureArtifactsDir();
  });

  test.afterAll(async () => {
    // Save comprehensive audit results
    const reportPath = path.join(artifactsDir, "ui_audit_results.json");
    await fs.writeFile(reportPath, JSON.stringify(auditResults, null, 2));

    // Generate summary report
    const summary = {
      timestamp: new Date().toISOString(),
      totalRoutes: ROUTES.length,
      successfulRoutes: auditResults.filter((r) => r.status === "success")
        .length,
      failedRoutes: auditResults.filter((r) => r.status === "error").length,
      timeoutRoutes: auditResults.filter((r) => r.status === "timeout").length,
      totalIssues: auditResults.reduce(
        (sum, r) =>
          sum +
          r.metrics.nanCells +
          r.metrics.infinityCells +
          r.metrics.missingFields.length +
          r.metrics.consoleErrors.length +
          r.metrics.networkErrors.length,
        0,
      ),
      routes: auditResults.map((r) => ({
        name: r.route,
        status: r.status,
        issues:
          r.metrics.nanCells +
          r.metrics.infinityCells +
          r.metrics.missingFields.length +
          r.metrics.consoleErrors.length +
          r.metrics.networkErrors.length,
      })),
    };

    await fs.writeFile(
      path.join(artifactsDir, "ui_audit_summary.json"),
      JSON.stringify(summary, null, 2),
    );
  });

  for (const route of ROUTES) {
    test(`Route: ${route.name} (${route.path})`, async ({ page }) => {
      const startTime = Date.now();
      const result: RouteAuditResult = {
        route: route.name,
        url: route.path,
        timestamp: new Date().toISOString(),
        screenshot: `${route.name}.png`,
        metrics: {
          cardCount: 0,
          tableCount: 0,
          nanCells: 0,
          infinityCells: 0,
          missingFields: [],
          staleBadges: 0,
          consoleErrors: [],
          networkErrors: [],
          loadTime: 0,
        },
        status: "success",
      };

      try {
        // Set up error capturing
        const consoleErrors = await captureConsoleErrors(page);
        const networkErrors = await captureNetworkErrors(page);

        // Navigate to route
        await page.goto(route.path, {
          waitUntil: "networkidle",
          timeout: 30000,
        });

        // Wait for critical data elements to load
        try {
          await page.waitForSelector(route.dataSelector, { timeout: 10000 });
        } catch (error) {
          console.warn(
            `Data selector not found for ${route.name}: ${route.dataSelector}`,
          );
        }

        // Additional wait for dynamic content
        await page.waitForTimeout(2000);

        // Analyze page content
        result.metrics = await analyzePageContent(page);
        result.metrics.consoleErrors = consoleErrors;
        result.metrics.networkErrors = networkErrors;
        result.metrics.loadTime = Date.now() - startTime;

        // Take full page screenshot
        const screenshotPath = path.join(artifactsDir, result.screenshot);
        await page.screenshot({
          path: screenshotPath,
          fullPage: true,
          animations: "disabled",
        });

        // Validate critical elements are present
        const hasContent = await page.evaluate(() => {
          const body = document.body.textContent || "";
          return body.length > 100; // Basic content check
        });

        if (!hasContent) {
          result.status = "error";
          result.error = "Page appears to be empty or not fully loaded";
        }

        // Check for unhandled exceptions
        if (consoleErrors.length > 0) {
          console.warn(`Console errors on ${route.name}:`, consoleErrors);
        }

        if (networkErrors.length > 0) {
          console.warn(`Network errors on ${route.name}:`, networkErrors);
        }
      } catch (error) {
        result.status = "error";
        result.error = error instanceof Error ? error.message : String(error);

        // Still try to take a screenshot for debugging
        try {
          const screenshotPath = path.join(
            artifactsDir,
            `error_${result.screenshot}`,
          );
          await page.screenshot({ path: screenshotPath, fullPage: true });
          result.screenshot = `error_${result.screenshot}`;
        } catch (screenshotError) {
          console.warn("Could not capture error screenshot:", screenshotError);
        }
      }

      auditResults.push(result);

      // Assertions for test failure
      expect(result.status).toBe("success");
      expect(result.metrics.consoleErrors.length).toBe(0);
      expect(result.metrics.networkErrors.length).toBe(0);
      expect(result.metrics.nanCells).toBe(0);
      expect(result.metrics.infinityCells).toBe(0);
    });
  }
});
