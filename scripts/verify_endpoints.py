#!/usr/bin/env python3
"""
ZiggyAI Endpoint Verification System
Comprehensive health checking for all backend routes.
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
import psutil
from pydantic import BaseModel


class EndpointTest(BaseModel):
    """Individual endpoint test result."""

    url: str
    method: str
    status_code: int
    response_time_ms: float
    success: bool
    error: str | None = None
    response_size: int = 0
    headers: dict[str, str] = {}


class EndpointReport(BaseModel):
    """Complete endpoint verification report."""

    timestamp: datetime
    total_endpoints: int
    successful: int
    failed: int
    average_response_time: float
    tests: list[EndpointTest]
    system_info: dict[str, Any]


class ZiggyEndpointVerifier:
    """Comprehensive endpoint testing system."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)

        # Core API endpoints to test
        self.endpoints = [
            # Health & Status
            ("GET", "/health"),
            ("GET", "/api/v1/health"),
            # Paper Trading System
            ("GET", "/api/v1/paper/status"),
            ("GET", "/api/v1/paper/health"),
            ("GET", "/api/v1/paper/trades"),
            ("GET", "/api/v1/paper/positions"),
            ("GET", "/api/v1/paper/theories"),
            ("GET", "/api/v1/paper/metrics"),
            # Data & Market
            ("GET", "/api/v1/market/status"),
            ("GET", "/api/v1/market/symbols"),
            ("GET", "/api/v1/data/news"),
            ("GET", "/api/v1/data/sentiment"),
            # Brain & Learning
            ("GET", "/api/v1/brain/status"),
            ("GET", "/api/v1/brain/queue"),
            ("GET", "/api/v1/brain/insights"),
            ("GET", "/api/v1/learning/stats"),
            # Portfolio & Analytics
            ("GET", "/api/v1/portfolio/overview"),
            ("GET", "/api/v1/portfolio/performance"),
            ("GET", "/api/v1/analytics/dashboard"),
            # WebSocket endpoints (HTTP check)
            ("GET", "/ws/news"),
            ("GET", "/ws/alerts"),
            ("GET", "/ws/portfolio"),
            # Static/Frontend routes
            ("GET", "/"),
            ("GET", "/docs"),
            ("GET", "/redoc"),
        ]

    async def test_endpoint(self, method: str, path: str) -> EndpointTest:
        """Test a single endpoint."""
        url = f"{self.base_url}{path}"
        start_time = time.time()

        try:
            response = await self.client.request(method, url)
            response_time = (time.time() - start_time) * 1000

            return EndpointTest(
                url=url,
                method=method,
                status_code=response.status_code,
                response_time_ms=round(response_time, 2),
                success=200 <= response.status_code < 400,
                response_size=len(response.content),
                headers=dict(response.headers),
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return EndpointTest(
                url=url,
                method=method,
                status_code=0,
                response_time_ms=round(response_time, 2),
                success=False,
                error=str(e),
            )

    async def run_all_tests(self) -> EndpointReport:
        """Run comprehensive endpoint tests."""
        print("🔍 Starting ZiggyAI endpoint verification...")

        # Test all endpoints concurrently
        tasks = [self.test_endpoint(method, path) for method, path in self.endpoints]

        tests = await asyncio.gather(*tasks)

        # Calculate statistics
        successful = sum(1 for t in tests if t.success)
        failed = len(tests) - successful
        avg_response_time = sum(t.response_time_ms for t in tests) / len(tests)

        # System information
        system_info = {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": (
                psutil.disk_usage("/").percent if hasattr(psutil.disk_usage("/"), "percent") else 0
            ),
            "python_version": (
                psutil.Process().exe() if hasattr(psutil.Process(), "exe") else "unknown"
            ),
        }

        report = EndpointReport(
            timestamp=datetime.now(),
            total_endpoints=len(tests),
            successful=successful,
            failed=failed,
            average_response_time=round(avg_response_time, 2),
            tests=tests,
            system_info=system_info,
        )

        await self.client.aclose()
        return report

    def print_report(self, report: EndpointReport) -> None:
        """Print human-readable report."""
        print("\n" + "=" * 60)
        print("🤖 ZIGGY ENDPOINT VERIFICATION REPORT")
        print("=" * 60)
        print(f"📅 Timestamp: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 Total Endpoints: {report.total_endpoints}")
        print(f"✅ Successful: {report.successful}")
        print(f"❌ Failed: {report.failed}")
        print(f"⚡ Avg Response Time: {report.average_response_time}ms")
        print(f"💻 CPU: {report.system_info.get('cpu_percent', 0):.1f}%")
        print(f"🧠 Memory: {report.system_info.get('memory_percent', 0):.1f}%")

        if report.failed > 0:
            print("\n❌ FAILED ENDPOINTS:")
            for test in report.tests:
                if not test.success:
                    print(f"  {test.method} {test.url}")
                    print(f"    Status: {test.status_code}")
                    print(f"    Error: {test.error or 'Unknown error'}")
                    print(f"    Time: {test.response_time_ms}ms")

        print("\n✅ SUCCESSFUL ENDPOINTS:")
        for test in report.tests:
            if test.success:
                status_emoji = "🟢" if test.status_code == 200 else "🟡"
                print(
                    f"  {status_emoji} {test.method} {test.url} ({test.status_code}) - {test.response_time_ms}ms"
                )

        success_rate = (report.successful / report.total_endpoints) * 100
        print(f"\n🎯 Success Rate: {success_rate:.1f}%")
        print("=" * 60)

    def save_report(self, report: EndpointReport, filename: str = None) -> str:
        """Save report to JSON file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"endpoint_report_{timestamp}.json"

        filepath = Path("reports") / filename
        filepath.parent.mkdir(exist_ok=True)

        with open(filepath, "w") as f:
            json.dump(report.dict(), f, indent=2, default=str)

        return str(filepath)


async def main():
    """Main execution function."""
    verifier = ZiggyEndpointVerifier()

    try:
        report = await verifier.run_all_tests()

        # Print results
        verifier.print_report(report)

        # Save report
        report_file = verifier.save_report(report)
        print(f"\n📄 Report saved to: {report_file}")

        # Exit with error code if any endpoints failed
        if report.failed > 0:
            print(f"\n⚠️  {report.failed} endpoints failed!")
            exit(1)
        else:
            print("\n🎉 All endpoints are healthy!")

    except KeyboardInterrupt:
        print("\n⚠️  Verification cancelled by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
