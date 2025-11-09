#!/usr/bin/env python3
"""
Test Runner

Runs all ClickUp Framework tests and generates reports.
"""

import sys
import unittest
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_all_tests(verbosity=2):
    """Run all tests and return results."""
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(os.path.abspath(__file__))
    suite = loader.discover(start_dir, pattern="test_*.py")

    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)

    return result


def print_summary(result):
    """Print test summary."""
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")

    if result.wasSuccessful():
        print("\n✓ ALL TESTS PASSED")
    else:
        print("\n✗ SOME TESTS FAILED")

    print("=" * 80)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Run ClickUp Framework tests")
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Show API coverage report after tests"
    )
    parser.add_argument(
        "--coverage-only",
        action="store_true",
        help="Only show API coverage report (skip tests)"
    )

    args = parser.parse_args()

    verbosity = 2 if args.verbose else 1

    if args.coverage_only:
        # Just show coverage
        from coverage_tracker import print_coverage_report
        print_coverage_report()
        return 0

    # Run tests
    print("=" * 80)
    print("Running ClickUp Framework Tests")
    print("=" * 80)
    print()

    result = run_all_tests(verbosity=verbosity)
    print_summary(result)

    # Show coverage if requested
    if args.coverage:
        print("\n")
        from coverage_tracker import print_coverage_report
        print_coverage_report()

    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
