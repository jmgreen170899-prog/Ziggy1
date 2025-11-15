#!/usr/bin/env python3
"""
Repository Integrity Check Script

This script checks for common CI/CD issues in the ZiggyClean repository:
1. UTF-8 BOM markers in critical configuration files
2. Duplicate dependencies in requirements files
3. Stray test files outside of backend/tests/
4. Test collection configuration consistency

Usage:
    python scripts/check_repo_integrity.py [--fix]

Options:
    --fix    Automatically fix detected issues (default: report only)
"""

import sys
import argparse
from pathlib import Path
from typing import List, Dict


class RepoIntegrityChecker:
    """Checks and optionally fixes repository integrity issues."""

    def __init__(self, repo_root: Path, fix_issues: bool = False):
        self.repo_root = repo_root
        self.fix_issues = fix_issues
        self.issues = []

    def check_bom_markers(self) -> List[str]:
        """Check for UTF-8 BOM markers in critical configuration files."""
        critical_files = [
            ".github/workflows/ci.yml",
            "backend/pytest.ini",
            "backend/requirements.lock",
            "backend/pyproject.toml",
        ]

        bom_issues = []
        utf8_bom = b"\xef\xbb\xbf"

        for file_path in critical_files:
            full_path = self.repo_root / file_path
            if not full_path.exists():
                continue

            try:
                with open(full_path, "rb") as f:
                    first_bytes = f.read(3)
                    if first_bytes == utf8_bom:
                        bom_issues.append(file_path)
                        if self.fix_issues:
                            # Remove BOM by reading as UTF-8 and writing back
                            with open(full_path, "r", encoding="utf-8") as rf:
                                content = rf.read()
                            with open(full_path, "w", encoding="utf-8") as wf:
                                wf.write(content)
                            print(f"✅ Fixed BOM marker in {file_path}")
            except Exception as e:
                print(f"⚠️  Error checking {file_path}: {e}")

        return bom_issues

    def check_duplicate_dependencies(self) -> List[str]:
        """Check for duplicate entries in requirements.lock."""
        requirements_file = self.repo_root / "backend" / "requirements.lock"

        if not requirements_file.exists():
            return []

        duplicates = []
        seen_packages = {}
        lines = []

        try:
            with open(requirements_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for i, line in enumerate(lines):
                line = line.strip()
                if "==" in line:
                    package = line.split("==")[0].strip()
                    if package in seen_packages:
                        duplicates.append(
                            f"{package} (lines {seen_packages[package]} and {i+1})"
                        )
                    else:
                        seen_packages[package] = i + 1

            if duplicates and self.fix_issues:
                # Remove duplicates by keeping only first occurrence
                unique_lines = []
                seen_packages = set()

                for line in lines:
                    line_stripped = line.strip()
                    if "==" in line_stripped:
                        package = line_stripped.split("==")[0].strip()
                        if package not in seen_packages:
                            unique_lines.append(line)
                            seen_packages.add(package)
                    else:
                        unique_lines.append(line)

                with open(requirements_file, "w", encoding="utf-8") as f:
                    f.writelines(unique_lines)
                print(
                    f"✅ Fixed {len(duplicates)} duplicate dependencies in requirements.lock"
                )

        except Exception as e:
            print(f"⚠️  Error checking requirements.lock: {e}")

        return duplicates

    def check_stray_test_files(self) -> List[str]:
        """Check for test files outside of backend/tests/ directory."""
        stray_tests = []

        # Check root directory
        for test_file in self.repo_root.glob("test_*.py"):
            stray_tests.append(str(test_file.relative_to(self.repo_root)))

        # Check backend root (should only be in backend/tests/)
        backend_dir = self.repo_root / "backend"
        if backend_dir.exists():
            for test_file in backend_dir.glob("test_*.py"):
                stray_tests.append(str(test_file.relative_to(self.repo_root)))

        if stray_tests and self.fix_issues:
            tests_dir = self.repo_root / "backend" / "tests"
            tests_dir.mkdir(exist_ok=True)

            for stray_test in stray_tests[
                :
            ]:  # Copy list to avoid modification during iteration
                src_path = self.repo_root / stray_test
                dst_path = tests_dir / src_path.name

                try:
                    src_path.rename(dst_path)
                    print(f"✅ Moved {stray_test} to backend/tests/")
                    stray_tests.remove(stray_test)
                except Exception as e:
                    print(f"⚠️  Error moving {stray_test}: {e}")

        return stray_tests

    def check_test_configuration(self) -> List[str]:
        """Check pytest configuration for consistency."""
        config_issues = []

        pytest_ini = self.repo_root / "backend" / "pytest.ini"
        pyproject_toml = self.repo_root / "backend" / "pyproject.toml"

        # Check pytest.ini
        if pytest_ini.exists():
            try:
                with open(pytest_ini, "r", encoding="utf-8") as f:
                    content = f.read()
                    if "testpaths" in content:
                        # Extract testpaths value
                        for line in content.split("\n"):
                            if line.strip().startswith("testpaths"):
                                if "tests" not in line:
                                    config_issues.append(
                                        "pytest.ini testpaths should include 'tests'"
                                    )
                    else:
                        config_issues.append(
                            "pytest.ini missing testpaths configuration"
                        )
            except Exception as e:
                config_issues.append(f"Error reading pytest.ini: {e}")

        # Check pyproject.toml pytest configuration
        if pyproject_toml.exists():
            try:
                with open(pyproject_toml, "r", encoding="utf-8") as f:
                    content = f.read()
                    if "[tool.pytest.ini_options]" in content:
                        if 'testpaths = ["tests"]' not in content:
                            config_issues.append(
                                "pyproject.toml pytest testpaths should be ['tests']"
                            )
            except Exception as e:
                config_issues.append(f"Error reading pyproject.toml: {e}")

        return config_issues

    def run_checks(self) -> Dict[str, List[str]]:
        """Run all integrity checks and return results."""
        results = {
            "bom_markers": self.check_bom_markers(),
            "duplicate_dependencies": self.check_duplicate_dependencies(),
            "stray_test_files": self.check_stray_test_files(),
            "test_configuration": self.check_test_configuration(),
        }

        return results

    def print_report(self, results: Dict[str, List[str]]) -> bool:
        """Print integrity check report. Returns True if all checks passed."""
        print("🔍 Repository Integrity Check Report")
        print("=" * 50)

        all_clean = True

        for check_name, issues in results.items():
            print(f"\n📋 {check_name.replace('_', ' ').title()}:")
            if not issues:
                print("  ✅ No issues found")
            else:
                all_clean = False
                for issue in issues:
                    print(f"  ❌ {issue}")

        print("\n" + "=" * 50)
        if all_clean:
            print("🎉 All integrity checks passed!")
        else:
            print("⚠️  Issues found. Run with --fix to auto-resolve where possible.")

        return all_clean


def main():
    parser = argparse.ArgumentParser(description="Check repository integrity")
    parser.add_argument(
        "--fix", action="store_true", help="Automatically fix detected issues"
    )
    args = parser.parse_args()

    # Find repository root (look for .git directory)
    repo_root = Path.cwd()
    while repo_root.parent != repo_root:
        if (repo_root / ".git").exists():
            break
        repo_root = repo_root.parent
    else:
        print("❌ Could not find repository root (.git directory)")
        sys.exit(1)

    print(f"📁 Repository root: {repo_root}")
    if args.fix:
        print("🔧 Auto-fix mode enabled")

    checker = RepoIntegrityChecker(repo_root, args.fix)
    results = checker.run_checks()
    all_clean = checker.print_report(results)

    # Exit with non-zero code if issues found (for CI use)
    sys.exit(0 if all_clean else 1)


if __name__ == "__main__":
    main()
