#!/usr/bin/env python3
"""
Systematic endpoint verification script.

This script verifies all backend endpoints one by one:
1. Checks if route exists in code
2. Verifies response model is defined
3. Checks if smoke test exists
4. Reports findings

Usage:
    python3 scripts/verify_all_endpoints.py
"""

import ast
import inspect
import sys
from pathlib import Path
from typing import Any

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Color codes for output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"


def analyze_route_file(file_path: Path) -> dict[str, Any]:
    """Analyze a route file to extract endpoint information."""
    with open(file_path) as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return {"error": "Failed to parse file"}
    
    endpoints = []
    router_prefix = ""
    
    # Find router definition and its prefix
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "router":
                    if isinstance(node.value, ast.Call):
                        for keyword in node.value.keywords:
                            if keyword.arg == "prefix":
                                if isinstance(keyword.value, ast.Constant):
                                    router_prefix = keyword.value.value
    
    # Find all route decorators
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call):
                    if hasattr(decorator.func, 'attr'):
                        method = decorator.func.attr
                        if method in ['get', 'post', 'put', 'delete', 'patch']:
                            path = ""
                            response_model = None
                            
                            # Extract path
                            if decorator.args:
                                if isinstance(decorator.args[0], ast.Constant):
                                    path = decorator.args[0].value
                            
                            # Extract response_model
                            for keyword in decorator.keywords:
                                if keyword.arg == "response_model":
                                    if isinstance(keyword.value, ast.Name):
                                        response_model = keyword.value.id
                            
                            endpoints.append({
                                "method": method.upper(),
                                "path": path,
                                "function": node.name,
                                "response_model": response_model,
                                "has_docstring": ast.get_docstring(node) is not None
                            })
    
    return {
        "router_prefix": router_prefix,
        "endpoints": endpoints,
        "file": file_path.name
    }


def find_test_for_endpoint(endpoint_path: str, test_dir: Path) -> bool:
    """Check if a test exists for the given endpoint."""
    # Normalize path for searching
    search_path = endpoint_path.replace("/", "_").replace("{", "").replace("}", "")
    
    for test_file in test_dir.glob("test_*.py"):
        with open(test_file) as f:
            content = f.read()
            # Simple heuristic: check if endpoint path appears in test file
            if endpoint_path in content or search_path in content:
                return True
    
    return False


def main():
    """Main verification function."""
    print(f"\n{BOLD}{'=' * 80}{RESET}")
    print(f"{BOLD}ZiggyAI Backend Endpoint Verification Report{RESET}")
    print(f"{BOLD}{'=' * 80}{RESET}\n")
    
    route_files = sorted(backend_dir.glob("app/api/routes_*.py"))
    test_dir = backend_dir / "tests" / "test_api_smoke"
    
    total_endpoints = 0
    endpoints_with_models = 0
    endpoints_with_tests = 0
    endpoints_with_docs = 0
    
    all_findings = []
    
    for route_file in route_files:
        print(f"\n{BLUE}Analyzing: {route_file.name}{RESET}")
        print("-" * 80)
        
        analysis = analyze_route_file(route_file)
        
        if "error" in analysis:
            print(f"{RED}  ✗ Error: {analysis['error']}{RESET}")
            continue
        
        router_prefix = analysis.get("router_prefix", "")
        endpoints = analysis.get("endpoints", [])
        
        if router_prefix:
            print(f"  Router prefix: {router_prefix}")
        
        for endpoint in endpoints:
            total_endpoints += 1
            
            full_path = router_prefix + endpoint['path']
            has_model = endpoint['response_model'] is not None
            has_test = find_test_for_endpoint(full_path, test_dir)
            has_doc = endpoint['has_docstring']
            
            if has_model:
                endpoints_with_models += 1
            if has_test:
                endpoints_with_tests += 1
            if has_doc:
                endpoints_with_docs += 1
            
            # Status indicators
            model_icon = f"{GREEN}✓{RESET}" if has_model else f"{RED}✗{RESET}"
            test_icon = f"{GREEN}✓{RESET}" if has_test else f"{YELLOW}?{RESET}"
            doc_icon = f"{GREEN}✓{RESET}" if has_doc else f"{YELLOW}?{RESET}"
            
            print(f"  [{model_icon}M {test_icon}T {doc_icon}D] {endpoint['method']:6} {full_path:40} ({endpoint['function']})")
            
            all_findings.append({
                "file": route_file.name,
                "method": endpoint['method'],
                "path": full_path,
                "function": endpoint['function'],
                "has_model": has_model,
                "has_test": has_test,
                "has_doc": has_doc,
                "response_model": endpoint['response_model']
            })
    
    # Summary
    print(f"\n{BOLD}{'=' * 80}{RESET}")
    print(f"{BOLD}Summary{RESET}")
    print(f"{BOLD}{'=' * 80}{RESET}\n")
    
    print(f"Total endpoints found: {total_endpoints}")
    print(f"Endpoints with response models: {endpoints_with_models} ({endpoints_with_models/total_endpoints*100:.1f}%)")
    print(f"Endpoints with tests: {endpoints_with_tests} ({endpoints_with_tests/total_endpoints*100:.1f}%)")
    print(f"Endpoints with docstrings: {endpoints_with_docs} ({endpoints_with_docs/total_endpoints*100:.1f}%)")
    
    # Endpoints needing attention
    print(f"\n{YELLOW}Endpoints needing response models:{RESET}")
    count = 0
    for finding in all_findings:
        if not finding['has_model']:
            print(f"  - {finding['method']:6} {finding['path']:50} in {finding['file']}")
            count += 1
            if count >= 10:
                remaining = sum(1 for f in all_findings if not f['has_model']) - 10
                if remaining > 0:
                    print(f"  ... and {remaining} more")
                break
    
    print(f"\n{YELLOW}Endpoints needing tests:{RESET}")
    count = 0
    for finding in all_findings:
        if not finding['has_test']:
            print(f"  - {finding['method']:6} {finding['path']:50} in {finding['file']}")
            count += 1
            if count >= 10:
                remaining = sum(1 for f in all_findings if not f['has_test']) - 10
                if remaining > 0:
                    print(f"  ... and {remaining} more")
                break
    
    print(f"\n{BOLD}Legend:{RESET}")
    print(f"  [M] = Response Model defined")
    print(f"  [T] = Smoke Test exists")
    print(f"  [D] = Docstring present")
    print()


if __name__ == "__main__":
    main()
