"""
Backend API Smoke Test - Tests all endpoints for basic functionality
"""

import asyncio
import json
import logging
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import httpx
import pytest


@dataclass
class EndpointResult:
    path: str
    method: str
    status_code: int
    response_time_ms: float
    success: bool
    error: str | None = None
    response_size: int = 0


class EndpointSmokeTest:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)
        self.results: list[EndpointResult] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def get_app_routes(self) -> list[dict[str, Any]]:
        """Introspect FastAPI app routes"""
        try:
            # Try to get OpenAPI schema which lists all routes
            response = await self.client.get(f"{self.base_url}/openapi.json")
            if response.status_code == 200:
                openapi_data = response.json()
                routes = []

                for path, methods in openapi_data.get("paths", {}).items():
                    for method in methods.keys():
                        if method.lower() in [
                            "get",
                            "head",
                            "options",
                        ]:  # Safe methods only
                            routes.append(
                                {"path": path, "method": method.upper(), "safe": True}
                            )

                return routes
        except Exception as e:
            logging.warning(f"Could not get routes from OpenAPI: {e}")

        # Fallback to known common routes
        return [
            {"path": "/", "method": "GET", "safe": True},
            {"path": "/health", "method": "GET", "safe": True},
            {"path": "/docs", "method": "GET", "safe": True},
            {"path": "/openapi.json", "method": "GET", "safe": True},
            {"path": "/api/chat/health", "method": "GET", "safe": True},
            {"path": "/api/market/health", "method": "GET", "safe": True},
            {"path": "/api/paper/health", "method": "GET", "safe": True},
            {"path": "/api/portfolio/health", "method": "GET", "safe": True},
            {"path": "/api/alerts", "method": "GET", "safe": True},
            {"path": "/api/decisions", "method": "GET", "safe": True},
            {"path": "/api/status", "method": "GET", "safe": True},
        ]

    async def test_endpoint(self, path: str, method: str) -> EndpointResult:
        """Test a single endpoint"""
        url = f"{self.base_url}{path}"
        start_time = time.time()

        try:
            if method.upper() == "GET":
                response = await self.client.get(url)
            elif method.upper() == "HEAD":
                response = await self.client.head(url)
            elif method.upper() == "OPTIONS":
                response = await self.client.options(url)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response_time_ms = (time.time() - start_time) * 1000

            # Determine success based on status code
            success = response.status_code < 400
            error = (
                None
                if success
                else f"HTTP {response.status_code}: {response.text[:200]}"
            )

            return EndpointResult(
                path=path,
                method=method,
                status_code=response.status_code,
                response_time_ms=response_time_ms,
                success=success,
                error=error,
                response_size=(
                    len(response.content) if hasattr(response, "content") else 0
                ),
            )

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return EndpointResult(
                path=path,
                method=method,
                status_code=0,
                response_time_ms=response_time_ms,
                success=False,
                error=str(e),
                response_size=0,
            )

    async def run_smoke_tests(self) -> dict[str, Any]:
        """Run smoke tests on all endpoints"""
        print("🔍 Discovering API endpoints...")
        routes = await self.get_app_routes()

        print(f"📡 Testing {len(routes)} endpoints...")

        for route in routes:
            result = await self.test_endpoint(route["path"], route["method"])
            self.results.append(result)

            # Log result
            status_icon = "✅" if result.success else "❌"
            print(
                f"{status_icon} {result.method} {result.path} -> {result.status_code} ({result.response_time_ms:.0f}ms)"
            )

            if not result.success and result.error:
                print(f"   Error: {result.error}")

        # Generate summary
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.success])
        failed_tests = total_tests - passed_tests

        failures = [r for r in self.results if not r.success]

        summary = {
            "timestamp": time.time(),
            "total_endpoints": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": (
                (passed_tests / total_tests * 100) if total_tests > 0 else 0
            ),
            "failures": [asdict(f) for f in failures],
            "all_results": [asdict(r) for r in self.results],
        }

        return summary

    async def save_results(self, output_path: str):
        """Save test results to JSON file"""
        summary = await self.run_smoke_tests()

        # Ensure output directory exists
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Save results
        with open(output_file, "w") as f:
            json.dump(summary, f, indent=2)

        print(f"\\n📊 Results saved to: {output_path}")
        print(
            f"✅ Passed: {summary['passed']}/{summary['total_endpoints']} ({summary['success_rate']:.1f}%)"
        )

        if summary["failed"] > 0:
            print(f"❌ Failed: {summary['failed']} endpoints")
            print("\\nFailed endpoints:")
            for failure in summary["failures"]:
                print(f"  - {failure['method']} {failure['path']}: {failure['error']}")

        return summary


async def main():
    """Main entry point for smoke tests"""
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    output_path = (
        sys.argv[2]
        if len(sys.argv) > 2
        else "artifacts/backend/endpoints_failures.json"
    )

    print(f"🚀 Starting API smoke tests for: {base_url}")

    async with EndpointSmokeTest(base_url) as tester:
        summary = await tester.save_results(output_path)

        # Exit with error code if tests failed
        if summary["failed"] > 0:
            print(f"\\n💥 {summary['failed']} endpoints failed!")
            sys.exit(1)
        else:
            print("\\n🎉 All endpoints passed!")
            sys.exit(0)


# Pytest integration
@pytest.mark.asyncio
async def test_all_endpoints():
    """Pytest wrapper for smoke tests"""
    async with EndpointSmokeTest() as tester:
        summary = await tester.run_smoke_tests()

        # Assert no failures
        assert (
            summary["failed"] == 0
        ), f"{summary['failed']} endpoints failed: {summary['failures']}"


if __name__ == "__main__":
    asyncio.run(main())
