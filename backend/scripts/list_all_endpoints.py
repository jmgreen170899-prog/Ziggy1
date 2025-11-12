#!/usr/bin/env python3
"""
List all registered endpoints in the ZiggyAI backend.
This script introspects the FastAPI app to discover all routes dynamically.
"""

import json
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from app.main import app
except Exception as e:
    print(f"Error importing app: {e}")
    print("Make sure all dependencies are installed (pip install -r requirements.txt)")
    sys.exit(1)


def extract_all_endpoints():
    """Extract all endpoints from the FastAPI app."""
    endpoints = []
    
    for route in app.routes:
        if not hasattr(route, "path"):
            continue
        
        path = route.path
        methods = getattr(route, "methods", set())
        name = getattr(route, "name", "")
        tags = getattr(route, "tags", []) or []
        include_in_schema = getattr(route, "include_in_schema", True)
        
        # Skip internal routes
        if path.startswith("/_"):
            continue
        
        for method in (sorted(methods) if methods else ["*"]):
            endpoints.append({
                "method": method,
                "path": path,
                "name": name,
                "tags": tags,
                "in_schema": include_in_schema
            })
    
    return endpoints


def main():
    print("=" * 80)
    print("ZiggyAI Backend - All Registered Endpoints")
    print("=" * 80)
    
    endpoints = extract_all_endpoints()
    
    # Sort by path then method
    endpoints.sort(key=lambda e: (e["path"], e["method"]))
    
    # Group by prefix
    by_prefix = {}
    for ep in endpoints:
        parts = ep["path"].split("/")
        prefix = f"/{parts[1]}" if len(parts) > 1 and parts[1] else "/"
        if prefix not in by_prefix:
            by_prefix[prefix] = []
        by_prefix[prefix].append(ep)
    
    # Print grouped endpoints
    total = 0
    for prefix in sorted(by_prefix.keys()):
        eps = by_prefix[prefix]
        print(f"\n{prefix} ({len(eps)} endpoints)")
        print("-" * 80)
        for ep in eps:
            schema_marker = "✓" if ep["in_schema"] else "✗"
            tags_str = f" [{', '.join(ep['tags'])}]" if ep["tags"] else ""
            print(f"  [{schema_marker}] {ep['method']:8} {ep['path']}{tags_str}")
            total += 1
    
    print(f"\n{'=' * 80}")
    print(f"Total: {total} endpoints across {len(by_prefix)} prefixes")
    print(f"{'=' * 80}")
    
    # Export as JSON for programmatic use
    output_file = backend_dir / "scripts" / "endpoints.json"
    with open(output_file, "w") as f:
        json.dump(endpoints, f, indent=2)
    print(f"\nEndpoints exported to: {output_file}")
    
    # Export GET-only endpoints for testing
    get_endpoints = [
        (ep["method"], ep["path"]) 
        for ep in endpoints 
        if ep["method"] == "GET" and ep["in_schema"]
    ]
    
    test_output = backend_dir / "scripts" / "test_endpoints.json"
    with open(test_output, "w") as f:
        json.dump(get_endpoints, f, indent=2)
    print(f"GET endpoints for testing exported to: {test_output}")


if __name__ == "__main__":
    main()
