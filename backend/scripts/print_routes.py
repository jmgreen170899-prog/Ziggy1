#!/usr/bin/env python3
"""Print all registered runtime routes for diagnostics.

This is a development/maintenance script that prints all routes
registered in the FastAPI application at runtime.
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.main import app


def main():
    """Print all registered routes with details."""
    print(f"\n{'='*80}")
    print(f"ZiggyAI Backend Routes - Total: {len(app.routes)}")
    print(f"{'='*80}\n")

    # Group routes by path prefix
    routes_by_prefix = {}

    for route in app.routes:
        if not hasattr(route, "path"):
            continue

        path = route.path
        methods = getattr(route, "methods", set())
        name = getattr(route, "name", "")
        include_in_schema = getattr(route, "include_in_schema", True)

        # Get tags if available
        tags = []
        if hasattr(route, "tags"):
            tags = route.tags or []

        # Determine prefix
        prefix = "/" + path.split("/")[1] if "/" in path and len(path) > 1 else "/"

        if prefix not in routes_by_prefix:
            routes_by_prefix[prefix] = []

        routes_by_prefix[prefix].append(
            {
                "path": path,
                "methods": sorted(methods) if methods else ["*"],
                "name": name,
                "tags": tags,
                "include_in_schema": include_in_schema,
            }
        )

    # Print routes grouped by prefix
    for prefix in sorted(routes_by_prefix.keys()):
        routes = routes_by_prefix[prefix]
        print(f"\n{prefix} ({len(routes)} routes)")
        print("-" * 80)

        for route in sorted(routes, key=lambda r: r["path"]):
            methods_str = ", ".join(route["methods"])
            schema_str = "✓" if route["include_in_schema"] else "✗"
            tags_str = f" [{', '.join(route['tags'])}]" if route["tags"] else ""

            print(f"  [{schema_str}] {methods_str:12} {route['path']:50} {tags_str}")

    print(f"\n{'='*80}")
    print(f"Legend: [✓] = included in OpenAPI schema, [✗] = hidden from schema")
    print(f"{'='*80}\n")

    # Summary stats
    schema_routes = sum(
        1
        for route in app.routes
        if hasattr(route, "include_in_schema") and route.include_in_schema
    )
    hidden_routes = len(app.routes) - schema_routes

    print(f"Summary:")
    print(f"  Total routes: {len(app.routes)}")
    print(f"  In OpenAPI schema: {schema_routes}")
    print(f"  Hidden from schema: {hidden_routes}")
    print()


if __name__ == "__main__":
    main()
