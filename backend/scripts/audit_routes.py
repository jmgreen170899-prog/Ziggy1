#!/usr/bin/env python3#!/usr/bin/env python3#!/usr/bin/env python3

"""

FastAPI Route Audit Script - Read-only analysis of routes""""""

"""

FastAPI Route Audit ScriptFastAPI Route Audit Script

import ast

import os

import sys

from pathlib import PathThis script performs a read-only audit of all routes in the codebaseThis script performs a read-only audit of all routes in the codebase



# Add backend to pathand compares them against the runtime FastAPI application to identifyand compares them against the runtime FastAPI application to identify

backend_root = Path(__file__).parent.parent

sys.path.insert(0, str(backend_root))unavailable routes.unavailable routes.



def scan_for_routes():

    """Scan all Python files for route definitions."""

    app_dir = backend_root / "app"IMPORTANT: This is a read-only audit - no modifications are made.IMPORTANT: This is a read-only audit - no modifications are made.

    routes_found = []

    routers_found = []""""""

    

    print(f"🔍 Scanning {app_dir} for routes...")

    

    for py_file in app_dir.rglob("*.py"):import astimport ast

        if "__pycache__" in str(py_file):

            continueimport osimport os

            

        try:import sysimport sys

            content = py_file.read_text(encoding="utf-8")

            tree = ast.parse(content)import importlibimport importlib

            

            # Find routes and routers in this fileimport tracebackimport traceback

            file_routes, file_routers = analyze_ast(tree, py_file)

            routes_found.extend(file_routes)from pathlib import Pathfrom pathlib import Path

            routers_found.extend(file_routers)

            from typing import Tuple, Anyfrom typing import Dict, List, Tuple, Set, Any

        except Exception as e:

            print(f"⚠️  Error parsing {py_file}: {e}")from dataclasses import dataclassfrom dataclasses import dataclass

    

    return routes_found, routers_foundfrom collections import defaultdict



def analyze_ast(tree, file_path):# Add backend to path for imports

    """Analyze AST for route decorators and router definitions."""

    routes = []backend_root = Path(__file__).parent.parent# Add backend to path for imports

    routers = []

    sys.path.insert(0, str(backend_root))backend_root = Path(__file__).parent.parent

    class RouteVisitor(ast.NodeVisitor):

        def visit_FunctionDef(self, node):sys.path.insert(0, str(backend_root))

            for decorator in node.decorator_list:

                route_info = parse_decorator(decorator, node, file_path)@dataclass

                if route_info:

                    routes.append(route_info)class RouteInfo:@dataclass

            self.generic_visit(node)

                file_path: strclass RouteInfo:

        def visit_Assign(self, node):

            # Look for router = APIRouter()    line_number: int    file_path: str

            if (len(node.targets) == 1 and 

                isinstance(node.targets[0], ast.Name)):    router_var: str    line_number: int

                var_name = node.targets[0].id

                if (isinstance(node.value, ast.Call) and    method: str    router_var: str

                    isinstance(node.value.func, ast.Name) and

                    node.value.func.id == "APIRouter"):    path: str    method: str

                    routers.append({

                        "file": str(file_path.relative_to(backend_root)),    include_in_schema: bool    path: str

                        "line": node.lineno,

                        "name": var_name    feature_flags: list[str]    include_in_schema: bool

                    })

            self.generic_visit(node)    function_name: str    feature_flags: List[str]

    

    visitor = RouteVisitor()    function_name: str

    visitor.visit(tree)

    return routes, routers@dataclass 



def parse_decorator(decorator, func_node, file_path):class RouterInfo:@dataclass 

    """Parse route decorators like @router.get('/path')."""

    if not isinstance(decorator, ast.Call):    file_path: strclass RouterInfo:

        return None

            line_number: int    file_path: str

    if not isinstance(decorator.func, ast.Attribute):

        return None    variable_name: str    line_number: int

        

    # Get router variable and method    imported_from: str    variable_name: str

    if isinstance(decorator.func.value, ast.Name):

        router_var = decorator.func.value.id    included_anywhere: bool    imported_from: str

        method = decorator.func.attr.upper()

            included_anywhere: bool

        # Get path from first argument

        path = Noneclass RouteAuditor:        yield name

        if decorator.args and isinstance(decorator.args[0], ast.Constant):

            path = decorator.args[0].value    def __init__(self):

            

        # Check for include_in_schema        self.static_routes: list[RouteInfo] = []def static_discover() -> Dict:

        include_in_schema = True

        for kw in decorator.keywords:        self.routers: list[RouterInfo] = []    results = {"routers": {}, "routes": [], "errors": []}

            if kw.arg == "include_in_schema" and isinstance(kw.value, ast.Constant):

                include_in_schema = kw.value.value        self.runtime_routes: set[Tuple[str, str]] = set()  # (method, path)    for modname in _iter_modules(APP_PKG):

                

        if path and method:        self.scan_errors: list[str] = []        try:

            return {

                "file": str(file_path.relative_to(backend_root)),        self.import_errors: list[str] = []            spec = importlib.util.find_spec(modname)

                "line": decorator.lineno,

                "router": router_var,                    if not spec or not spec.origin or not spec.origin.endswith(".py"):

                "method": method,

                "path": path,    def scan_python_files(self, directory: Path) -> list[Path]:                continue

                "function": func_node.name,

                "include_in_schema": include_in_schema        """Find all Python files in the directory."""            text = Path(spec.origin).read_text(encoding="utf-8", errors="ignore")

            }

            python_files = []            router_vars = set(re.findall(r"(\\w+)\\s*=\\s*APIRouter\\(", text))

    return None

        for root, dirs, files in os.walk(directory):            for m in ROUTE_DECORATORS.finditer(text):

def get_runtime_routes():

    """Get routes from running FastAPI app."""            # Skip common non-source directories                rvar, method, args = m.groups()

    runtime_routes = set()

                dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', '.pytest_cache', 'node_modules'}]                path = re.search(r'["\']([^"\']+)["\']', args or "")

    try:

        from app.main import app                            path = path.group(1) if path else "<unknown>"

        from fastapi.routing import APIRoute

                    for file in files:                line = text[:m.start()].count("\\n") + 1

        for route in app.routes:

            if isinstance(route, APIRoute):                if file.endswith('.py'):                results["routes"].append({

                for method in route.methods:

                    if method != "HEAD":  # Skip auto-generated HEAD                    python_files.append(Path(root) / file)                    "module": modname, "file": spec.origin, "line": line,

                        runtime_routes.add((method, route.path))

                                return python_files                    "router_var": rvar, "method": method.upper(), "path": path,

    except Exception as e:

        print(f"⚠️  Could not import FastAPI app: {e}")                        "include_in_schema_hint": "include_in_schema=False" in args

        

    return runtime_routes    def extract_feature_flags(self, node) -> list[str]:                })



def main():        """Extract os.getenv() calls that might be feature flags."""            for m in ADD_API_ROUTE.finditer(text):

    print("📊 FastAPI Route Audit - Read-Only Analysis")

    print("=" * 60)        flags = []                args = m.group(2)

    

    # Scan static routes                        path = re.search(r'["\']([^"\']+)["\']', args or "")

    static_routes, routers = scan_for_routes()

            class FlagVisitor(ast.NodeVisitor):                path = path.group(1) if path else "<unknown>"

    # Get runtime routes  

    runtime_routes = get_runtime_routes()            def visit_Call(self, node):                line = text[:m.start()].count("\\n") + 1

    

    print(f"\n📈 SUMMARY:")                # Look for os.getenv, os.environ.get patterns                results["routes"].append({

    print(f"  • Static routes found: {len(static_routes)}")

    print(f"  • Runtime routes: {len(runtime_routes)}")                if (isinstance(node.func, ast.Attribute) and                     "module": modname, "file": spec.origin, "line": line,

    print(f"  • Routers found: {len(routers)}")

                        isinstance(node.func.value, ast.Name) and                    "router_var": "<add_api_route>", "method": "*", "path": path,

    print(f"\n🌐 RUNTIME ROUTES ({len(runtime_routes)}):")

    for method, path in sorted(runtime_routes):                    node.func.value.id == 'os' and                    "include_in_schema_hint": "include_in_schema=False" in args

        print(f"  {method:8} {path}")

                        node.func.attr in ['getenv']):                })

    print(f"\n📋 STATIC ROUTES FOUND ({len(static_routes)}):")

    unavailable = []                    if node.args and isinstance(node.args[0], ast.Constant):            if router_vars:

    

    for route in static_routes:                        flags.append(node.args[0].value)                results["routers"][modname] = sorted(router_vars)

        route_key = (route["method"], route["path"])

        status = "✅" if route_key in runtime_routes else "❌"                elif (isinstance(node.func, ast.Attribute) and        except Exception as e:

        

        if route_key not in runtime_routes:                      isinstance(node.func.value, ast.Attribute) and            results["errors"].append({"module": modname, "error": repr(e)})

            unavailable.append(route)

                                  isinstance(node.func.value.value, ast.Name) and    return results

        schema_note = "" if route["include_in_schema"] else " [hidden]"

        print(f"  {status} {route['file']}:{route['line']}")                      node.func.value.value.id == 'os' and

        print(f"     {route['method']:8} {route['path']} ({route['router']}.{route['function']}){schema_note}")

                          node.func.value.attr == 'environ' anddef runtime_registered() -> Dict:

    if unavailable:

        print(f"\n❌ UNAVAILABLE ROUTES ({len(unavailable)}):")                      node.func.attr == 'get'):    out = {"routes": [], "errors": []}

        for route in unavailable:

            print(f"  • {route['file']}:{route['line']}")                    if node.args and isinstance(node.args[0], ast.Constant):    try:

            print(f"    {route['method']:8} {route['path']}")

            print(f"    Router: {route['router']}, Function: {route['function']}")                        flags.append(node.args[0].value)        app_mod = importlib.import_module("app.main")

            

            # Try to determine why it's unavailable                self.generic_visit(node)        app: FastAPI = getattr(app_mod, "app")

            reason = "router not included in main app"

            if not route["include_in_schema"]:                for r in app.routes:

                reason += ", hidden from schema"

            print(f"    Likely reason: {reason}")        visitor = FlagVisitor()            if isinstance(r, APIRoute):

            print()

    else:        visitor.visit(node)                out["routes"].append({

        print(f"\n✅ All static routes are available at runtime!")

            return flags                    "path": r.path,

    print(f"\n🔧 ROUTERS FOUND ({len(routers)}):")

    for router in routers:                        "methods": sorted(list(r.methods)),

        print(f"  • {router['file']}:{router['line']} - {router['name']}")

        def analyze_file(self, file_path: Path):                    "include_in_schema": r.include_in_schema,

    print(f"\n✅ AUDIT COMPLETE")

        """Analyze a single Python file for routes and routers."""                    "tags": r.tags,

if __name__ == "__main__":

    main()        try:                    "name": r.name

            content = file_path.read_text(encoding='utf-8')                })

            tree = ast.parse(content)    except Exception:

        except Exception as e:        out["errors"].append({"stage":"import app.main","error": traceback.format_exc()})

            self.scan_errors.append(f"Failed to parse {file_path}: {e}")    return out

            return

            def detect_feature_flags(modname: str):

        relative_path = str(file_path.relative_to(backend_root))    flags = []

            try:

        class RouteVisitor(ast.NodeVisitor):        spec = importlib.util.find_spec(modname)

            def __init__(self, auditor):        if spec and spec.origin:

                self.auditor = auditor            text = Path(spec.origin).read_text(encoding="utf-8", errors="ignore")

                self.routers_in_file = {}  # var_name -> (line, imported_from)            for envkey in re.findall(r'os\\.getenv\\(\\s*[\'"]([A-Z0-9_]+)[\'"]', text):

                                val = os.getenv(envkey)

            def visit_ImportFrom(self, node):                flags.append(f"{envkey}={'<unset>' if val is None else val}")

                # Track APIRouter imports    except Exception:

                if node.module and 'fastapi' in node.module:        pass

                    for alias in node.names:    return sorted(set(flags))

                        if alias.name == 'APIRouter':

                            # This file imports APIRouterdef main():

                            pass    static = static_discover()

                self.generic_visit(node)    runtime = runtime_registered()

                

            def visit_Assign(self, node):    runtime_paths = {r["path"] for r in runtime["routes"]}

                # Look for router = APIRouter() assignments    missing = []

                if (len(node.targets) == 1 and     for d in static["routes"]:

                    isinstance(node.targets[0], ast.Name)):        if d["path"] not in runtime_paths:

                    var_name = node.targets[0].id            missing.append({

                                    **d,

                    if (isinstance(node.value, ast.Call) and                "possible_feature_flags": detect_feature_flags(d["module"]) or None

                        isinstance(node.value.func, ast.Name) and            })

                        node.value.func.id == 'APIRouter'):

                        self.routers_in_file[var_name] = (node.lineno, 'fastapi.APIRouter')    report = {

                                "summary": {

                self.generic_visit(node)            "static_routes": len(static["routes"]),

                        "runtime_routes": len(runtime["routes"]),

            def visit_FunctionDef(self, node):            "unavailable_routes": len(missing),

                # Look for route decorators            "static_errors": len(static["errors"]),

                for decorator in node.decorator_list:            "runtime_errors": len(runtime["errors"]),

                    route_info = self.parse_route_decorator(decorator, node)        },

                    if route_info:        "unavailable_routes": missing,

                        route_info.file_path = relative_path        "static_errors": static["errors"],

                        route_info.function_name = node.name        "runtime_errors": runtime["errors"],

                        # Extract feature flags from the function body    }

                        route_info.feature_flags = self.auditor.extract_feature_flags(node)    print(json.dumps(report, indent=2))

                        self.auditor.static_routes.append(route_info)

                        if __name__ == "__main__":

                self.generic_visit(node)    main()

            
            def parse_route_decorator(self, decorator, func_node) -> RouteInfo | None:
                """Parse a route decorator to extract route information."""
                router_var = None
                method = None
                path = None
                include_in_schema = True
                line_number = decorator.lineno
                
                # Handle @router.get("/path"), @router.post("/path"), etc.
                if (isinstance(decorator, ast.Call) and
                    isinstance(decorator.func, ast.Attribute)):
                    
                    # Get router variable name
                    if isinstance(decorator.func.value, ast.Name):
                        router_var = decorator.func.value.id
                        method = decorator.func.attr.upper()
                        
                        # Get path from first argument
                        if decorator.args and isinstance(decorator.args[0], ast.Constant):
                            path = decorator.args[0].value
                            
                        # Check for include_in_schema keyword argument
                        for keyword in decorator.keywords:
                            if keyword.arg == 'include_in_schema':
                                if isinstance(keyword.value, ast.Constant):
                                    include_in_schema = keyword.value.value
                                    
                        if router_var and method and path:
                            return RouteInfo(
                                file_path="",  # Will be set by caller
                                line_number=line_number,
                                router_var=router_var,
                                method=method,
                                path=path,
                                include_in_schema=include_in_schema,
                                feature_flags=[],  # Will be set by caller
                                function_name=""  # Will be set by caller
                            )
                
                # Handle @app.get("/path") direct app decorators
                elif (isinstance(decorator, ast.Call) and
                      isinstance(decorator.func, ast.Attribute) and
                      isinstance(decorator.func.value, ast.Name)):
                    
                    router_var = decorator.func.value.id
                    method = decorator.func.attr.upper()
                    
                    if decorator.args and isinstance(decorator.args[0], ast.Constant):
                        path = decorator.args[0].value
                        
                    # Check for include_in_schema
                    for keyword in decorator.keywords:
                        if keyword.arg == 'include_in_schema':
                            if isinstance(keyword.value, ast.Constant):
                                include_in_schema = keyword.value.value
                                
                    if router_var and method and path:
                        return RouteInfo(
                            file_path="",
                            line_number=line_number,
                            router_var=router_var,
                            method=method,
                            path=path,
                            include_in_schema=include_in_schema,
                            feature_flags=[],
                            function_name=""
                        )
                
                return None
            
            def visit_Call(self, node):
                # Look for app.include_router() calls
                if (isinstance(node.func, ast.Attribute) and
                    isinstance(node.func.value, ast.Name) and
                    node.func.attr == 'include_router'):
                    
                    if node.args and isinstance(node.args[0], ast.Name):
                        router_name = node.args[0].id
                        # Mark this router as included
                        if router_name in self.routers_in_file:
                            line, imported_from = self.routers_in_file[router_name]
                            self.auditor.routers.append(RouterInfo(
                                file_path=relative_path,
                                line_number=line,
                                variable_name=router_name,
                                imported_from=imported_from,
                                included_anywhere=True
                            ))
                        
                self.generic_visit(node)
        
        visitor = RouteVisitor(self)
        visitor.visit(tree)
        
        # Add any routers that weren't included
        for router_name, (line, imported_from) in visitor.routers_in_file.items():
            # Check if we already recorded this router as included
            already_recorded = any(
                r.file_path == relative_path and r.variable_name == router_name
                for r in self.routers
            )
            if not already_recorded:
                self.routers.append(RouterInfo(
                    file_path=relative_path,
                    line_number=line,
                    variable_name=router_name,
                    imported_from=imported_from,
                    included_anywhere=False
                ))
    
    def get_runtime_routes(self):
        """Get routes from the running FastAPI application."""
        try:
            from app.main import app
            from fastapi.routing import APIRoute
            
            for route in app.routes:
                if isinstance(route, APIRoute):
                    for method in route.methods:
                        if method != 'HEAD':  # HEAD is auto-generated
                            self.runtime_routes.add((method, route.path))
                            
        except Exception as e:
            self.import_errors.append(f"Failed to import FastAPI app: {e}")
    
    def find_unavailable_routes(self) -> list[RouteInfo]:
        """Find routes that exist in code but not in runtime."""
        unavailable = []
        
        for route in self.static_routes:
            route_key = (route.method, route.path)
            if route_key not in self.runtime_routes:
                unavailable.append(route)
                
        return unavailable
    
    def run_audit(self):
        """Run the complete audit."""
        print("🔍 Starting FastAPI Route Audit...")
        print(f"📁 Scanning directory: {backend_root}")
        
        # Scan all Python files
        python_files = self.scan_python_files(backend_root / "app")
        print(f"📄 Found {len(python_files)} Python files")
        
        # Analyze each file
        for file_path in python_files:
            self.analyze_file(file_path)
            
        # Get runtime routes
        self.get_runtime_routes()
        
        # Find unavailable routes
        unavailable_routes = self.find_unavailable_routes()
        
        # Print results
        self.print_results(unavailable_routes)
        
    def print_results(self, unavailable_routes: list[RouteInfo]):
        """Print the audit results."""
        print("\n" + "="*80)
        print("📊 FASTAPI ROUTE AUDIT RESULTS")
        print("="*80)
        
        print(f"\n📈 SUMMARY:")
        print(f"  • Total static routes found: {len(self.static_routes)}")
        print(f"  • Total runtime routes: {len(self.runtime_routes)}")
        print(f"  • Unavailable routes: {len(unavailable_routes)}")
        print(f"  • Scan errors: {len(self.scan_errors)}")
        print(f"  • Import errors: {len(self.import_errors)}")
        
        if self.scan_errors:
            print(f"\n⚠️  SCAN ERRORS:")
            for error in self.scan_errors:
                print(f"  • {error}")
                
        if self.import_errors:
            print(f"\n⚠️  IMPORT ERRORS:")
            for error in self.import_errors:
                print(f"  • {error}")
        
        print(f"\n🌐 RUNTIME ROUTES ({len(self.runtime_routes)}):")
        for method, path in sorted(self.runtime_routes):
            print(f"  {method:8} {path}")
            
        if unavailable_routes:
            print(f"\n❌ UNAVAILABLE ROUTES ({len(unavailable_routes)}):")
            for route in unavailable_routes:
                reason = self.determine_unavailability_reason(route)
                flags_str = f" [flags: {', '.join(route.feature_flags)}]" if route.feature_flags else ""
                schema_str = "" if route.include_in_schema else " [hidden from schema]"
                print(f"  • {route.file_path}:{route.line_number}")
                print(f"    {route.method:8} {route.path}")
                print(f"    Router: {route.router_var}, Function: {route.function_name}{schema_str}{flags_str}")
                print(f"    Reason: {reason}")
                print()
        else:
            print(f"\n✅ ALL STATIC ROUTES ARE AVAILABLE AT RUNTIME!")
            
        # Show router inclusion status
        unincluded_routers = [r for r in self.routers if not r.included_anywhere]
        if unincluded_routers:
            print(f"\n🚫 UNINCLUDED ROUTERS ({len(unincluded_routers)}):")
            for router in unincluded_routers:
                print(f"  • {router.file_path}:{router.line_number} - {router.variable_name}")
                print(f"    Imported from: {router.imported_from}")
                
        print(f"\n✅ AUDIT COMPLETE")
    
    def determine_unavailability_reason(self, route: RouteInfo) -> str:
        """Determine why a route might be unavailable."""
        reasons = []
        
        # Check if router is never included
        router_included = any(
            r.variable_name == route.router_var and r.included_anywhere 
            for r in self.routers
        )
        
        if not router_included:
            reasons.append("router never included in app")
            
        if not route.include_in_schema:
            reasons.append("hidden from OpenAPI schema")
            
        if route.feature_flags:
            reasons.append("possibly gated by feature flags")
            
        if not reasons:
            reasons.append("unknown - check imports and app configuration")
            
        return ", ".join(reasons)

def main():
    auditor = RouteAuditor()
    auditor.run_audit()

if __name__ == "__main__":
    main()