#!/usr/bin/env python3
"""
Comprehensive endpoint testing script for ZiggyAI backend.
Tests all registered routes for proper responses and documents results.
"""

import sys
import json
from pathlib import Path

# Add backend to path for imports
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from fastapi.testclient import TestClient
from app.main import app

def test_all_endpoints():
    """Test all registered endpoints and generate report."""
    client = TestClient(app)
    
    # Get all routes
    routes = []
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            for method in route.methods:
                if method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                    routes.append({
                        'method': method,
                        'path': route.path,
                        'name': route.name if hasattr(route, 'name') else 'unknown'
                    })
    
    results = {
        'total': len(routes),
        'success': 0,
        'client_error': 0,
        'server_error': 0,
        'endpoints': []
    }
    
    print(f"\n🔍 Testing {len(routes)} endpoints...\n")
    
    for route_info in sorted(routes, key=lambda x: (x['path'], x['method'])):
        method = route_info['method']
        path = route_info['path']
        
        # Skip OpenAPI docs endpoints
        if '/docs' in path or '/redoc' in path or '/openapi.json' in path:
            continue
        
        # Skip endpoints with path parameters for now (need specific test data)
        if '{' in path:
            results['endpoints'].append({
                **route_info,
                'status': 'SKIPPED',
                'reason': 'Path parameter required'
            })
            continue
        
        try:
            # Test the endpoint
            if method == 'GET':
                response = client.get(path)
            elif method == 'POST':
                response = client.post(path, json={})
            elif method == 'PUT':
                response = client.put(path, json={})
            elif method == 'DELETE':
                response = client.delete(path)
            elif method == 'PATCH':
                response = client.patch(path, json={})
            else:
                continue
            
            status_code = response.status_code
            
            # Categorize response
            if status_code < 400:
                status = 'SUCCESS'
                results['success'] += 1
                symbol = '✅'
            elif status_code < 500:
                status = 'CLIENT_ERROR'
                results['client_error'] += 1
                symbol = '⚠️'
            else:
                status = 'SERVER_ERROR'
                results['server_error'] += 1
                symbol = '❌'
            
            print(f"{symbol} {method:6} {path:50} -> {status_code}")
            
            results['endpoints'].append({
                **route_info,
                'status': status,
                'status_code': status_code,
                'response_size': len(response.content) if response.content else 0
            })
            
        except Exception as e:
            print(f"❌ {method:6} {path:50} -> EXCEPTION: {str(e)[:50]}")
            results['endpoints'].append({
                **route_info,
                'status': 'EXCEPTION',
                'error': str(e)
            })
    
    # Print summary
    print("\n" + "="*80)
    print("📊 ENDPOINT TEST SUMMARY")
    print("="*80)
    print(f"Total Endpoints Tested: {results['total']}")
    print(f"✅ Success (2xx-3xx):   {results['success']}")
    print(f"⚠️  Client Errors (4xx): {results['client_error']}")
    print(f"❌ Server Errors (5xx): {results['server_error']}")
    print(f"⏭️  Skipped:            {len([e for e in results['endpoints'] if e.get('status') == 'SKIPPED'])}")
    
    # Calculate health percentage
    testable = results['total'] - len([e for e in results['endpoints'] if e.get('status') == 'SKIPPED'])
    if testable > 0:
        health_pct = (results['success'] / testable) * 100
        print(f"\n🎯 API Health: {health_pct:.1f}%")
        
        if results['server_error'] > 0:
            print(f"\n⚠️  WARNING: {results['server_error']} endpoints returning 5xx errors!")
    
    # Save results to file
    output_path = backend_path / 'endpoint_test_results.json'
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: {output_path}")
    
    return results['server_error'] == 0 and results['success'] > 0

if __name__ == '__main__':
    success = test_all_endpoints()
    sys.exit(0 if success else 1)
