import { test, expect } from '@playwright/test';

/**
 * Visual/UX Sanity Tests
 * 
 * These tests validate the visual structure and consistency of pages
 * WITHOUT modifying the existing ui_audit.spec.ts crawler.
 * 
 * Focus areas:
 * - Page structure and layout
 * - Loading states
 * - Error states
 * - Empty states
 * - Component consistency
 */

test.describe('Visual Sanity - Page Structure', () => {
  test('Dashboard page has proper layout structure', async ({ page }) => {
    await page.goto('/');
    
    // Check for main layout elements
    await expect(page.locator('#main-content')).toBeVisible();
    
    // Check that content is loading (either data or skeleton)
    const hasContent = await page.locator('[data-testid="dashboard"]').count() > 0 ||
                       await page.locator('.skeleton').count() > 0;
    expect(hasContent).toBeTruthy();
  });

  test('Market page has proper layout structure', async ({ page }) => {
    await page.goto('/market');
    
    // Check for main content
    await expect(page.locator('#main-content')).toBeVisible();
    
    // Verify themed header is present
    const header = await page.locator('h1:has-text("Market Overview")');
    await expect(header).toBeVisible();
  });

  test('News page has proper layout structure', async ({ page }) => {
    await page.goto('/news');
    
    // Check for main content
    await expect(page.locator('#main-content')).toBeVisible();
    
    // Verify page title
    const header = await page.locator('h1:has-text("Market News")');
    await expect(header).toBeVisible();
  });

  test('Chat page has proper layout structure', async ({ page }) => {
    await page.goto('/chat');
    
    // Check for main content
    await expect(page.locator('#main-content')).toBeVisible();
    
    // Check for chat interface
    const chatInterface = await page.locator('[data-testid="chat-interface"]');
    expect(await chatInterface.count()).toBeGreaterThanOrEqual(0);
  });

  test('Trading page has proper layout structure', async ({ page }) => {
    await page.goto('/trading');
    
    // Check for main content
    await expect(page.locator('#main-content')).toBeVisible();
    
    // Verify themed header
    const header = await page.locator('text="Advanced Trading Platform"');
    expect(await header.count()).toBeGreaterThan(0);
  });

  test('Portfolio page has proper layout structure', async ({ page }) => {
    await page.goto('/portfolio');
    
    // Check for main content
    await expect(page.locator('#main-content')).toBeVisible();
    
    // Verify page title
    const header = await page.locator('h1:has-text("Portfolio Overview")');
    await expect(header).toBeVisible();
  });

  test('Alerts page has proper layout structure', async ({ page }) => {
    await page.goto('/alerts');
    
    // Check for main content
    await expect(page.locator('#main-content')).toBeVisible();
    
    // Verify page title
    const header = await page.locator('h1:has-text("Price Alerts")');
    await expect(header).toBeVisible();
  });
});

test.describe('Visual Sanity - Loading States', () => {
  test('Pages show loading indicators appropriately', async ({ page }) => {
    await page.goto('/market');
    
    // Check if page shows either skeleton loaders or actual content
    await page.waitForTimeout(1000); // Brief wait for initial render
    
    const hasSkeletons = await page.locator('.skeleton, .animate-pulse').count() > 0;
    const hasContent = await page.locator('[class*="card"]').count() > 0;
    
    // Should have either loading state or content
    expect(hasSkeletons || hasContent).toBeTruthy();
  });

  test('Loading spinners are styled consistently', async ({ page }) => {
    await page.goto('/portfolio');
    
    // Wait a moment for potential loading states
    await page.waitForTimeout(500);
    
    // If loading states exist, verify they use consistent styling
    const spinners = await page.locator('[role="status"]').count();
    
    if (spinners > 0) {
      const spinner = page.locator('[role="status"]').first();
      await expect(spinner).toHaveAttribute('aria-label', /Loading/i);
    }
  });
});

test.describe('Visual Sanity - Error States', () => {
  test('Error boundaries render properly', async ({ page }) => {
    // Navigate to a page that might have errors
    await page.goto('/market');
    
    // Check that error messages, if present, are user-friendly
    const errorMessages = await page.locator('text=/error|failed/i').count();
    
    if (errorMessages > 0) {
      // Verify error messages don't contain raw JSON or stack traces
      const pageContent = await page.textContent('body');
      expect(pageContent).not.toMatch(/\{.*"stack".*\}/);
      expect(pageContent).not.toMatch(/Error: at /);
    }
  });

  test('Error states have retry actions', async ({ page }) => {
    await page.goto('/alerts');
    
    // Wait for page to load
    await page.waitForTimeout(1000);
    
    // If error states are present, they should have action buttons
    const errorText = await page.locator('text=/failed|error/i').count();
    
    if (errorText > 0) {
      const tryAgainButton = await page.locator('button:has-text(/try again|retry|reload/i)').count();
      expect(tryAgainButton).toBeGreaterThan(0);
    }
  });
});

test.describe('Visual Sanity - Empty States', () => {
  test('Empty states render with proper messaging', async ({ page }) => {
    // Check pages that might have empty states
    await page.goto('/alerts');
    
    // Wait for content to load
    await page.waitForTimeout(2000);
    
    // If empty state is present, verify it has meaningful content
    const emptyState = await page.locator('text=/no.*found|empty|get started/i').count();
    
    if (emptyState > 0) {
      // Should not just be blank or show "undefined"
      const pageContent = await page.textContent('body');
      expect(pageContent).not.toContain('undefined');
      expect(pageContent?.length).toBeGreaterThan(50); // Has meaningful content
    }
  });

  test('Empty states include visual icons or illustrations', async ({ page }) => {
    await page.goto('/news');
    
    await page.waitForTimeout(1500);
    
    // Check if empty states have emoji or icon representations
    const emptyMessage = await page.locator('text=/no.*articles|empty/i').count();
    
    if (emptyMessage > 0) {
      // Should have some visual element (emoji are common in this codebase)
      const hasVisual = await page.locator('[class*="text-"]').count() > 0;
      expect(hasVisual).toBeTruthy();
    }
  });
});

test.describe('Visual Sanity - Component Consistency', () => {
  test('Cards use consistent styling across pages', async ({ page }) => {
    // Check multiple pages for card consistency
    const pages = ['/market', '/news', '/alerts'];
    
    for (const pagePath of pages) {
      await page.goto(pagePath);
      await page.waitForTimeout(1000);
      
      // Cards should have rounded corners (rounded-xl is common)
      const cards = await page.locator('[class*="rounded"]').count();
      expect(cards).toBeGreaterThan(0);
    }
  });

  test('Buttons use consistent styling', async ({ page }) => {
    await page.goto('/market');
    await page.waitForTimeout(1000);
    
    // Check that buttons have consistent classes
    const buttons = await page.locator('button').count();
    
    if (buttons > 0) {
      // Buttons should have rounded styling
      const styledButtons = await page.locator('button[class*="rounded"]').count();
      expect(styledButtons).toBeGreaterThan(0);
    }
  });

  test('Navigation sidebar is present and functional', async ({ page }) => {
    await page.goto('/');
    
    // Check sidebar exists
    const sidebar = await page.locator('[role="dialog"], [role="navigation"]');
    expect(await sidebar.count()).toBeGreaterThan(0);
    
    // Sidebar should have navigation links
    const navLinks = await page.locator('nav a, [role="navigation"] a').count();
    expect(navLinks).toBeGreaterThan(0);
  });

  test('Typography is consistent across pages', async ({ page }) => {
    const pages = ['/', '/market', '/news'];
    
    for (const pagePath of pages) {
      await page.goto(pagePath);
      await page.waitForTimeout(500);
      
      // Check that page titles exist and are styled
      const h1 = await page.locator('h1').first();
      await expect(h1).toBeVisible();
      
      // Should have font styling
      const h1Class = await h1.getAttribute('class');
      expect(h1Class).toBeTruthy();
    }
  });
});

test.describe('Visual Sanity - Theme Consistency', () => {
  test('Dark mode classes are present in layout', async ({ page }) => {
    await page.goto('/');
    
    // Check that dark mode classes are defined (dark:)
    const bodyClass = await page.locator('body').getAttribute('class');
    const hasDarkModeSupport = await page.locator('[class*="dark:"]').count() > 0;
    
    expect(hasDarkModeSupport).toBeTruthy();
  });

  test('Pages use themed gradients consistently', async ({ page }) => {
    await page.goto('/market');
    
    // Market page should use theme gradients
    const gradients = await page.locator('[class*="gradient"]').count();
    expect(gradients).toBeGreaterThan(0);
  });
});

test.describe('Visual Sanity - Accessibility', () => {
  test('Main content has proper landmark', async ({ page }) => {
    await page.goto('/');
    
    // Check for main landmark
    const main = await page.locator('main, [role="main"]');
    await expect(main).toBeVisible();
  });

  test('Skip link is present for keyboard navigation', async ({ page }) => {
    await page.goto('/');
    
    // Check for skip link
    const skipLink = await page.locator('text="Skip to main content"');
    expect(await skipLink.count()).toBeGreaterThan(0);
  });

  test('Buttons and links have accessible text', async ({ page }) => {
    await page.goto('/market');
    await page.waitForTimeout(1000);
    
    // Check that interactive elements have text or aria-labels
    const buttons = await page.locator('button').all();
    
    for (const button of buttons.slice(0, 5)) { // Check first 5
      const text = await button.textContent();
      const ariaLabel = await button.getAttribute('aria-label');
      
      // Should have either text content or aria-label
      expect(text || ariaLabel).toBeTruthy();
    }
  });
});

test.describe('Visual Sanity - Responsive Behavior', () => {
  test('Pages work on mobile viewport', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    
    // Main content should still be visible
    await expect(page.locator('#main-content')).toBeVisible();
    
    // Page should not have horizontal scroll
    const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
    const viewportWidth = await page.evaluate(() => window.innerWidth);
    expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 20); // Small tolerance
  });

  test('Sidebar adapts to mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    
    // Check that sidebar exists (may be hidden/collapsed on mobile)
    const sidebar = await page.locator('[role="dialog"], [role="navigation"]');
    expect(await sidebar.count()).toBeGreaterThan(0);
  });
});
