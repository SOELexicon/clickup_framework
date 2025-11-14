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


def save_json_reports(result):
    """Save test results to JSON files."""
    import json
    from datetime import datetime

    # Prepare test results data
    tests = []

    # Add failures
    for test, traceback in result.failures:
        tests.append({
            'nodeid': str(test),
            'outcome': 'failed',
            'call': {
                'longrepr': traceback
            },
            'duration': 0  # unittest doesn't track duration per test
        })

    # Add errors
    for test, traceback in result.errors:
        tests.append({
            'nodeid': str(test),
            'outcome': 'error',
            'call': {
                'longrepr': traceback
            },
            'duration': 0
        })

    # Create test report
    test_report = {
        'created': datetime.now().isoformat(),
        'duration': 0,
        'tests': tests,
        'summary': {
            'total': result.testsRun,
            'passed': result.testsRun - len(result.failures) - len(result.errors),
            'failed': len(result.failures),
            'error': len(result.errors),
            'skipped': len(result.skipped)
        }
    }

    # Save test report (only failures and errors)
    with open('test_report.json', 'w') as f:
        json.dump(test_report, f, indent=2)
    print(f"✓ Saved test report to test_report.json ({len(tests)} failures/errors)")

    # Save summary
    summary = {
        'timestamp': datetime.now().isoformat(),
        'tests_run': result.testsRun,
        'successes': result.testsRun - len(result.failures) - len(result.errors),
        'failures': len(result.failures),
        'errors': len(result.errors),
        'skipped': len(result.skipped),
        'success': result.wasSuccessful()
    }

    with open('test_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"✓ Saved test summary to test_summary.json")

    # Save detailed errors to separate file
    if result.failures or result.errors:
        errors_data = {
            'timestamp': datetime.now().isoformat(),
            'failures': [
                {
                    'test': str(test),
                    'traceback': traceback
                }
                for test, traceback in result.failures
            ],
            'errors': [
                {
                    'test': str(test),
                    'traceback': traceback
                }
                for test, traceback in result.errors
            ]
        }

        with open('test_errors.json', 'w') as f:
            json.dump(errors_data, f, indent=2)
        print(f"✓ Saved detailed errors to test_errors.json")


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

    # Save JSON reports
    save_json_reports(result)

    # Print summary
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
