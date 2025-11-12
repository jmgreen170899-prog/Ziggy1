const routes = [
  { name: 'home', path: '/' },
  { name: 'chat', path: '/chat' },
  { name: 'market', path: '/market' },
  { name: 'alerts', path: '/alerts' },
  { name: 'paper', path: '/paper-trading' },
  { name: 'portfolio', path: '/portfolio' },
  { name: 'settings', path: '/settings' },
  { name: 'status', path: '/status' }
];

const BASE_URL = 'http://localhost:3002';

async function checkRoutes() {
  console.log('Checking route accessibility...\n');
  
  for (const route of routes) {
    const url = `${BASE_URL}${route.path}`;
    try {
      const response = await fetch(url);
      const status = response.status;
      const statusText = response.statusText;
      
      if (status === 200) {
        console.log(`✓ ${route.name.padEnd(10)} (${route.path.padEnd(15)}) - ${status} ${statusText}`);
      } else {
        console.log(`✗ ${route.name.padEnd(10)} (${route.path.padEnd(15)}) - ${status} ${statusText}`);
      }
    } catch (error) {
      console.log(`✗ ${route.name.padEnd(10)} (${route.path.padEnd(15)}) - Error: ${error.message}`);
    }
  }
  
  console.log('\nNote: Manual verification in browser still needed for UI rendering and console errors.');
}

checkRoutes().catch(console.error);