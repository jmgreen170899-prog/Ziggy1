import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import fs from 'fs/promises';
import path from 'path';

async function testAxeAuditSystem() {
  console.log('Testing Accessibility audit system...');
  
  const artifactsDir = path.join(process.cwd(), 'artifacts', 'ui');
  await fs.mkdir(artifactsDir, { recursive: true });

  console.log('Starting Playwright browser...');
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  // Test with a simple, known site
  const testUrl = 'https://example.com';
  console.log(`Testing with: ${testUrl}`);
  
  try {
    await page.goto(testUrl, { waitUntil: 'networkidle' });
    
    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();
    
    const result = {
      route: 'test',
      url: testUrl,
      timestamp: new Date().toISOString(),
      violations: accessibilityScanResults.violations.length,
      passes: accessibilityScanResults.passes.length,
      incomplete: accessibilityScanResults.incomplete.length,
      inapplicable: accessibilityScanResults.inapplicable.length
    };
    
    // Save test report
    const reportPath = path.join(artifactsDir, 'axe_test.json');
    await fs.writeFile(reportPath, JSON.stringify(accessibilityScanResults, null, 2));
    
    console.log('✓ Test completed successfully');
    console.log(`✓ Violations: ${result.violations}, Passes: ${result.passes}, Incomplete: ${result.incomplete}`);
    console.log(`✓ Report saved: ${reportPath}`);
    
  } catch (error) {
    console.error('✗ Test failed:', error.message);
  }

  await browser.close();
  console.log('✓ Browser closed');
}

testAxeAuditSystem().catch(console.error);