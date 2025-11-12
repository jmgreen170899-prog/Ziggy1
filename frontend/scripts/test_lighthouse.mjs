import lighthouse from 'lighthouse';
import * as chromeLauncher from 'chrome-launcher';

console.log('Starting simple lighthouse test...');

try {
  console.log('Launching Chrome...');
  const chrome = await chromeLauncher.launch({ 
    chromeFlags: ['--headless', '--no-sandbox', '--disable-dev-shm-usage'] 
  });
  console.log('Chrome launched on port:', chrome.port);
  
  const options = {
    logLevel: 'info',
    output: 'json',
    onlyCategories: ['performance'],
    port: chrome.port,
  };
  
  console.log('Testing lighthouse on example.com...');
  const result = await lighthouse('https://example.com', options);
  console.log('Lighthouse completed!');
  console.log('Performance score:', result.lhr.categories.performance.score * 100);
  
  await chrome.kill();
  console.log('Done!');
} catch (error) {
  console.error('Error:', error);
  process.exit(1);
}