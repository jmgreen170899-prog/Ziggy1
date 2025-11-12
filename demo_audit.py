#!/usr/bin/env python3
"""
Demo script to show the ZiggyAI Code Health Audit System in action
Run this to see what the system looks like without running actual audits
"""

import json
import time
from datetime import datetime
from pathlib import Path


def create_demo_artifacts():
    """Create demo artifacts to show what the system generates"""

    print("🎬 Creating demo artifacts for ZiggyAI Code Health Audit...")

    # Ensure directories exist
    artifacts_dir = Path("artifacts")
    ui_dir = artifacts_dir / "ui"
    frontend_dir = artifacts_dir / "frontend"
    backend_dir = artifacts_dir / "backend"

    for dir_path in [ui_dir, frontend_dir, backend_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)

    # Demo UI audit results
    ui_audit_results = [
        {
            "route": "home",
            "url": "/",
            "timestamp": datetime.now().isoformat(),
            "screenshot": "home.png",
            "metrics": {
                "cardCount": 4,
                "tableCount": 2,
                "nanCells": 0,
                "infinityCells": 0,
                "missingFields": [],
                "staleBadges": 1,
                "consoleErrors": [],
                "networkErrors": [],
                "loadTime": 1250,
            },
            "status": "success",
        },
        {
            "route": "market",
            "url": "/market",
            "timestamp": datetime.now().isoformat(),
            "screenshot": "market.png",
            "metrics": {
                "cardCount": 6,
                "tableCount": 1,
                "nanCells": 2,  # P0 issue!
                "infinityCells": 0,
                "missingFields": ["price_change", "volume"],
                "staleBadges": 3,
                "consoleErrors": [
                    "TypeError: Cannot read property 'price' of undefined"
                ],  # P0 issue!
                "networkErrors": [],
                "loadTime": 2100,
            },
            "status": "success",
        },
        {
            "route": "alerts",
            "url": "/alerts",
            "timestamp": datetime.now().isoformat(),
            "screenshot": "error_alerts.png",
            "metrics": {
                "cardCount": 0,
                "tableCount": 0,
                "nanCells": 0,
                "infinityCells": 0,
                "missingFields": [],
                "staleBadges": 0,
                "consoleErrors": ["Network Error: Failed to fetch alerts"],
                "networkErrors": ["500 - http://localhost:8000/api/alerts"],  # P0 issue!
                "loadTime": 15000,
            },
            "status": "error",  # P0 issue!
            "error": "Route failed to load - API error",
        },
    ]

    with open(ui_dir / "ui_audit_results.json", "w") as f:
        json.dump(ui_audit_results, f, indent=2)

    # Demo Lighthouse results
    lighthouse_results = [
        {
            "route": "home",
            "url": "http://localhost:3000/",
            "timestamp": datetime.now().isoformat(),
            "scores": {"performance": 85, "accessibility": 92, "bestPractices": 88},
            "metrics": {
                "firstContentfulPaint": 1200,
                "largestContentfulPaint": 2100,
                "cumulativeLayoutShift": 0.05,
                "totalBlockingTime": 150,
                "speedIndex": 1800,
            },
            "issues": {"performanceIssues": [], "accessibilityIssues": []},
        },
        {
            "route": "market",
            "url": "http://localhost:3000/market",
            "timestamp": datetime.now().isoformat(),
            "scores": {
                "performance": 45,  # P1 issue!
                "accessibility": 78,  # P1 issue!
                "bestPractices": 85,
            },
            "metrics": {
                "firstContentfulPaint": 2500,
                "largestContentfulPaint": 4200,
                "cumulativeLayoutShift": 0.15,  # P1 issue!
                "totalBlockingTime": 890,
                "speedIndex": 3200,
            },
            "issues": {
                "performanceIssues": [
                    {
                        "id": "largest-contentful-paint",
                        "title": "Largest Contentful Paint",
                        "score": 0.2,
                    },
                    {
                        "id": "cumulative-layout-shift",
                        "title": "Cumulative Layout Shift",
                        "score": 0.1,
                    },
                ],
                "accessibilityIssues": [
                    {
                        "id": "color-contrast",
                        "title": "Background and foreground colors do not have sufficient contrast ratio",
                        "score": 0.8,
                    }
                ],
            },
        },
    ]

    with open(ui_dir / "lighthouse_summary.json", "w") as f:
        json.dump(lighthouse_results, f, indent=2)

    # Demo backend audit results
    backend_audit_results = {
        "timestamp": datetime.now().isoformat(),
        "backend_path": "./backend",
        "base_url": "http://localhost:8000",
        "artifacts_dir": "./artifacts/backend",
        "audits": {
            "syntax_check": {
                "tool": "ruff",
                "success": False,  # P1 issue!
                "console_output": "Found 5 errors in backend code",
                "errors": "",
                "report_file": "./artifacts/backend/ruff_report.json",
            },
            "type_check": {
                "tool": "mypy",
                "success": True,
                "output": "Success: no issues found in 45 source files.",
                "errors": "",
                "report_dir": "./artifacts/backend/mypy_report",
            },
            "security_check": {
                "tool": "bandit",
                "success": False,  # P1 issue!
                "console_output": "Found 2 medium severity security issues",
                "errors": "",
                "report_file": "./artifacts/backend/bandit_report.json",
            },
            "endpoint_smoke": {
                "tool": "endpoint_smoke_test",
                "success": False,  # P0 issue!
                "summary": {
                    "timestamp": time.time(),
                    "total_endpoints": 12,
                    "passed": 9,
                    "failed": 3,
                    "success_rate": 75.0,
                    "failures": [
                        {
                            "path": "/api/alerts",
                            "method": "GET",
                            "status_code": 500,
                            "error": "Internal Server Error: Database connection failed",
                        },
                        {
                            "path": "/api/portfolio/trades",
                            "method": "GET",
                            "status_code": 404,
                            "error": "Not Found",
                        },
                    ],
                },
                "report_file": "./artifacts/backend/endpoints_failures.json",
            },
            "health_endpoint": {
                "tool": "health_endpoint",
                "success": False,  # P0 issue!
                "status_code": 500,
                "error": "Health endpoint returned 500: Database connection failed",
                "url": "http://localhost:8000/paper/health",
            },
        },
    }

    with open(backend_dir / "backend_audit_results.json", "w") as f:
        json.dump(backend_audit_results, f, indent=2)

    # Demo endpoint failures
    endpoint_failures = {
        "timestamp": time.time(),
        "total_endpoints": 12,
        "passed": 9,
        "failed": 3,
        "success_rate": 75.0,
        "failures": [
            {
                "path": "/api/alerts",
                "method": "GET",
                "status_code": 500,
                "success": False,
                "error": "HTTP 500: Internal Server Error - Database connection timeout",
                "response_time_ms": 5000,
            },
            {
                "path": "/api/portfolio/trades",
                "method": "GET",
                "status_code": 404,
                "success": False,
                "error": "HTTP 404: Endpoint not found",
                "response_time_ms": 150,
            },
            {
                "path": "/paper/health",
                "method": "GET",
                "status_code": 500,
                "success": False,
                "error": "HTTP 500: Health check failed - strict isolation error",
                "response_time_ms": 3000,
            },
        ],
        "all_results": [],  # Would contain all endpoint test results
    }

    with open(backend_dir / "endpoints_failures.json", "w") as f:
        json.dump(endpoint_failures, f, indent=2)

    print("✅ Demo artifacts created!")
    return True


def generate_demo_report():
    """Generate a demo health report"""
    print("📊 Generating demo CODE_HEALTH_REPORT.md...")

    # Import and run the report generator
    import sys

    sys.path.append("scripts")

    try:
        from generate_code_health_report import CodeHealthReportGenerator

        generator = CodeHealthReportGenerator(".")
        report = generator.generate_consolidated_report()

        with open("CODE_HEALTH_REPORT.md", "w", encoding="utf-8") as f:
            f.write(report)

        print("✅ Demo report generated: CODE_HEALTH_REPORT.md")
        return True

    except ImportError:
        print("⚠️ Could not import report generator - creating simple demo report")

        demo_report = f"""# 🏥 ZiggyAI Code Health Report (DEMO)

**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Strategy**: UI-First → API-Second  
**Status**: 🔴 CRITICAL

## 📊 Executive Summary

| Component | Health Score | P0 Issues | P1 Issues | P2 Issues | Status |
|-----------|--------------|-----------|-----------|-----------|---------|
| **Frontend UI** | 65% | 2 | 3 | 1 | 🔴 CRITICAL |
| **Backend API** | 55% | 2 | 2 | 0 | 🔴 CRITICAL |
| **Overall** | 60% | 4 | 5 | 1 | ❌ NOT READY |

### 🎯 Production Readiness
- **P0 (Critical)**: 4 issues ❌ BLOCKING
- **P1 (High)**: 5 issues ⚠️
- **P2 (Polish)**: 1 issues 📝

---

## 🚨 Priority Issues

### Critical (P0) - Must Fix Before Production
🚨 Frontend route **alerts** completely broken: Route failed to load - API error
🚨 Frontend **market** has 1 console errors
🚨 Frontend **market** displays NaN values in UI
🚨 API endpoint **GET /api/alerts** returns 5xx error: HTTP 500: Internal Server Error - Database connection timeout
🚨 Health endpoint `/paper/health` is broken: Health endpoint returned 500: Database connection failed

### High Priority (P1) - Fix This Sprint  
⚠️ Frontend **market** has 2 missing/empty data fields
⚠️ Frontend **market** poor performance score: 45%
⚠️ Frontend **market** accessibility issues: 78%
⚠️ Frontend **market** high layout shift: 0.150
⚠️ Backend **syntax_check** check failed: Found 5 errors in backend code
⚠️ Backend **security_check** check failed: Found 2 medium severity security issues

### Polish (P2) - Technical Debt
📝 Frontend **home** slow load time: 1250ms

---

This is a DEMO report showing what critical issues look like.
In a real audit, you would see:
- Actual screenshots in artifacts/ui/
- Detailed error logs and stack traces  
- Specific line numbers and file locations
- Actionable fix suggestions for each issue

Run the actual audit with: make audit-all
"""

        with open("CODE_HEALTH_REPORT.md", "w") as f:
            f.write(demo_report)

        print("✅ Demo report created!")
        return True


def show_demo_summary():
    """Show what the demo represents"""

    print("\n" + "=" * 60)
    print("🎬 DEMO COMPLETE - Here's what you just saw:")
    print("=" * 60)

    print("\n📱 FRONTEND ISSUES FOUND:")
    print("  🚨 P0: Alerts page completely broken (API error)")
    print("  🚨 P0: Market page shows NaN values to users")
    print("  🚨 P0: Console errors on market page")
    print("  ⚠️ P1: Poor performance & accessibility scores")
    print("  ⚠️ P1: High layout shift causing visual jumps")
    print("  📝 P2: Slow load times")

    print("\n🔧 BACKEND ISSUES FOUND:")
    print("  🚨 P0: Health endpoint failing (500 errors)")
    print("  🚨 P0: Multiple API endpoints returning 5xx")
    print("  ⚠️ P1: Syntax errors in Python code")
    print("  ⚠️ P1: Security vulnerabilities detected")

    print("\n📊 WHAT THIS MEANS:")
    print("  ❌ NOT READY FOR PRODUCTION")
    print("  🔴 4 P0 issues MUST be fixed immediately")
    print("  ⚠️ 5 P1 issues should be fixed this sprint")
    print("  📝 1 P2 issue is technical debt")

    print("\n📁 ARTIFACTS GENERATED:")
    print("  📄 CODE_HEALTH_REPORT.md - Main report with action items")
    print("  📊 artifacts/ui/ - Frontend test results & screenshots")
    print("  📊 artifacts/backend/ - API test results & security scans")

    print("\n🚀 NEXT STEPS IN REAL USAGE:")
    print("  1. Fix P0 issues first (broken routes, API errors)")
    print("  2. Run 'make audit-all' to verify fixes")
    print("  3. Address P1 issues (performance, security)")
    print("  4. Monitor with regular audits")

    print("\n💡 TRY THE REAL AUDIT:")
    print("  make dev-setup     # Install dependencies")
    print("  make audit-all     # Run full audit on your code")
    print("  open CODE_HEALTH_REPORT.md  # View results")

    print("\n🎯 PRODUCTION READINESS:")
    print("  ✅ Ready when: Zero P0 issues + key P1s resolved")
    print("  🔄 Monitor with: Regular audit runs in CI/CD")
    print("  📈 Track with: Health score trends over time")


def main():
    """Run the demo"""
    print("🎬 ZiggyAI Code Health Audit System - DEMO MODE")
    print("=" * 50)
    print("This demo shows what the audit system finds without")
    print("running actual tests on your code.")
    print("=" * 50)

    input("Press Enter to start the demo...")

    # Create demo data
    if create_demo_artifacts():
        print("✅ Step 1: Created sample audit artifacts")

    time.sleep(1)

    # Generate demo report
    if generate_demo_report():
        print("✅ Step 2: Generated health report")

    time.sleep(1)

    # Show summary
    show_demo_summary()

    print("\n📖 Open CODE_HEALTH_REPORT.md to see the full demo report!")


if __name__ == "__main__":
    main()
