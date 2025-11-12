import lighthouse from 'lighthouse';
import * as chromeLauncher from 'chrome-launcher';
import fs from 'fs/promises';
import path from 'path';

// Routes to audit
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

const BASE_URL = process.env.LIGHTHOUSE_URL || 'http://localhost:3002';

async function runLighthouse() {
  console.log('Starting Lighthouse audit...');
  const artifactsDir = path.join(process.cwd(), 'artifacts', 'ui');
  console.log('Artifacts directory:', artifactsDir);
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

  console.log('Starting Chrome...');
  const chrome = await chromeLauncher.launch({ 
    chromeFlags: ['--headless', '--no-sandbox', '--disable-dev-shm-usage'] 
  });
  console.log('Chrome launched successfully on port:', chrome.port);
  
  const options = {
    logLevel: 'info',
    output: 'json',
    onlyCategories: ['performance', 'accessibility', 'best-practices'],
    port: chrome.port,
  };

  const results = [];

  console.log(`Auditing ${ROUTES.length} routes against ${BASE_URL}`);

  for (const route of ROUTES) {
    const url = `${BASE_URL}${route.path}`;
    console.log(`Auditing ${route.name}: ${url}`);
    
    try {
      console.log('Launching lighthouse...');
      const runnerResult = await lighthouse(url, options);
      console.log('Lighthouse completed for', route.name);
      
      if (!runnerResult || !runnerResult.lhr) {
        throw new Error('Invalid lighthouse result');
      }

      const lhr = runnerResult.lhr;
      
      const result = {
        route: route.name,
        url: url,
        timestamp: new Date().toISOString(),
        scores: {
          performance: lhr.categories.performance?.score ? Math.round(lhr.categories.performance.score * 100) : 0,
          accessibility: lhr.categories.accessibility?.score ? Math.round(lhr.categories.accessibility.score * 100) : 0,
          bestPractices: lhr.categories['best-practices']?.score ? Math.round(lhr.categories['best-practices'].score * 100) : 0,
        },
        metrics: {
          firstContentfulPaint: lhr.audits['first-contentful-paint']?.numericValue || 0,
          largestContentfulPaint: lhr.audits['largest-contentful-paint']?.numericValue || 0,
          cumulativeLayoutShift: lhr.audits['cumulative-layout-shift']?.numericValue || 0,
          totalBlockingTime: lhr.audits['total-blocking-time']?.numericValue || 0,
          speedIndex: lhr.audits['speed-index']?.numericValue || 0,
        },
        issues: {
          performanceIssues: lhr.categories.performance?.auditRefs?.filter(ref => 
            lhr.audits[ref.id]?.score !== null && lhr.audits[ref.id]?.score < 0.9
          ).map(ref => ({
            id: ref.id,
            title: lhr.audits[ref.id]?.title,
            score: lhr.audits[ref.id]?.score,
            description: lhr.audits[ref.id]?.description
          })) || [],
          accessibilityIssues: lhr.categories.accessibility?.auditRefs?.filter(ref => 
            lhr.audits[ref.id]?.score !== null && lhr.audits[ref.id]?.score < 1
          ).map(ref => ({
            id: ref.id,
            title: lhr.audits[ref.id]?.title,
            score: lhr.audits[ref.id]?.score,
            description: lhr.audits[ref.id]?.description
          })) || []
        }
      };

      results.push(result);

      // Save individual report
      const reportPath = path.join(artifactsDir, `lh_${route.name}.json`);
      await fs.writeFile(reportPath, JSON.stringify(lhr, null, 2));
      console.log(`✓ Saved report: ${reportPath}`);
      
      console.log(`✓ ${route.name}: Performance ${result.scores.performance}, A11y ${result.scores.accessibility}, Best Practices ${result.scores.bestPractices}`);
    } catch (error) {
      console.error(`✗ Failed to audit ${route.name}:`, error.message);
      results.push({
        route: route.name,
        url: url,
        timestamp: new Date().toISOString(),
        error: error.message,
        scores: { performance: 0, accessibility: 0, bestPractices: 0 },
        metrics: {},
        issues: { performanceIssues: [], accessibilityIssues: [] }
      });
    }
  }

  // Save summary report
  const summaryPath = path.join(artifactsDir, 'lighthouse_summary.json');
  await fs.writeFile(summaryPath, JSON.stringify(results, null, 2));
  console.log(`✓ Saved summary: ${summaryPath}`);

  // Generate flags for critical issues
  const flags = results.reduce((acc, result) => {
    if (result.scores?.performance < 50) acc.push(`Low performance: ${result.route} (${result.scores.performance})`);
    if (result.scores?.accessibility < 80) acc.push(`Accessibility issues: ${result.route} (${result.scores.accessibility})`);
    if (result.metrics?.cumulativeLayoutShift > 0.1) acc.push(`High layout shift: ${result.route} (${result.metrics.cumulativeLayoutShift})`);
    return acc;
  }, []);

  console.log('\n=== Lighthouse Audit Complete ===');
  console.log(`Audited ${results.length} routes`);
  console.log(`Reports saved to: ${artifactsDir}`);
  console.log(`Critical issues found: ${flags.length}`);
  if (flags.length > 0) {
    console.log('\nCritical Issues:');
    flags.forEach(flag => console.log(`  ⚠️  ${flag}`));
  }

  await chrome.kill();
  
  return results;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  runLighthouse().catch(console.error);
}

export default runLighthouse;