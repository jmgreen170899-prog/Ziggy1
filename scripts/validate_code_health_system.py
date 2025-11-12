#!/usr/bin/env python3
"""
Quick validation test for ZiggyAI Code Health Deep Dive system.
"""

import json
import subprocess
import sys
from pathlib import Path


def test_script_compilation():
    """Test that all Python scripts compile without syntax errors."""
    print("🐍 Testing Python script compilation...")

    scripts = [
        "scripts/code_health_deep_dive.py",
        "scripts/verify_endpoints.py",
        "scripts/detect_duplicates.py",
    ]

    for script in scripts:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", script], capture_output=True, text=True
            )

            if result.returncode == 0:
                print(f"  ✅ {script}")
            else:
                print(f"  ❌ {script}: {result.stderr}")
                return False
        except Exception as e:
            print(f"  ❌ {script}: {e}")
            return False

    return True


def test_imports():
    """Test that all required Python modules can be imported."""
    print("\n📦 Testing Python imports...")

    required_modules = [
        "asyncio",
        "json",
        "subprocess",
        "pathlib",
        "datetime",
        "time",
        "typing",
        "re",
    ]

    for module in required_modules:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except ImportError as e:
            print(f"  ❌ {module}: {e}")
            return False

    return True


def test_optional_tools():
    """Test availability of optional code quality tools."""
    print("\n🔧 Testing optional tools...")

    tools = [
        ("ruff", [sys.executable, "-m", "ruff", "--version"]),
        ("mypy", [sys.executable, "-m", "mypy", "--version"]),
        ("bandit", [sys.executable, "-m", "bandit", "--version"]),
        ("vulture", [sys.executable, "-m", "vulture", "--version"]),
        ("black", [sys.executable, "-m", "black", "--version"]),
    ]

    available_tools = 0

    for tool_name, cmd in tools:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"  ✅ {tool_name}")
                available_tools += 1
            else:
                print(f"  ⚠️  {tool_name} (not installed)")
        except Exception:
            print(f"  ⚠️  {tool_name} (not available)")

    print(f"\n📊 {available_tools}/{len(tools)} tools available")
    return available_tools >= 2  # At least 2 tools should be available


def test_file_structure():
    """Test that all required files and directories exist."""
    print("\n📁 Testing file structure...")

    required_paths = [
        "backend",
        "frontend",
        "scripts",
        "scripts/code_health_deep_dive.py",
        "scripts/verify_endpoints.py",
        "scripts/detect_duplicates.py",
        "scripts/run_code_health.ps1",
    ]

    for path in required_paths:
        if Path(path).exists():
            print(f"  ✅ {path}")
        else:
            print(f"  ❌ {path} (missing)")
            return False

    return True


def test_report_generation():
    """Test that reports directory can be created."""
    print("\n📄 Testing report generation...")

    try:
        Path("reports").mkdir(exist_ok=True)
        test_file = Path("reports/test_validation.json")

        test_data = {"timestamp": "2025-01-13T20:00:00", "test": "validation", "status": "success"}

        with open(test_file, "w") as f:
            json.dump(test_data, f, indent=2)

        if test_file.exists():
            print("  ✅ Report directory writable")
            test_file.unlink()  # Clean up
            return True
        else:
            print("  ❌ Report generation failed")
            return False

    except Exception as e:
        print(f"  ❌ Report generation error: {e}")
        return False


def main():
    """Run all validation tests."""
    print("🧪 ZiggyAI Code Health System Validation")
    print("=" * 50)

    tests = [
        ("File Structure", test_file_structure),
        ("Script Compilation", test_script_compilation),
        ("Python Imports", test_imports),
        ("Optional Tools", test_optional_tools),
        ("Report Generation", test_report_generation),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"\n✅ {test_name} PASSED")
            else:
                print(f"\n❌ {test_name} FAILED")
        except Exception as e:
            print(f"\n❌ {test_name} FAILED: {e}")

    print("\n" + "=" * 50)
    print(f"🎯 VALIDATION SUMMARY: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All validation tests passed! System ready for use.")
        return 0
    elif passed >= total - 1:
        print("⚠️  System mostly ready, minor issues detected.")
        return 0
    else:
        print("❌ Critical validation failures. Check dependencies.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
