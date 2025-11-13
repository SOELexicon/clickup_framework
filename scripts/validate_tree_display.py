#!/usr/bin/env python3
"""
Run critical tree and hierarchy validation tests before commit.

This ensures that tree pipe rendering (├─, └─, │) works correctly
and prevents broken tree display from being committed.
"""

import subprocess
import sys


def run_tests():
    """Run tree validation tests."""
    print("🔍 Running tree validation tests...")

    # Critical test files that must pass
    test_files = [
        "tests/components/test_tree.py",
        "tests/format_tests/test_tree_alignment.py",
        "tests/commands/test_hierarchy_tree_rendering.py",
    ]

    # Run pytest on these specific files
    cmd = (
        ["python", "-m", "pytest"]
        + test_files
        + [
            "-v",
            "--tb=short",
            "-x",  # Stop on first failure
        ]
    )

    result = subprocess.run(cmd, capture_output=False)

    if result.returncode != 0:
        print("\n❌ Tree validation tests FAILED!")
        print("Tree pipe rendering is broken. Please fix before committing.")
        print("\nAffected areas:")
        print("  - Tree formatting (├─, └─, │ characters)")
        print("  - Hierarchy command display")
        print("  - Tree alignment and spacing")
        return False

    print("\n✅ Tree validation tests PASSED!")
    return True


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
