import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import fs from 'fs/promises';
import path from 'path';

// Routes to audit for accessibility
const ROUTES = [
  { name: 'home', path: '/' },
  { name: 'chat', path: '/chat' },
  { name: 'market', path: '/market' },
  { name: 'alerts', path: '/alerts' },
  { name: 'paper-trading', path: '/paper' },
  { name: 'portfolio', path: '/portfolio' },
  { name: 'settings', path: '/settings' },
  { name: 'status', path: '/status' },
];

const BASE_URL = process.env.ACCESSIBILITY_URL || 'http://localhost:3002';

async function runAccessibilityAudit() {
  console.log('Starting Accessibility (axe-core) audit...');
  
  const artifactsDir = path.join(process.cwd(), 'artifacts', 'ui');
  await fs.mkdir(artifactsDir, { recursive: true });

  console.log('Testing connection to', BASE_URL);
  
  // Test connection first
  try {
    const testResponse = await fetch(BASE_URL);
    console.log('✓ Server is responding with status:', testResponse.status);
  } catch (error) {
    console.error('✗ Server is not responding. Please ensure the dev server is running on', BASE_URL);
    console.error('Run: npm run dev');
    console.error('Error:', error.message);
    process.exit(1);
  }

  console.log('Starting Playwright browser...');
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  const results = [];
  let totalViolations = 0;

  console.log(`Auditing ${ROUTES.length} routes for accessibility...`);

  for (const route of ROUTES) {
    const url = `${BASE_URL}${route.path}`;
    console.log(`Auditing ${route.name}: ${url}`);
    
    try {
      // Navigate to the page
      await page.goto(url, { waitUntil: 'networkidle' });
      
      // Wait a bit for any dynamic content to load
      await page.waitForTimeout(2000);
      
      // Run axe accessibility analysis
      const accessibilityScanResults = await new AxeBuilder({ page }).analyze();
      
      const routeResult = {
        route: route.name,
        url: url,
        timestamp: new Date().toISOString(),
        violations: accessibilityScanResults.violations.length,
        passes: accessibilityScanResults.passes.length,
        incomplete: accessibilityScanResults.incomplete.length,
        inapplicable: accessibilityScanResults.inapplicable.length,
        details: {
          violations: accessibilityScanResults.violations.map(violation => ({
            id: violation.id,
            impact: violation.impact,
            description: violation.description,
            help: violation.help,
            helpUrl: violation.helpUrl,
            nodes: violation.nodes.length,
            tags: violation.tags
          })),
          incomplete: accessibilityScanResults.incomplete.map(incomplete => ({
            id: incomplete.id,
            impact: incomplete.impact,
            description: incomplete.description,
            help: incomplete.help,
            nodes: incomplete.nodes.length
          }))
        }
      };

      results.push(routeResult);
      totalViolations += routeResult.violations;

      // Save individual detailed report
      const reportPath = path.join(artifactsDir, `axe_${route.name}.json`);
      await fs.writeFile(reportPath, JSON.stringify(accessibilityScanResults, null, 2));
      console.log(`✓ Saved detailed report: ${reportPath}`);
      
      console.log(`✓ ${route.name}: ${routeResult.violations} violations, ${routeResult.passes} passes`);
      
      if (routeResult.violations > 0) {
        console.log(`   ⚠️ Found ${routeResult.violations} accessibility issues`);
        routeResult.details.violations.forEach(violation => {
          console.log(`      • ${violation.id}: ${violation.description} (${violation.impact})`);
        });
      }

    } catch (error) {
      console.error(`✗ Failed to audit ${route.name}:`, error.message);
      results.push({
        route: route.name,
        url: url,
        timestamp: new Date().toISOString(),
        error: error.message,
        violations: 0,
        passes: 0,
        incomplete: 0,
        inapplicable: 0,
        details: { violations: [], incomplete: [] }
      });
    }
  }

  await browser.close();

  // Save summary report
  const summaryPath = path.join(artifactsDir, 'accessibility_summary.json');
  await fs.writeFile(summaryPath, JSON.stringify(results, null, 2));
  console.log(`✓ Saved summary: ${summaryPath}`);

  // Generate critical issues report
  const criticalIssues = results.reduce((acc, result) => {
    if (result.details?.violations) {
      const critical = result.details.violations.filter(v => v.impact === 'critical');
      const serious = result.details.violations.filter(v => v.impact === 'serious');
      if (critical.length > 0) acc.push(`${result.route}: ${critical.length} critical issues`);
      if (serious.length > 0) acc.push(`${result.route}: ${serious.length} serious issues`);
    }
    return acc;
  }, []);

  console.log('\n=== Accessibility Audit Complete ===');
  console.log(`Audited ${results.length} routes`);
  console.log(`Total violations found: ${totalViolations}`);
  console.log(`Reports saved to: ${artifactsDir}`);
  console.log(`Critical/Serious issues: ${criticalIssues.length}`);
  
  if (criticalIssues.length > 0) {
    console.log('\nCritical/Serious Issues:');
    criticalIssues.forEach(issue => console.log(`  🚨 ${issue}`));
  }
  
  if (totalViolations === 0) {
    console.log('🎉 No accessibility violations found!');
  }

  return results;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  runAccessibilityAudit().catch(console.error);
}

export default runAccessibilityAudit;