#!/usr/bin/env python3
"""
Generate consolidated Code Health Report for ZiggyAI
Combines frontend and backend audit results into a single actionable report
"""
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


class CodeHealthReportGenerator:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.artifacts_dir = self.project_root / "artifacts"

    def load_frontend_results(self) -> dict[str, Any]:
        """Load frontend audit results"""
        results = {
            "ui_audit": None,
            "lighthouse": None,
            "jscpd": None,
            "type_check": None,
            "lint_check": None,
        }

        # UI audit results
        ui_audit_path = self.artifacts_dir / "ui" / "ui_audit_results.json"
        if ui_audit_path.exists():
            with open(ui_audit_path) as f:
                results["ui_audit"] = json.load(f)

        # Lighthouse results
        lighthouse_path = self.artifacts_dir / "ui" / "lighthouse_summary.json"
        if lighthouse_path.exists():
            with open(lighthouse_path) as f:
                results["lighthouse"] = json.load(f)

        # Frontend duplication
        jscpd_path = self.artifacts_dir / "frontend" / "jscpd-report.json"
        if jscpd_path.exists():
            with open(jscpd_path) as f:
                results["jscpd"] = json.load(f)

        return results

    def load_backend_results(self) -> dict[str, Any]:
        """Load backend audit results"""
        results = {
            "audit_summary": None,
            "endpoints": None,
            "schemathesis": None,
            "security": None,
            "dead_code": None,
        }

        # Main backend audit results
        audit_path = self.artifacts_dir / "backend" / "backend_audit_results.json"
        if audit_path.exists():
            with open(audit_path) as f:
                results["audit_summary"] = json.load(f)

        # Endpoint smoke test results
        endpoints_path = self.artifacts_dir / "backend" / "endpoints_failures.json"
        if endpoints_path.exists():
            with open(endpoints_path) as f:
                results["endpoints"] = json.load(f)

        # Schemathesis fuzzing results
        schema_path = self.artifacts_dir / "backend" / "schemathesis_report.json"
        if schema_path.exists():
            with open(schema_path) as f:
                results["schemathesis"] = json.load(f)

        return results

    def analyze_p0_issues(
        self, frontend_results: dict, backend_results: dict
    ) -> list[str]:
        """Identify P0 (critical) issues"""
        p0_issues = []

        # Frontend P0 issues
        if frontend_results.get("ui_audit"):
            for result in frontend_results["ui_audit"]:
                if result.get("status") == "error":
                    p0_issues.append(
                        f"🚨 Frontend route **{result['route']}** completely broken: {result.get('error', 'Unknown error')}"
                    )

                if result.get("metrics", {}).get("consoleErrors"):
                    error_count = len(result["metrics"]["consoleErrors"])
                    if error_count > 0:
                        p0_issues.append(
                            f"🚨 Frontend **{result['route']}** has {error_count} console errors"
                        )

                if result.get("metrics", {}).get("nanCells", 0) > 0:
                    p0_issues.append(
                        f"🚨 Frontend **{result['route']}** displays NaN values in UI"
                    )

        # Backend P0 issues
        if backend_results.get("endpoints"):
            failed_endpoints = backend_results["endpoints"].get("failures", [])
            for failure in failed_endpoints:
                if failure.get("status_code", 0) >= 500:
                    p0_issues.append(
                        f"🚨 API endpoint **{failure['method']} {failure['path']}** returns 5xx error: {failure.get('error', 'Unknown error')}"
                    )

        if backend_results.get("audit_summary"):
            audits = backend_results["audit_summary"].get("audits", {})

            # Health endpoint failures
            health_audit = audits.get("health_endpoint", {})
            if not health_audit.get("success", True):
                p0_issues.append(
                    f"🚨 Health endpoint `/paper/health` is broken: {health_audit.get('error', 'Unknown error')}"
                )

            # Endpoint smoke test failures
            smoke_audit = audits.get("endpoint_smoke", {})
            if not smoke_audit.get("success", True):
                summary = smoke_audit.get("summary", {})
                failed_count = summary.get("failed", 0)
                if failed_count > 0:
                    p0_issues.append(
                        f"🚨 {failed_count} API endpoints completely failing"
                    )

        return p0_issues

    def analyze_p1_issues(
        self, frontend_results: dict, backend_results: dict
    ) -> list[str]:
        """Identify P1 (high priority) issues"""
        p1_issues = []

        # Frontend P1 issues
        if frontend_results.get("ui_audit"):
            for result in frontend_results["ui_audit"]:
                metrics = result.get("metrics", {})

                if metrics.get("missingFields"):
                    count = len(metrics["missingFields"])
                    if count > 0:
                        p1_issues.append(
                            f"⚠️ Frontend **{result['route']}** has {count} missing/empty data fields"
                        )

                if metrics.get("networkErrors"):
                    count = len(metrics["networkErrors"])
                    if count > 0:
                        p1_issues.append(
                            f"⚠️ Frontend **{result['route']}** has {count} network errors"
                        )

        if frontend_results.get("lighthouse"):
            for result in frontend_results["lighthouse"]:
                scores = result.get("scores", {})

                perf = scores.get("performance", 100)
                if perf < 70:
                    p1_issues.append(
                        f"⚠️ Frontend **{result['route']}** poor performance score: {perf}%"
                    )

                a11y = scores.get("accessibility", 100)
                if a11y < 80:
                    p1_issues.append(
                        f"⚠️ Frontend **{result['route']}** accessibility issues: {a11y}%"
                    )

                cls = result.get("metrics", {}).get("cumulativeLayoutShift", 0)
                if cls > 0.1:
                    p1_issues.append(
                        f"⚠️ Frontend **{result['route']}** high layout shift: {cls:.3f}"
                    )

        # Backend P1 issues
        if backend_results.get("audit_summary"):
            audits = backend_results["audit_summary"].get("audits", {})

            for audit_name, audit_result in audits.items():
                if not audit_result.get("success", True) and audit_name not in [
                    "endpoint_smoke",
                    "health_endpoint",
                ]:
                    error = audit_result.get("error", "Failed")
                    p1_issues.append(
                        f"⚠️ Backend **{audit_name}** check failed: {error}"
                    )

        if backend_results.get("endpoints"):
            failures = backend_results["endpoints"].get("failures", [])
            for failure in failures:
                status = failure.get("status_code", 0)
                if 400 <= status < 500:
                    p1_issues.append(
                        f"⚠️ API endpoint **{failure['method']} {failure['path']}** returns 4xx: {failure.get('error', 'Unknown')}"
                    )

        return p1_issues

    def analyze_p2_issues(
        self, frontend_results: dict, backend_results: dict
    ) -> list[str]:
        """Identify P2 (polish/optimization) issues"""
        p2_issues = []

        # Frontend P2 issues
        if frontend_results.get("jscpd"):
            duplicates = frontend_results["jscpd"].get("duplicates", [])
            if duplicates:
                p2_issues.append(
                    f"📝 Frontend has {len(duplicates)} code duplication blocks"
                )

        if frontend_results.get("ui_audit"):
            for result in frontend_results["ui_audit"]:
                load_time = result.get("metrics", {}).get("loadTime", 0)
                if load_time > 5000:
                    p2_issues.append(
                        f"📝 Frontend **{result['route']}** slow load time: {load_time:.0f}ms"
                    )

        # Backend P2 issues - dead code, duplications, etc.
        if backend_results.get("audit_summary"):
            audits = backend_results["audit_summary"].get("audits", {})

            dead_code = audits.get("dead_code", {})
            if (
                dead_code.get("success") is False
                and "unused" in dead_code.get("output", "").lower()
            ):
                p2_issues.append("📝 Backend has unused/dead code detected")

            duplication = audits.get("duplication", {})
            if duplication.get("success") is False:
                p2_issues.append("📝 Backend has code duplication issues")

        return p2_issues

    def generate_action_items(
        self, p0_issues: list[str], p1_issues: list[str], p2_issues: list[str]
    ) -> str:
        """Generate actionable checklist"""

        action_items = "## ✅ Action Items Checklist\\n\\n"

        action_items += "### 🚨 Immediate (P0) - Fix Before Production\\n\\n"
        if p0_issues:
            for i, issue in enumerate(p0_issues, 1):
                clean_issue = issue.replace("🚨 ", "").replace("**", "")
                action_items += f"- [ ] **P0-{i}**: {clean_issue}\\n"
        else:
            action_items += "✅ No P0 issues found!\\n"

        action_items += "\\n### ⚠️ High Priority (P1) - Fix This Sprint\\n\\n"
        if p1_issues:
            for i, issue in enumerate(p1_issues, 1):
                clean_issue = issue.replace("⚠️ ", "").replace("**", "")
                action_items += f"- [ ] **P1-{i}**: {clean_issue}\\n"
        else:
            action_items += "✅ No P1 issues found!\\n"

        action_items += "\\n### 📝 Polish (P2) - Technical Debt\\n\\n"
        if p2_issues:
            for i, issue in enumerate(p2_issues, 1):
                clean_issue = issue.replace("📝 ", "").replace("**", "")
                action_items += f"- [ ] **P2-{i}**: {clean_issue}\\n"
        else:
            action_items += "✅ No P2 issues found!\\n"

        return action_items

    def generate_consolidated_report(self) -> str:
        """Generate the main consolidated health report"""

        frontend_results = self.load_frontend_results()
        backend_results = self.load_backend_results()

        p0_issues = self.analyze_p0_issues(frontend_results, backend_results)
        p1_issues = self.analyze_p1_issues(frontend_results, backend_results)
        p2_issues = self.analyze_p2_issues(frontend_results, backend_results)

        # Calculate health scores
        frontend_health = self.calculate_frontend_health(frontend_results)
        backend_health = self.calculate_backend_health(backend_results)

        report = f"""# 🏥 ZiggyAI Code Health Report

**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Strategy**: UI-First → API-Second  
**Status**: {"🟢 HEALTHY" if len(p0_issues) == 0 else "🔴 CRITICAL" if len(p0_issues) > 0 else "🟡 NEEDS ATTENTION"}

## 📊 Executive Summary

| Component | Health Score | P0 Issues | P1 Issues | P2 Issues | Status |
|-----------|--------------|-----------|-----------|-----------|---------|
| **Frontend UI** | {frontend_health['score']}% | {len([i for i in p0_issues if 'Frontend' in i])} | {len([i for i in p1_issues if 'Frontend' in i])} | {len([i for i in p2_issues if 'Frontend' in i])} | {frontend_health['status']} |
| **Backend API** | {backend_health['score']}% | {len([i for i in p0_issues if 'Backend' in i or 'API' in i])} | {len([i for i in p1_issues if 'Backend' in i or 'API' in i])} | {len([i for i in p2_issues if 'Backend' in i])} | {backend_health['status']} |
| **Overall** | {(frontend_health['score'] + backend_health['score']) // 2}% | {len(p0_issues)} | {len(p1_issues)} | {len(p2_issues)} | {"✅ READY" if len(p0_issues) == 0 else "❌ NOT READY"} |

### 🎯 Production Readiness
- **P0 (Critical)**: {len(p0_issues)} issues {"✅" if len(p0_issues) == 0 else "❌ BLOCKING"}
- **P1 (High)**: {len(p1_issues)} issues {"✅" if len(p1_issues) == 0 else "⚠️"}
- **P2 (Polish)**: {len(p2_issues)} issues 📝

---

## 🚨 Priority Issues

### Critical (P0) - Must Fix Before Production
{chr(10).join(p0_issues) if p0_issues else "✅ No critical issues found!"}

### High Priority (P1) - Fix This Sprint  
{chr(10).join(p1_issues) if p1_issues else "✅ No high priority issues found!"}

### Polish (P2) - Technical Debt
{chr(10).join(p2_issues) if p2_issues else "✅ No polish issues found!"}

---

## 📱 Frontend UI Health

**Routes Tested**: {len(frontend_results.get('ui_audit', []))}  
**Performance Average**: {self.get_avg_performance(frontend_results)}%  
**Accessibility Average**: {self.get_avg_accessibility(frontend_results)}%

### Route Status
"""

        # Add route details
        if frontend_results.get("ui_audit"):
            report += "| Route | Status | Console Errors | Network Errors | Data Issues | Performance | A11y |\\n"
            report += "|-------|--------|----------------|----------------|-------------|-------------|------|\\n"

            for result in frontend_results["ui_audit"]:
                route = result.get("route", "unknown")
                status = "✅" if result.get("status") == "success" else "❌"
                console_errors = len(result.get("metrics", {}).get("consoleErrors", []))
                network_errors = len(result.get("metrics", {}).get("networkErrors", []))
                data_issues = result.get("metrics", {}).get("nanCells", 0) + result.get(
                    "metrics", {}
                ).get("infinityCells", 0)

                # Find corresponding lighthouse data
                lighthouse_data = next(
                    (
                        lr
                        for lr in frontend_results.get("lighthouse", [])
                        if lr.get("route") == route
                    ),
                    {},
                )
                perf = lighthouse_data.get("scores", {}).get("performance", "N/A")
                a11y = lighthouse_data.get("scores", {}).get("accessibility", "N/A")

                report += f"| {route} | {status} | {console_errors} | {network_errors} | {data_issues} | {perf}% | {a11y}% |\\n"

        report += f"""

---

## 🔧 Backend API Health

**Endpoints Tested**: {backend_results.get('endpoints', {}).get('total_endpoints', 0)}  
**Success Rate**: {backend_results.get('endpoints', {}).get('success_rate', 0):.1f}%  
**Health Endpoint**: {self.get_health_endpoint_status(backend_results)}

### Audit Results
"""

        # Add backend audit details
        if backend_results.get("audit_summary"):
            audits = backend_results["audit_summary"].get("audits", {})
            report += "| Audit | Status | Details |\\n"
            report += "|-------|--------|---------|\\n"

            for audit_name, audit_result in audits.items():
                status = "✅" if audit_result.get("success", False) else "❌"
                error = (
                    audit_result.get("error", "No details")[:50] + "..."
                    if audit_result.get("error", "")
                    else "Passed"
                )
                report += f"| {audit_name.replace('_', ' ').title()} | {status} | {error} |\\n"

        report += f"""

---

{self.generate_action_items(p0_issues, p1_issues, p2_issues)}

---

## 📁 Artifacts & Evidence

### Frontend
- [UI Audit Results](artifacts/ui/ui_audit_results.json)
- [Lighthouse Reports](artifacts/ui/) - Performance & A11y per route
- [Playwright Screenshots](artifacts/ui/) - Visual evidence per route
- [Code Duplication](artifacts/frontend/jscpd-report.json)

### Backend  
- [API Health Summary](artifacts/backend/backend_audit_results.json)
- [Endpoint Failures](artifacts/backend/endpoints_failures.json)
- [Security Scan](artifacts/backend/bandit_report.json)
- [Type Check Results](artifacts/backend/mypy_report/)

---

## 🎯 Acceptance Criteria

### ✅ Ready for Production When:

**Frontend (Phase 1)**
- [ ] Zero P0 issues (broken routes, console errors, NaN values)
- [ ] All routes load successfully with data-loaded selectors
- [ ] Performance scores > 70% average
- [ ] Accessibility scores > 80% average  
- [ ] TTL badges properly indicate data freshness
- [ ] Screenshots show fully rendered data for every tab

**Backend (Phase 2)**  
- [ ] Zero P0 issues (5xx errors, health endpoint failures)
- [ ] All endpoints return < 400 status codes for valid requests
- [ ] `/paper/health` returns 200 with required fields when active
- [ ] Security scan shows no high/critical vulnerabilities
- [ ] Type checking passes with strict mode

**Integration**
- [ ] Frontend receives real-time data from backend
- [ ] WebSocket connections stable under load
- [ ] Error boundaries handle API failures gracefully

---

## 🚀 Quick Start Commands

```bash
# Frontend audit (run from /frontend)
npm run audit:fe:all          # Type check, lint, duplication, unused code
npm run audit:fe:ui           # Playwright visual audit + screenshots  
npm run audit:fe:lighthouse   # Performance & accessibility
npm run audit:fe:report       # Generate UI_HEALTH_REPORT.md

# Backend audit (run from /backend)  
python scripts/backend_health_audit.py  # Full backend audit
python scripts/run_schemathesis.py     # API fuzzing
python tests/test_endpoints_smoke.py   # Endpoint smoke tests

# Consolidated report (run from project root)
python scripts/generate_code_health_report.py
```

---

*This report prioritizes **user-facing issues first**. Fix the frontend UI completely before hardening the backend API. Focus on detection, clear diagnostics, and minimal targeted fixes to get the UI pristine, then the API green.*

**Next Steps**: {"Work through P0 issues immediately" if p0_issues else "Address P1 issues this sprint" if p1_issues else "Monitor and maintain current health"}
"""

        return report

    def calculate_frontend_health(self, results: dict) -> dict[str, Any]:
        """Calculate frontend health score"""
        if not results.get("ui_audit"):
            return {"score": 0, "status": "❌ NO DATA"}

        total_routes = len(results["ui_audit"])
        successful_routes = len(
            [r for r in results["ui_audit"] if r.get("status") == "success"]
        )

        success_rate = (
            (successful_routes / total_routes * 100) if total_routes > 0 else 0
        )

        # Factor in performance if available
        perf_avg = self.get_avg_performance(results)
        a11y_avg = self.get_avg_accessibility(results)

        # Weighted score: 50% success rate, 25% performance, 25% accessibility
        score = int(success_rate * 0.5 + perf_avg * 0.25 + a11y_avg * 0.25)

        if score >= 80:
            status = "✅ EXCELLENT"
        elif score >= 60:
            status = "🟡 GOOD"
        elif score >= 40:
            status = "🟠 NEEDS WORK"
        else:
            status = "🔴 CRITICAL"

        return {"score": score, "status": status}

    def calculate_backend_health(self, results: dict) -> dict[str, Any]:
        """Calculate backend health score"""
        if not results.get("audit_summary"):
            return {"score": 0, "status": "❌ NO DATA"}

        audits = results["audit_summary"].get("audits", {})
        total_audits = len(audits)
        successful_audits = len([a for a in audits.values() if a.get("success", False)])

        success_rate = (
            (successful_audits / total_audits * 100) if total_audits > 0 else 0
        )

        # Factor in endpoint success rate if available
        endpoint_success = results.get("endpoints", {}).get("success_rate", 100)

        # Weighted score: 70% audit success, 30% endpoint success
        score = int(success_rate * 0.7 + endpoint_success * 0.3)

        if score >= 80:
            status = "✅ EXCELLENT"
        elif score >= 60:
            status = "🟡 GOOD"
        elif score >= 40:
            status = "🟠 NEEDS WORK"
        else:
            status = "🔴 CRITICAL"

        return {"score": score, "status": status}

    def get_avg_performance(self, frontend_results: dict) -> float:
        """Get average performance score from lighthouse results"""
        lighthouse = frontend_results.get("lighthouse", [])
        if not lighthouse:
            return 100  # Default if no data

        scores = [r.get("scores", {}).get("performance", 100) for r in lighthouse]
        return sum(scores) / len(scores) if scores else 100

    def get_avg_accessibility(self, frontend_results: dict) -> float:
        """Get average accessibility score from lighthouse results"""
        lighthouse = frontend_results.get("lighthouse", [])
        if not lighthouse:
            return 100  # Default if no data

        scores = [r.get("scores", {}).get("accessibility", 100) for r in lighthouse]
        return sum(scores) / len(scores) if scores else 100

    def get_health_endpoint_status(self, backend_results: dict) -> str:
        """Get health endpoint status"""
        if not backend_results.get("audit_summary"):
            return "❌ UNKNOWN"

        health_audit = (
            backend_results["audit_summary"]
            .get("audits", {})
            .get("health_endpoint", {})
        )
        if health_audit.get("success", False):
            return "✅ HEALTHY"
        else:
            return f"❌ FAILED: {health_audit.get('error', 'Unknown error')}"


def main():
    """Main entry point"""
    project_root = sys.argv[1] if len(sys.argv) > 1 else "."

    generator = CodeHealthReportGenerator(project_root)
    report = generator.generate_consolidated_report()

    # Save the report
    report_path = Path(project_root) / "CODE_HEALTH_REPORT.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"📝 Code Health Report generated: {report_path}")

    # Also generate summary for CI/CD
    frontend_results = generator.load_frontend_results()
    backend_results = generator.load_backend_results()

    p0_issues = generator.analyze_p0_issues(frontend_results, backend_results)

    if p0_issues:
        print(f"💥 CRITICAL: {len(p0_issues)} P0 issues found!")
        for issue in p0_issues:
            print(f"  - {issue}")
        print("\\n🚫 NOT READY FOR PRODUCTION")
        sys.exit(1)
    else:
        print("✅ No P0 issues found - Ready for production!")
        sys.exit(0)


if __name__ == "__main__":
    main()
