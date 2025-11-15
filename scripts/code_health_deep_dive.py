#!/usr/bin/env python3
"""
ZiggyAI Master Code Health Deep Dive
Comprehensive automated quality assurance system.
"""

import asyncio
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


class CodeHealthResult:
    """Individual health check result."""

    def __init__(self, name: str, success: bool, details: dict[str, Any] = None):
        self.name = name
        self.success = success
        self.details = details or {}
        self.timestamp = datetime.now()
        self.duration_seconds = 0.0


class CodeHealthReport:
    """Master code health report."""

    def __init__(self):
        self.timestamp = datetime.now()
        self.results: list[CodeHealthResult] = []
        self.total_checks = 0
        self.passed_checks = 0
        self.failed_checks = 0
        self.warnings = 0
        self.critical_issues = 0

    def add_result(self, result: CodeHealthResult):
        """Add a health check result."""
        self.results.append(result)
        self.total_checks += 1
        if result.success:
            self.passed_checks += 1
        else:
            self.failed_checks += 1

    def get_success_rate(self) -> float:
        """Calculate overall success rate."""
        return (
            (self.passed_checks / self.total_checks * 100)
            if self.total_checks > 0
            else 0.0
        )


class ZiggyCodeHealthChecker:
    """Master code health checking system."""

    def __init__(self):
        self.report = CodeHealthReport()
        self.scripts_dir = Path("scripts")
        self.backend_dir = Path("backend")
        self.frontend_dir = Path("frontend")

    async def run_backend_syntax_check(self) -> CodeHealthResult:
        """Check Python syntax errors."""
        print("🐍 Checking Python syntax...")
        start_time = time.time()

        try:
            # Run ruff check
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "ruff",
                    "check",
                    "backend/",
                    "scripts/",
                    "*.py",
                    "--output-format=json",
                ],
                capture_output=True,
                text=True,
                cwd=".",
            )

            duration = time.time() - start_time

            if result.returncode == 0:
                health_result = CodeHealthResult(
                    "Python Syntax Check",
                    True,
                    {
                        "tool": "ruff",
                        "files_checked": "backend/, scripts/, *.py",
                        "issues_found": 0,
                    },
                )
            else:
                try:
                    issues = json.loads(result.stdout) if result.stdout else []
                except json.JSONDecodeError:
                    issues = []

                health_result = CodeHealthResult(
                    "Python Syntax Check",
                    False,
                    {
                        "tool": "ruff",
                        "files_checked": "backend/, scripts/, *.py",
                        "issues_found": len(issues),
                        "issues": issues[:10],  # First 10 issues
                        "stderr": result.stderr,
                    },
                )

            health_result.duration_seconds = duration
            return health_result

        except Exception as e:
            health_result = CodeHealthResult(
                "Python Syntax Check", False, {"error": str(e), "tool": "ruff"}
            )
            health_result.duration_seconds = time.time() - start_time
            return health_result

    async def run_frontend_syntax_check(self) -> CodeHealthResult:
        """Check TypeScript syntax errors."""
        print("⚛️  Checking TypeScript syntax...")
        start_time = time.time()

        try:
            # Run TypeScript compiler check
            result = subprocess.run(
                ["npx", "tsc", "--noEmit", "--project", "tsconfig.strict.json"],
                capture_output=True,
                text=True,
                cwd="frontend",
            )

            duration = time.time() - start_time

            if result.returncode == 0:
                health_result = CodeHealthResult(
                    "TypeScript Syntax Check",
                    True,
                    {
                        "tool": "tsc",
                        "config": "tsconfig.strict.json",
                        "errors_found": 0,
                    },
                )
            else:
                # Parse TypeScript errors
                error_lines = result.stdout.split("\n") if result.stdout else []
                errors = [line for line in error_lines if line.strip()]

                health_result = CodeHealthResult(
                    "TypeScript Syntax Check",
                    False,
                    {
                        "tool": "tsc",
                        "config": "tsconfig.strict.json",
                        "errors_found": len(errors),
                        "errors": errors[:15],  # First 15 errors
                        "stderr": result.stderr,
                    },
                )

            health_result.duration_seconds = duration
            return health_result

        except Exception as e:
            health_result = CodeHealthResult(
                "TypeScript Syntax Check", False, {"error": str(e), "tool": "tsc"}
            )
            health_result.duration_seconds = time.time() - start_time
            return health_result

    async def run_security_check(self) -> CodeHealthResult:
        """Check for security vulnerabilities."""
        print("🔒 Running security analysis...")
        start_time = time.time()

        try:
            # Run bandit security check
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "bandit",
                    "-r",
                    "backend/",
                    "scripts/",
                    "-f",
                    "json",
                    "-ll",  # Low confidence level
                ],
                capture_output=True,
                text=True,
                cwd=".",
            )

            duration = time.time() - start_time

            try:
                bandit_data = json.loads(result.stdout) if result.stdout else {}
                issues = bandit_data.get("results", [])

                critical_issues = [
                    i for i in issues if i.get("issue_severity") == "HIGH"
                ]

                health_result = CodeHealthResult(
                    "Security Check",
                    len(critical_issues) == 0,
                    {
                        "tool": "bandit",
                        "total_issues": len(issues),
                        "critical_issues": len(critical_issues),
                        "issues": issues[:5],  # First 5 issues
                        "summary": bandit_data.get("metrics", {}),
                    },
                )

            except json.JSONDecodeError:
                health_result = CodeHealthResult(
                    "Security Check",
                    result.returncode == 0,
                    {
                        "tool": "bandit",
                        "raw_output": result.stdout,
                        "stderr": result.stderr,
                    },
                )

            health_result.duration_seconds = duration
            return health_result

        except Exception as e:
            health_result = CodeHealthResult(
                "Security Check", False, {"error": str(e), "tool": "bandit"}
            )
            health_result.duration_seconds = time.time() - start_time
            return health_result

    async def run_endpoint_verification(self) -> CodeHealthResult:
        """Verify all API endpoints are functional."""
        print("🌐 Verifying API endpoints...")
        start_time = time.time()

        try:
            # Run endpoint verification script
            result = subprocess.run(
                [sys.executable, "scripts/verify_endpoints.py"],
                capture_output=True,
                text=True,
                cwd=".",
            )

            duration = time.time() - start_time

            # Check for report file
            latest_report = None
            reports_dir = Path("reports")
            if reports_dir.exists():
                report_files = list(reports_dir.glob("endpoint_report_*.json"))
                if report_files:
                    latest_report = max(report_files, key=lambda x: x.stat().st_mtime)

            if result.returncode == 0:
                health_result = CodeHealthResult(
                    "Endpoint Verification",
                    True,
                    {
                        "tool": "verify_endpoints.py",
                        "all_endpoints_healthy": True,
                        "report_file": str(latest_report) if latest_report else None,
                    },
                )
            else:
                health_result = CodeHealthResult(
                    "Endpoint Verification",
                    False,
                    {
                        "tool": "verify_endpoints.py",
                        "failed_endpoints": True,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "report_file": str(latest_report) if latest_report else None,
                    },
                )

            health_result.duration_seconds = duration
            return health_result

        except Exception as e:
            health_result = CodeHealthResult(
                "Endpoint Verification",
                False,
                {"error": str(e), "tool": "verify_endpoints.py"},
            )
            health_result.duration_seconds = time.time() - start_time
            return health_result

    async def run_duplicate_detection(self) -> CodeHealthResult:
        """Detect code duplications."""
        print("🔍 Detecting code duplications...")
        start_time = time.time()

        try:
            # Run duplicate detection script
            subprocess.run(
                [sys.executable, "scripts/detect_duplicates.py"],
                capture_output=True,
                text=True,
                cwd=".",
            )

            duration = time.time() - start_time

            # Check for report file
            latest_report = None
            reports_dir = Path("reports")
            if reports_dir.exists():
                report_files = list(reports_dir.glob("duplicate_code_report_*.json"))
                if report_files:
                    latest_report = max(report_files, key=lambda x: x.stat().st_mtime)

                    # Load report data
                    try:
                        with open(latest_report) as f:
                            report_data = json.load(f)
                        summary = report_data.get("summary", {})
                    except Exception:
                        summary = {}
                else:
                    summary = {}
            else:
                summary = {}

            critical_duplicates = summary.get("critical_duplications", 0)

            health_result = CodeHealthResult(
                "Duplicate Detection",
                critical_duplicates == 0,
                {
                    "tool": "detect_duplicates.py",
                    "total_duplications": summary.get("total_duplications", 0),
                    "critical_duplications": critical_duplicates,
                    "python_duplicates": summary.get("python_duplicates", 0),
                    "typescript_duplicates": summary.get("typescript_duplicates", 0),
                    "report_file": str(latest_report) if latest_report else None,
                },
            )

            health_result.duration_seconds = duration
            return health_result

        except Exception as e:
            health_result = CodeHealthResult(
                "Duplicate Detection",
                False,
                {"error": str(e), "tool": "detect_duplicates.py"},
            )
            health_result.duration_seconds = time.time() - start_time
            return health_result

    async def run_dead_code_detection(self) -> CodeHealthResult:
        """Detect unused/dead code."""
        print("🧹 Detecting dead code...")
        start_time = time.time()

        try:
            # Run vulture for Python dead code detection
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "vulture",
                    "backend/",
                    "scripts/",
                    "--min-confidence",
                    "80",
                ],
                capture_output=True,
                text=True,
                cwd=".",
            )

            duration = time.time() - start_time

            # Parse vulture output
            dead_code_lines = result.stdout.split("\n") if result.stdout else []
            dead_code_items = [line for line in dead_code_lines if line.strip()]

            health_result = CodeHealthResult(
                "Dead Code Detection",
                len(dead_code_items) < 10,
                {
                    "tool": "vulture",
                    "dead_code_items": len(dead_code_items),
                    "items": dead_code_items[:10],  # First 10 items
                    "threshold": "< 10 items acceptable",
                },
            )

            health_result.duration_seconds = duration
            return health_result

        except Exception as e:
            health_result = CodeHealthResult(
                "Dead Code Detection", False, {"error": str(e), "tool": "vulture"}
            )
            health_result.duration_seconds = time.time() - start_time
            return health_result

    async def run_all_checks(self) -> CodeHealthReport:
        """Run all code health checks."""
        print("🏥 Starting ZiggyAI Code Health Deep Dive...")
        print("=" * 60)

        # Run all checks
        checks = [
            self.run_backend_syntax_check(),
            self.run_frontend_syntax_check(),
            self.run_security_check(),
            self.run_dead_code_detection(),
            self.run_duplicate_detection(),
            self.run_endpoint_verification(),
        ]

        results = await asyncio.gather(*checks, return_exceptions=True)

        # Process results
        for result in results:
            if isinstance(result, Exception):
                error_result = CodeHealthResult(
                    "Unknown Check", False, {"error": str(result)}
                )
                self.report.add_result(error_result)
            else:
                self.report.add_result(result)

        return self.report

    def print_detailed_report(self):
        """Print comprehensive health report."""
        print("\n" + "=" * 60)
        print("🏥 ZIGGY CODE HEALTH DEEP DIVE REPORT")
        print("=" * 60)
        print(f"📅 Timestamp: {self.report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🧪 Total Checks: {self.report.total_checks}")
        print(f"✅ Passed: {self.report.passed_checks}")
        print(f"❌ Failed: {self.report.failed_checks}")
        print(f"📊 Success Rate: {self.report.get_success_rate():.1f}%")

        print("\n📋 DETAILED RESULTS:")
        print("-" * 40)

        for result in self.report.results:
            status = "✅" if result.success else "❌"
            duration = f"({result.duration_seconds:.2f}s)"
            print(f"{status} {result.name} {duration}")

            if not result.success and result.details:
                if "error" in result.details:
                    print(f"    Error: {result.details['error']}")
                if "issues_found" in result.details:
                    print(f"    Issues: {result.details['issues_found']}")
                if "critical_issues" in result.details:
                    print(f"    Critical: {result.details['critical_issues']}")

        # Overall health assessment
        print("\n🎯 HEALTH ASSESSMENT:")
        if self.report.get_success_rate() >= 90:
            print("🟢 EXCELLENT - Code health is excellent!")
        elif self.report.get_success_rate() >= 70:
            print("🟡 GOOD - Code health is acceptable with minor issues")
        elif self.report.get_success_rate() >= 50:
            print("🟠 FAIR - Code health needs attention")
        else:
            print("🔴 POOR - Critical code health issues detected!")

        print("=" * 60)

    def save_report(self) -> str:
        """Save comprehensive report to JSON."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"reports/code_health_report_{timestamp}.json"

        Path("reports").mkdir(exist_ok=True)

        report_data = {
            "timestamp": self.report.timestamp.isoformat(),
            "summary": {
                "total_checks": self.report.total_checks,
                "passed_checks": self.report.passed_checks,
                "failed_checks": self.report.failed_checks,
                "success_rate": self.report.get_success_rate(),
            },
            "results": [
                {
                    "name": r.name,
                    "success": r.success,
                    "timestamp": r.timestamp.isoformat(),
                    "duration_seconds": r.duration_seconds,
                    "details": r.details,
                }
                for r in self.report.results
            ],
        }

        with open(report_file, "w") as f:
            json.dump(report_data, f, indent=2)

        return report_file


async def main():
    """Main execution function."""
    checker = ZiggyCodeHealthChecker()

    try:
        # Run all health checks
        report = await checker.run_all_checks()

        # Print detailed report
        checker.print_detailed_report()

        # Save report
        report_file = checker.save_report()
        print(f"\n📄 Full report saved to: {report_file}")

        # Exit with appropriate code
        if report.get_success_rate() < 70:
            print("\n⚠️  Code health below acceptable threshold!")
            sys.exit(1)
        else:
            print("\n🎉 Code health check complete!")

    except KeyboardInterrupt:
        print("\n⚠️  Health check cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Health check failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
