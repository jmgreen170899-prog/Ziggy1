"""
API Fuzzing with Schemathesis - Automated testing against OpenAPI schema
"""

import json
import subprocess
import sys
from pathlib import Path

import click


def run_schemathesis_tests(
    base_url: str = "http://localhost:8000",
    output_path: str = "artifacts/backend/schemathesis_report.json",
    max_examples: int = 50,
    timeout: int = 30,
) -> dict:
    """
    Run schemathesis tests against the API

    Args:
        base_url: Base URL of the API
        output_path: Path to save the test results
        max_examples: Maximum number of test examples per endpoint
        timeout: Timeout in seconds for each request

    Returns:
        Dictionary containing test results
    """

    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"🔍 Running schemathesis tests against {base_url}")
    print(f"📊 Max examples per endpoint: {max_examples}")
    print(f"⏱️  Request timeout: {timeout}s")

    # Build schemathesis command
    cmd = [
        "schemathesis",
        "run",
        f"{base_url}/openapi.json",
        "--checks",
        "all",
        "--max-examples",
        str(max_examples),
        "--request-timeout",
        str(timeout * 1000),  # Convert to milliseconds
        "--hypothesis-suppress-health-check=too_slow",
        "--hypothesis-suppress-health-check=data_too_large",
        "--report",
        "json",
        "--output",
        output_path,
        "--no-color",
    ]

    try:
        print(f"🚀 Executing: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute overall timeout
        )

        print(f"📤 Exit code: {result.returncode}")

        if result.stdout:
            print("📝 Stdout:")
            print(result.stdout)

        if result.stderr:
            print("⚠️ Stderr:")
            print(result.stderr)

        # Try to load the generated report
        try:
            with open(output_path) as f:
                report_data = json.load(f)

            # Parse and summarize results
            summary = parse_schemathesis_report(report_data)

            # Add execution metadata
            summary["execution"] = {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(cmd),
            }

            # Save enhanced summary
            summary_path = output_path.replace(".json", "_summary.json")
            with open(summary_path, "w") as f:
                json.dump(summary, f, indent=2)

            print(f"✅ Enhanced summary saved to: {summary_path}")

            return summary

        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"❌ Could not parse schemathesis report: {e}")

            # Create minimal error report
            error_summary = {
                "success": False,
                "error": str(e),
                "execution": {
                    "exit_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "command": " ".join(cmd),
                },
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "errors": 0,
                "failures": [],
            }

            with open(output_path, "w") as f:
                json.dump(error_summary, f, indent=2)

            return error_summary

    except subprocess.TimeoutExpired:
        print("⏰ Schemathesis tests timed out!")
        timeout_summary = {
            "success": False,
            "error": "Test execution timed out",
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "errors": 1,
            "failures": [{"error": "Execution timeout", "endpoint": "N/A"}],
        }

        with open(output_path, "w") as f:
            json.dump(timeout_summary, f, indent=2)

        return timeout_summary

    except Exception as e:
        print(f"💥 Unexpected error running schemathesis: {e}")
        error_summary = {
            "success": False,
            "error": str(e),
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "errors": 1,
            "failures": [{"error": str(e), "endpoint": "N/A"}],
        }

        with open(output_path, "w") as f:
            json.dump(error_summary, f, indent=2)

        return error_summary


def parse_schemathesis_report(report_data: dict) -> dict:
    """
    Parse schemathesis JSON report and extract key metrics

    Args:
        report_data: Raw schemathesis report data

    Returns:
        Summarized report with key metrics
    """

    # Extract basic stats
    total_tests = report_data.get("total", 0)
    passed = report_data.get("passed", 0)
    failed = report_data.get("failed", 0)
    errors = report_data.get("errors", 0)

    # Extract failures and errors
    failures = []

    # Parse test results if available
    for test_result in report_data.get("results", []):
        if test_result.get("status") in ["FAILED", "ERROR"]:
            failure = {
                "endpoint": f"{test_result.get('method', 'UNKNOWN')} {test_result.get('path', 'UNKNOWN')}",
                "status": test_result.get("status"),
                "error": test_result.get("message", "No error message"),
                "example": test_result.get("example", {}),
                "response_status": test_result.get("response", {}).get("status_code"),
                "checks": test_result.get("checks", []),
            }
            failures.append(failure)

    # Calculate success rate
    success_rate = (passed / total_tests * 100) if total_tests > 0 else 0

    summary = {
        "success": failed == 0 and errors == 0,
        "timestamp": report_data.get("timestamp"),
        "total_tests": total_tests,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "success_rate": round(success_rate, 2),
        "failures": failures,
        "metadata": {
            "schemathesis_version": report_data.get("schemathesis_version"),
            "targets": report_data.get("targets", []),
            "duration": report_data.get("duration"),
        },
    }

    return summary


@click.command()
@click.option("--base-url", default="http://localhost:8000", help="Base URL of the API")
@click.option(
    "--output", default="artifacts/backend/schemathesis_report.json", help="Output file path"
)
@click.option("--max-examples", default=50, help="Maximum examples per endpoint")
@click.option("--timeout", default=30, help="Request timeout in seconds")
def main(base_url: str, output: str, max_examples: int, timeout: int):
    """Run schemathesis API fuzzing tests"""

    summary = run_schemathesis_tests(
        base_url=base_url, output_path=output, max_examples=max_examples, timeout=timeout
    )

    print("\\n" + "=" * 50)
    print("📊 SCHEMATHESIS TEST SUMMARY")
    print("=" * 50)
    print(f"✅ Total Tests: {summary['total_tests']}")
    print(f"✅ Passed: {summary['passed']}")
    print(f"❌ Failed: {summary['failed']}")
    print(f"💥 Errors: {summary['errors']}")
    print(f"📈 Success Rate: {summary.get('success_rate', 0)}%")

    if summary["failures"]:
        print("\\n🔍 FAILURE DETAILS:")
        for i, failure in enumerate(summary["failures"][:5], 1):  # Show first 5 failures
            print(f"  {i}. {failure['endpoint']}")
            print(f"     Status: {failure['status']}")
            print(f"     Error: {failure['error'][:100]}...")

    if summary["failed"] > 0 or summary["errors"] > 0:
        print(f"\\n💥 API has issues! Check {output} for details.")
        sys.exit(1)
    else:
        print("\\n🎉 All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
