#!/usr/bin/env python3
"""
ZiggyAI Duplicate Code Detection System
Find code duplications across Python and TypeScript/React files.
"""

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


class DuplicateReport:
    """Code duplication analysis report."""

    def __init__(self):
        self.timestamp = datetime.now()
        self.python_duplicates: list[dict[str, Any]] = []
        self.typescript_duplicates: list[dict[str, Any]] = []
        self.total_files_scanned = 0
        self.total_duplications = 0
        self.critical_duplications = 0

    def add_python_duplicate(self, duplicate: dict[str, Any]):
        """Add Python code duplication."""
        self.python_duplicates.append(duplicate)
        self.total_duplications += 1
        if duplicate.get("lines", 0) > 20:  # Critical if >20 lines
            self.critical_duplications += 1

    def add_typescript_duplicate(self, duplicate: dict[str, Any]):
        """Add TypeScript/React duplication."""
        self.typescript_duplicates.append(duplicate)
        self.total_duplications += 1
        if duplicate.get("lines", 0) > 15:  # Critical if >15 lines
            self.critical_duplications += 1


class ZiggyDuplicateDetector:
    """Comprehensive duplicate code detection for ZiggyAI."""

    def __init__(self):
        self.root_path = Path(".")
        self.report = DuplicateReport()

        # Python file patterns
        self.python_patterns = ["backend/**/*.py", "scripts/**/*.py", "*.py"]

        # TypeScript/React patterns
        self.frontend_patterns = [
            "frontend/src/**/*.ts",
            "frontend/src/**/*.tsx",
            "frontend/pages/**/*.ts",
            "frontend/pages/**/*.tsx",
            "frontend/components/**/*.ts",
            "frontend/components/**/*.tsx",
        ]

    def find_python_files(self) -> list[Path]:
        """Find all Python files to analyze."""
        files = []
        for pattern in self.python_patterns:
            files.extend(self.root_path.glob(pattern))

        # Filter out __pycache__, .venv, etc.
        return [
            f
            for f in files
            if not any(part.startswith(".") or part == "__pycache__" for part in f.parts)
        ]

    def find_frontend_files(self) -> list[Path]:
        """Find all TypeScript/React files to analyze."""
        files = []
        for pattern in self.frontend_patterns:
            files.extend(self.root_path.glob(pattern))

        # Filter out node_modules, .next, etc.
        return [
            f
            for f in files
            if not any(
                part in ["node_modules", ".next", "build", "dist", "coverage"] for part in f.parts
            )
        ]

    def analyze_python_similarity(self, files: list[Path]) -> None:
        """Analyze Python code for duplications using simple heuristics."""
        print("🐍 Analyzing Python code duplications...")

        # Extract function definitions and their content
        functions = {}

        for file_path in files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                # Find function definitions
                func_pattern = r"def\s+(\w+)\s*\([^)]*\):[^\\n]*\\n((?:\s+.*\\n)*)"
                matches = re.finditer(func_pattern, content, re.MULTILINE)

                for match in matches:
                    func_name = match.group(1)
                    func_body = match.group(2).strip()

                    if len(func_body) > 100:  # Only check substantial functions
                        if func_body in functions:
                            # Found duplicate!
                            original_file = functions[func_body]["file"]
                            duplicate = {
                                "type": "function",
                                "name": func_name,
                                "original_file": str(original_file),
                                "duplicate_file": str(file_path),
                                "lines": len(func_body.split("\\n")),
                                "body_hash": hash(func_body),
                                "similarity": "exact",
                            }
                            self.report.add_python_duplicate(duplicate)
                        else:
                            functions[func_body] = {"file": file_path, "name": func_name}

            except Exception as e:
                print(f"⚠️  Error analyzing {file_path}: {e}")

    def analyze_frontend_similarity(self, files: list[Path]) -> None:
        """Analyze TypeScript/React code for duplications."""
        print("⚛️  Analyzing TypeScript/React code duplications...")

        # Extract React components and functions
        components = {}

        for file_path in files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                # Find React component definitions
                component_patterns = [
                    r"export\s+(?:default\s+)?(?:function|const)\s+(\w+)[^{]*{([^}]+(?:{[^}]*}[^}]*)*)}",
                    r"const\s+(\w+)\s*[:=][^{]*{([^}]+(?:{[^}]*}[^}]*)*)}",
                ]

                for pattern in component_patterns:
                    matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)

                    for match in matches:
                        comp_name = match.group(1)
                        comp_body = match.group(2).strip()

                        if len(comp_body) > 200:  # Only check substantial components
                            # Normalize whitespace for comparison
                            normalized_body = re.sub(r"\\s+", " ", comp_body)

                            if normalized_body in components:
                                # Found duplicate!
                                original_file = components[normalized_body]["file"]
                                duplicate = {
                                    "type": "component",
                                    "name": comp_name,
                                    "original_file": str(original_file),
                                    "duplicate_file": str(file_path),
                                    "lines": len(comp_body.split("\\n")),
                                    "body_hash": hash(normalized_body),
                                    "similarity": "high",
                                }
                                self.report.add_typescript_duplicate(duplicate)
                            else:
                                components[normalized_body] = {"file": file_path, "name": comp_name}

            except Exception as e:
                print(f"⚠️  Error analyzing {file_path}: {e}")

    def check_common_patterns(self) -> None:
        """Check for common anti-patterns and code smells."""
        print("🔍 Checking for common code patterns...")

        # Check for repeated API endpoint patterns
        api_patterns = {}

        # Scan backend routes for similar patterns
        backend_files = list(Path("backend/app").glob("**/*.py"))

        for file_path in backend_files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                # Look for route definitions
                route_pattern = r'@router\\.(get|post|put|delete)\\(["\']([^"\']+)["\']\\)'
                matches = re.finditer(route_pattern, content)

                for match in matches:
                    method = match.group(1)
                    path = match.group(2)
                    pattern_key = f"{method}:{path}"

                    if pattern_key in api_patterns:
                        duplicate = {
                            "type": "api_route",
                            "pattern": pattern_key,
                            "original_file": str(api_patterns[pattern_key]),
                            "duplicate_file": str(file_path),
                            "lines": 1,
                            "severity": "warning",
                        }
                        self.report.add_python_duplicate(duplicate)
                    else:
                        api_patterns[pattern_key] = file_path

            except Exception as e:
                print(f"⚠️  Error checking patterns in {file_path}: {e}")

    def run_jscpd_if_available(self) -> dict[str, Any] | None:
        """Run jscpd tool if available for comprehensive duplicate detection."""
        try:
            # Check if jscpd is installed
            result = subprocess.run(
                ["npx", "jscpd", "--version"], capture_output=True, text=True, cwd="frontend"
            )

            if result.returncode == 0:
                print("🔧 Running jscpd for comprehensive duplicate detection...")

                # Run jscpd on frontend
                cmd = [
                    "npx",
                    "jscpd",
                    "--min-lines",
                    "5",
                    "--min-tokens",
                    "50",
                    "--formats",
                    "typescript,tsx,javascript,jsx",
                    "--output",
                    "../reports/jscpd-report.json",
                    "--reporters",
                    "json",
                    "src/",
                ]

                result = subprocess.run(cmd, cwd="frontend", capture_output=True, text=True)

                if result.returncode == 0 and Path("reports/jscpd-report.json").exists():
                    with open("reports/jscpd-report.json") as f:
                        return json.load(f)

        except Exception as e:
            print(f"⚠️  jscpd not available: {e}")

        return None

    def generate_report(self) -> str:
        """Generate comprehensive duplicate code report."""
        # Count files
        python_files = self.find_python_files()
        frontend_files = self.find_frontend_files()
        self.report.total_files_scanned = len(python_files) + len(frontend_files)

        # Run analysis
        self.analyze_python_similarity(python_files)
        self.analyze_frontend_similarity(frontend_files)
        self.check_common_patterns()

        # Try jscpd for additional analysis
        jscpd_data = self.run_jscpd_if_available()

        # Generate report
        report_data = {
            "timestamp": self.report.timestamp.isoformat(),
            "summary": {
                "total_files_scanned": self.report.total_files_scanned,
                "total_duplications": self.report.total_duplications,
                "critical_duplications": self.report.critical_duplications,
                "python_duplicates": len(self.report.python_duplicates),
                "typescript_duplicates": len(self.report.typescript_duplicates),
            },
            "python_duplicates": self.report.python_duplicates,
            "typescript_duplicates": self.report.typescript_duplicates,
            "jscpd_analysis": jscpd_data,
        }

        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"reports/duplicate_code_report_{timestamp}.json"
        Path("reports").mkdir(exist_ok=True)

        with open(report_file, "w") as f:
            json.dump(report_data, f, indent=2)

        return report_file

    def print_summary(self):
        """Print duplicate code summary."""
        print("\\n" + "=" * 60)
        print("🔍 ZIGGY DUPLICATE CODE ANALYSIS")
        print("=" * 60)
        print(f"📁 Files Scanned: {self.report.total_files_scanned}")
        print(f"🔄 Total Duplications: {self.report.total_duplications}")
        print(f"⚠️  Critical Duplications: {self.report.critical_duplications}")
        print(f"🐍 Python Duplicates: {len(self.report.python_duplicates)}")
        print(f"⚛️  TypeScript Duplicates: {len(self.report.typescript_duplicates)}")

        if self.report.critical_duplications > 0:
            print("\\n❌ CRITICAL DUPLICATIONS FOUND:")
            for dup in self.report.python_duplicates + self.report.typescript_duplicates:
                if dup.get("lines", 0) > 15:
                    print(f"  📄 {dup['name']} ({dup['lines']} lines)")
                    print(f"     Original: {dup['original_file']}")
                    print(f"     Duplicate: {dup['duplicate_file']}")

        success = self.report.total_duplications == 0
        if success:
            print("\\n🎉 No significant code duplications found!")
        else:
            print(f"\\n⚠️  Found {self.report.total_duplications} duplications")

        print("=" * 60)


def main():
    """Main execution function."""
    detector = ZiggyDuplicateDetector()

    try:
        print("🔍 Starting ZiggyAI duplicate code detection...")

        report_file = detector.generate_report()
        detector.print_summary()

        print(f"\\n📄 Report saved to: {report_file}")

        # Exit with error if critical duplications found
        if detector.report.critical_duplications > 0:
            print(f"\\n⚠️  {detector.report.critical_duplications} critical duplications found!")
            sys.exit(1)
        else:
            print("\\n✅ Code duplication analysis complete!")

    except KeyboardInterrupt:
        print("\\n⚠️  Analysis cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\\n❌ Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
