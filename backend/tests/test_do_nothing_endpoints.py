"""
Test that verifies no do-nothing endpoints exist

Shells out to static_endpoint_audit.py and fails if it finds any issues.
"""

import subprocess
import sys
from pathlib import Path


def test_no_do_nothing_endpoints():
    """Verify there are no do-nothing endpoints"""
    # Find the static audit script
    backend_dir = Path(__file__).parent.parent
    audit_script = backend_dir / "scripts" / "static_endpoint_audit.py"

    assert audit_script.exists(), f"Audit script not found at {audit_script}"

    # Run the audit
    result = subprocess.run(
        [sys.executable, str(audit_script)],
        capture_output=True,
        text=True,
        cwd=backend_dir,
    )

    # Print output for debugging
    print("\n" + "=" * 80)
    print("Static Endpoint Audit Output:")
    print("=" * 80)
    print(result.stdout)
    if result.stderr:
        print("Errors/Warnings:")
        print(result.stderr)
    print("=" * 80)

    # The audit script exits with 1 if it finds issues, 0 if clean
    assert result.returncode == 0, (
        "Static endpoint audit found do-nothing endpoints. "
        "See output above for details. "
        "To mark an endpoint as intentionally placeholder, add: # pragma: placeholder-ok"
    )
