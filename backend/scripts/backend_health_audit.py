#!/usr/bin/env python3
"""
Backend Code Health Audit - Comprehensive analysis of backend codebase
"""

import asyncio
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx


class BackendHealthAudit:
    def __init__(self, backend_path: str = ".", base_url: str = "http://localhost:8000"):
        self.backend_path = Path(backend_path)
        self.base_url = base_url
        self.artifacts_dir = Path("../artifacts/backend")
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def run_command(self, command: list[str], cwd: Path = None) -> dict[str, Any]:
        """Run a shell command and capture output"""
        try:
            result = subprocess.run(
                command, cwd=cwd or self.backend_path, capture_output=True, text=True, timeout=300
            )

            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(command),
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": "Command timed out",
                "command": " ".join(command),
            }
        except Exception as e:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "command": " ".join(command),
            }

    def run_ruff_check(self) -> dict[str, Any]:
        """Run ruff linter on backend code"""
        print("🔍 Running ruff syntax/style check...")

        result = self.run_command(
            [
                "ruff",
                "check",
                ".",
                "--format",
                "json",
                "--output-file",
                str(self.artifacts_dir / "ruff_report.json"),
            ]
        )

        # Also run without JSON for console output
        console_result = self.run_command(["ruff", "check", "."])

        return {
            "tool": "ruff",
            "success": result["success"],
            "console_output": console_result["stdout"],
            "errors": result["stderr"],
            "report_file": str(self.artifacts_dir / "ruff_report.json"),
        }

    def run_mypy_check(self) -> dict[str, Any]:
        """Run mypy type checking"""
        print("🔍 Running mypy type check...")

        result = self.run_command(
            [
                "mypy",
                ".",
                "--ignore-missing-imports",
                "--show-error-codes",
                "--json-report",
                str(self.artifacts_dir / "mypy_report"),
            ]
        )

        return {
            "tool": "mypy",
            "success": result["success"],
            "output": result["stdout"],
            "errors": result["stderr"],
            "report_dir": str(self.artifacts_dir / "mypy_report"),
        }

    def run_bandit_security_check(self) -> dict[str, Any]:
        """Run bandit security analysis"""
        print("🔍 Running bandit security check...")

        result = self.run_command(
            [
                "bandit",
                "-r",
                ".",
                "-f",
                "json",
                "-o",
                str(self.artifacts_dir / "bandit_report.json"),
            ]
        )

        # Also run for console output
        console_result = self.run_command(["bandit", "-r", "."])

        return {
            "tool": "bandit",
            "success": result["success"],
            "console_output": console_result["stdout"],
            "errors": result["stderr"],
            "report_file": str(self.artifacts_dir / "bandit_report.json"),
        }

    def run_vulture_dead_code(self) -> dict[str, Any]:
        """Run vulture to find dead code"""
        print("🔍 Running vulture dead code detection...")

        # Create a basic whitelist file
        whitelist_content = """
# Vulture whitelist for common false positives
*.test_*
*.conftest
*.__init__
*.main
*.app
        """

        whitelist_path = self.artifacts_dir / "vulture_whitelist.py"
        with open(whitelist_path, "w") as f:
            f.write(whitelist_content.strip())

        result = self.run_command(["vulture", ".", str(whitelist_path), "--json"])

        # Save JSON output
        if result["success"] and result["stdout"]:
            try:
                json_data = json.loads(result["stdout"])
                with open(self.artifacts_dir / "vulture_report.json", "w") as f:
                    json.dump(json_data, f, indent=2)
            except json.JSONDecodeError:
                # Fallback: save raw output
                with open(self.artifacts_dir / "vulture_report.txt", "w") as f:
                    f.write(result["stdout"])

        return {
            "tool": "vulture",
            "success": result["success"],
            "output": result["stdout"],
            "errors": result["stderr"],
            "report_file": str(self.artifacts_dir / "vulture_report.json"),
        }

    def run_jscpd_duplication(self) -> dict[str, Any]:
        """Run jscpd to find code duplication"""
        print("🔍 Running jscpd duplication detection...")

        result = self.run_command(
            [
                "jscpd",
                ".",
                "--min-lines",
                "5",
                "--min-tokens",
                "50",
                "--format",
                "python",
                "--reporters",
                "json",
                "--output",
                str(self.artifacts_dir),
            ]
        )

        return {
            "tool": "jscpd",
            "success": result["success"],
            "output": result["stdout"],
            "errors": result["stderr"],
            "report_file": str(self.artifacts_dir / "jscpd-report.json"),
        }

    async def run_endpoint_smoke_tests(self) -> dict[str, Any]:
        """Run endpoint smoke tests"""
        print("🔍 Running API endpoint smoke tests...")

        try:
            # Import and run the smoke test
            sys.path.append(str(self.backend_path))
            from tests.test_endpoints_smoke import EndpointSmokeTest

            async with EndpointSmokeTest(self.base_url) as tester:
                summary = await tester.run_smoke_tests()

                # Save results
                report_path = self.artifacts_dir / "endpoints_failures.json"
                with open(report_path, "w") as f:
                    json.dump(summary, f, indent=2)

                return {
                    "tool": "endpoint_smoke_test",
                    "success": summary["failed"] == 0,
                    "summary": summary,
                    "report_file": str(report_path),
                }

        except Exception as e:
            return {
                "tool": "endpoint_smoke_test",
                "success": False,
                "error": str(e),
                "report_file": str(self.artifacts_dir / "endpoints_failures.json"),
            }

    def run_schemathesis_fuzz(self) -> dict[str, Any]:
        """Run schemathesis API fuzzing"""
        print("🔍 Running schemathesis API fuzzing...")

        try:
            # Run the schemathesis script
            result = self.run_command(
                [
                    "python",
                    "scripts/run_schemathesis.py",
                    "--base-url",
                    self.base_url,
                    "--output",
                    str(self.artifacts_dir / "schemathesis_report.json"),
                    "--max-examples",
                    "25",
                ]
            )

            return {
                "tool": "schemathesis",
                "success": result["success"],
                "output": result["stdout"],
                "errors": result["stderr"],
                "report_file": str(self.artifacts_dir / "schemathesis_report.json"),
            }

        except Exception as e:
            return {
                "tool": "schemathesis",
                "success": False,
                "error": str(e),
                "report_file": str(self.artifacts_dir / "schemathesis_report.json"),
            }

    async def check_health_endpoint(self) -> dict[str, Any]:
        """Check the health endpoint specifically"""
        print("🔍 Checking /paper/health endpoint...")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/paper/health")

                if response.status_code == 200:
                    health_data = response.json()

                    # Validate expected fields
                    expected_fields = [
                        "paper_enabled",
                        "strict_isolation",
                        "broker",
                        "recent_trades_5m",
                        "total_trades_today",
                        "last_trade_at",
                        "db_ok",
                    ]

                    missing_fields = [
                        field for field in expected_fields if field not in health_data
                    ]

                    return {
                        "tool": "health_endpoint",
                        "success": len(missing_fields) == 0,
                        "status_code": response.status_code,
                        "response": health_data,
                        "missing_fields": missing_fields,
                        "url": f"{self.base_url}/paper/health",
                    }
                else:
                    return {
                        "tool": "health_endpoint",
                        "success": False,
                        "status_code": response.status_code,
                        "error": response.text,
                        "url": f"{self.base_url}/paper/health",
                    }

        except Exception as e:
            return {
                "tool": "health_endpoint",
                "success": False,
                "error": str(e),
                "url": f"{self.base_url}/paper/health",
            }

    async def run_full_audit(self) -> dict[str, Any]:
        """Run complete backend health audit"""
        print("🚀 Starting Backend Health Audit...")
        print(f"📁 Backend path: {self.backend_path}")
        print(f"🌐 API URL: {self.base_url}")
        print(f"📊 Artifacts: {self.artifacts_dir}")

        results = {
            "timestamp": datetime.now().isoformat(),
            "backend_path": str(self.backend_path),
            "base_url": self.base_url,
            "artifacts_dir": str(self.artifacts_dir),
            "audits": {},
        }

        # Run all audits
        audit_functions = [
            ("syntax_check", self.run_ruff_check),
            ("type_check", self.run_mypy_check),
            ("security_check", self.run_bandit_security_check),
            ("dead_code", self.run_vulture_dead_code),
            ("duplication", self.run_jscpd_duplication),
            ("endpoint_smoke", self.run_endpoint_smoke_tests),
            ("health_endpoint", self.check_health_endpoint),
            ("api_fuzz", self.run_schemathesis_fuzz),
        ]

        for audit_name, audit_func in audit_functions:
            try:
                print(f"\\n📋 Running {audit_name}...")
                if asyncio.iscoroutinefunction(audit_func):
                    result = await audit_func()
                else:
                    result = audit_func()

                results["audits"][audit_name] = result

                status = "✅" if result.get("success", False) else "❌"
                print(f"{status} {audit_name} completed")

            except Exception as e:
                print(f"💥 {audit_name} failed: {e}")
                results["audits"][audit_name] = {
                    "tool": audit_name,
                    "success": False,
                    "error": str(e),
                }

        # Save comprehensive results
        results_path = self.artifacts_dir / "backend_audit_results.json"
        with open(results_path, "w") as f:
            json.dump(results, f, indent=2)

        print(f"\\n📊 Full audit results saved: {results_path}")
        return results

    def generate_summary_report(self, results: dict[str, Any]) -> str:
        """Generate human-readable summary report"""

        audits = results["audits"]
        total_audits = len(audits)
        successful_audits = sum(1 for audit in audits.values() if audit.get("success", False))

        report = f"""# Backend API Health Report

Generated: {results["timestamp"]}
Backend Path: {results["backend_path"]}
API URL: {results["base_url"]}

## Executive Summary

- **Total Audits**: {total_audits}
- **Successful**: {successful_audits} ✅
- **Failed**: {total_audits - successful_audits} ❌
- **Success Rate**: {successful_audits / total_audits * 100:.1f}%

## Audit Results

"""

        for audit_name, audit_result in audits.items():
            status = "✅" if audit_result.get("success", False) else "❌"
            tool = audit_result.get("tool", audit_name)

            report += f"### {status} {tool.title()}\n\n"

            if audit_result.get("success", False):
                report += "No issues found.\\n\\n"
            else:
                if "error" in audit_result:
                    report += f"**Error**: {audit_result['error']}\\n\\n"
                if audit_result.get("output"):
                    report += f"**Output**: {audit_result['output'][:200]}...\\n\\n"

            if "report_file" in audit_result:
                report += f"**Details**: See {audit_result['report_file']}\\n\\n"

        # Priority issues
        p0_issues = []
        p1_issues = []

        for audit_name, audit_result in audits.items():
            if not audit_result.get("success", False):
                if audit_name in ["endpoint_smoke", "health_endpoint"]:
                    p0_issues.append(f"**{audit_name}**: {audit_result.get('error', 'Failed')}")
                else:
                    p1_issues.append(f"**{audit_name}**: {audit_result.get('error', 'Failed')}")

        if p0_issues:
            report += "## 🚨 P0 Issues (Critical)\n\n"
            for issue in p0_issues:
                report += f"- {issue}\\n"
            report += "\\n"

        if p1_issues:
            report += "## ⚠️ P1 Issues (High Priority)\n\n"
            for issue in p1_issues:
                report += f"- {issue}\\n"
            report += "\\n"

        report += f"""## 📁 Artifacts

All detailed reports are available in: `{results["artifacts_dir"]}/`

- [Backend Audit Results](artifacts/backend/backend_audit_results.json)
- [Endpoint Failures](artifacts/backend/endpoints_failures.json)
- [Ruff Report](artifacts/backend/ruff_report.json)
- [Bandit Security Report](artifacts/backend/bandit_report.json)
- [Vulture Dead Code](artifacts/backend/vulture_report.json)

## 🎯 Action Items

### Immediate (P0)
"""

        for i, issue in enumerate(p0_issues, 1):
            report += f"- [ ] **P0-{i}**: {issue.replace('**', '').replace(':', ' -')}\\n"

        report += "\\n### High Priority (P1)\\n"

        for i, issue in enumerate(p1_issues, 1):
            report += f"- [ ] **P1-{i}**: {issue.replace('**', '').replace(':', ' -')}\\n"

        return report


async def main():
    """Main entry point"""
    backend_path = sys.argv[1] if len(sys.argv) > 1 else "."
    base_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8000"

    auditor = BackendHealthAudit(backend_path, base_url)
    results = await auditor.run_full_audit()

    # Generate markdown report
    report = auditor.generate_summary_report(results)
    report_path = Path("API_HEALTH_REPORT.md")

    with open(report_path, "w") as f:
        f.write(report)

    print(f"\\n📝 Summary report generated: {report_path}")

    # Exit with appropriate code
    failed_audits = sum(
        1 for audit in results["audits"].values() if not audit.get("success", False)
    )

    if failed_audits > 0:
        print(f"\\n💥 {failed_audits} audits failed!")
        sys.exit(1)
    else:
        print("\\n🎉 All audits passed!")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
