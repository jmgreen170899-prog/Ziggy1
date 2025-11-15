#!/usr/bin/env python3
"""
Static Endpoint Audit - Find "do-nothing" endpoints

This script parses backend code to find FastAPI endpoints that:
- Have empty/pass-only bodies
- Raise NotImplementedError
- Return placeholder values without using inputs
- Are not annotated with "# pragma: placeholder-ok"

Exit codes:
  0: No issues found
  1: Found problematic endpoints
"""

import ast
import sys
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class EndpointIssue:
    """Represents a problematic endpoint"""

    file: str
    line: int
    method: str
    path: str
    reason: str


class EndpointVisitor(ast.NodeVisitor):
    """AST visitor to find FastAPI endpoints and analyze them"""

    def __init__(self, filepath: str, source_lines: List[str]):
        self.filepath = filepath
        self.source_lines = source_lines
        self.issues: List[EndpointIssue] = []
        self.in_router_decorator = False
        self.current_decorator_info = None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definitions to check if they're FastAPI endpoints"""
        # Check if function has FastAPI route decorators
        for decorator in node.decorator_list:
            endpoint_info = self._parse_decorator(decorator)
            if endpoint_info:
                # Check if endpoint has pragma comment
                if self._has_pragma_ok(node):
                    continue

                # Analyze the function body
                issue_reason = self._analyze_function_body(node)
                if issue_reason:
                    self.issues.append(
                        EndpointIssue(
                            file=self.filepath,
                            line=node.lineno,
                            method=endpoint_info["method"],
                            path=endpoint_info["path"],
                            reason=issue_reason,
                        )
                    )

        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definitions"""
        # Reuse the same logic as sync functions
        self.visit_FunctionDef(node)  # type: ignore

    def _parse_decorator(self, decorator: ast.expr) -> Dict[str, str] | None:
        """Parse a decorator to extract HTTP method and path"""
        # Handle @router.get("/path"), @router.post("/path"), etc.
        if isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Attribute):
                # Check if it's a router method (get, post, put, delete, patch)
                method_name = decorator.func.attr
                if method_name in [
                    "get",
                    "post",
                    "put",
                    "delete",
                    "patch",
                    "options",
                    "head",
                ]:
                    # Extract the path from the first argument
                    if decorator.args and isinstance(decorator.args[0], ast.Constant):
                        path = decorator.args[0].value
                        return {"method": method_name.upper(), "path": str(path)}

        # Handle @app.get("/path"), etc.
        if isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Attribute):
                if hasattr(decorator.func, "value") and isinstance(
                    decorator.func.value, ast.Name
                ):
                    if decorator.func.value.id in ["app", "router"]:
                        method_name = decorator.func.attr
                        if method_name in [
                            "get",
                            "post",
                            "put",
                            "delete",
                            "patch",
                            "options",
                            "head",
                        ]:
                            if decorator.args and isinstance(
                                decorator.args[0], ast.Constant
                            ):
                                path = decorator.args[0].value
                                return {
                                    "method": method_name.upper(),
                                    "path": str(path),
                                }

        return None

    def _has_pragma_ok(self, node: ast.FunctionDef) -> bool:
        """Check if function has '# pragma: placeholder-ok' comment"""
        # Check the line before the function definition
        if node.lineno > 1:
            prev_line = self.source_lines[node.lineno - 2].strip()
            if (
                "pragma: placeholder-ok" in prev_line
                or "pragma:placeholder-ok" in prev_line
            ):
                return True

        # Check first line of function
        if node.lineno < len(self.source_lines):
            func_line = self.source_lines[node.lineno - 1].strip()
            if (
                "pragma: placeholder-ok" in func_line
                or "pragma:placeholder-ok" in func_line
            ):
                return True

        # Check docstring
        if node.body and isinstance(node.body[0], ast.Expr):
            if isinstance(node.body[0].value, ast.Constant):
                docstring = node.body[0].value.value
                if isinstance(docstring, str) and "pragma: placeholder-ok" in docstring:
                    return True

        return False

    def _analyze_function_body(self, node: ast.FunctionDef) -> str | None:
        """Analyze function body to detect do-nothing patterns"""
        # Skip if no body
        if not node.body:
            return "Empty function body"

        # Get actual statements (skip docstring if present)
        statements = node.body
        if statements and isinstance(statements[0], ast.Expr):
            if isinstance(statements[0].value, ast.Constant):
                # First statement is a docstring, skip it
                statements = statements[1:]

        # Check for empty body after docstring
        if not statements:
            return "Empty function body (only docstring)"

        # Check for single pass statement
        if len(statements) == 1:
            stmt = statements[0]

            # Check for 'pass'
            if isinstance(stmt, ast.Pass):
                return "Function body is only 'pass'"

            # Check for '...' (Ellipsis)
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
                if stmt.value.value == Ellipsis or stmt.value.value == ...:
                    return "Function body is only '...'"

            # Check for raising NotImplementedError
            if isinstance(stmt, ast.Raise):
                if isinstance(stmt.exc, ast.Call):
                    if isinstance(stmt.exc.func, ast.Name):
                        if stmt.exc.func.id == "NotImplementedError":
                            return "Raises NotImplementedError"

            # Check for simple placeholder returns like {"ok": True}
            if isinstance(stmt, ast.Return):
                if self._is_placeholder_return(stmt, node):
                    return "Returns placeholder without using inputs"

        return None

    def _is_placeholder_return(self, stmt: ast.Return, func: ast.FunctionDef) -> bool:
        """Check if return statement is a simple placeholder"""
        if not stmt.value:
            return False

        # Check for {"ok": True} or similar simple dict literals
        if isinstance(stmt.value, ast.Dict):
            # Allow if function has no parameters (besides self/request)
            params = [arg.arg for arg in func.args.args]
            # Filter out common framework params
            user_params = [
                p
                for p in params
                if p not in ["self", "request", "req", "response", "resp"]
            ]

            if user_params and len(stmt.value.keys) <= 2:
                # Has user params but returns simple dict - might be placeholder
                # Check if it's just {"ok": True} or {"status": "..."}
                if all(isinstance(k, ast.Constant) for k in stmt.value.keys):
                    keys = [
                        k.value for k in stmt.value.keys if isinstance(k, ast.Constant)
                    ]
                    if set(keys) <= {"ok", "status", "message", "msg"}:
                        # Check if values are constants
                        if all(isinstance(v, ast.Constant) for v in stmt.value.values):
                            return True

        return False


def audit_file(filepath: Path) -> List[EndpointIssue]:
    """Audit a single Python file for problematic endpoints"""
    try:
        source = filepath.read_text(encoding="utf-8")
        source_lines = source.splitlines()
        tree = ast.parse(source, filename=str(filepath))

        visitor = EndpointVisitor(str(filepath), source_lines)
        visitor.visit(tree)

        return visitor.issues
    except SyntaxError:
        # Skip files with syntax errors
        return []
    except Exception as e:
        print(f"Warning: Failed to parse {filepath}: {e}", file=sys.stderr)
        return []


def audit_directory(root_dir: Path) -> List[EndpointIssue]:
    """Audit all Python files in a directory"""
    all_issues = []

    # Find all .py files
    for py_file in root_dir.rglob("*.py"):
        # Skip test files, migrations, __pycache__, etc.
        if any(
            part in py_file.parts
            for part in ["__pycache__", ".pytest_cache", "tests", "test", "migrations"]
        ):
            continue

        issues = audit_file(py_file)
        all_issues.extend(issues)

    return all_issues


def print_report(issues: List[EndpointIssue]) -> None:
    """Print a formatted report of issues"""
    if not issues:
        print("✅ No do-nothing endpoints found!")
        return

    print("=" * 100)
    print(f"❌ Found {len(issues)} problematic endpoint(s)")
    print("=" * 100)
    print()
    print(f"{'File:Line':<50} {'Method':<8} {'Path':<30} {'Reason':<30}")
    print("-" * 100)

    for issue in sorted(issues, key=lambda x: (x.file, x.line)):
        location = f"{issue.file}:{issue.line}"
        print(f"{location:<50} {issue.method:<8} {issue.path:<30} {issue.reason:<30}")

    print()
    print("=" * 100)
    print(
        "To mark an endpoint as intentionally placeholder, add: # pragma: placeholder-ok"
    )
    print("=" * 100)


def main() -> int:
    """Main entry point"""
    # Find backend directory
    script_dir = Path(__file__).parent
    backend_dir = script_dir.parent
    app_dir = backend_dir / "app"

    if not app_dir.exists():
        print(f"Error: app directory not found at {app_dir}", file=sys.stderr)
        return 1

    print(f"Scanning {app_dir} for do-nothing endpoints...")
    print()

    issues = audit_directory(app_dir)
    print_report(issues)

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
