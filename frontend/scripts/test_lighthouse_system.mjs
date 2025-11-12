import lighthouse from 'lighthouse';
import * as chromeLauncher from 'chrome-launcher';
import fs from 'fs/promises';
import path from 'path';

async function testLighthouseWithMockData() {
  console.log('Testing Lighthouse audit system...');
  
  const artifactsDir = path.join(process.cwd(), 'artifacts', 'ui');
  await fs.mkdir(artifactsDir, { recursive: true });

  console.log('Starting Chrome...');
  const chrome = await chromeLauncher.launch({ 
    chromeFlags: ['--headless', '--no-sandbox', '--disable-dev-shm-usage'] 
  });
  console.log('Chrome launched successfully');
  
  const options = {
    logLevel: 'info',
    output: 'json',
    onlyCategories: ['performance', 'accessibility', 'best-practices'],
    port: chrome.port,
  };

  // Test with a simple, fast loading site
  const testUrl = 'https://example.com';
  console.log(`Testing with: ${testUrl}`);
  
  try {
    const runnerResult = await lighthouse(testUrl, options);
    const lhr = runnerResult.lhr;
    
    const result = {
      route: 'test',
      url: testUrl,
      timestamp: new Date().toISOString(),
      scores: {
        performance: lhr.categories.performance?.score ? Math.round(lhr.categories.performance.score * 100) : 0,
        accessibility: lhr.categories.accessibility?.score ? Math.round(lhr.categories.accessibility.score * 100) : 0,
        bestPractices: lhr.categories['best-practices']?.score ? Math.round(lhr.categories['best-practices'].score * 100) : 0,
      }
    };
    
    // Save test report
    const reportPath = path.join(artifactsDir, 'lh_test.json');
    await fs.writeFile(reportPath, JSON.stringify(lhr, null, 2));
    
    console.log('✓ Test completed successfully');
    console.log(`✓ Performance: ${result.scores.performance}, A11y: ${result.scores.accessibility}, Best Practices: ${result.scores.bestPractices}`);
    console.log(`✓ Report saved: ${reportPath}`);
    
  } catch (error) {
    console.error('✗ Test failed:', error.message);
  }

  await chrome.kill();
  console.log('✓ Chrome closed');
}

testLighthouseWithMockData().catch(console.error);