console.log('Testing localhost connection...');

try {
  const response = await fetch('http://localhost:3002');
  console.log('Status:', response.status);
  console.log('Headers:', Object.fromEntries(response.headers.entries()));
  const text = await response.text();
  console.log('Response length:', text.length);
  console.log('Content type:', response.headers.get('content-type'));
  console.log('First 200 chars:', text.substring(0, 200));
} catch (error) {
  console.error('Fetch error:', error.message);
}